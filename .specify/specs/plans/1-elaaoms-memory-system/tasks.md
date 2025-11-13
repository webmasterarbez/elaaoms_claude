# Tasks: ELAAOMS Memory Management Platform

**Feature**: [1-elaaoms-memory-system](../features/1-elaaoms-memory-system.md)  
**Plan**: [plan.md](./plan.md)  
**Created**: 2024-12-19

## Overview

This document provides an actionable, dependency-ordered task list for implementing the ELAAOMS memory management platform. Tasks are organized by functional requirements (user stories) to enable independent implementation and testing.

## Code Quality Requirements

**All implementation tasks must comply with the ELAAOMS Development Constitution:**

- **Type Hints**: All function parameters and return values must include type hints
- **Docstrings**: All functions and classes must include docstrings
- **Code Style**: Follow PEP 8 with 100-character line limit, 4-space indentation, double quotes
- **Error Handling**: Comprehensive try-except blocks with proper logging
- **Security**: HMAC validation, input validation with Pydantic, no secrets in code
- **Testing**: Maintain >80% code coverage, test security-sensitive code paths
- **Documentation**: Update documentation in same PR as code changes
- **CHANGELOG**: Update CHANGELOG.md in same PR as code changes per constitution requirements

## Implementation Strategy

**MVP Scope**: Phase 1-4 (Setup, Foundational, FR6 Webhook Integration, FR3 Post-Call Memory Extraction)
- Core webhook infrastructure
- Basic memory extraction and storage
- Enables end-to-end memory capture

**Incremental Delivery**:
1. MVP: Memory extraction and storage (FR3, FR6)
2. Phase 2: Pre-call personalization (FR1)
3. Phase 3: Real-time search (FR2)
4. Phase 4: Deduplication and sharing (FR5, FR4)
5. Phase 5: Multi-provider support (FR9)
6. Phase 6: Performance optimization (FR7, FR8)

## Dependencies

**Story Completion Order**:
1. Setup (Phase 1) → Must complete first
2. Foundational (Phase 2) → Blocks all user stories
3. FR6: Webhook Integration (Phase 3) → Required for FR1, FR2, FR3
4. FR3: Post-Call Memory Extraction (Phase 4) → Provides data for FR1, FR2
5. FR1: Pre-Call Context Retrieval (Phase 5) → Depends on FR3
6. FR2: Real-Time Memory Search (Phase 6) → Depends on FR3
7. FR5: Memory Deduplication (Phase 7) → Enhances FR3
8. FR4: Cross-Agent Memory Sharing (Phase 8) → Depends on FR3, FR5
9. FR9: LLM Provider Support (Phase 9) → Enhances FR3
10. FR7: Data Organization (Phase 10) → Optimization
11. FR8: Performance & Scalability (Phase 11) → Optimization
12. Polish (Phase 12) → Final improvements

## Parallel Execution Opportunities

**Within FR6 (Phase 3)**:
- T010 [P] and T011 [P] can run in parallel (different files)
- T012 [P] and T013 [P] can run in parallel (different files)

**Within FR3 (Phase 4)**:
- T025 [P] and T026 [P] can run in parallel (different clients)
- T027 [P] and T028 [P] can run in parallel (different services)

**Within FR1 (Phase 5)**:
- T040 [P] and T041 [P] can run in parallel (different managers)

**Within FR2 (Phase 6)**:
- T050 [P] and T051 [P] can run in parallel (different components)

---

## Phase 1: Setup

**Goal**: Initialize project structure and development environment

**Independent Test Criteria**: Project structure exists, dependencies installable, Docker services startable

### Tasks

- [X] T001 Create project directory structure per implementation plan in backend/
- [X] T002 Create requirements.txt with FastAPI 0.104.1, Pydantic 2.5.0, HTTPX 0.25.2, Uvicorn 0.24.0, Pyngrok 7.4.1
- [X] T003 Create docker-compose.yml with postgres, openmemory, and backend services
- [X] T004 Create .env.example template with all required environment variables
- [X] T005 Create .gitignore excluding .env, data/, venv/, __pycache__, *.pyc
- [X] T006 Create README.md with project overview, setup instructions, and quick start guide
- [X] T007 Create data/ directory structure: data/payloads/, data/logs/
- [X] T008 Create backend/config/ directory for settings module
- [X] T009 Create CHANGELOG.md with initial version entry following conventional commits format

---

## Phase 2: Foundational

**Goal**: Implement core infrastructure components required by all user stories

**Independent Test Criteria**: Configuration loads, logging works, health endpoint responds, HMAC validation functions

### Tasks

- [X] T010 Create backend/config/settings.py with Pydantic Settings for environment configuration
- [X] T011 [P] Create backend/app/auth.py with HMAC-SHA256 signature validation function (with constant-time comparison to prevent timing attacks)
- [X] T012 [P] Create backend/app/storage.py with file system operations for payload storage
- [X] T013 [P] Create backend/main.py with FastAPI app initialization and CORS configuration
- [X] T014 [P] Implement GET /health endpoint in backend/app/routes.py with dependency checks
- [X] T015 Create logging configuration in backend/config/logging.py with structured logging, request ID tracking, and API key masking (max 8 characters) per constitution

---

## Phase 3: FR6 - Webhook Integration with ElevenLabs

**Goal**: Implement three webhook endpoints with HMAC validation and request/response models

**Story**: FR6 - System provides three webhook endpoints with HMAC-SHA256 validation

**Independent Test Criteria**: All three webhooks accept requests, validate HMAC signatures, return proper responses, handle errors gracefully

### Tasks

- [X] T016 [US6] Create backend/app/models.py with Pydantic models: ClientDataRequest, ClientDataResponse, SearchMemoryRequest, SearchMemoryResponse, PostCallRequest, PostCallResponse, ErrorResponse
- [X] T017 [US6] Implement POST /webhook/client-data endpoint in backend/app/routes.py with HMAC validation
- [X] T018 [US6] Implement POST /webhook/search-memory endpoint in backend/app/routes.py with HMAC validation
- [X] T019 [US6] Implement POST /webhook/post-call endpoint in backend/app/routes.py with HMAC validation and payload saving
- [X] T020 [US6] Create request ID generation middleware in backend/app/middleware.py for all requests
- [X] T021 [US6] Implement error handling middleware in backend/app/middleware.py with consistent error response format
- [X] T022 [US6] Add request validation using Pydantic models in all webhook endpoints

---

## Phase 4: FR3 - Automatic Post-Call Memory Extraction

**Goal**: Extract memories from conversation transcripts using LLM and store in OpenMemory

**Story**: FR3 - System automatically extracts five types of memories from transcripts within 20 seconds

**Independent Test Criteria**: Transcripts processed, memories extracted with correct types and importance ratings, stored in OpenMemory, handles failures with retry logic

### Tasks

- [X] T023 [US3] Create backend/app/openmemory_client.py with OpenMemoryClient class for memory storage and retrieval
- [X] T024 [US3] Implement store_memory method in backend/app/openmemory_client.py with metadata support
- [X] T025 [US3] Implement search_memories method in backend/app/openmemory_client.py with semantic search
- [X] T026 [P] [US3] Create backend/app/llm_service.py with LLMService abstraction class
- [X] T027 [P] [US3] Create backend/app/llm_clients/openai_client.py with OpenAI memory extraction implementation
- [X] T028 [P] [US3] Create backend/app/llm_clients/anthropic_client.py with Anthropic memory extraction implementation
- [X] T029 [P] [US3] Implement extract_memories method in backend/app/llm_service.py with structured output (5 memory types, importance 1-10)
- [X] T030 [US3] Create backend/app/background_jobs.py with BackgroundJobProcessor class for async memory extraction
- [X] T031 [US3] Implement memory extraction job in backend/app/background_jobs.py with LLM call and OpenMemory storage
- [X] T032 [US3] Integrate background job queue in POST /webhook/post-call endpoint in backend/app/routes.py
- [X] T033 [US3] Implement retry logic in backend/app/background_jobs.py with 3 attempts (1min, 5min, 30min exponential backoff)
- [X] T034 [US3] Add error handling in backend/app/background_jobs.py to save transcript with "extraction_failed" status after retries exhausted
- [X] T035 [US3] Create backend/app/elevenlabs_client.py with ElevenLabsClient class for agent profile fetching

---

## Phase 5: FR1 - Pre-Call Context Retrieval

**Goal**: Retrieve caller context and generate personalized greeting before conversation starts

**Story**: FR1 - System retrieves caller context within 2 seconds and returns structured JSON (max 2000 tokens)

**Independent Test Criteria**: Context retrieved in <2s, includes memories/preferences/insights, formatted as structured JSON, handles missing caller ID gracefully

### Tasks

- [X] T036 [US1] Create backend/app/caller_memory_manager.py with CallerMemoryManager class for retrieving caller memories
- [X] T037 [US1] Implement get_last_conversation_memories method in backend/app/caller_memory_manager.py
- [X] T038 [US1] Implement get_high_importance_cross_agent_memories method in backend/app/caller_memory_manager.py (importance >= 8)
- [X] T039 [US1] Create backend/app/agent_profile_manager.py with AgentProfileManager class for caching agent profiles
- [X] T040 [US1] Implement get_agent_profile method in backend/app/agent_profile_manager.py with 24-hour TTL caching
- [X] T041 [P] [US1] Implement generate_personalized_first_message method in backend/app/llm_service.py using agent profile and memories
- [X] T042 [P] [US1] Implement format_context_json method in backend/app/caller_memory_manager.py with structured JSON (memories, preferences, relationship_insights) and 2000 token limit
- [X] T043 [US1] Update POST /webhook/client-data endpoint in backend/app/routes.py to retrieve memories, generate greeting, and return structured context
- [X] T044 [US1] Add graceful handling for missing caller_id in POST /webhook/client-data endpoint in backend/app/routes.py with generic greeting fallback

---

## Phase 6: FR2 - Real-Time Memory Search During Calls

**Goal**: Enable agents to search caller memory history during active conversations

**Story**: FR2 - Memory search completes in <3 seconds, returns ranked results with relevance scores

**Independent Test Criteria**: Search completes in <3s, results ranked by relevance, includes memory type/timestamp/score, handles concurrent searches

### Tasks

- [X] T045 [US2] Implement search_memories_by_caller method in backend/app/caller_memory_manager.py with semantic search
- [X] T046 [US2] Add relevance threshold filtering (default 0.7) in backend/app/caller_memory_manager.py search methods
- [X] T047 [US2] Implement search_all_agents option in backend/app/caller_memory_manager.py for cross-agent memory search
- [X] T048 [US2] Create format_memory_results method in backend/app/caller_memory_manager.py with memory type, timestamp, relevance score
- [X] T049 [US2] Create create_memory_summary method in backend/app/caller_memory_manager.py for natural language summary generation
- [X] T050 [US2] Update POST /webhook/search-memory endpoint in backend/app/routes.py to execute search and return ranked results
- [X] T051 [P] [US2] Add result limit configuration (default 5, max 100) in POST /webhook/search-memory endpoint in backend/app/routes.py
- [X] T052 [P] [US2] Implement concurrent search handling in POST /webhook/search-memory endpoint in backend/app/routes.py

---

## Phase 7: FR5 - Intelligent Memory Deduplication

**Goal**: Check for similar memories before storing to avoid redundancy and reinforce existing memories

**Story**: FR5 - System uses semantic similarity (cosine similarity >0.85) to detect duplicates and reinforce existing memories

**Independent Test Criteria**: Similar memories detected, existing memories reinforced (timestamp, conversation_id, confidence updated), new memories stored when no match found

### Tasks

- [X] T053 [US5] Implement check_similar_memories method in backend/app/openmemory_client.py using semantic search with 0.85 similarity threshold
- [X] T054 [US5] Create reinforce_memory method in backend/app/openmemory_client.py to update timestamp, conversation_id, and confidence score
- [X] T055 [US5] Integrate deduplication check in memory extraction job in backend/app/background_jobs.py before storing new memories
- [X] T056 [US5] Implement conflict detection in backend/app/background_jobs.py to store conflicting memories with conflict markers
- [X] T057 [US5] Add similarity threshold configuration (default 0.85) in backend/config/settings.py

---

## Phase 8: FR4 - Cross-Agent Memory Sharing

**Goal**: Share high-importance memories (importance >= 8) across all agents in organization

**Story**: FR4 - Memories with importance >= 8 are automatically shareable across agents with zero data loss

**Independent Test Criteria**: High-importance memories marked as shareable, accessible by all agents, appear in pre-call context, audit trail maintained

### Tasks

- [X] T058 [US4] Implement mark_memory_as_shareable method in backend/app/openmemory_client.py for memories with importance >= 8
- [X] T059 [US4] Update memory extraction job in backend/app/background_jobs.py to automatically mark high-importance memories as shareable
- [X] T060 [US4] Update get_high_importance_cross_agent_memories method in backend/app/caller_memory_manager.py to include shareable memories from all agents
- [X] T061 [US4] Create audit logging for shared memory access in backend/app/caller_memory_manager.py with agent_id and memory_id tracking
- [X] T062 [US4] Update POST /webhook/client-data endpoint in backend/app/routes.py to include cross-agent shared memories in context

---

## Phase 9: FR9 - LLM Provider Support

**Goal**: Support both OpenAI and Anthropic LLM providers with configurable selection

**Story**: FR9 - System supports OpenAI and Anthropic with per-organization or global configuration

**Independent Test Criteria**: Provider selection works, fallback to alternative provider on failure, retry logic handles transient errors, responses validated

### Tasks

- [X] T063 [US9] Add LLM_PROVIDER configuration in backend/config/settings.py (openai, anthropic, or auto)
- [X] T064 [US9] Implement provider selection logic in backend/app/llm_service.py based on organization or global setting
- [X] T065 [US9] Add fallback provider logic in backend/app/llm_service.py when primary provider fails
- [X] T066 [US9] Implement response validation in backend/app/llm_service.py using Pydantic models before memory storage
- [X] T067 [US9] Add provider-specific timeout configuration (30s for LLM calls) in backend/config/settings.py

---

## Phase 10: FR7 - Data Organization by Conversation and Caller

**Goal**: Optimize data organization for fast retrieval (<2s pre-call, <3s search)

**Story**: FR7 - All memories indexed by caller_id and conversation_id, supports efficient querying

**Independent Test Criteria**: Queries complete within targets, indexes exist, referential integrity maintained

### Tasks

- [X] T068 [US7] Verify OpenMemory indexes on caller_id, conversation_id, agent_id, type, importance_rating in backend/app/openmemory_client.py
- [X] T069 [US7] Implement query optimization in backend/app/caller_memory_manager.py for pre-call context retrieval (<2s target)
- [X] T070 [US7] Implement query optimization in backend/app/caller_memory_manager.py for memory search (<3s target)
- [X] T071 [US7] Add referential integrity checks in backend/app/openmemory_client.py when storing memories
- [X] T072 [US7] Implement date range and importance rating filtering in backend/app/caller_memory_manager.py query methods

---

## Phase 11: FR8 - System Performance and Scalability

**Goal**: Ensure system handles 100+ concurrent requests and meets performance targets

**Story**: FR8 - System handles 100 concurrent requests, meets latency targets (95th percentile), maintains performance under load

**Independent Test Criteria**: Load testing shows 100+ concurrent requests handled, p95 latency within targets, monitoring and alerting functional

### Tasks

- [X] T073 [US8] Configure async/await patterns throughout backend/app/ for non-blocking I/O operations
- [X] T074 [US8] Implement connection pooling for OpenMemory queries in backend/app/openmemory_client.py
- [X] T075 [US8] Add performance monitoring endpoints in backend/app/routes.py for latency metrics (p50, p95, p99)
- [X] T076 [US8] Create performance alerting in backend/app/monitoring.py for degradation detection
- [X] T077 [US8] Add load testing scripts in tests/load/ for validating 100 concurrent request target

---

## Phase 12: Polish & Cross-Cutting Concerns

**Goal**: Final improvements, documentation, error handling, and production readiness

**Independent Test Criteria**: All edge cases handled, documentation complete, error messages clear, production-ready

### Tasks

- [X] T078 Handle missing caller_id edge case in all webhook endpoints in backend/app/routes.py with graceful fallbacks
- [X] T079 Implement long conversation chunking (>10K tokens) in backend/app/llm_service.py for memory extraction
- [X] T080 Add concurrent call handling with proper locking in backend/app/background_jobs.py
- [X] T081 Implement privacy filters for sensitive information detection in backend/app/privacy.py
- [X] T082 Add memory deletion endpoint for GDPR compliance in backend/app/routes.py (POST /webhook/delete-memory)
- [X] T083 Create comprehensive error messages with request IDs in all error responses
- [X] T084 Add request tracing with correlation IDs in all log messages
- [X] T085 Update API documentation in backend/app/routes.py with detailed endpoint descriptions
- [X] T086 Create deployment documentation in docs/DEPLOYMENT.md with production setup instructions
- [X] T087 Add integration test suite in tests/integration/ for end-to-end webhook flows
- [X] T088 Create .env.example with all required variables and descriptions
- [X] T089 Add Docker healthcheck directives in docker-compose.yml
- [X] T090 Implement graceful shutdown handling in backend/main.py
- [X] T091 Add unit test suite in tests/unit/ for all components (OpenMemoryClient, LLMService, CallerMemoryManager, etc.) with >80% code coverage
- [X] T092 Add security test suite in tests/security/ for HMAC validation, input validation, error handling, and API key masking
- [X] T093 Add POST /echo endpoint in backend/app/routes.py for testing webhook payloads
- [X] T094 Add validation for HMAC secret minimum length (32 bytes) in backend/config/settings.py
- [X] T095 Add conflict flagging in pre-call context in backend/app/caller_memory_manager.py to expose conflict history to agents
- [X] T096 Add organization-level privacy controls validation in backend/app/caller_memory_manager.py
- [X] T097 Add memory extraction accuracy validation task or acceptance test criteria (validate 85% accuracy requirement from FR3)

---

## Task Summary

**Total Tasks**: 97

**Tasks by Phase**:
- Phase 1 (Setup): 9 tasks
- Phase 2 (Foundational): 6 tasks
- Phase 3 (FR6 - Webhooks): 7 tasks
- Phase 4 (FR3 - Memory Extraction): 13 tasks
- Phase 5 (FR1 - Pre-Call Context): 9 tasks
- Phase 6 (FR2 - Memory Search): 8 tasks
- Phase 7 (FR5 - Deduplication): 5 tasks
- Phase 8 (FR4 - Cross-Agent Sharing): 5 tasks
- Phase 9 (FR9 - LLM Providers): 5 tasks
- Phase 10 (FR7 - Data Organization): 5 tasks
- Phase 11 (FR8 - Performance): 5 tasks
- Phase 12 (Polish): 20 tasks

**Parallel Opportunities**: 10 tasks marked with [P] can be executed in parallel

**MVP Scope**: Phases 1-4 (35 tasks) provide core memory extraction and storage functionality

