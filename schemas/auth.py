"""
Pydantic schemas for authentication and user/department management.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """Request schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: str = Field(..., min_length=1, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)


class UserLoginRequest(BaseModel):
    """Request schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Response schema for user data."""
    user_id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    role: str = "reporter"


class UserAuthResponse(BaseModel):
    """Response schema for user authentication."""
    user_id: str
    email: str
    session_token: str
    refresh_token: str
    profile: UserResponse


class DepartmentRegisterRequest(BaseModel):
    """Request schema for department registration."""
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8)
    department_type: str = Field(..., description="Type of department (e.g., 'municipal', 'environmental', 'emergency')")
    contact_phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    jurisdiction: Optional[str] = Field(None, max_length=200, description="Geographic jurisdiction")


class DepartmentLoginRequest(BaseModel):
    """Request schema for department login."""
    email: EmailStr
    password: str


class DepartmentResponse(BaseModel):
    """Response schema for department data."""
    department_id: str
    name: str
    email: str
    department_type: str
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    jurisdiction: Optional[str] = None
    is_active: bool = True


class DepartmentAuthResponse(BaseModel):
    """Response schema for department authentication."""
    department_id: str
    email: str
    session_token: str
    refresh_token: str
    department: DepartmentResponse


class UserUpdateRequest(BaseModel):
    """Request schema for updating user profile."""
    full_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)


class DepartmentUpdateRequest(BaseModel):
    """Request schema for updating department profile."""
    name: Optional[str] = Field(None, max_length=200)
    contact_phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    jurisdiction: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None
