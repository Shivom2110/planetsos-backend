# Supabase Integration Summary

## Overview

Supabase has been integrated into PlanetsOS backend for user and department account management. This enables:

1. **User Accounts**: Reporters can create accounts, login, and have their tickets linked to their profile
2. **Department Accounts**: Responders (departments) can create accounts, login, and have tickets assigned to them
3. **Authentication**: Secure authentication using Supabase Auth
4. **Database**: PostgreSQL database managed by Supabase for user/department data

## What Was Added

### 1. Dependencies
- Added `supabase==2.3.0` to `requirements.txt`

### 2. New Files Created

#### Services
- `services/supabase_service.py` - Supabase client and database operations
  - User management (create, authenticate, get, update)
  - Department management (create, authenticate, get, update, list)
  - Ticket linking (link tickets to users and departments)

#### Schemas
- `schemas/auth.py` - Pydantic models for authentication
  - User registration/login requests and responses
  - Department registration/login requests and responses
  - Profile update requests

#### Routes
- `routes_auth.py` - Authentication API endpoints
  - User registration and login
  - Department registration and login
  - Profile management (get/update)
  - Department listing

#### Database
- `supabase_migration.sql` - SQL schema for Supabase tables
  - `users` table
  - `departments` table
  - `ticket_users` linking table
  - `ticket_departments` linking table
  - Row Level Security policies
  - Indexes for performance

#### Documentation
- `SUPABASE_SETUP.md` - Complete setup guide
- `README_SUPABASE.md` - This file

### 3. Modified Files

#### `app.py`
- Added import for auth routes and Supabase service
- Included auth router in FastAPI app
- Updated `/report` endpoint to optionally link tickets to authenticated users
- Updated `/respond` endpoint to optionally link tickets to authenticated departments

## API Endpoints Added

### User Endpoints
- `POST /auth/user/register` - Register new user
- `POST /auth/user/login` - Login user
- `GET /auth/user/profile` - Get user profile (requires auth)
- `PUT /auth/user/profile` - Update user profile (requires auth)

### Department Endpoints
- `POST /auth/department/register` - Register new department
- `POST /auth/department/login` - Login department
- `GET /auth/department/profile` - Get department profile (requires auth)
- `PUT /auth/department/profile` - Update department profile (requires auth)
- `GET /auth/departments` - List all active departments

## Environment Variables Required

Add to `.env`:
```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Setup Instructions

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create Supabase project**:
   - Go to https://supabase.com
   - Create a new project
   - Get your project URL and anon key

3. **Set environment variables**:
   - Add `SUPABASE_URL` and `SUPABASE_ANON_KEY` to `.env`

4. **Run database migration**:
   - Open Supabase SQL Editor
   - Copy and paste `supabase_migration.sql`
   - Run the SQL

5. **Start the server**:
   ```bash
   uvicorn app:app --reload
   ```

## How It Works

### User Flow

1. User registers via `POST /auth/user/register`
2. User logs in via `POST /auth/user/login` → receives `session_token`
3. User creates ticket via `POST /report` with `Authorization: Bearer <token>` header
4. Ticket is automatically linked to user in `ticket_users` table

### Department Flow

1. Department registers via `POST /auth/department/register`
2. Department logs in via `POST /auth/department/login` → receives `session_token`
3. Department responds to ticket via `POST /respond` with `Authorization: Bearer <token>` header
4. Ticket is automatically linked to department in `ticket_departments` table

### Anonymous Flow

- Users can still create tickets without authentication (anonymous reports)
- Departments can still respond without authentication (if needed)
- Tickets are simply not linked to accounts in these cases

## Database Schema

### Users Table
```sql
- id (UUID, primary key, references auth.users)
- email (TEXT, unique)
- full_name (TEXT)
- phone (TEXT, optional)
- role (TEXT, default 'reporter')
- created_at, updated_at (timestamps)
```

### Departments Table
```sql
- id (UUID, primary key, references auth.users)
- name (TEXT)
- email (TEXT, unique)
- department_type (TEXT)
- contact_phone (TEXT, optional)
- address (TEXT, optional)
- jurisdiction (TEXT, optional)
- is_active (BOOLEAN, default TRUE)
- created_at, updated_at (timestamps)
```

### Linking Tables
- `ticket_users`: Links `ticket_id` (TEXT) to `user_id` (UUID)
- `ticket_departments`: Links `ticket_id` (TEXT) to `department_id` (UUID)

## Security Features

1. **Row Level Security (RLS)**: Enabled on all tables
2. **User Isolation**: Users can only see/update their own profiles
3. **Department Isolation**: Departments can only see/update their own profiles
4. **Public Department List**: Active departments are visible to all (for ticket assignment)
5. **Token-based Auth**: JWT tokens for secure authentication

## Testing

### Test User Registration
```bash
curl -X POST "http://localhost:8000/auth/user/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
  }'
```

### Test User Login
```bash
curl -X POST "http://localhost:8000/auth/user/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

### Test Department Registration
```bash
curl -X POST "http://localhost:8000/auth/department/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Department",
    "email": "dept@example.com",
    "password": "testpassword123",
    "department_type": "environmental"
  }'
```

## Next Steps

1. Set up email verification in Supabase (optional)
2. Add password reset functionality
3. Add OAuth providers (Google, GitHub, etc.)
4. Create admin endpoints for managing departments
5. Add ticket assignment notifications
6. Create dashboard endpoints for users to view their tickets
7. Create dashboard endpoints for departments to view assigned tickets

## Notes

- Supabase integration is **optional** - the app works without it
- If Supabase is not configured, authentication endpoints return 503 errors
- Tickets can still be created/responded to without authentication (anonymous mode)
- All Supabase operations gracefully handle missing configuration
