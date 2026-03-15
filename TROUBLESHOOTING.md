# Troubleshooting "Resolution Too Deep" Error

## Common Causes

The "resolution too deep" error in Python typically occurs due to:

1. **Circular Imports** - Modules importing each other in a loop
2. **Deep Type Validation** - Pydantic models with deep nesting causing recursion
3. **EmailStr Validation** - Pydantic's EmailStr can cause deep validation in some cases

## Fixes Applied

### 1. Supabase Service Import
- Made Supabase imports optional/defensive
- Service works even if package isn't installed
- Uses `Any` type instead of `Client` to avoid type resolution issues

### 2. Pydantic Model Configuration
- Added `model_config` to nested models
- Disabled `validate_assignment` to reduce validation depth
- Enabled `str_strip_whitespace` for cleaner string handling

### 3. Removed Duplicate load_dotenv()
- Only called once in app.py
- Removed from supabase_service.py to avoid conflicts

## If Error Persists

### Check 1: Verify No Circular Imports
```bash
python3 -c "import app" 2>&1 | grep -i "circular\|import"
```

### Check 2: Test Individual Modules
```bash
python3 -c "from schemas.auth import UserResponse; print('OK')"
python3 -c "from services.supabase_service import supabase_service; print('OK')"
python3 -c "from routes_auth import router; print('OK')"
```

### Check 3: Check Pydantic Version
```bash
pip show pydantic
```
Should be version 2.x. If using v1, upgrade:
```bash
pip install --upgrade pydantic
```

### Check 4: Simplify EmailStr Usage
If EmailStr is causing issues, you can temporarily replace it:
```python
# Instead of:
email: EmailStr

# Use:
email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
```

### Check 5: Run with Type Checking Disabled
```bash
python3 -X dev app.py
```

## Quick Fix

If you're still getting the error, try this minimal test:

```python
# test_minimal.py
from fastapi import FastAPI
from schemas.auth import UserResponse

app = FastAPI()

@app.get("/test")
def test():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)
```

Run: `python3 test_minimal.py`

If this works, the issue is in the route definitions or nested models.

## When Does the Error Occur?

Please note when you see the error:
- [ ] When starting the server (`uvicorn app:app`)
- [ ] When accessing `/docs` (OpenAPI generation)
- [ ] When making a specific API request
- [ ] When importing modules

This will help identify the exact cause.
