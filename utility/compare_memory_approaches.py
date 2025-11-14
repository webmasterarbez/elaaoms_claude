#!/usr/bin/env python3
"""
Compare different memory extraction approaches for a conversation.

This script retrieves and compares memories created by:
1. Direct /memory/add (full transcript)
2. Chunked /memory/add (interaction-level)
3. Current LLM extraction approach

Usage:
    python utility/compare_memory_approaches.py <conversation_id>
    python utility/compare_memory_approaches.py conv_01k04qved0ej19h9h0ddcgqnbz

Environment Variables:
    OPENMEMORY_API_URL: OpenMemory API URL (default: http://localhost:8080)
    OPENMEMORY_API_KEY: OpenMemory API key (optional, for authentication)
"""

import os
import sys
import json
import logging
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import Counter, defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_env_file() -> None:
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    value = value.strip('"').strip("'")
                    os.environ[key.strip()] = value
        logger.debug("Loaded environment variables from .env file")


def load_conversation_payload(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Load conversation payload to extract caller_id."""
    payload_path = Path(__file__).parent.parent / "backend" / "data" / "payloads" / conversation_id
    transcript_file = payload_path / f"{conversation_id}_transcription.json"
    
    if not transcript_file.exists():
        logger.error(f"Conversation file not found: {transcript_file}")
        return None
    
    try:
        with open(transcript_file, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Error loading conversation payload: {e}")
        return None


def get_caller_id(payload: Dict[str, Any]) -> Optional[str]:
    """Extract caller_id from payload."""
    dynamic_vars = payload.get("data", {}).get("conversation_initiation_client_data", {}).get("dynamic_variables", {})
    if not dynamic_vars:
        dynamic_vars = payload.get("data", {}).get("dynamic_variables", {})
    return dynamic_vars.get("system__caller_id")


def query_memories_by_tags(api_url: str, api_key: str, caller_id: str, conversation_id: str) -> List[Dict[str, Any]]:
    """
    Query OpenMemory for all memories related to this conversation.
    
    Returns memories tagged with test approaches or conversation_id.
    """
    headers = {
        "Content-Type": "application/json"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    # Query for all memories for this user
    payload = {
        "query": "",  # Empty query to get all memories
        "k": 1000,
        "filters": {
            "user_id": caller_id
        }
    }
    
    try:
        response = requests.post(
            f"{api_url}/memory/query",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"Query failed: {response.status_code} - {response.text}")
            return []
        
        result = response.json()
        memory_list = result.get("matches", [])
        
        # Fetch full memory details (including metadata) for each memory
        memories = []
        for mem in memory_list:
            memory_id = mem.get("id")
            if not memory_id:
                continue
            
            try:
                mem_response = requests.get(
                    f"{api_url}/memory/{memory_id}",
                    headers=headers,
                    timeout=10
                )
                if mem_response.status_code == 200:
                    full_memory = mem_response.json()
                    full_memory["score"] = mem.get("score")
                    full_memory["salience"] = mem.get("salience")
                    memories.append(full_memory)
            except Exception as e:
                logger.warning(f"Failed to fetch memory {memory_id}: {e}")
        
        return memories
        
    except Exception as e:
        logger.error(f"Error querying memories: {e}", exc_info=True)
        return []


def categorize_memories(memories: List[Dict[str, Any]], conversation_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Categorize memories by extraction approach.
    
    Returns:
        Dict with keys: 'direct_add', 'chunked_add', 'llm_extraction', 'other'
    """
    categorized = {
        "direct_add": [],
        "chunked_add": [],
        "llm_extraction": [],
        "ingest": [],
        "other": []
    }
    
    for mem in memories:
        metadata = mem.get("metadata", {})
        if not isinstance(metadata, dict):
            continue
        
        # Check for test approach tags
        test_approach = metadata.get("test_approach", "")
        conv_id = metadata.get("conversation_id", "")
        
        # Also check tags
        tags = mem.get("tags", [])
        if isinstance(tags, list):
            for tag in tags:
                if tag.startswith("test_"):
                    test_approach = tag.replace("test_", "")
                    break
        
        # Categorize
        if test_approach == "direct_add" or (conv_id == conversation_id and len(mem.get("content", "")) > 20000):
            categorized["direct_add"].append(mem)
        elif test_approach == "chunked_add":
            categorized["chunked_add"].append(mem)
        elif test_approach == "ingest":
            categorized["ingest"].append(mem)
        elif conv_id == conversation_id and metadata.get("extraction_method") == "llm_extraction":
            categorized["llm_extraction"].append(mem)
        elif conv_id == conversation_id:
            categorized["other"].append(mem)
    
    return categorized


def analyze_memory_group(memories: List[Dict[str, Any]], group_name: str) -> Dict[str, Any]:
    """Analyze a group of memories and return statistics."""
    if not memories:
        return {
            "count": 0,
            "message": f"No memories found for {group_name}"
        }
    
    # Sector distribution
    sectors = []
    primary_sectors = []
    for mem in memories:
        mem_sectors = mem.get("sectors", [])
        if isinstance(mem_sectors, list):
            sectors.extend(mem_sectors)
        primary = mem.get("primary_sector")
        if primary:
            primary_sectors.append(primary)
    
    sector_counts = Counter(primary_sectors)
    
    # Content analysis
    content_lengths = [len(mem.get("content", "")) for mem in memories]
    avg_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
    min_length = min(content_lengths) if content_lengths else 0
    max_length = max(content_lengths) if content_lengths else 0
    
    # Sample content (first few memories)
    sample_contents = [mem.get("content", "")[:200] + "..." if len(mem.get("content", "")) > 200 else mem.get("content", "") 
                      for mem in memories[:5]]
    
    return {
        "count": len(memories),
        "sector_distribution": dict(sector_counts),
        "primary_sectors": dict(Counter(primary_sectors)),
        "content_stats": {
            "avg_length": round(avg_length, 1),
            "min_length": min_length,
            "max_length": max_length,
            "total_chars": sum(content_lengths)
        },
        "sample_contents": sample_contents,
        "memory_ids": [mem.get("id") for mem in memories[:10]]
    }


def print_comparison_report(categorized: Dict[str, List[Dict[str, Any]]], conversation_id: str):
    """Print a comprehensive comparison report."""
    print("\n" + "=" * 80)
    print(f"MEMORY EXTRACTION APPROACH COMPARISON")
    print(f"Conversation: {conversation_id}")
    print("=" * 80)
    
    # Analyze each approach
    analyses = {}
    for approach, memories in categorized.items():
        analyses[approach] = analyze_memory_group(memories, approach)
    
    # Summary table
    print("\n📊 SUMMARY")
    print("-" * 80)
    print(f"{'Approach':<20} {'Count':<10} {'Avg Length':<15} {'Sectors':<35}")
    print("-" * 80)
    
    approach_names = {
        "direct_add": "Direct Add (Full)",
        "chunked_add": "Chunked Add",
        "llm_extraction": "LLM Extraction",
        "ingest": "Multimodal Ingest",
        "other": "Other"
    }
    
    for approach, analysis in analyses.items():
        if analysis["count"] == 0:
            continue
        
        name = approach_names.get(approach, approach)
        count = analysis["count"]
        avg_len = analysis["content_stats"]["avg_length"]
        sectors = ", ".join([f"{k}({v})" for k, v in list(analysis["sector_distribution"].items())[:3]])
        
        print(f"{name:<20} {count:<10} {avg_len:<15.1f} {sectors:<35}")
    
    # Detailed analysis for each approach
    print("\n" + "=" * 80)
    print("DETAILED ANALYSIS")
    print("=" * 80)
    
    for approach, analysis in analyses.items():
        if analysis["count"] == 0:
            continue
        
        name = approach_names.get(approach, approach)
        print(f"\n🔍 {name.upper()}")
        print("-" * 80)
        print(f"Total Memories: {analysis['count']}")
        print(f"\nSector Distribution:")
        for sector, count in sorted(analysis["sector_distribution"].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / analysis["count"]) * 100
            print(f"  {sector:15} {count:4} ({percentage:5.1f}%)")
        
        print(f"\nContent Statistics:")
        stats = analysis["content_stats"]
        print(f"  Average length: {stats['avg_length']:.1f} characters")
        print(f"  Min length:     {stats['min_length']} characters")
        print(f"  Max length:     {stats['max_length']} characters")
        print(f"  Total content:  {stats['total_chars']:,} characters")
        
        if analysis["sample_contents"]:
            print(f"\nSample Contents (first {len(analysis['sample_contents'])}):")
            for i, content in enumerate(analysis["sample_contents"], 1):
                print(f"  {i}. {content}")
        
        if analysis["memory_ids"]:
            print(f"\nMemory IDs (first {len(analysis['memory_ids'])}):")
            for i, mem_id in enumerate(analysis["memory_ids"][:5], 1):
                print(f"  {i}. {mem_id}")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)
    
    chunked_count = analyses.get("chunked_add", {}).get("count", 0)
    llm_count = analyses.get("llm_extraction", {}).get("count", 0)
    direct_count = analyses.get("direct_add", {}).get("count", 0)
    
    if chunked_count > 0:
        chunked_sectors = analyses.get("chunked_add", {}).get("sector_distribution", {})
        print(f"\n✅ Chunked Add Approach:")
        print(f"   - Created {chunked_count} memories")
        print(f"   - Good sector distribution: {len(chunked_sectors)} different sectors")
        print(f"   - Best for: Creating many searchable memories with automatic sector classification")
    
    if llm_count > 0:
        llm_sectors = analyses.get("llm_extraction", {}).get("sector_distribution", {})
        print(f"\n✅ LLM Extraction Approach:")
        print(f"   - Created {llm_count} memories")
        print(f"   - Sector distribution: {len(llm_sectors)} different sectors")
        print(f"   - Best for: Structured, atomic fact extraction with custom importance levels")
    
    if direct_count > 0:
        print(f"\n⚠️  Direct Add (Full) Approach:")
        print(f"   - Created only {direct_count} memory (entire transcript)")
        print(f"   - Not recommended: Too large, less searchable")
    
    print("\n" + "=" * 80)


def main():
    """Main entry point."""
    load_env_file()
    
    if len(sys.argv) < 2:
        logger.error("Usage: python utility/compare_memory_approaches.py <conversation_id>")
        sys.exit(1)
    
    conversation_id = sys.argv[1]
    
    logger.info(f"Comparing memory extraction approaches for conversation: {conversation_id}")
    
    # Load conversation to get caller_id
    payload = load_conversation_payload(conversation_id)
    if not payload:
        logger.error(f"Failed to load conversation payload")
        sys.exit(1)
    
    caller_id = get_caller_id(payload)
    if not caller_id:
        logger.error("Could not extract caller_id from payload")
        sys.exit(1)
    
    logger.info(f"Caller ID: {caller_id}")
    
    # Get API configuration
    api_url = os.getenv("OPENMEMORY_API_URL", "http://localhost:8080").rstrip("/")
    api_key = os.getenv("OPENMEMORY_API_KEY", "")
    
    # Query memories
    logger.info("Querying OpenMemory for memories...")
    all_memories = query_memories_by_tags(api_url, api_key, caller_id, conversation_id)
    logger.info(f"Found {len(all_memories)} total memories for caller {caller_id}")
    
    # Categorize memories
    categorized = categorize_memories(all_memories, conversation_id)
    
    # Print counts
    print("\n" + "=" * 80)
    print("MEMORY COUNTS BY APPROACH")
    print("=" * 80)
    for approach, memories in categorized.items():
        print(f"{approach:20} {len(memories):4} memories")
    
    # Generate comparison report
    print_comparison_report(categorized, conversation_id)
    
    # Save detailed results to file
    output_dir = Path(__file__).parent.parent / "data" / "memory_comparisons"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"comparison_{conversation_id}.json"
    
    results = {
        "conversation_id": conversation_id,
        "caller_id": caller_id,
        "timestamp": str(Path(__file__).stat().st_mtime),
        "approaches": {}
    }
    
    for approach, memories in categorized.items():
        if memories:
            results["approaches"][approach] = {
                "count": len(memories),
                "analysis": analyze_memory_group(memories, approach),
                "memory_ids": [mem.get("id") for mem in memories]
            }
    
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    main()

