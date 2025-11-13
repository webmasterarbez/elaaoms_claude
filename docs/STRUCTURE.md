# Project Structure Guide

This document explains the reorganized project structure and the rationale behind it.

## Overview

The project has been reorganized following industry-standard best practices for multi-component applications. The new structure provides clear separation of concerns, better maintainability, and easier navigation.

## Directory Structure

```
elaaoms_claude/
├── backend/                      # Python FastAPI backend application
├── frontend/                    # Frontend applications (React, Static HTML)
├── docs/                       # All project documentation
├── docker/                     # Docker configuration files
├── scripts/                    # Utility scripts
├── utility/                    # Helper utilities and tools
├── tests/                      # Test files
├── data/                       # Runtime data (gitignored)
├── .github/                    # GitHub templates and workflows
├── docker-compose.yml         # Backend service orchestration
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── LICENSE                   # MIT License
└── README.md                 # Main project documentation
```

## Directory Details

### `/backend/` - Backend Application

Contains the complete Python FastAPI backend application.

```
backend/
├── app/                        # Application code
│   ├── __init__.py            # FastAPI app initialization
│   ├── auth.py                # HMAC signature verification
│   ├── models.py              # Pydantic models
│   ├── routes.py              # API endpoints
│   ├── storage.py             # File storage handlers
│   ├── background_jobs.py     # Async job processing
│   ├── llm_service.py         # LLM integration
│   ├── openmemory_client.py   # OpenMemory API client
│   └── elevenlabs_client.py   # ElevenLabs API client
├── config/                    # Configuration
│   ├── __init__.py
│   └── settings.py            # Settings and environment variables
├── main.py                    # Application entry point
└── requirements.txt           # Python dependencies
```

**Running the backend:**
```bash
cd backend
python main.py
```

### `/frontend/` - Frontend Applications

Contains all frontend applications with clear naming.

```
frontend/
├── react-portfolio/           # React-based portfolio/documentation site
│   ├── src/                   # React source code
│   │   ├── components/        # React components
│   │   ├── App.js            # Main app component
│   │   └── index.js          # Entry point
│   ├── public/               # Static assets
│   ├── package.json          # Node dependencies
│   └── README.md             # React app documentation
└── landing-page/             # Static HTML landing page
    ├── css/                  # Stylesheets
    ├── js/                   # JavaScript files
    ├── images/               # Image assets
    ├── index.html           # Main HTML file
    └── README.md            # Landing page documentation
```

**Running the React portfolio:**
```bash
cd frontend/react-portfolio
npm install
npm start
```

**Viewing the landing page:**
```bash
cd frontend/landing-page
python -m http.server 8080
# Open http://localhost:8080
```

### `/docs/` - Documentation

All project documentation in one organized location.

```
docs/
├── MEMORY_SYSTEM_GUIDE.md          # Memory system implementation
├── DEPLOYMENT.md                   # Deployment instructions
├── CONTRIBUTING.md                 # Contribution guidelines
├── SECURITY.md                     # Security policies
├── CHANGELOG.md                    # Version history
├── CODE_DOCUMENTATION_ALIGNMENT.md # Technical analysis
├── DOCUMENTATION_REVIEW.md         # Documentation review
├── MARKETING_STRATEGY.md           # Marketing documentation
├── EMAIL_MARKETING_CAMPAIGN.md     # Email marketing guide
├── PORTFOLIO_GUIDE.md              # Portfolio development guide
└── STRUCTURE.md                    # This file
```

### `/docker/` - Docker Configuration

Docker-related files for containerization.

```
docker/
└── Dockerfile                 # Backend container definition
```

The `Dockerfile` is configured to:
- Build the Python backend
- Install all dependencies
- Create necessary directories
- Expose port 8000
- Run the FastAPI application

### `/scripts/` - Utility Scripts

Automation and utility scripts.

```
scripts/
├── ngrok_config.py            # Ngrok tunnel configuration
└── services.sh                # Service management script
```

### `/utility/` - Helper Utilities

Tools for development and testing.

```
utility/
├── get_conversation.py        # Fetch conversations from ElevenLabs
├── generate_hmac.py          # Generate HMAC signatures for testing
├── sample_payload.json       # Sample webhook payload
└── README.md                 # Utility documentation
```

### `/tests/` - Test Files

Unit and integration tests.

```
tests/
└── test_webhook.py           # Webhook endpoint tests
```

### `/data/` - Runtime Data (Gitignored)

Generated at runtime, not committed to git.

```
data/
├── payloads/                 # Webhook payloads
│   └── [conversation_id]/   # Organized by conversation
└── logs/                     # Application logs
    └── app.log
```

**Note:** This directory is created automatically. Only `.gitkeep` files are tracked in git.

### `/.github/` - GitHub Configuration

GitHub-specific templates and workflows.

```
.github/
├── ISSUE_TEMPLATE/
│   ├── bug_report.md
│   ├── feature_request.md
│   └── question.md
└── PULL_REQUEST_TEMPLATE.md
```

## Key Configuration Files

### Root Level

- **`docker-compose.yml`** - Orchestrates the backend service (OpenMemory must be configured independently)
- **`.env.example`** - Template for environment variables
- **`.gitignore`** - Git ignore rules
- **`LICENSE`** - MIT License
- **`README.md`** - Main project documentation

## Changes from Previous Structure

### What Changed

1. **Backend consolidation**: Moved `app/`, `config/`, `main.py`, and `requirements.txt` into `backend/`
2. **Frontend organization**: Renamed and moved:
   - `portfolio/` → `frontend/react-portfolio/`
   - `website/` → `frontend/landing-page/`
3. **Documentation centralization**: Moved all `.md` files (except README) to `docs/`
4. **Docker organization**: Moved `Dockerfile` to `docker/`
5. **Data directory**: Created `data/` for runtime files (replacing root-level `payloads/`)

### Path Updates

All paths have been updated in:
- `README.md` - All documentation links and file references
- `.env.example` - Payload path changed to `./data/payloads`
- `backend/config/settings.py` - Default payload path updated
- `docker/Dockerfile` - Build paths updated for new structure
- `docker-compose.yml` - Volume mounts and paths updated

## Benefits of New Structure

### 1. Clear Separation of Concerns
- Backend code is isolated in `backend/`
- Frontend applications have their own space
- Documentation doesn't clutter the root

### 2. Better Scalability
- Easy to add new frontend applications
- Backend can be developed independently
- Documentation can grow without affecting code

### 3. Standard Industry Practice
- Follows common monorepo patterns
- Familiar structure for new contributors
- Easier to navigate for experienced developers

### 4. Improved Docker Support
- Clear containerization strategy
- Easy to add service-specific Dockerfiles
- Better multi-stage build support

### 5. Clean Root Directory
- Only essential files at root level
- Less confusion about what goes where
- Easier to find configuration files

## Development Workflow

### Starting the Full Stack

```bash
# Using Docker Compose (recommended)
# Note: OpenMemory must be configured and running independently
docker-compose up -d

# Or manually:
# Ensure OpenMemory is running independently, then:
# Terminal: Start Backend
cd backend
python main.py

# Terminal 3: Start React Portfolio (optional)
cd frontend/react-portfolio
npm start

# Terminal 4: Serve Landing Page (optional)
cd frontend/landing-page
python -m http.server 8080
```

### Adding New Components

**New backend module:**
```bash
touch backend/app/new_module.py
```

**New frontend app:**
```bash
mkdir frontend/new-app
```

**New documentation:**
```bash
touch docs/NEW_GUIDE.md
```

## Migration Notes

If you have an existing installation, update your:

1. **Environment variables** - Path to payloads is now `./data/payloads`
2. **Scripts** - Update any scripts that reference old paths
3. **Documentation links** - Update bookmarks to docs
4. **Docker volumes** - Update volume mounts if using custom docker-compose

## Questions?

- See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
- See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment instructions
- See [README.md](../README.md) for general documentation

## Maintaining This Structure

When adding new files or directories:

1. **Backend code** → `backend/app/`
2. **Configuration** → `backend/config/`
3. **Frontend apps** → `frontend/[app-name]/`
4. **Documentation** → `docs/`
5. **Scripts** → `scripts/`
6. **Tests** → `tests/`
7. **Utilities** → `utility/`

**Never** add application code directly to the root directory.
