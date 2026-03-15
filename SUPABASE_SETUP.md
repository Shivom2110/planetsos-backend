# Supabase Setup Guide

This guide explains how to set up Supabase for user and department account management in PlanetsOS.

## Prerequisites

1. A Supabase account (sign up at https://supabase.com)
2. A Supabase project created

## Setup Steps

### 1. Create Supabase Project

1. Go to https://supabase.com and sign in
2. Click "New Project"
3. Fill in project details:
   - Name: `planetsos` (or your preferred name)
   - Database Password: (choose a strong password)
   - Region: (choose closest to your users)
4. Wait for project to be created (takes ~2 minutes)

### 2. Get API Credentials

1. In your Supabase project dashboard, go to **Settings** → **API**
2. Copy the following values:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon/public key** (starts with `eyJ...`)

### 3. Set Environment Variables

Add these to your `.env` file:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 4. Run Database Migration

1. In Supabase dashboard, go to **SQL Editor**
2. Click **New Query**
3. Copy and paste the contents of `supabase_migration.sql`
4. Click **Run** (or press Cmd/Ctrl + Enter)
5. Verify tables were created by checking **Table Editor**

### 5. Verify Tables Created

You should see these tables in the **Table Editor**:
- `users` - User (reporter) accounts
- `departments` - Department (responder) accounts
- `ticket_users` - Links tickets to users
- `ticket_departments` - Links tickets to departments

## Database Schema Overview

### Users Table
Stores user (reporter) account information:
- `id` - UUID (linked to auth.users)
- `email` - User email
- `full_name` - User's full name
- `phone` - Contact phone (optional)
- `role` - Always "reporter" for users
- `created_at` - Account creation timestamp
- `updated_at` - Last update timestamp

### Departments Table
Stores department (responder) account information:
- `id` - UUID (linked to auth.users)
- `name` - Department name
- `email` - Department email
- `department_type` - Type (e.g., "municipal", "environmental", "emergency")
- `contact_phone` - Contact phone (optional)
- `address` - Physical address (optional)
- `jurisdiction` - Geographic jurisdiction (optional)
- `is_active` - Whether department is active
- `created_at` - Account creation timestamp
- `updated_at` - Last update timestamp

### Linking Tables
- `ticket_users` - Links tickets to reporting users
- `ticket_departments` - Links tickets to responding departments

## API Endpoints

### User Authentication

- `POST /auth/user/register` - Register new user
- `POST /auth/user/login` - Login user
- `GET /auth/user/profile` - Get user profile (requires auth token)
- `PUT /auth/user/profile` - Update user profile (requires auth token)

### Department Authentication

- `POST /auth/department/register` - Register new department
- `POST /auth/department/login` - Login department
- `GET /auth/department/profile` - Get department profile (requires auth token)
- `PUT /auth/department/profile` - Update department profile (requires auth token)
- `GET /auth/departments` - List all active departments

## Example Usage

### Register a User

```bash
curl -X POST "http://localhost:8000/auth/user/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepassword123",
    "full_name": "John Doe",
    "phone": "+1-555-0123"
  }'
```

### Login User

```bash
curl -X POST "http://localhost:8000/auth/user/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepassword123"
  }'
```

Response includes `session_token` which should be used in `Authorization: Bearer <token>` header.

### Register a Department

```bash
curl -X POST "http://localhost:8000/auth/department/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "City Environmental Department",
    "email": "env@city.gov",
    "password": "securepassword123",
    "department_type": "environmental",
    "contact_phone": "+1-555-0100",
    "address": "123 Main St, City, State",
    "jurisdiction": "City of Example"
  }'
```

### Create Ticket (with Authentication)

```bash
curl -X POST "http://localhost:8000/report" \
  -H "Authorization: Bearer <session_token>" \
  -F "role=reporter" \
  -F "latitude=40.7128" \
  -F "longitude=-74.0060" \
  -F "reporter_text=Plastic waste in river" \
  -F "file=@image.jpg"
```

The ticket will be automatically linked to the authenticated user.

### Respond to Ticket (with Authentication)

```bash
curl -X POST "http://localhost:8000/respond" \
  -H "Authorization: Bearer <department_session_token>" \
  -F "ticket_id=<ticket_id>" \
  -F "responder_type=environmental" \
  -F "latitude=40.7128" \
  -F "longitude=-74.0060" \
  -F "responder_text=We will send a cleanup crew"
```

The ticket will be automatically linked to the authenticated department.

## Row Level Security (RLS)

Supabase uses Row Level Security to ensure:
- Users can only view/update their own profiles
- Departments can only view/update their own profiles
- Users can view their own ticket links
- Departments can view their own ticket links
- Anyone can view active departments (for ticket assignment)

## Troubleshooting

### "Supabase not configured" error
- Check that `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set in `.env`
- Restart the FastAPI server after adding environment variables

### "Table does not exist" error
- Make sure you ran the migration SQL in Supabase SQL Editor
- Check that tables appear in Table Editor

### Authentication fails
- Verify email and password are correct
- Check that user/department was created successfully
- Ensure token is being sent in `Authorization: Bearer <token>` header

### Permission denied errors
- Check Row Level Security policies are set correctly
- Verify user is authenticated with valid token

## Next Steps

1. Set up email templates in Supabase for email verification (optional)
2. Configure OAuth providers if needed (Google, GitHub, etc.)
3. Set up email notifications for ticket assignments
4. Add more department types as needed
