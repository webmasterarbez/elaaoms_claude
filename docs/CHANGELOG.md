# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation review and alignment analysis
- HMAC signature generator utility for testing webhooks
- Sample test payload for webhook testing
- CONTRIBUTING.md with development guidelines
- CHANGELOG.md for tracking project history
- Comprehensive troubleshooting section in README.md
- Error response examples in documentation
- Configuration alignment matrix
- Quick links section in README.md
- Badges for license, Python version, and Docker support

### Changed
- **BREAKING:** Fixed OpenAI SDK to use v1.x API (AsyncOpenAI)
- Updated README.md with complete rewrite and restructuring
- Fixed audio webhook format documentation (JSON+base64 instead of multipart)
- Fixed transcript format in examples (array instead of string)
- Updated Dockerfile CMD to use correct module reference
- Fixed datetime timezone comparisons across codebase
- Removed Groq provider references (not implemented)
- Prioritized memory system features over legacy endpoints in docs
- Consolidated duplicate configuration sections

### Fixed
- Project name typo: ELAUAOMS → ELAAOMS
- Hardcoded installation paths in README.md
- Missing /webhook endpoint documentation (removed)
- Incomplete requirements.txt listing in docs
- Timezone-aware vs timezone-naive datetime comparison bugs
- OpenAI SDK deprecated API calls (openai.ChatCompletion.acreate)
- Models.py datetime.utcnow() deprecated usage

### Removed
- Generic /webhook endpoint documentation (not implemented)
- Groq LLM provider from documentation (not implemented)

## [1.0.0] - 2025-11-12

### Added
- Initial release of ELAAOMS (ElevenLabs Agents Universal Agentic Open Memory System)
- Three webhook endpoints for ElevenLabs integration:
  - `/webhook/client-data` - Personalized first messages
  - `/webhook/search-memory` - Real-time memory search during calls
  - `/webhook/post-call` - Memory extraction and storage
- HMAC-SHA256 webhook signature validation
- Automatic memory extraction using LLM (OpenAI/Anthropic)
- Background job processing for async memory extraction
- OpenMemory integration for memory storage and retrieval
- ElevenLabs API client for agent profile fetching
- Multi-agent memory sharing support
- Memory deduplication logic
- Agent profile caching (24-hour TTL)
- Configurable memory relevance thresholds
- Docker and Docker Compose support
- ngrok integration for testing
- Comprehensive documentation:
  - README.md - Main documentation
  - MEMORY_SYSTEM_GUIDE.md - Complete implementation guide
  - DEPLOYMENT.md - Production deployment guide
  - utility/README.md - Utility scripts documentation
- Utility scripts:
  - get_conversation.py - Fetch conversations from ElevenLabs API
- Environment-based configuration via .env files
- Structured logging throughout application
- Health check endpoint
- Echo endpoint for testing
- Automatic payload storage to disk
- CORS support

### Technical Details
- FastAPI 0.104.1 web framework
- Pydantic 2.5.0 for data validation
- Python 3.10+ support
- OpenAI SDK 1.6.1 integration
- Anthropic SDK 0.25.1 integration
- PostgreSQL-backed OpenMemory storage
- Uvicorn ASGI server
- Docker containerization
- Background job queue using Python threading

### Documentation
- Complete API endpoint documentation with examples
- Request/response format specifications
- HMAC signature validation guide
- ElevenLabs webhook configuration instructions
- OpenMemory setup guide
- Deployment options (Docker, cloud providers, local)
- Configuration management documentation
- Troubleshooting guides
- Example payloads and curl commands

## Version History

### Version Numbering

- **Major version (X.0.0)**: Incompatible API changes
- **Minor version (0.X.0)**: New functionality (backwards-compatible)
- **Patch version (0.0.X)**: Bug fixes (backwards-compatible)

### Release Notes

#### v1.0.0 (2025-11-12) - Initial Release
First production-ready release of the universal memory system for ElevenLabs AI agents.

**Key Features:**
- Automatic memory extraction from all conversations
- Personalized greetings for returning callers
- Real-time memory search during active calls
- Multi-agent memory sharing
- Production-ready Docker deployment
- Comprehensive documentation

**Supported LLM Providers:**
- OpenAI (gpt-4-turbo, gpt-3.5-turbo)
- Anthropic (claude-3-opus, claude-3-sonnet)

**Infrastructure:**
- OpenMemory for memory storage
- PostgreSQL database
- FastAPI web framework
- Python 3.10+

---

## Migration Guides

### Migrating to v1.0.1 (Unreleased)

**OpenAI SDK Changes:**
If you're upgrading from a pre-release version, the OpenAI SDK integration has changed:

```python
# Old (deprecated):
import openai
openai.api_key = api_key
response = await openai.ChatCompletion.acreate(...)

# New (v1.0.1+):
from openai import AsyncOpenAI
client = AsyncOpenAI(api_key=api_key)
response = await client.chat.completions.create(...)
```

**Datetime Changes:**
All datetime operations now use timezone-aware datetime:

```python
# Old:
from datetime import datetime
now = datetime.utcnow()

# New:
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
```

**Configuration Changes:**
- Groq provider removed (not implemented)
- Only `openai` and `anthropic` supported for `LLM_PROVIDER`

---

## Known Issues

See [GitHub Issues](https://github.com/webmasterarbez/elaaoms_claude/issues) for current known issues.

## Roadmap

### Planned for v1.1.0
- [ ] Performance benchmarks and optimization
- [ ] Additional LLM provider support (if requested)
- [ ] Enhanced memory categorization
- [ ] Memory importance auto-tuning
- [ ] Advanced deduplication algorithms
- [ ] Memory analytics dashboard
- [ ] Bulk memory import/export tools

### Planned for v1.2.0
- [ ] Voice sentiment analysis integration
- [ ] Multi-language memory translation
- [ ] Custom memory schemas
- [ ] Webhook retry mechanisms
- [ ] Rate limiting implementation
- [ ] Prometheus metrics export

### Future Considerations
- Admin dashboard for memory management
- GraphQL API support
- Memory versioning and history
- Advanced search capabilities
- Kubernetes deployment templates
- CI/CD pipeline templates

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

## Support

For questions, issues, or feature requests:
- 📖 Check the [documentation](README.md)
- 🐛 [Report bugs](https://github.com/webmasterarbez/elaaoms_claude/issues)
- 💡 [Request features](https://github.com/webmasterarbez/elaaoms_claude/issues)
- 💬 [Discussions](https://github.com/webmasterarbez/elaaoms_claude/discussions)

---

*This changelog follows the [Keep a Changelog](https://keepachangelog.com/) format.*
