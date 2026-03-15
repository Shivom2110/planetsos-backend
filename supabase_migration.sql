-- PlanetsOS Supabase Database Schema
-- Run this SQL in your Supabase SQL Editor to create the necessary tables

-- ==================== USERS TABLE ====================
-- Stores user (reporter) account information
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    phone TEXT,
    role TEXT DEFAULT 'reporter',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own profile
CREATE POLICY "Users can view own profile"
    ON users FOR SELECT
    USING (auth.uid() = id);

-- Policy: Users can update their own profile
CREATE POLICY "Users can update own profile"
    ON users FOR UPDATE
    USING (auth.uid() = id);

-- ==================== DEPARTMENTS TABLE ====================
-- Stores department (responder) account information
CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    department_type TEXT NOT NULL,
    contact_phone TEXT,
    address TEXT,
    jurisdiction TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE departments ENABLE ROW LEVEL SECURITY;

-- Policy: Departments can read their own profile
CREATE POLICY "Departments can view own profile"
    ON departments FOR SELECT
    USING (auth.uid() = id);

-- Policy: Departments can update their own profile
CREATE POLICY "Departments can update own profile"
    ON departments FOR UPDATE
    USING (auth.uid() = id);

-- Policy: Anyone can view active departments (for assignment)
CREATE POLICY "Anyone can view active departments"
    ON departments FOR SELECT
    USING (is_active = TRUE);

-- ==================== TICKET-USERS LINKING TABLE ====================
-- Links tickets to users (reporters)
CREATE TABLE IF NOT EXISTS ticket_users (
    ticket_id TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (ticket_id, user_id)
);

-- Enable Row Level Security
ALTER TABLE ticket_users ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own ticket links
CREATE POLICY "Users can view own ticket links"
    ON ticket_users FOR SELECT
    USING (auth.uid() = user_id);

-- ==================== TICKET-DEPARTMENTS LINKING TABLE ====================
-- Links tickets to departments (responders)
CREATE TABLE IF NOT EXISTS ticket_departments (
    ticket_id TEXT NOT NULL,
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (ticket_id, department_id)
);

-- Enable Row Level Security
ALTER TABLE ticket_departments ENABLE ROW LEVEL SECURITY;

-- Policy: Departments can view their own ticket links
CREATE POLICY "Departments can view own ticket links"
    ON ticket_departments FOR SELECT
    USING (auth.uid() = department_id);

-- ==================== INDEXES ====================
-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_departments_email ON departments(email);
CREATE INDEX IF NOT EXISTS idx_departments_type ON departments(department_type);
CREATE INDEX IF NOT EXISTS idx_departments_active ON departments(is_active);
CREATE INDEX IF NOT EXISTS idx_ticket_users_user_id ON ticket_users(user_id);
CREATE INDEX IF NOT EXISTS idx_ticket_users_ticket_id ON ticket_users(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_departments_dept_id ON ticket_departments(department_id);
CREATE INDEX IF NOT EXISTS idx_ticket_departments_ticket_id ON ticket_departments(ticket_id);

-- ==================== FUNCTIONS ====================
-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers to auto-update updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_departments_updated_at
    BEFORE UPDATE ON departments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
