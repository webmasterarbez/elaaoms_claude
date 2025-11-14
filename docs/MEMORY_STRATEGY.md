# Memory Storage & Retrieval Strategy

## Executive Summary

This document outlines an optimized strategy for storing and retrieving conversation memories that:
- **Saves all important memories** without duplicates
- **Enables fast retrieval** during live calls (<500ms)
- **Scales efficiently** as memory count grows
- **Maintains data quality** with structured, searchable content

## Current System Analysis

### Performance Issues Identified

1. **Low Memory Extraction Rate**
   - Current: 2 memories from 293-item conversation (0.7% coverage)
   - Target: 20-50+ memories per conversation
   - Issue: LLM prompt too conservative, extracts too few facts

2. **Inefficient Deduplication**
   - Current: One-by-one semantic similarity checks (N API calls)
   - Issue: Slow, expensive, rate-limited
   - Impact: 58 memories took ~4 seconds, hit rate limits

3. **No Caching Layer**
   - Current: Every call queries OpenMemory directly
   - Issue: Network latency, API rate limits
   - Impact: Slow retrieval during calls

4. **Mixed Content Quality**
   - Chunked approach: Raw dialogue (not searchable facts)
   - LLM approach: Structured facts (but too few)
   - Issue: No unified strategy

## Proposed Strategy: Hybrid Two-Tier System

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CONVERSATION TRANSCRIPT                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   ENHANCED LLM EXTRACTION      │
        │   (20-50+ structured facts)    │
        └───────────────┬───────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌───────────────┐              ┌───────────────┐
│  TIER 1:      │              │  TIER 2:      │
│  STRUCTURED   │              │  CONTEXT      │
│  MEMORIES     │              │  CHUNKS       │
│               │              │               │
│ - Atomic facts│              │ - Full turns  │
│ - Searchable  │              │ - Reference   │
│ - Fast access │              │ - Less frequent│
└───────────────┘              └───────────────┘
        │                               │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   SMART DEDUPLICATION         │
        │   (Batch + Hash-based)        │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   OPENMEMORY STORAGE          │
        │   (With metadata indexing)    │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   CACHE LAYER                 │
        │   (Recent memories)           │
        └───────────────────────────────┘
```

## Implementation Strategy

### Phase 1: Enhanced LLM Extraction

**Goal**: Extract 20-50+ structured memories per conversation

**Changes**:
1. **Enhanced Prompt**:
   - Target: "Extract 20-50+ atomic facts"
   - Explicitly request HSG sector classification
   - Request importance scores for all facts
   - Emphasize comprehensiveness over brevity

2. **Multi-Pass Extraction**:
   - Pass 1: Extract obvious facts (names, dates, preferences)
   - Pass 2: Extract implicit facts (emotions, relationships, patterns)
   - Pass 3: Extract contextual facts (background, history)

3. **Chunking Strategy**:
   - Split large transcripts into 10-15 message chunks
   - Extract from each chunk independently
   - Merge and deduplicate results

**Expected Output**: 20-50 structured memories per conversation

### Phase 2: Smart Deduplication

**Goal**: Fast, efficient duplicate detection without API overhead

**Strategy**:

1. **Content Hash Check** (Instant - O(1)):
   ```python
   import hashlib
   
   def get_content_hash(content: str) -> str:
       # Normalize: lowercase, strip whitespace, remove punctuation
       normalized = content.lower().strip()
       return hashlib.sha256(normalized.encode()).hexdigest()
   ```
   - Store hash in metadata: `metadata.content_hash`
   - Check hash before semantic search
   - Exact duplicates: instant detection

2. **Batch Semantic Search** (Fast - 1 API call):
   ```python
   # Instead of N individual searches, batch check:
   all_extracted_contents = [m["content"] for m in memories]
   similar_memories = await batch_semantic_search(
       user_id=caller_id,
       queries=all_extracted_contents,
       threshold=0.85
   )
   ```
   - Single API call for all memories
   - OpenMemory supports batch queries
   - Map results back to extracted memories

3. **Deduplication Logic**:
   ```python
   for memory in extracted_memories:
       # Step 1: Check exact hash match
       if hash_exists(memory.content_hash):
           reinforce_existing(memory)
           continue
       
       # Step 2: Check semantic similarity (from batch results)
       similar = find_similar_in_batch_results(memory, similar_memories)
       if similar and similarity_score >= 0.85:
           reinforce_existing(similar)
           continue
       
       # Step 3: Store new memory
       store_new_memory(memory)
   ```

**Performance**: 
- Current: N API calls (58 calls = ~4 seconds + rate limits)
- Proposed: 1 batch call + hash lookups (~200ms)

### Phase 3: Two-Tier Storage

**Tier 1: Structured Memories (Primary)**
- **Content**: LLM-extracted atomic facts
- **Format**: Structured, searchable, with metadata
- **Access**: Fast, frequently queried
- **Examples**:
  - "Ken grew up in Richfield, Minnesota"
  - "Ken prefers express shipping"
  - "Ken's favorite car brand is Ford"

**Tier 2: Context Chunks (Secondary)**
- **Content**: Full conversation turns (user/agent pairs)
- **Format**: Raw dialogue chunks
- **Access**: Less frequent, for reference
- **Use Case**: When structured memory needs context
- **Storage**: Only for conversations >50 turns

**Benefits**:
- Structured memories: Fast search, clean results
- Context chunks: Full conversation preserved
- Separation: Different access patterns, different storage

### Phase 4: Caching Layer

**Goal**: Sub-500ms memory retrieval during calls

**Strategy**:

1. **In-Memory Cache** (Redis or local):
   ```python
   # Cache structure
   cache_key = f"memories:{caller_id}:{agent_id}"
   cache_value = {
       "memories": [...],  # Recent memories
       "timestamp": ...,   # Cache timestamp
       "ttl": 3600         # 1 hour TTL
   }
   ```

2. **Cache Population**:
   - On memory storage: Invalidate cache
   - On call start: Pre-fetch recent memories
   - Background: Refresh cache every 5 minutes

3. **Cache Strategy**:
   - **Recent Memories**: Last 50 memories (fast access)
   - **Frequent Queries**: Cached search results
   - **Agent Context**: Pre-loaded for active calls

4. **Fallback**:
   - Cache miss → Query OpenMemory
   - Update cache for next time

**Performance**:
- Cache hit: <50ms (in-memory)
- Cache miss: ~200ms (OpenMemory query)
- Target: 90%+ cache hit rate

### Phase 5: Metadata Indexing

**Goal**: Fast filtering without full-text search

**Strategy**:

1. **Rich Metadata**:
   ```json
   {
     "content": "Ken prefers express shipping",
     "metadata": {
       "caller_id": "+16124833213",
       "agent_id": "agent_xyz",
       "conversation_id": "conv_abc",
       "content_hash": "sha256_hash",
       "category": "preference",
       "importance": 7,
       "sector": "semantic",
       "entities": ["Ken", "shipping"],
       "extracted_at": "2025-11-14T08:00:00Z",
       "type": "conversation_memory"
     },
     "tags": ["preference", "shipping", "express"]
   }
   ```

2. **Indexed Fields**:
   - `metadata.conversation_id` → Fast conversation lookup
   - `metadata.content_hash` → Instant duplicate check
   - `metadata.importance` → Filter by importance
   - `metadata.sector` → Filter by HSG sector
   - `tags` → Fast tag-based filtering

3. **Query Optimization**:
   ```python
   # Fast: Metadata filter + semantic search
   memories = await search_memories(
       user_id=caller_id,
       query="shipping preference",
       filters={
           "metadata.importance": {"$gte": 5},
           "metadata.sector": "semantic"
       }
   )
   ```

## Performance Targets

### Storage Performance
- **Memory Extraction**: <30 seconds for 293-item conversation
- **Deduplication**: <500ms for 50 memories (batch)
- **Storage**: <2 seconds for 50 memories (batch API)

### Retrieval Performance
- **Cache Hit**: <50ms (in-memory)
- **Cache Miss**: <200ms (OpenMemory query)
- **Search Query**: <300ms (with metadata filters)
- **Pre-call Context**: <500ms (cached recent memories)

### Scalability
- **Memory Growth**: Linear with conversation count
- **Query Performance**: Constant time with caching
- **Deduplication**: O(N) with batch operations

## Implementation Plan

### Step 1: Enhance LLM Extraction (Week 1)
- [ ] Update prompt to target 20-50+ memories
- [ ] Add HSG sector classification
- [ ] Implement multi-pass extraction
- [ ] Test with sample conversations

### Step 2: Implement Smart Deduplication (Week 1-2)
- [ ] Add content hash to metadata
- [ ] Implement batch semantic search
- [ ] Update deduplication logic
- [ ] Test performance improvements

### Step 3: Add Caching Layer (Week 2)
- [ ] Set up Redis or in-memory cache
- [ ] Implement cache population logic
- [ ] Add cache invalidation
- [ ] Test cache hit rates

### Step 4: Two-Tier Storage (Week 2-3)
- [ ] Separate structured vs context storage
- [ ] Update storage logic
- [ ] Test retrieval performance
- [ ] Monitor storage growth

### Step 5: Optimization & Monitoring (Week 3-4)
- [ ] Add performance monitoring
- [ ] Optimize query patterns
- [ ] Tune cache TTLs
- [ ] Document best practices

## Expected Outcomes

### Memory Coverage
- **Before**: 2 memories from 293-item conversation (0.7%)
- **After**: 30-50 memories from 293-item conversation (10-17%)
- **Improvement**: 15-25x increase

### Performance
- **Deduplication**: 4 seconds → 200ms (20x faster)
- **Retrieval**: 500ms → 50ms (10x faster with cache)
- **Storage**: Sequential → Batch (5x faster)

### Data Quality
- **Structured**: All memories are atomic, searchable facts
- **No Duplicates**: Hash + semantic deduplication
- **Fast Access**: Cached recent memories
- **Comprehensive**: 20-50+ memories per conversation

## Risk Mitigation

### Risk 1: LLM Extraction Quality
- **Mitigation**: Multi-pass extraction, validation rules
- **Fallback**: Store transcript chunks if extraction fails

### Risk 2: Cache Invalidation
- **Mitigation**: Event-driven invalidation, TTL fallback
- **Monitoring**: Cache hit rate alerts

### Risk 3: Batch API Limits
- **Mitigation**: Chunk batch requests, retry logic
- **Fallback**: Sequential processing if batch fails

### Risk 4: Storage Growth
- **Mitigation**: Two-tier storage, archive old context chunks
- **Monitoring**: Storage size alerts

## Success Metrics

1. **Memory Coverage**: >10% of conversation content extracted
2. **Deduplication Speed**: <500ms for 50 memories
3. **Retrieval Speed**: <200ms for cached queries
4. **Cache Hit Rate**: >90% for recent memories
5. **Storage Efficiency**: <5% duplicate memories

## Conclusion

This hybrid two-tier strategy provides:
- ✅ **Comprehensive coverage**: 20-50+ memories per conversation
- ✅ **Fast retrieval**: <500ms with caching
- ✅ **No duplicates**: Hash + semantic deduplication
- ✅ **Scalable**: Batch operations, efficient storage
- ✅ **High quality**: Structured, searchable facts

The strategy balances comprehensiveness with performance, ensuring all important memories are captured while maintaining fast access during live calls.

