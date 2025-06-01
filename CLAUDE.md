# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FinMan is a personal and family financial management API built with FastAPI, designed for Ukrainian users with support for multiple banks (MonoBank, PUMB, Revolut, Wise). It handles real-time transaction processing, PDF statement parsing, multi-currency support, and group financial management.

## Architecture

**Tech Stack:**
- FastAPI 1.0.0 with Uvicorn/Gunicorn
- MySQL database with SQLAlchemy 2.0.36 ORM
- Alembic for database migrations
- JWT authentication with custom OAuth2
- Docker containerization

**API Structure:**
The API is organized by feature modules in `/api/`:
- `categories/` - Expense categories
- `core/` - Bank integrations (erste/, pumb/, revolut/, wise/)
- `groups/` - Family/group management
- `mono/` - MonoBank real-time API integration
- `payments/` - Transaction processing
- `utilities/` - Utility endpoints

**Key Models:**
- Users, Payments, Categories, Groups, MonoUsers, Currencies
- Located in `/models/models.py`
- Uses SQLAlchemy 2.0 async patterns

## Development Commands

**Local Development:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8090
```

**Docker:**
```bash
docker compose up -d  # Includes auto-migration on startup
```

**Database Migrations:**
```bash
alembic upgrade head
alembic revision --autogenerate -m "description"
```

**Currency Data:**
```bash
python scripts/get_currencies.py
```

## Configuration

Environment variables required (see `.env`):
- Database connection (MySQL)
- MonoBank API credentials
- JWT secrets
- CORS origins
- Logging configuration

## Bank Integration Patterns

**MonoBank:** Real-time webhook processing with user token management
**PUMB:** PDF statement parsing with sequence number tracking
**Revolut/Wise:** Statement file import functionality

Each bank integration follows the pattern:
- Core processing in `/api/core/{bank}/funcs.py`
- API endpoints in respective route modules
- Transaction normalization for unified payment processing

## Key Development Notes

- FastAPI dependency injection used for auth and database sessions
- Custom exception handling in `/app/exceptions.py`
- Structured logging with rotation
- Multi-currency support with automatic exchange rate fetching
- Group-based financial management for families
- No current test suite (empty `/tests/` directory)