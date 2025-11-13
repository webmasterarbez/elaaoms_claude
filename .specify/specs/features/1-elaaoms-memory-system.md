# Specification: ELAAOMS Memory Management Platform

**Status**: Draft  
**Created**: 2024-12-19  
**Last Updated**: 2024-12-19  
**Feature Number**: 1

## Overview

ELAAOMS (ElevenLabs Agents Universal Agentic Open Memory System) is an intelligent memory management platform that enables AI voice agents to remember, learn from, and personalize conversations across multiple customer interactions. The system automatically captures conversation context during phone calls, extracts meaningful information, and uses that knowledge to provide personalized experiences when customers call back—whether they're speaking to the same agent or a different one.

## User Scenarios & Testing

### Scenario 1: Returning Customer Support Call
**Context**: A customer calls about a delayed package. Three days later, they call back.

**Flow**:
1. Customer initiates call to support
2. System recognizes caller ID and retrieves previous conversation context (completes in under 2 seconds)
3. Agent receives pre-call context including previous issue about delayed package
4. Agent greets customer: "Hi again! I see we were tracking your package XYZ-789 last time. Let me check the latest status for you."
5. Customer confirms it's the same issue
6. Agent provides update without customer needing to explain situation again
7. After call ends, system automatically extracts new memories from conversation (completes within 20 seconds)

**Expected Outcome**: Customer doesn't need to repeat their situation. Agent has immediate context and can provide personalized service.

### Scenario 2: Sales Follow-up with Interest Tracking
**Context**: A potential customer expresses interest in a specific product feature during one call. When they call back, the sales agent knows their interests.

**Flow**:
1. Customer calls sales and discusses interest in Product Feature X
2. After call, system extracts memory: "Customer interested in Product Feature X"
3. Customer calls back two weeks later (different agent)
4. System provides pre-call context: "Previous interest in Product Feature X"
5. New agent continues conversation naturally: "I understand you were interested in Feature X. Let me show you how it works..."
6. During call, agent searches memory: "What did we discuss about pricing?" (returns results in under 3 seconds)

**Expected Outcome**: Sales agent can continue conversation naturally with full context of customer interests and previous discussions.

### Scenario 3: Multi-Agent Handoff with Context Preservation
**Context**: A customer speaks with a technical support agent who documents a critical system configuration. When the customer later calls billing, that agent can see the technical context.

**Flow**:
1. Customer calls technical support about system configuration
2. Technical agent documents critical configuration details
3. System extracts high-importance memory (rated 9/10): "Customer has custom system configuration requiring special billing treatment"
4. Memory is marked as cross-agent shareable (importance ≥ 8/10)
5. Customer calls billing department (different agent, different department)
6. Billing agent receives pre-call context including technical configuration details
7. Billing agent understands why certain charges exist and can explain them accurately

**Expected Outcome**: Cross-agent memory sharing enables seamless handoffs without information loss. Customer doesn't need to re-explain technical context.

### Scenario 4: Repeat Caller Recognition and Loyalty Acknowledgment
**Context**: A customer who frequently calls for order status checks is greeted warmly with acknowledgment of their loyalty.

**Flow**:
1. Customer has called 15 times in past 3 months for order status
2. System recognizes caller and retrieves relationship insights: "Frequent caller, prefers proactive updates"
3. Agent greets: "Hi [Name]! Good to hear from you again. I see you have 3 active orders. Would you like me to check the status of all of them?"
4. Customer appreciates the proactive approach
5. System extracts new memory reinforcing customer preference for proactive updates

**Expected Outcome**: Personalized greeting increases customer satisfaction. Agent efficiency improves through proactive information delivery.

### Scenario 5: Real-Time Memory Search During Active Call
**Context**: During an active call, customer asks "What was my last order number?"

**Flow**:
1. Customer is on active call with agent
2. Customer asks: "What was my last order number?"
3. Agent triggers memory search query
4. System searches customer's conversation history
5. Results returned in under 3 seconds, ranked by relevance
6. Agent reads top result: "Last order: XYZ-789, placed on [date]"
7. Agent provides answer to customer

**Expected Outcome**: Agent can answer customer questions about previous interactions in real-time without ending the call.

## Functional Requirements

### FR1: Pre-Call Context Retrieval
**Description**: When a customer initiates a call, the system must immediately recognize returning callers and provide the AI agent with relevant context from previous conversations.

**Acceptance Criteria**:
- System retrieves caller context within 2 seconds for 95% of calls
- Context includes: previous conversation summaries, extracted memories, customer preferences, relationship insights
- Agent receives context before greeting customer
- System handles cases where caller ID is unavailable gracefully
- Context is formatted for easy consumption by AI agent

### FR2: Real-Time Memory Search During Calls
**Description**: During active calls, AI agents must be able to search the customer's conversation history to answer questions about previous interactions.

**Acceptance Criteria**:
- Memory search completes in under 3 seconds for 95% of queries
- Results are ranked by relevance to the search query
- Search returns top N most relevant memories (configurable, default 5)
- Search works across all previous conversations for the caller
- System handles concurrent searches from multiple active calls
- Search results include memory type, timestamp, and relevance score

### FR3: Automatic Post-Call Memory Extraction
**Description**: After each call ends, the system must automatically analyze the full conversation transcript and extract meaningful memories.

**Acceptance Criteria**:
- Memory extraction completes within 20 seconds of call completion for 90% of calls
- System extracts five types of memories:
  - Factual information (orders, account details, dates, numbers)
  - Customer preferences (communication style, product interests, service preferences)
  - Reported issues (problems, complaints, concerns)
  - Emotional context (satisfaction level, frustration indicators, positive feedback)
  - Relationship insights (call frequency, loyalty indicators, interaction patterns)
- Each extracted memory includes: content, type, importance rating (1-10), timestamp, conversation ID
- Extraction accuracy: at least 85% of extracted memories are factually correct and relevant
- System handles extraction failures gracefully with retry logic

### FR4: Cross-Agent Memory Sharing
**Description**: High-importance memories (rated 8/10 or above) must be accessible across different AI agents within the same organization.

**Acceptance Criteria**:
- Memories with importance rating ≥ 8/10 are automatically marked as shareable
- All agents in the same organization can access shared memories
- Shared memories appear in pre-call context for any agent
- Memory sharing works seamlessly with zero data loss
- System maintains audit trail of which agents accessed which shared memories
- Organization-level privacy controls are respected

### FR5: Intelligent Memory Deduplication
**Description**: Before storing new memories, the system must check against existing memories to avoid redundancy.

**Acceptance Criteria**:
- System compares new memory against existing memories for the same caller
- If similar memory exists (similarity threshold configurable, default 85%), system reinforces existing memory rather than creating duplicate
- Reinforcement updates: timestamp, conversation ID, confidence score
- If no similar memory exists, new memory is stored
- Deduplication completes as part of memory extraction process
- System handles conflicting memories (customer says different things) by storing both with conflict markers

### FR6: Webhook Integration with ElevenLabs
**Description**: System must integrate with ElevenLabs Conversational AI API through webhook endpoints.

**Acceptance Criteria**:
- System provides three webhook endpoints:
  - Pre-call client data webhook (receives caller info, returns context)
  - In-call memory search webhook (receives search query, returns results)
  - Post-call transcription webhook (receives transcript, triggers extraction)
- All webhooks validate incoming requests using HMAC-SHA256 signatures
- Webhooks respond within ElevenLabs timeout limits
- System handles webhook failures gracefully with appropriate error responses
- Webhook payloads are validated against expected schema

### FR7: Data Organization by Conversation and Caller
**Description**: System must organize stored data by conversation and caller for efficient retrieval.

**Acceptance Criteria**:
- All memories are indexed by caller ID for fast retrieval
- All memories are linked to specific conversation IDs
- System supports querying by: caller ID, conversation ID, memory type, date range, importance rating
- Data organization enables sub-2-second pre-call context retrieval
- Data organization enables sub-3-second memory search
- System maintains referential integrity between conversations and memories

### FR8: System Performance and Scalability
**Description**: System must handle concurrent operations and scale to support production workloads.

**Acceptance Criteria**:
- System handles at least 100 concurrent call processing requests
- Pre-call context retrieval: under 2 seconds for 95% of requests
- Real-time memory search: under 3 seconds for 95% of requests
- Post-call memory extraction: within 20 seconds for 90% of requests
- System maintains performance under peak load
- System provides monitoring and alerting for performance degradation

### FR9: LLM Provider Support
**Description**: System must support both OpenAI and Anthropic LLM providers for memory extraction.

**Acceptance Criteria**:
- System can be configured to use either OpenAI or Anthropic for memory extraction
- Provider selection is configurable per organization or globally
- System handles LLM API errors gracefully (rate limits, timeouts, failures)
- System implements retry logic for transient LLM failures
- System falls back to alternative provider if primary fails (if configured)
- LLM responses are validated before memory storage

## Success Criteria

### Quantitative Metrics
- **Pre-call context retrieval**: Completes in under 2 seconds for 95% of calls
- **Real-time memory search**: Returns results in under 3 seconds for 95% of queries
- **Post-call memory extraction**: Completes within 20 seconds of call completion for 90% of calls
- **Memory extraction accuracy**: At least 85% of extracted memories are factually correct and relevant
- **Concurrent processing**: System handles at least 100 concurrent call processing requests
- **Cross-agent memory sharing**: Zero data loss when memories are shared across agents
- **Deduplication effectiveness**: At least 90% of duplicate memories are detected and reinforced rather than duplicated

### Qualitative Measures
- **Customer satisfaction**: Personalized greetings and context-aware interactions increase customer satisfaction scores by measurable amount (baseline to be established)
- **Agent efficiency**: Agents report improved efficiency in resolving repeat customer issues (measured through agent feedback surveys)
- **First-call resolution**: Improved first-call resolution rates through better context availability
- **Customer retention**: Better customer retention through memorable, personalized interactions (measured through repeat call rates and customer feedback)

### Business Value Metrics
- **Reduced customer frustration**: Measurable reduction in customers having to repeat information (tracked through conversation analysis)
- **Improved resolution rates**: Increased first-call resolution rates through better context
- **Enhanced personalization**: Scale personalized experiences across all customer interactions
- **Competitive differentiation**: System provides unique value proposition in AI voice agent market

## Key Entities

### Caller
- **Attributes**: Caller ID (phone number), organization ID, first seen date, last seen date, total conversations
- **Relationships**: Has many Conversations, has many Memories

### Conversation
- **Attributes**: Conversation ID, agent ID, caller ID, start time, end time, duration, transcript, status
- **Relationships**: Belongs to Caller, has many Memories, linked to Organization

### Memory
- **Attributes**: Memory ID, caller ID, conversation ID, content, type (factual/preference/issue/emotion/relationship), importance rating (1-10), is_shareable (boolean), created timestamp, last reinforced timestamp, confidence score
- **Relationships**: Belongs to Caller, belongs to Conversation, may be shared across Agents

### Agent
- **Attributes**: Agent ID, organization ID, name, capabilities
- **Relationships**: Belongs to Organization, can access shared Memories (importance ≥ 8/10)

### Organization
- **Attributes**: Organization ID, name, LLM provider preference, privacy settings
- **Relationships**: Has many Agents, has many Callers, has many Conversations

### Memory Search Query
- **Attributes**: Query text, caller ID, conversation ID (current), timestamp, result limit
- **Relationships**: Returns ranked Memories

## Edge Cases

### EC1: Unavailable Caller ID
**Scenario**: Caller ID is not available (blocked numbers, international calls, technical issues)
**Handling**: 
- System attempts to identify caller through other means (if available: name, account number, session tokens)
- If no identification possible, system creates anonymous session
- Memories are stored but not linked to persistent caller identity
- When caller ID becomes available later, system attempts to merge anonymous memories with caller profile

### EC2: Very Long Conversations (1+ Hour)
**Scenario**: Conversation transcript exceeds typical length, potentially causing memory extraction timeouts
**Handling**:
- System processes transcript in chunks if necessary
- Memory extraction focuses on most important segments (beginning, key moments, end)
- System extracts memories incrementally during long calls if possible
- Extraction time limit is extended proportionally for longer conversations, but capped at reasonable maximum

### EC3: Memory Extraction Failure (LLM API Errors)
**Scenario**: LLM API returns errors, rate limits, or timeouts during memory extraction
**Handling**:
- System implements exponential backoff retry logic
- Failed extractions are queued for retry with increasing delays
- System logs extraction failures for manual review
- After maximum retry attempts, system stores raw transcript for later processing
- System notifies administrators of persistent extraction failures

### EC4: Conflicting Memories
**Scenario**: Customer provides different information in different calls (e.g., different address, different preference)
**Handling**:
- System stores both memories with conflict markers
- Most recent memory is given higher priority in retrieval
- System flags conflicts for agent awareness in pre-call context
- Agents can see conflict history and resolution suggestions
- System learns from agent resolutions to improve conflict handling

### EC5: Simultaneous Calls from Same Customer
**Scenario**: Multiple calls from the same customer occur at the same time
**Handling**:
- Each call is processed independently with its own conversation ID
- Pre-call context includes all previous conversations (excluding concurrent ones)
- Post-call extraction processes each conversation separately
- System handles race conditions in memory storage through proper locking mechanisms
- Deduplication checks against all memories, including those from concurrent calls

### EC6: Memory Storage/Retrieval Limits
**Scenario**: System reaches storage capacity or retrieval performance degrades due to volume
**Handling**:
- System prioritizes memories by importance rating and recency
- Lower-importance, older memories may be archived or summarized
- System maintains at least N most recent memories per caller (configurable, default 100)
- Critical memories (importance ≥ 8/10) are never archived
- System provides administrators with storage usage alerts and recommendations

### EC7: Privacy Controls for Sensitive Information
**Scenario**: Sensitive information (PII, payment details, health information) is inadvertently captured
**Handling**:
- System implements configurable privacy filters to detect and redact sensitive patterns
- Organizations can define custom privacy rules
- Sensitive memories are flagged and require special access permissions
- System supports memory deletion requests for privacy compliance
- Audit logs track all access to sensitive memories

### EC8: Caller ID Spoofing or Shared Phone Numbers
**Scenario**: Caller ID is spoofed or multiple people use the same phone number
**Handling**:
- System uses additional signals beyond caller ID when available (voice patterns, conversation history patterns)
- System flags potential spoofing when conversation patterns don't match historical caller profile
- For shared numbers, system attempts to distinguish callers through conversation context
- Agents are notified when caller identity confidence is low
- System supports manual caller identity correction by agents

### EC9: OpenMemory Service Unavailability
**Scenario**: External memory storage service (OpenMemory) is temporarily unavailable
**Handling**:
- System implements graceful degradation: continues operating with local cache
- New memories are queued locally until service is restored
- Pre-call context uses cached data when available
- System retries connection with exponential backoff
- Administrators are alerted to service unavailability
- System maintains data consistency when service is restored

### EC10: High-Frequency Callers (Spam, Testing)
**Scenario**: Very high call frequency from same caller (potential spam or testing)
**Handling**:
- System detects unusual call patterns (e.g., >10 calls per hour from same caller)
- High-frequency callers are flagged for review
- System may throttle memory extraction for high-frequency callers to prevent resource exhaustion
- Testing/scenario callers can be marked with special flags to exclude from analytics
- System maintains separate handling rules for legitimate high-frequency customers (e.g., VIP support)

## Assumptions

1. **ElevenLabs API Availability**: ElevenLabs Conversational AI API is available and provides required webhook capabilities
2. **Caller ID Reliability**: Caller ID is available for majority of calls, with fallback mechanisms for edge cases
3. **Transcript Quality**: ElevenLabs provides accurate, complete conversation transcripts
4. **LLM Provider Availability**: OpenAI and Anthropic APIs are available with sufficient rate limits for production use
5. **OpenMemory Integration**: OpenMemory service is available for memory storage and retrieval
6. **Network Latency**: Network latency between components is within acceptable ranges for sub-3-second response times
7. **Organization Structure**: Organizations have clear agent hierarchies and sharing boundaries
8. **Memory Importance Rating**: LLM can reliably assign importance ratings (1-10) to extracted memories
9. **Call Volume**: Typical call volume is within system capacity, with scaling mechanisms for peak loads
10. **Data Retention**: Organizations have defined data retention policies that system will respect

## Dependencies

1. **ElevenLabs Conversational AI API**: Required for webhook integration and conversation data
2. **OpenMemory Service**: Required for persistent memory storage and retrieval
3. **LLM Providers (OpenAI/Anthropic)**: Required for memory extraction from transcripts
4. **HMAC-SHA256 Validation Library**: Required for webhook security
5. **Webhook Infrastructure**: FastAPI or similar framework for webhook endpoints
6. **Database/Storage System**: For organizing and indexing memories by caller and conversation
7. **Background Job Processing**: For asynchronous memory extraction (to meet 20-second completion target)
8. **Monitoring and Logging**: For performance tracking and debugging

## Out of Scope

### Initial Version Exclusions
- **Voice Biometric Authentication**: Not included in initial version
- **Real-Time Transcription**: Relying on ElevenLabs for transcripts, not implementing own transcription
- **Multi-Language Memory Translation**: Memories stored in original language only
- **Video Call Support**: Voice calls only, no video call memory management
- **CRM System Integration**: Beyond basic webhooks, no deep CRM integration
- **Custom Memory Taxonomy**: Standard five memory types only, no organization-specific taxonomies
- **Memory Export/Data Portability**: No export features for customer data portability
- **Analytics Dashboard**: No built-in dashboard for memory insights (may be added later)
- **Memory Editing by Agents**: Agents cannot manually edit or delete memories (system-managed only)
- **Advanced Conflict Resolution UI**: Basic conflict flagging only, no sophisticated resolution workflows
- **Memory Versioning**: No version history for memory changes beyond reinforcement tracking
- **Advanced Search Filters**: Basic relevance ranking only, no complex filtering UI

