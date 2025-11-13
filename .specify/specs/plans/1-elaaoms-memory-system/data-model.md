# Data Model: ELAAOMS Memory Management Platform

**Feature**: [1-elaaoms-memory-system](../features/1-elaaoms-memory-system.md)  
**Created**: 2024-12-19

## Overview

This document defines the data entities, relationships, validation rules, and state transitions for the ELAAOMS memory management platform. The data model is designed to support efficient memory storage, retrieval, and cross-agent sharing.

## Core Entities

### Caller

**Description**: Represents a customer who calls the AI agent system. Identified primarily by phone number (caller ID).

**Attributes**:
- `caller_id` (string, required, unique): Phone number or unique identifier
- `organization_id` (string, required): Organization this caller belongs to
- `first_seen_date` (datetime, required): First time this caller was seen
- `last_seen_date` (datetime, required): Most recent interaction timestamp
- `total_conversations` (integer, default: 0): Count of conversations with this caller

**Relationships**:
- Has many Conversations
- Has many Memories

**Validation Rules**:
- `caller_id` must be non-empty string
- `organization_id` must be non-empty string
- `first_seen_date` <= `last_seen_date`
- `total_conversations` >= 0

**Indexes**:
- Primary key: `caller_id`
- Index: `organization_id` (for organization-level queries)
- Index: `last_seen_date` (for recent caller queries)

**State Transitions**:
- Created when first call received
- Updated on each new conversation (increment `total_conversations`, update `last_seen_date`)

### Conversation

**Description**: Represents a single phone call conversation between a caller and an AI agent.

**Attributes**:
- `conversation_id` (string, required, unique): Unique identifier from ElevenLabs
- `agent_id` (string, required): AI agent identifier
- `caller_id` (string, required): Caller identifier
- `organization_id` (string, required): Organization identifier
- `start_time` (datetime, required): Conversation start timestamp
- `end_time` (datetime, optional): Conversation end timestamp
- `duration` (integer, optional): Duration in seconds
- `transcript` (text, optional): Full conversation transcript
- `status` (enum, required): One of: "initiated", "active", "completed", "failed", "extraction_pending", "extraction_completed", "extraction_failed"

**Relationships**:
- Belongs to Caller
- Belongs to Agent
- Belongs to Organization
- Has many Memories

**Validation Rules**:
- `conversation_id` must be non-empty string
- `agent_id` must be non-empty string
- `caller_id` must be non-empty string
- `start_time` must be valid datetime
- `end_time` must be >= `start_time` if provided
- `duration` must be >= 0 if provided
- `status` must be valid enum value

**Indexes**:
- Primary key: `conversation_id`
- Index: `caller_id` (for caller history queries)
- Index: `agent_id` (for agent-specific queries)
- Index: `organization_id` (for organization queries)
- Index: `start_time` (for time-based queries)
- Index: `status` (for status filtering)

**State Transitions**:
```
initiated → active → completed → extraction_pending → extraction_completed
                              ↓
                        extraction_failed
```
- `initiated`: Call started, webhook received
- `active`: Call in progress
- `completed`: Call ended, transcript received
- `extraction_pending`: Memory extraction job queued
- `extraction_completed`: Memories successfully extracted
- `extraction_failed`: Memory extraction failed after retries
- `failed`: Call initiation failed

### Memory

**Description**: Represents an extracted memory from a conversation. Stored in OpenMemory with vector embeddings for semantic search.

**Attributes**:
- `memory_id` (string, required, unique): Unique identifier from OpenMemory
- `caller_id` (string, required): Caller identifier
- `conversation_id` (string, required): Conversation identifier
- `agent_id` (string, optional): Agent identifier (null for cross-agent shared memories)
- `organization_id` (string, required): Organization identifier
- `content` (text, required): Memory content/text
- `type` (enum, required): One of: "factual", "preference", "issue", "emotion", "relationship"
- `importance_rating` (integer, required): Importance score 1-10
- `is_shareable` (boolean, required): Whether memory is shared across agents (importance >= 8)
- `created_timestamp` (datetime, required): When memory was first created
- `last_reinforced_timestamp` (datetime, optional): When memory was last reinforced
- `confidence_score` (float, optional): Confidence in memory accuracy (0.0-1.0)
- `reinforcement_count` (integer, default: 0): Number of times memory was reinforced
- `embedding` (vector, required): Vector embedding for semantic search
- `metadata` (json, optional): Additional metadata (source_quote, conflict_markers, etc.)

**Relationships**:
- Belongs to Caller
- Belongs to Conversation
- May belong to Agent (if agent-specific)
- May be shared across Agents (if is_shareable=true)

**Validation Rules**:
- `memory_id` must be non-empty string
- `caller_id` must be non-empty string
- `conversation_id` must be non-empty string
- `content` must be non-empty string (max 10,000 characters)
- `type` must be valid enum value
- `importance_rating` must be between 1 and 10
- `is_shareable` = true if `importance_rating` >= 8
- `confidence_score` must be between 0.0 and 1.0 if provided
- `reinforcement_count` >= 0
- `embedding` must be valid vector (dimension matches model)

**Indexes**:
- Primary key: `memory_id`
- Vector index: `embedding` (for semantic search)
- Index: `caller_id` (for caller memory queries)
- Index: `conversation_id` (for conversation memory queries)
- Index: `agent_id` (for agent-specific queries, nullable)
- Index: `organization_id` (for organization queries)
- Index: `type` (for type filtering)
- Index: `importance_rating` (for importance filtering)
- Index: `is_shareable` (for cross-agent queries)
- Index: `created_timestamp` (for time-based queries)

**State Transitions**:
- Created when memory extracted from transcript
- Reinforced when similar memory found (increment `reinforcement_count`, update `last_reinforced_timestamp`)
- Updated when importance rating changes (if crosses threshold 8, update `is_shareable`)

### Agent

**Description**: Represents an AI agent within an organization.

**Attributes**:
- `agent_id` (string, required, unique): Unique identifier from ElevenLabs
- `organization_id` (string, required): Organization identifier
- `name` (string, optional): Agent name
- `capabilities` (json, optional): Agent capabilities/configuration
- `profile_cached_at` (datetime, optional): When agent profile was last cached
- `profile_ttl_hours` (integer, default: 24): Cache TTL in hours

**Relationships**:
- Belongs to Organization
- Has many Conversations
- Can access shared Memories (importance >= 8/10)

**Validation Rules**:
- `agent_id` must be non-empty string
- `organization_id` must be non-empty string
- `profile_ttl_hours` > 0

**Indexes**:
- Primary key: `agent_id`
- Index: `organization_id` (for organization agent queries)

**State Transitions**:
- Created when first webhook received with agent_id
- Updated when agent profile refreshed from ElevenLabs API

### Organization

**Description**: Represents an organization using the ELAAOMS system.

**Attributes**:
- `organization_id` (string, required, unique): Unique identifier
- `name` (string, optional): Organization name
- `llm_provider` (enum, optional): Preferred LLM provider ("openai" or "anthropic")
- `privacy_settings` (json, optional): Privacy configuration (retention policies, sensitive data filters)
- `hmac_secret` (string, required): HMAC secret for webhook validation
- `created_at` (datetime, required): Organization creation timestamp

**Relationships**:
- Has many Agents
- Has many Callers
- Has many Conversations
- Has many Memories

**Validation Rules**:
- `organization_id` must be non-empty string
- `llm_provider` must be valid enum value if provided
- `hmac_secret` must be non-empty string (min 32 bytes for security)

**Indexes**:
- Primary key: `organization_id`

**State Transitions**:
- Created during system setup
- Updated when configuration changes

### Memory Search Query

**Description**: Represents a memory search request (ephemeral, not persisted).

**Attributes**:
- `query_text` (string, required): Search query text
- `caller_id` (string, required): Caller to search memories for
- `conversation_id` (string, optional): Current conversation ID
- `agent_id` (string, optional): Agent ID (for agent-specific search)
- `search_all_agents` (boolean, default: false): Whether to search across all agents
- `relevance_threshold` (float, default: 0.7): Minimum relevance score (0.0-1.0)
- `result_limit` (integer, default: 5): Maximum number of results
- `timestamp` (datetime, required): Query timestamp

**Relationships**:
- Returns ranked Memories

**Validation Rules**:
- `query_text` must be non-empty string (max 1000 characters)
- `caller_id` must be non-empty string
- `relevance_threshold` must be between 0.0 and 1.0
- `result_limit` must be between 1 and 100

## Entity Relationships

```
Organization
  ├── has many Agents
  ├── has many Callers
  ├── has many Conversations
  └── has many Memories

Caller
  ├── belongs to Organization
  ├── has many Conversations
  └── has many Memories

Conversation
  ├── belongs to Caller
  ├── belongs to Agent
  ├── belongs to Organization
  └── has many Memories

Memory
  ├── belongs to Caller
  ├── belongs to Conversation
  ├── may belong to Agent (optional)
  └── may be shared across Agents (if is_shareable=true)

Agent
  ├── belongs to Organization
  ├── has many Conversations
  └── can access shared Memories (importance >= 8)
```

## Data Validation Rules

### Cross-Entity Validation

1. **Referential Integrity**:
   - All `caller_id` references must exist in Caller table
   - All `conversation_id` references must exist in Conversation table
   - All `agent_id` references must exist in Agent table
   - All `organization_id` references must exist in Organization table

2. **Memory Sharing Rules**:
   - Memories with `importance_rating` >= 8 must have `is_shareable` = true
   - Shared memories can have `agent_id` = null or specific agent_id
   - Cross-agent search queries return memories where `is_shareable` = true

3. **Conversation Status Rules**:
   - Conversations with `status` = "completed" must have `end_time` and `duration`
   - Conversations with `status` = "extraction_completed" must have associated Memories
   - Failed conversations can have `status` = "extraction_failed" without Memories

4. **Timestamp Consistency**:
   - `last_reinforced_timestamp` >= `created_timestamp` for Memories
   - `end_time` >= `start_time` for Conversations
   - `last_seen_date` >= `first_seen_date` for Callers

## Data Storage Strategy

### OpenMemory Storage

**Memories** are stored in OpenMemory with:
- Vector embeddings for semantic search (cosine similarity)
- Metadata indexed for filtering (caller_id, agent_id, type, importance, etc.)
- Automatic deduplication based on semantic similarity (threshold: 0.85)

### File System Storage

**Conversation Payloads** are stored on disk:
- Path: `./data/payloads/{conversation_id}/`
- Files:
  - `{conversation_id}_transcription.json`: Full transcript
  - `{conversation_id}_audio.mp3`: Audio file (if provided)
  - `{conversation_id}_failure.json`: Failure information (if applicable)

### Caching Strategy

**Agent Profiles** are cached in-memory:
- TTL: 24 hours (configurable via `AGENT_PROFILE_TTL_HOURS`)
- Cache key: `agent_id`
- Invalidation: On profile update or TTL expiry

## Data Lifecycle

### Memory Lifecycle

1. **Creation**: Memory extracted from transcript during post-call processing
2. **Deduplication**: Check against existing memories using semantic similarity
3. **Storage**: Store new memory or reinforce existing memory
4. **Sharing**: Mark as shareable if importance >= 8
5. **Reinforcement**: Update when similar memory found in future conversations
6. **Deletion**: Manual deletion only (no automatic expiry)

### Conversation Lifecycle

1. **Initiated**: Webhook received, conversation created
2. **Active**: Call in progress
3. **Completed**: Call ended, transcript received
4. **Extraction Pending**: Memory extraction job queued
5. **Extraction Completed**: Memories successfully extracted
6. **Extraction Failed**: Extraction failed after retries, transcript saved for manual processing

## Query Patterns

### Pre-Call Context Retrieval

**Query**: Get recent memories for caller
- Filter: `caller_id` = {caller_id}
- Sort: By `created_timestamp` DESC
- Limit: Top 10 most recent
- Include: Cross-agent shared memories (`is_shareable` = true)

### Memory Search

**Query**: Semantic search for memories
- Vector search: Query embedding vs memory embeddings
- Filter: `caller_id` = {caller_id}
- Optional filter: `agent_id` = {agent_id} (if not searching all agents)
- Filter: `relevance_score` >= {threshold}
- Sort: By relevance score DESC
- Limit: Top N results (default: 5)

### Deduplication Check

**Query**: Find similar existing memories
- Vector search: New memory embedding vs existing memory embeddings
- Filter: `caller_id` = {caller_id}
- Filter: `similarity_score` >= 0.85
- Return: Most similar memory if found

## Data Migration & Backups

### Backup Strategy

- **OpenMemory**: PostgreSQL backups (daily)
- **File System**: Payload backups to S3/Cloud Storage (daily)
- **Configuration**: Environment variables backed up to secrets manager

### Migration Considerations

- Vector embeddings must be regenerated if embedding model changes
- Memory deduplication may need recalculation if similarity threshold changes
- Organization-level data isolation must be maintained during migrations

