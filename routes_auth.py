"""
Authentication routes for users and departments.
Handles registration, login, and profile management.
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import logging

from schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    UserAuthResponse,
    DepartmentRegisterRequest,
    DepartmentLoginRequest,
    DepartmentResponse,
    DepartmentAuthResponse,
    UserUpdateRequest,
    DepartmentUpdateRequest
)
from services.supabase_service import supabase_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


# ==================== USER ROUTES ====================

@router.post("/user/register", response_model=UserResponse)
async def register_user(request: UserRegisterRequest):
    """
    Register a new user account (reporter).
    
    Creates both an authentication account and a user profile.
    """
    if not supabase_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="User registration service is not available. Supabase not configured."
        )
    
    # Check if user already exists
    existing_user = supabase_service.get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )
    
    # Create user
    user_data = supabase_service.create_user(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        phone=request.phone,
        role="reporter"
    )
    
    if not user_data:
        raise HTTPException(
            status_code=500,
            detail="Failed to create user account"
        )
    
    return UserResponse(**user_data)


@router.post("/user/login", response_model=UserAuthResponse)
async def login_user(request: UserLoginRequest):
    """
    Authenticate a user and return session tokens.
    
    Returns user profile and authentication tokens.
    """
    if not supabase_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Authentication service is not available. Supabase not configured."
        )
    
    auth_data = supabase_service.authenticate_user(
        email=request.email,
        password=request.password
    )
    
    if not auth_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    return UserAuthResponse(**auth_data)


@router.get("/user/profile", response_model=UserResponse)
async def get_user_profile(
    authorization: Optional[str] = Header(None)
):
    """
    Get current user profile.
    
    Requires authentication token in Authorization header.
    """
    if not supabase_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Service not available"
        )
    
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization token required"
        )
    
    # Extract token (assuming "Bearer <token>" format)
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    try:
        # Verify token and get user
        user = supabase_service.client.auth.get_user(token)
        if not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        profile = supabase_service.get_user_by_id(user.user.id)
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        return UserResponse(
            user_id=profile["id"],
            email=profile["email"],
            full_name=profile["full_name"],
            phone=profile.get("phone"),
            role=profile.get("role", "reporter")
        )
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.put("/user/profile", response_model=UserResponse)
async def update_user_profile(
    request: UserUpdateRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Update current user profile.
    
    Requires authentication token in Authorization header.
    """
    if not supabase_service.is_available():
        raise HTTPException(status_code=503, detail="Service not available")
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization token required")
    
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    try:
        user = supabase_service.client.auth.get_user(token)
        if not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        updated = supabase_service.update_user_profile(
            user_id=user.user.id,
            full_name=request.full_name,
            phone=request.phone
        )
        
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update profile")
        
        return UserResponse(
            user_id=updated["id"],
            email=updated["email"],
            full_name=updated["full_name"],
            phone=updated.get("phone"),
            role=updated.get("role", "reporter")
        )
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ==================== DEPARTMENT ROUTES ====================

@router.post("/department/register", response_model=DepartmentResponse)
async def register_department(request: DepartmentRegisterRequest):
    """
    Register a new department account (responder).
    
    Creates both an authentication account and a department profile.
    """
    if not supabase_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Department registration service is not available. Supabase not configured."
        )
    
    # Check if department already exists
    existing_dept = supabase_service.get_department_by_id(request.email)  # Using email as check
    # Note: In production, you'd want a proper email check
    
    # Create department
    dept_data = supabase_service.create_department(
        name=request.name,
        email=request.email,
        password=request.password,
        department_type=request.department_type,
        contact_phone=request.contact_phone,
        address=request.address,
        jurisdiction=request.jurisdiction
    )
    
    if not dept_data:
        raise HTTPException(
            status_code=500,
            detail="Failed to create department account"
        )
    
    return DepartmentResponse(**dept_data)


@router.post("/department/login", response_model=DepartmentAuthResponse)
async def login_department(request: DepartmentLoginRequest):
    """
    Authenticate a department and return session tokens.
    
    Returns department profile and authentication tokens.
    """
    if not supabase_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Authentication service is not available. Supabase not configured."
        )
    
    auth_data = supabase_service.authenticate_department(
        email=request.email,
        password=request.password
    )
    
    if not auth_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    return DepartmentAuthResponse(**auth_data)


@router.get("/department/profile", response_model=DepartmentResponse)
async def get_department_profile(
    authorization: Optional[str] = Header(None)
):
    """
    Get current department profile.
    
    Requires authentication token in Authorization header.
    """
    if not supabase_service.is_available():
        raise HTTPException(status_code=503, detail="Service not available")
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization token required")
    
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    try:
        user = supabase_service.client.auth.get_user(token)
        if not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        dept = supabase_service.get_department_by_id(user.user.id)
        if not dept:
            raise HTTPException(status_code=404, detail="Department profile not found")
        
        return DepartmentResponse(**dept)
    except Exception as e:
        logger.error(f"Error getting department profile: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.put("/department/profile", response_model=DepartmentResponse)
async def update_department_profile(
    request: DepartmentUpdateRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Update current department profile.
    
    Requires authentication token in Authorization header.
    """
    if not supabase_service.is_available():
        raise HTTPException(status_code=503, detail="Service not available")
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization token required")
    
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    try:
        user = supabase_service.client.auth.get_user(token)
        if not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        updated = supabase_service.update_department(
            department_id=user.user.id,
            name=request.name,
            contact_phone=request.contact_phone,
            address=request.address,
            jurisdiction=request.jurisdiction,
            is_active=request.is_active
        )
        
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update profile")
        
        return DepartmentResponse(**updated)
    except Exception as e:
        logger.error(f"Error updating department profile: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.get("/departments", response_model=list[DepartmentResponse])
async def list_departments(department_type: Optional[str] = None):
    """
    List all active departments.
    
    Optionally filter by department_type.
    """
    if not supabase_service.is_available():
        raise HTTPException(status_code=503, detail="Service not available")
    
    if department_type:
        departments = supabase_service.get_department_by_type(department_type)
    else:
        departments = supabase_service.get_all_departments()
    
    return [DepartmentResponse(**dept) for dept in departments]
