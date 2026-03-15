#!/usr/bin/env python3
"""
Quick test script to verify Supabase integration structure.
Tests imports and basic functionality without requiring Supabase connection.
"""
import sys
import os

print("=" * 60)
print("Testing Supabase Integration")
print("=" * 60)

# Test 1: Check if required files exist
print("\n[1] Checking file structure...")
files_to_check = [
    "services/supabase_service.py",
    "schemas/auth.py",
    "routes_auth.py",
    "supabase_migration.sql",
    "SUPABASE_SETUP.md",
    "README_SUPABASE.md"
]

all_exist = True
for file in files_to_check:
    exists = os.path.exists(file)
    status = "✓" if exists else "✗"
    print(f"  {status} {file}")
    if not exists:
        all_exist = False

if all_exist:
    print("  ✓ All required files exist")
else:
    print("  ✗ Some files are missing")
    sys.exit(1)

# Test 2: Test imports (without Supabase package)
print("\n[2] Testing Python imports...")

try:
    from schemas.auth import (
        UserRegisterRequest,
        UserLoginRequest,
        DepartmentRegisterRequest,
        UserResponse,
        DepartmentResponse
    )
    print("  ✓ Auth schemas import successfully")
except ImportError as e:
    print(f"  ✗ Failed to import auth schemas: {e}")
    sys.exit(1)

try:
    # Test if supabase_service can be imported (will fail if supabase package not installed)
    try:
        from services.supabase_service import supabase_service
        print("  ✓ Supabase service imports successfully")
        print(f"    - Supabase available: {supabase_service.is_available()}")
    except ImportError as e:
        if "supabase" in str(e).lower():
            print("  ⚠ Supabase service import failed (supabase package not installed)")
            print("    This is expected. Run: pip install -r requirements.txt")
        else:
            print(f"  ✗ Failed to import supabase service: {e}")
            sys.exit(1)
except Exception as e:
    print(f"  ✗ Unexpected error: {e}")
    sys.exit(1)

# Test 3: Test route imports (may fail if supabase not installed)
print("\n[3] Testing route imports...")
try:
    from routes_auth import router
    print("  ✓ Auth routes import successfully")
    print(f"    - Router prefix: {router.prefix}")
    print(f"    - Router tags: {router.tags}")
except ImportError as e:
    if "supabase" in str(e).lower():
        print("  ⚠ Auth routes import failed (supabase package not installed)")
        print("    This is expected. Run: pip install -r requirements.txt")
        print("    Routes will work once supabase is installed")
    else:
        print(f"  ✗ Failed to import auth routes: {e}")
        sys.exit(1)
except Exception as e:
    print(f"  ✗ Unexpected error importing routes: {e}")
    sys.exit(1)

# Test 4: Test app.py integration
print("\n[4] Testing app.py integration...")
try:
    # Check if app.py has the imports
    with open("app.py", "r") as f:
        app_content = f.read()
        
    has_auth_import = "from routes_auth" in app_content
    has_supabase_import = "from services.supabase_service" in app_content
    has_router_include = "app.include_router(auth_router)" in app_content
    
    if has_auth_import and has_supabase_import and has_router_include:
        print("  ✓ app.py has all required imports and router inclusion")
    else:
        print("  ✗ app.py missing some integration:")
        print(f"    - Auth router import: {has_auth_import}")
        print(f"    - Supabase service import: {has_supabase_import}")
        print(f"    - Router inclusion: {has_router_include}")
        sys.exit(1)
except Exception as e:
    print(f"  ✗ Error checking app.py: {e}")
    sys.exit(1)

# Test 5: Check requirements.txt
print("\n[5] Checking requirements.txt...")
try:
    with open("requirements.txt", "r") as f:
        requirements = f.read()
    
    if "supabase" in requirements.lower():
        print("  ✓ requirements.txt includes supabase")
    else:
        print("  ✗ requirements.txt missing supabase")
        sys.exit(1)
except Exception as e:
    print(f"  ✗ Error checking requirements.txt: {e}")
    sys.exit(1)

# Test 6: Check SQL migration file
print("\n[6] Checking SQL migration file...")
try:
    with open("supabase_migration.sql", "r") as f:
        sql_content = f.read()
    
    required_tables = ["users", "departments", "ticket_users", "ticket_departments"]
    missing_tables = []
    
    for table in required_tables:
        if f"CREATE TABLE" in sql_content and table in sql_content:
            print(f"  ✓ Migration includes '{table}' table")
        else:
            missing_tables.append(table)
    
    if missing_tables:
        print(f"  ✗ Missing tables in migration: {missing_tables}")
        sys.exit(1)
except Exception as e:
    print(f"  ✗ Error checking migration file: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ All integration tests passed!")
print("=" * 60)
print("\nNext steps:")
print("1. Install dependencies: pip install -r requirements.txt")
print("2. Set up Supabase: See SUPABASE_SETUP.md")
print("3. Add environment variables to .env:")
print("   SUPABASE_URL=...")
print("   SUPABASE_ANON_KEY=...")
print("4. Run the server: uvicorn app:app --reload")
print("\n")
