# Implementation Plan: ELAAOMS Memory Management Platform

**Feature**: [1-elaaoms-memory-system](../features/1-elaaoms-memory-system.md)  
**Status**: Planning  
**Created**: 2024-12-19  
**Last Updated**: 2024-12-19

## Technical Context

### Technology Stack

**Backend Framework**: Python 3.10+ with FastAPI 0.104.1
- Rationale: Native async support for concurrent webhook handling, automatic OpenAPI documentation, built-in validation via Pydantic, excellent performance for I/O-bound operations
- FastAPI's dependency injection system simplifies service integration and testing
- Automatic Swagger UI at /docs reduces documentation overhead

**API Server**: Uvicorn 0.24.0 (ASGI server)
- Rationale: Production-ready async server with excellent performance, graceful shutdowns, and worker process management
- Supports HTTP/1.1 and HTTP/2 for optimal client compatibility

**Data Validation**: Pydantic 2.5.0
- Rationale: Type-safe request/response models with automatic validation, serialization, and documentation generation
- Version 2.x provides significant performance improvements over 1.x

**Configuration Management**: Pydantic Settings 2.1.0 + python-dotenv 1.0.0
- Rationale: Type-safe environment variable loading with validation, default values, and nested configuration objects
- Supports multiple environment files for dev/staging/production

**Memory Storage**: OpenMemory (PostgreSQL-backed vector database)
- Rationale: Purpose-built for conversational AI memory with built-in semantic search, deduplication, and reinforcement learning capabilities
- PostgreSQL backend provides ACID compliance, proven reliability, and mature ecosystem
- Uses caviraoss/openmemory:latest Docker image for simplified deployment

**LLM Providers**: Multi-provider support (OpenAI 1.6.1, Anthropic 0.25.1)
- Rationale: Flexibility to choose cost-effective or high-quality models based on use case
- OpenAI GPT-4 Turbo for high-accuracy memory extraction
- Anthropic Claude as alternative for longer context windows or pricing considerations
- Abstraction layer allows switching providers without code changes

**HTTP Client**: HTTPX 0.25.2
- Rationale: Modern async HTTP client with connection pooling, timeout handling, and retry logic
- Better async support than requests library

**Security**: HMAC-SHA256 signature validation
- Rationale: Industry-standard webhook authentication prevents unauthorized access and replay attacks
- ElevenLabs-compatible signature format: "t=timestamp,v0=hash"
- 30-minute timestamp tolerance prevents replay attacks while allowing for clock skew

**Development Tunnel**: Pyngrok 7.4.1
- Rationale: Programmatic ngrok integration for local development testing with ElevenLabs webhooks
- Auto-generates public URLs without manual ngrok CLI management

**Containerization**: Docker + Docker Compose
- Rationale: Consistent development and production environments, simplified multi-service orchestration
- Three-container architecture: backend, openmemory, postgres

### System Architecture

**Three-Tier Architecture Pattern**:
1. API Layer (FastAPI) - Webhook endpoints, request validation, authentication
2. Service Layer - Business logic, LLM integration, memory extraction
3. Data Layer - OpenMemory API client, PostgreSQL persistence

**API Design Pattern**:
- RESTful endpoints with POST for webhook receiving, GET for health checks
- Request/Response wrapper pattern with consistent structure:
  * status: "success" | "error"
  * message: Human-readable description
  * request_id: UUID for tracing
  * data: Payload-specific information
- Automatic exception handling middleware
- CORS enabled for cross-origin requests

### Primary Data Flows

**1. Pre-Call Context Retrieval (Client-Data Webhook)**:
- ElevenLabs → /webhook/client-data
- Extract caller_id and agent_id from request
- Query OpenMemory for caller's recent memories
- Rank by relevance and recency
- Generate personalized greeting using memory summary
- Return first_message to ElevenLabs
- Performance target: <2 seconds total

**2. In-Call Memory Search (Server Tool)**:
- ElevenLabs Agent → /webhook/search-memory
- Parse search query and caller context
- Execute semantic search in OpenMemory
- Filter by relevance threshold (default 0.7)
- Optionally search across all agents or single agent
- Rank results by relevance score
- Generate natural language summary
- Return structured results to agent
- Performance target: <3 seconds total

**3. Post-Call Memory Extraction (Transcription Webhook)**:
- ElevenLabs → /webhook/post-call
- Validate HMAC-SHA256 signature
- Save transcription payload to disk (./data/payloads/{conversation_id}/)
- Queue background job for memory extraction
- Return 200 OK immediately (<1 second)
- Background Job (async):
  - Fetch/cache agent profile from ElevenLabs API
  - Construct LLM prompt with transcript and agent context
  - Extract memories using structured output format
  - For each memory: assign importance score (1-10) and category
  - Query OpenMemory for similar existing memories (deduplication)
  - Store new memories or reinforce existing ones
  - Handle high-importance memories (≥8): mark for cross-agent sharing
  - Performance target: Complete within 20 seconds

### API Endpoints Structure

**Health & Utility**:
- GET /health → Simple status check
- POST /echo → Testing endpoint that returns payload
- GET /docs → Auto-generated Swagger UI

**Memory System (Primary)**:
- POST /webhook/client-data → Pre-call personalization
- POST /webhook/search-memory → Real-time memory search
- POST /webhook/post-call → Post-call processing with three subtypes:
  * type: post_call_transcription → JSON transcript
  * type: post_call_audio → Base64-encoded MP3
  * type: call_initiation_failure → Error notification

### Authentication & Security Implementation

**HMAC Validation Flow**:
1. Extract elevenlabs-signature header
2. Parse format: "t={timestamp},v0={signature}"
3. Validate timestamp is within 30 minutes (prevent replay attacks)
4. Reconstruct signed payload: "{timestamp}.{raw_body}"
5. Compute HMAC-SHA256 using shared secret
6. Compare computed signature with provided signature (constant-time comparison)
7. Reject with 401 if validation fails

**Request Tracing**:
- Generate UUID for every incoming request
- Include in all log messages and error responses
- Return in API response for client-side debugging

**Structured Logging**:
- Python logging module with formatted output
- Log levels: DEBUG (development), INFO (production), ERROR (failures)
- Include request_id, endpoint, caller_id, agent_id in context
- Separate logs for: incoming webhooks, LLM calls, OpenMemory operations, errors

### Data Storage Strategy

**File System Storage**:
- Webhook payloads: ./data/payloads/{conversation_id}/
  * {conversation_id}_transcription.json
  * {conversation_id}_audio.mp3
  * {conversation_id}_failure.json
- Application logs: ./data/logs/app.log
- Organized by conversation for easy debugging and auditing

**OpenMemory Storage**:
- Memories indexed by: caller_id, agent_id, conversation_id
- Vector embeddings for semantic search
- Metadata: importance_score, category, timestamp, conversation_id
- Automatic deduplication based on semantic similarity
- Memory reinforcement: increment confidence when similar memory extracted

**Caching Strategy**:
- Agent profiles cached for 24 hours (configurable via AGENT_PROFILE_TTL_HOURS)
- In-memory Python dictionary with TTL checking
- Reduces API calls to ElevenLabs
- Cache invalidation on profile update webhook (future enhancement)

### Background Job Processing

**Threading-Based Async Jobs**:
- Memory extraction runs in separate thread to avoid blocking webhook response
- ThreadPoolExecutor for concurrent job processing
- Queue-based architecture for job management (future: Celery for production scale)

**Error Handling**:
- Retry logic for transient LLM API failures (3 retries with exponential backoff: 1min, 5min, 30min)
- Graceful degradation: save transcript even if memory extraction fails
- Error logging with full context for debugging

### Memory Extraction LLM Strategy

**Prompt Engineering**:
- Structured prompt with clear instructions for five memory categories
- Include agent profile context (name, role, company) for relevance
- Request importance scores (1-10) and confidence levels
- Ask for justification/source quote from transcript

**Structured Output Format**:
- JSON schema enforcement using LLM function calling / tools
- Pydantic models for response validation
- Fields: category, content, importance, confidence, source_quote, timestamp

**Model Selection**:
- Default: OpenAI GPT-4 Turbo (128K context, high accuracy)
- Alternative: Anthropic Claude 3 Opus/Sonnet (200K context, nuanced understanding)
- Configurable via LLM_PROVIDER environment variable

**Deduplication Algorithm**:
1. For each extracted memory, query OpenMemory with semantic search
2. If cosine similarity score >0.85, consider it a duplicate
3. Instead of creating new memory, increment reinforcement counter on existing
4. Update timestamp to reflect most recent occurrence
5. If extracted memory has higher importance, update importance score

### Performance Optimization

**Async Operations**:
- FastAPI async endpoints for non-blocking I/O
- HTTPX async client for concurrent API calls
- Database connection pooling for OpenMemory queries

**Parallel Processing**:
- Agent profile fetch and memory search run concurrently
- Multiple background jobs process simultaneously (thread pool)
- Batch API calls when possible

**Response Time Targets**:
- /webhook/client-data: <2 seconds (blocking)
- /webhook/search-memory: <3 seconds (blocking)
- /webhook/post-call: <1 second (async job queued)

**Timeout Configuration**:
- LLM API calls: 30 second timeout
- OpenMemory queries: 10 second timeout
- ElevenLabs API calls: 15 second timeout
- Webhook response: Must complete within 30 seconds (ElevenLabs limit)

### Scalability Architecture

**Horizontal Scaling Strategy**:
- Stateless FastAPI instances behind load balancer
- Shared PostgreSQL database for OpenMemory
- Redis for distributed caching (future enhancement)
- Message queue (RabbitMQ/Redis) for background jobs at scale

**Database Scaling**:
- PostgreSQL read replicas for query scaling
- Connection pooling to limit database connections
- Indexed queries on caller_id, agent_id, conversation_id

**Rate Limiting (Future)**:
- Token bucket algorithm per caller_id
- Prevent abuse from high-frequency callers
- Configurable limits per endpoint

### Monitoring & Observability

**Health Checks**:
- /health endpoint for load balancer health checks
- Docker healthcheck directives in docker-compose.yml
- Check OpenMemory connectivity in health endpoint

**Metrics to Track**:
- Request latency (p50, p95, p99) per endpoint
- Memory extraction success rate
- LLM API call duration and failure rate
- OpenMemory query performance
- Background job queue length and processing time

**Logging Strategy**:
- Structured JSON logs for production parsing
- Log aggregation with ELK stack or CloudWatch
- Error alerting on repeated failures
- Request tracing with correlation IDs

### Deployment Strategy

**Development Environment**:
- Local Python virtual environment
- Docker Compose for OpenMemory + PostgreSQL
- Ngrok for webhook testing with ElevenLabs
- Hot reload with uvicorn --reload

**Staging Environment**:
- Docker Compose deployment on VPS/EC2
- Separate .env file with staging credentials
- SSL/TLS via Let's Encrypt + Nginx reverse proxy
- Rate limiting and request logging

**Production Environment**:
- Kubernetes cluster or AWS ECS for container orchestration
- Multi-instance FastAPI with load balancer
- Managed PostgreSQL (RDS/Cloud SQL) for reliability
- S3/Cloud Storage for payload backups
- CDN for static assets (if frontend added)
- Secrets management via AWS Secrets Manager / HashiCorp Vault

**CI/CD Pipeline**:
- GitHub Actions for automated testing
- Pytest for unit and integration tests
- Docker image building and registry push
- Automated deployment to staging on merge to develop
- Manual promotion to production with approval

**Configuration Management**:
- Environment-specific .env files
- Secrets never committed to git
- .env.example as template for required variables
- Pydantic Settings validation on startup

### Integration Patterns

**ElevenLabs Integration**:
- Agent Configuration: Enable "Client Data" webhook and "Server Tools" for memory search
- Dynamic Variables: Configure system__caller_id for caller identification
- HMAC Secret: Configure matching secret in ElevenLabs dashboard and .env
- Webhook URLs: Point to public endpoints (ngrok for dev, domain for prod)

**OpenMemory Integration**:
- RESTful API client with authentication
- Endpoints: /memories (CRUD), /search (semantic), /reinforcement
- Error handling for service unavailability
- Fallback to local storage if OpenMemory down (future enhancement)

**LLM Provider Integration**:
- Abstraction layer for provider-agnostic code
- Separate client classes: OpenAIClient, AnthropicClient
- Unified interface: extract_memories(transcript, agent_profile) → List[Memory]
- Provider selection via LLM_PROVIDER environment variable

### Edge Case Handling

**Missing Caller ID**:
- Log warning and proceed without personalization
- Generic first message: "Hello! How can I help you today?"
- Still extract memories, store with conversation_id only
- Future: Use voice biometrics or other identifiers

**Long Conversations**:
- Chunk transcripts >10,000 tokens before sending to LLM
- Extract memories per chunk, then deduplicate across chunks
- Use sliding window to maintain context between chunks

**LLM API Failures**:
- Retry with exponential backoff (3 attempts: 1min, 5min, 30min)
- Fall back to alternative provider if configured
- If all attempts fail: save transcript for manual review, log error
- Alert operations team on repeated failures

**Concurrent Calls from Same Caller**:
- Use conversation_id as unique identifier (not just caller_id)
- Lock mechanism for memory updates (database transactions)
- Eventually consistent memory view acceptable

**High-Importance Cross-Agent Memories**:
- Flag memories with importance ≥8 for global visibility
- Store with agent_id=null or agent_id="*" for cross-agent queries
- Search query option: search_all_agents=true

**Privacy & Security**:
- Never log full transcripts at INFO level (DEBUG only)
- Redact sensitive patterns (SSN, credit cards) before storing
- Manual deletion only (no automatic expiry deletion)
- GDPR compliance: provide memory deletion endpoint

**Very Long Processing**:
- If memory extraction exceeds 60 seconds, log warning but continue
- Consider splitting into multiple background jobs
- Monitor job duration and optimize prompt for faster extraction

### Service Dependencies

**Critical Dependencies**:
- ElevenLabs API: Provides webhooks and agent profiles
- OpenMemory: Core memory storage and search
- PostgreSQL: Persistence layer for OpenMemory
- LLM Provider (OpenAI/Anthropic): Memory extraction engine

**Failure Modes**:
- ElevenLabs down: Cannot receive webhooks (external dependency)
- OpenMemory down: Degrade to generic responses, queue memories for later
- PostgreSQL down: OpenMemory fails, same as above
- LLM API down: Cannot extract memories, save transcripts for retry

**Health Check Dependencies**:
- /health checks OpenMemory connectivity
- Returns "degraded" status if OpenMemory unreachable
- Load balancer routes traffic only to "healthy" instances

### Development Workflow

**Local Setup**:
1. Clone repository
2. Create Python virtual environment
3. Install requirements: pip install -r backend/requirements.txt
4. Copy .env.example → .env and fill in credentials
5. Start services: docker-compose up -d
6. Start backend: python backend/main.py
7. Start ngrok: python scripts/ngrok_config.py
8. Configure ElevenLabs webhooks with ngrok URL

**Testing Strategy**:
- Unit tests for auth, LLM service, OpenMemory client
- Integration tests for full webhook flows
- HMAC signature generation utility for testing
- Mock LLM responses for deterministic tests
- Load testing with locust or k6

**Code Organization**:
- backend/app/routes.py: API endpoint definitions
- backend/app/models.py: Pydantic request/response models
- backend/app/auth.py: HMAC signature verification
- backend/app/storage.py: File system operations
- backend/app/background_jobs.py: Async memory extraction
- backend/app/llm_service.py: LLM provider abstraction
- backend/app/openmemory_client.py: OpenMemory API client
- backend/app/elevenlabs_client.py: ElevenLabs API client
- backend/config/settings.py: Environment configuration

**Version Control**:
- Git with feature branch workflow
- .gitignore: .env, data/, venv/, __pycache__
- Conventional commits for clear history
- Pull request reviews before merge

**Documentation**:
- README.md: Overview, setup, API reference
- docs/MEMORY_SYSTEM_GUIDE.md: Detailed implementation guide
- docs/DEPLOYMENT.md: Production deployment instructions
- Inline code comments for complex logic
- Swagger/OpenAPI automatic documentation

## Constitution Check

### Pre-Design Review

**Project Purpose Alignment**: ✅
- System enables AI voice agents to remember and personalize conversations
- Aligns with ELAAOMS mission of intelligent memory management

**Core Principles Compliance**: ✅
- Type hints required on all functions
- Docstrings on all functions/classes
- Request ID tracking for traceability
- HMAC validation for security
- Async/await for I/O operations
- Pydantic models for validation

**Development Standards**: ✅
- FastAPI patterns followed
- Error handling with HTTPException
- Structured logging with request IDs
- Settings management via pydantic-settings

**Security Requirements**: ✅
- HMAC-SHA256 webhook validation
- No hardcoded secrets
- Environment-based configuration
- Privacy controls for sensitive information

**Documentation Rules**: ✅
- Code-docs alignment maintained
- Swagger/OpenAPI auto-documentation
- Inline comments for complex logic

### Gate Evaluation

**Gate 1: Specification Complete**: ✅ PASS
- All functional requirements defined
- Success criteria measurable
- Edge cases identified
- Clarifications resolved

**Gate 2: Technical Feasibility**: ✅ PASS
- All dependencies identified and available
- Performance targets achievable
- Scalability strategy defined

**Gate 3: Security Review**: ✅ PASS
- Authentication mechanism defined (HMAC)
- Privacy controls specified
- Audit logging planned

**Gate 4: Resource Availability**: ✅ PASS
- Technology stack selected
- External services identified
- Deployment strategy defined

## Phase 0: Outline & Research

See [research.md](./research.md) for detailed research findings and technology decisions.

## Phase 1: Design & Contracts

### Data Model
See [data-model.md](./data-model.md) for entity definitions, relationships, and validation rules.

### API Contracts
See [contracts/](./contracts/) directory for OpenAPI specifications.

### Quick Start Guide
See [quickstart.md](./quickstart.md) for setup and development instructions.

## Phase 2: Implementation Tasks

Implementation tasks will be generated in the next phase using `/speckit.tasks`.

