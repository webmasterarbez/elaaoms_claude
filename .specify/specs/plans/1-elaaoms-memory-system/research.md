# Research & Technology Decisions: ELAAOMS Memory Management Platform

**Feature**: [1-elaaoms-memory-system](../features/1-elaaoms-memory-system.md)  
**Created**: 2024-12-19

## Technology Stack Decisions

### Backend Framework: FastAPI 0.104.1

**Decision**: Use Python 3.10+ with FastAPI 0.104.1

**Rationale**:
- Native async/await support for concurrent webhook handling (critical for <2s response times)
- Automatic OpenAPI/Swagger documentation generation reduces maintenance overhead
- Built-in Pydantic integration for type-safe request/response validation
- Excellent performance for I/O-bound operations (API calls, database queries)
- Dependency injection system simplifies service integration and testing
- Active community and comprehensive documentation

**Alternatives Considered**:
- **Flask**: Lacks native async support, would require additional async libraries
- **Django**: Over-engineered for API-only service, heavier resource footprint
- **Tornado**: Lower-level async framework, more boilerplate required
- **Starlette**: FastAPI is built on Starlette but adds validation and docs

**Best Practices Applied**:
- Use async endpoints for all I/O operations
- Leverage FastAPI's automatic request validation
- Utilize dependency injection for service clients
- Enable CORS for cross-origin requests

### API Server: Uvicorn 0.24.0

**Decision**: Use Uvicorn as ASGI server

**Rationale**:
- Production-ready async server with excellent performance
- Graceful shutdowns and worker process management
- Supports HTTP/1.1 and HTTP/2
- Recommended by FastAPI documentation
- Easy configuration via command line or programmatic API

**Alternatives Considered**:
- **Gunicorn with Uvicorn workers**: More complex, not needed for single-service deployment
- **Hypercorn**: Alternative ASGI server, less mature ecosystem

### Data Validation: Pydantic 2.5.0

**Decision**: Use Pydantic 2.5.0 for request/response models

**Rationale**:
- Type-safe models with automatic validation and serialization
- Version 2.x provides 5-50x performance improvements over 1.x
- Automatic OpenAPI schema generation
- Excellent error messages for validation failures
- Native support for complex types (Optional, List, Dict, etc.)

**Best Practices Applied**:
- Use Field() for required fields with descriptions
- Include json_schema_extra examples in model Config
- Validate all webhook payloads before processing

### Memory Storage: OpenMemory (PostgreSQL-backed)

**Decision**: Use OpenMemory for memory storage and retrieval

**Rationale**:
- Purpose-built for conversational AI memory management
- Built-in semantic search using vector embeddings
- Automatic deduplication and reinforcement capabilities
- PostgreSQL backend provides ACID compliance and proven reliability
- Docker image simplifies deployment (caviraoss/openmemory:latest)
- RESTful API for easy integration

**Alternatives Considered**:
- **Direct PostgreSQL with pgvector**: More implementation work, no built-in deduplication
- **Pinecone/Weaviate**: Managed services, additional cost and vendor lock-in
- **Redis with vector search**: Not designed for persistent memory storage

**Best Practices Applied**:
- Index memories by caller_id, agent_id, conversation_id
- Use semantic similarity for deduplication (cosine similarity >0.85)
- Implement connection pooling for database queries
- Handle service unavailability gracefully with local queue

### LLM Providers: Multi-Provider Support

**Decision**: Support both OpenAI and Anthropic with abstraction layer

**Rationale**:
- Flexibility to choose cost-effective or high-quality models
- OpenAI GPT-4 Turbo: 128K context, high accuracy, fast responses
- Anthropic Claude: 200K context, nuanced understanding, alternative pricing
- Abstraction layer allows switching providers without code changes
- Fallback capability if one provider fails

**Model Selection Strategy**:
- Default: OpenAI GPT-4 Turbo for memory extraction (high accuracy)
- Alternative: Anthropic Claude 3 Opus/Sonnet (longer context, nuanced understanding)
- Configurable per organization or globally via LLM_PROVIDER environment variable

**Best Practices Applied**:
- Unified interface: extract_memories(transcript, agent_profile) → List[Memory]
- Structured output using function calling / tools
- Retry logic with exponential backoff (3 attempts: 1min, 5min, 30min)
- Timeout configuration (30 seconds for LLM calls)

### HTTP Client: HTTPX 0.25.2

**Decision**: Use HTTPX for async HTTP requests

**Rationale**:
- Modern async HTTP client with connection pooling
- Built-in timeout handling and retry logic
- Better async support than requests library
- Compatible with FastAPI's async patterns
- Supports HTTP/2

**Alternatives Considered**:
- **requests**: Synchronous, blocks event loop
- **aiohttp**: More complex API, HTTPX is simpler

### Security: HMAC-SHA256 Validation

**Decision**: Use HMAC-SHA256 for webhook signature validation

**Rationale**:
- Industry-standard webhook authentication
- Prevents unauthorized access and replay attacks
- ElevenLabs-compatible signature format: "t=timestamp,v0=hash"
- 30-minute timestamp tolerance prevents replay attacks while allowing clock skew
- Constant-time comparison prevents timing attacks

**Implementation Pattern**:
1. Extract elevenlabs-signature header
2. Parse format: "t={timestamp},v0={signature}"
3. Validate timestamp is within 30 minutes
4. Reconstruct signed payload: "{timestamp}.{raw_body}"
5. Compute HMAC-SHA256 using shared secret
6. Compare computed signature with provided signature (constant-time)
7. Reject with 401 if validation fails

### Development Tunnel: Pyngrok 7.4.1

**Decision**: Use Pyngrok for local development webhook testing

**Rationale**:
- Programmatic ngrok integration
- Auto-generates public URLs without manual ngrok CLI management
- Simplifies local development workflow
- Free tier sufficient for development

## Architecture Patterns

### Three-Tier Architecture

**Decision**: Implement API Layer, Service Layer, Data Layer separation

**Rationale**:
- Clear separation of concerns
- Easier testing and maintenance
- Scalable architecture pattern
- Standard industry practice

**Layer Responsibilities**:
1. **API Layer (FastAPI)**: Webhook endpoints, request validation, authentication
2. **Service Layer**: Business logic, LLM integration, memory extraction
3. **Data Layer**: OpenMemory API client, PostgreSQL persistence

### Request/Response Wrapper Pattern

**Decision**: Use consistent response structure across all endpoints

**Rationale**:
- Standardized error handling
- Easier client-side integration
- Consistent logging and tracing
- Better debugging experience

**Structure**:
```json
{
  "status": "success" | "error",
  "message": "Human-readable description",
  "request_id": "UUID for tracing",
  "data": { /* Payload-specific information */ }
}
```

### Background Job Processing

**Decision**: Use ThreadPoolExecutor for async memory extraction

**Rationale**:
- Avoids blocking webhook response
- Simple implementation for initial version
- Sufficient for 100 concurrent requests target
- Can migrate to Celery/RQ for production scale

**Future Enhancement**:
- Celery with Redis/RabbitMQ for distributed job processing
- Job persistence and retry mechanisms
- Priority queues for high-importance memories

## Performance Optimization Strategies

### Async Operations

**Decision**: Use async/await for all I/O operations

**Rationale**:
- Non-blocking I/O improves concurrency
- Better resource utilization
- Required for <2s and <3s response time targets

**Implementation**:
- FastAPI async endpoints
- HTTPX async client
- Database connection pooling

### Parallel Processing

**Decision**: Run independent operations concurrently

**Rationale**:
- Reduces total response time
- Better resource utilization
- Critical for meeting performance targets

**Examples**:
- Agent profile fetch and memory search run concurrently
- Multiple background jobs process simultaneously
- Batch API calls when possible

### Caching Strategy

**Decision**: Cache agent profiles for 24 hours (configurable)

**Rationale**:
- Reduces API calls to ElevenLabs
- Improves response time for pre-call context
- Agent profiles change infrequently

**Implementation**:
- In-memory Python dictionary with TTL checking
- Cache invalidation on profile update (future enhancement)

## Security & Privacy Decisions

### Authentication Model

**Decision**: Trust agents based on organization membership only (no additional authentication)

**Rationale**:
- Simplified architecture for initial version
- HMAC validation ensures webhook authenticity
- Organization-level isolation provides security boundary
- Can add role-based access control in future if needed

### Data Retention

**Decision**: Manual deletion only, no automatic expiry deletion

**Rationale**:
- Organizations have defined retention policies
- Manual deletion provides explicit control
- Avoids accidental data loss
- Supports GDPR compliance with explicit deletion requests

### Privacy Controls

**Decision**: Implement configurable privacy filters for sensitive information

**Rationale**:
- Prevents inadvertent storage of PII, payment details, health information
- Organizations can define custom privacy rules
- Sensitive memories flagged and require special access
- Audit logs track all access to sensitive memories

## Scalability Decisions

### Horizontal Scaling

**Decision**: Stateless FastAPI instances behind load balancer

**Rationale**:
- Stateless design enables horizontal scaling
- Shared PostgreSQL database for OpenMemory
- Can add Redis for distributed caching
- Message queue for background jobs at scale

### Database Scaling

**Decision**: PostgreSQL read replicas for query scaling

**Rationale**:
- Read-heavy workload (memory searches, context retrieval)
- Read replicas distribute query load
- Connection pooling limits database connections
- Indexed queries on caller_id, agent_id, conversation_id

## Integration Patterns

### ElevenLabs Integration

**Decision**: Three webhook endpoints for different call phases

**Rationale**:
- Pre-call: Personalization before conversation starts
- In-call: Real-time memory search during conversation
- Post-call: Memory extraction after conversation ends

**Configuration Requirements**:
- Enable "Client Data" webhook
- Enable "Server Tools" for memory search
- Configure system__caller_id dynamic variable
- Set matching HMAC secret

### OpenMemory Integration

**Decision**: RESTful API client with error handling

**Rationale**:
- Simple integration pattern
- Standard HTTP operations
- Graceful degradation if service unavailable
- Future: Fallback to local storage

### LLM Provider Integration

**Decision**: Abstraction layer with unified interface

**Rationale**:
- Provider-agnostic code
- Easy to switch providers
- Support multiple providers simultaneously
- Configurable per organization

**Interface**:
```python
async def extract_memories(
    transcript: str,
    agent_profile: dict
) -> List[Memory]:
    """Extract memories from transcript using LLM"""
```

## Edge Case Handling Strategies

### Missing Caller ID

**Decision**: Proceed with generic greeting, still extract memories

**Rationale**:
- Doesn't block conversation flow
- Memories can be linked later if caller ID becomes available
- Future: Use voice biometrics or other identifiers

### Long Conversations

**Decision**: Chunk transcripts >10,000 tokens, extract per chunk, deduplicate

**Rationale**:
- LLM context limits require chunking
- Maintains context with sliding window
- Deduplication ensures no duplicate memories across chunks

### LLM API Failures

**Decision**: 3 retries with exponential backoff, then save transcript for manual processing

**Rationale**:
- Transient failures are common
- Exponential backoff prevents overwhelming API
- Manual processing ensures no data loss
- Alert operations team on repeated failures

### Concurrent Calls

**Decision**: Use conversation_id as unique identifier, database transactions for locking

**Rationale**:
- Prevents race conditions in memory storage
- Eventually consistent memory view acceptable
- Database transactions ensure data integrity

## Monitoring & Observability

### Health Checks

**Decision**: /health endpoint checks OpenMemory connectivity

**Rationale**:
- Load balancer health checks
- Docker healthcheck directives
- Returns "degraded" status if dependencies unavailable

### Metrics to Track

**Decision**: Request latency, success rates, API call durations, queue lengths

**Rationale**:
- Performance monitoring
- Error detection
- Capacity planning
- SLA compliance

### Logging Strategy

**Decision**: Structured JSON logs with request IDs

**Rationale**:
- Production log parsing
- Request tracing
- Error debugging
- Audit trails

## Deployment Strategy

### Development Environment

**Decision**: Local Python venv, Docker Compose, Ngrok

**Rationale**:
- Fast iteration cycle
- Easy local testing
- Webhook testing with ElevenLabs
- Hot reload for development

### Production Environment

**Decision**: Kubernetes/ECS with managed PostgreSQL

**Rationale**:
- Container orchestration for scaling
- Managed database for reliability
- Secrets management for security
- S3/Cloud Storage for backups

## Summary

All technology decisions have been made based on:
- Performance requirements (<2s, <3s, <20s targets)
- Scalability needs (100 concurrent requests)
- Security requirements (HMAC validation, privacy controls)
- Development velocity (FastAPI, Pydantic, Docker)
- Operational simplicity (OpenMemory, managed services)

No critical unknowns remain. All technical decisions are documented and ready for implementation.

