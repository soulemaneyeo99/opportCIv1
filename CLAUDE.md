# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpportuCI is an AI-powered opportunity platform for Ivorian youth. It aggregates scholarships, internships, jobs, and training opportunities while providing personalized recommendations, interview simulations, and learning paths.

## Commands

```bash
# Development setup
make install              # Install Python dependencies
make setup-dev            # Full dev setup (install + migrate + collectstatic)
cp backend/.env.example backend/.env.local  # Required before running

# Running locally
make run                  # Django dev server on :8000
make celery-worker        # Background task worker
make celery-beat          # Scheduled tasks

# Docker (full stack)
make docker-up            # Start all services (db, redis, backend, frontend, celery)
make docker-down          # Stop all services
make docker-logs          # View logs

# Database
make migrate              # Apply migrations
make makemigrations       # Create new migrations
make seed                 # Populate test data

# Testing
make test                 # Full test suite with coverage
make test-fast            # Quick tests (no coverage)
pytest backend/apps/accounts/tests/ -v  # Single app tests
pytest -k "test_user" -v  # Run tests matching pattern

# Code quality
make format               # black + isort
make lint                 # flake8 + pylint
make type-check           # mypy
```

## Architecture

### Backend (Django 4.2 + DRF)

**App Structure:** Each app in `backend/apps/` follows this pattern:
```
apps/{app_name}/
├── models/          # Domain models (split by entity)
├── api/
│   ├── views.py     # DRF ViewSets
│   ├── serializers.py
│   ├── urls.py
│   └── permissions.py
├── services/        # Business logic (keep views thin)
├── tasks/           # Celery async tasks
└── admin.py
```

**Domain Apps:**
- `accounts` - Custom User model with email as username, UserProfile with Ivorian context (cities, phone validation)
- `opportunities` - Opportunity, OpportunityCategory, UserOpportunity (saved/applied/viewed relations)
- `learning` - Formation > Course > Lesson hierarchy with quiz system (Question/Answer/UserProgress)
- `simulations` - InterviewSimulation with AI-powered conversations stored in JSONField
- `credibility` - Gamification: CredibilityPoints, Badge, Achievement with level progression
- `ai` - GeminiAIService wrapping Google's Gemini API for all AI features
- `notifications` - Generic notification system with ContentType for polymorphic relations
- `content` - Content scraping and aggregation
- `analytics` - Dashboard and reporting services

**AI Service (`backend/apps/ai/services/gemini_service.py`):**
Central AI hub using Gemini. Methods return structured JSON for:
- `get_opportunity_recommendations()` - Match user profile to opportunities
- `generate_career_advice()` - Personalized career guidance
- `analyze_skill_gaps()` - Compare user skills vs target position
- `generate_interview_response()` / `evaluate_interview()` - Power interview simulations
- `generate_learning_path()` - Create personalized module sequences

**Key Settings:**
- Auth: JWT via SimpleJWT (1h access / 7d refresh tokens)
- Async: Celery with Redis broker, django-celery-beat for scheduling
- WebSocket: Django Channels with Redis channel layer
- Cache: django-redis with 5min default TTL
- API docs: drf-yasg at `/api/docs/`

### Frontend (Next.js + TypeScript + Tailwind)

Located in `frontend/`. Types in `frontend/src/types/`. Connects to backend API at `NEXT_PUBLIC_API_URL`.

### Infrastructure

- `docker-compose.yml` - Full dev stack: PostgreSQL 15, Redis 7, Django, Celery worker/beat, Flower, Next.js
- Services: db (:5432), redis (:6379), backend (:8000), frontend (:3000), flower (:5555)

## Conventions

- **Language:** French for user-facing text (models use `gettext_lazy`), English for code
- **Currency:** XOF (CFA Franc) for financial fields
- **Location:** Default to Côte d'Ivoire context (cities, phone regex `+225...`)
- **UUIDs:** Used as primary keys for Opportunity, InterviewSimulation
- **Slugs:** Auto-generated from titles with uniqueness handling
- **Pagination:** StandardResultsSetPagination (20 items/page) defined in `core/pagination.py`

## API Routes

All API routes prefixed with `/api/`:
- `/api/accounts/` - Auth, registration, profile
- `/api/opportunities/` - CRUD + recommendations
- `/api/learning/` - Formations, courses, progress
- `/api/simulations/` - Interview simulations
- `/api/credibility/` - Points, badges, achievements
- `/api/notifications/` - User notifications

Admin: `/admin/`
