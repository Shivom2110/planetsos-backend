"""
Supabase service for user and department account management.
Handles authentication, user registration, and department management.
"""
import os
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class SupabaseService:
    """Service for Supabase database operations."""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        self.client: Optional[Client] = None
        
        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
                logger.info("Supabase client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.client = None
        else:
            logger.warning("Supabase credentials not configured")
    
    def is_available(self) -> bool:
        """Check if Supabase is configured and available."""
        return self.client is not None
    
    # ==================== USER OPERATIONS ====================
    
    def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        phone: Optional[str] = None,
        role: str = "reporter"
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new user account (reporter).
        Returns user data if successful, None otherwise.
        """
        if not self.client:
            logger.warning("Supabase not configured, cannot create user")
            return None
        
        try:
            # Create auth user
            auth_response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name,
                        "phone": phone,
                        "role": role
                    }
                }
            })
            
            if not auth_response.user:
                logger.error("Failed to create auth user")
                return None
            
            user_id = auth_response.user.id
            
            # Create user profile in users table
            profile_data = {
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "phone": phone,
                "role": role,
                "created_at": "now()"
            }
            
            profile_response = self.client.table("users").insert(profile_data).execute()
            
            if profile_response.data:
                logger.info(f"User created successfully: {email}")
                return {
                    "user_id": user_id,
                    "email": email,
                    "full_name": full_name,
                    "phone": phone,
                    "role": role
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user and return session data.
        Returns user data with session token if successful.
        """
        if not self.client:
            logger.warning("Supabase not configured, cannot authenticate")
            return None
        
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user and response.session:
                # Get user profile
                profile = self.get_user_by_id(response.user.id)
                
                return {
                    "user_id": response.user.id,
                    "email": response.user.email,
                    "session_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "profile": profile
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by ID."""
        if not self.client:
            return None
        
        try:
            response = self.client.table("users").select("*").eq("id", user_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user profile by email."""
        if not self.client:
            return None
        
        try:
            response = self.client.table("users").select("*").eq("email", email).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def update_user_profile(
        self,
        user_id: str,
        full_name: Optional[str] = None,
        phone: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update user profile."""
        if not self.client:
            return None
        
        try:
            updates = {}
            if full_name:
                updates["full_name"] = full_name
            if phone:
                updates["phone"] = phone
            
            if not updates:
                return None
            
            updates["updated_at"] = "now()"
            
            response = self.client.table("users").update(updates).eq("id", user_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return None
    
    # ==================== DEPARTMENT OPERATIONS ====================
    
    def create_department(
        self,
        name: str,
        email: str,
        password: str,
        department_type: str,
        contact_phone: Optional[str] = None,
        address: Optional[str] = None,
        jurisdiction: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new department account (responder).
        Returns department data if successful, None otherwise.
        """
        if not self.client:
            logger.warning("Supabase not configured, cannot create department")
            return None
        
        try:
            # Create auth user for department
            auth_response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "name": name,
                        "role": "department"
                    }
                }
            })
            
            if not auth_response.user:
                logger.error("Failed to create department auth user")
                return None
            
            dept_id = auth_response.user.id
            
            # Create department profile in departments table
            dept_data = {
                "id": dept_id,
                "name": name,
                "email": email,
                "department_type": department_type,
                "contact_phone": contact_phone,
                "address": address,
                "jurisdiction": jurisdiction,
                "is_active": True,
                "created_at": "now()"
            }
            
            dept_response = self.client.table("departments").insert(dept_data).execute()
            
            if dept_response.data:
                logger.info(f"Department created successfully: {name}")
                return {
                    "department_id": dept_id,
                    "name": name,
                    "email": email,
                    "department_type": department_type,
                    "contact_phone": contact_phone,
                    "address": address,
                    "jurisdiction": jurisdiction
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating department: {e}")
            return None
    
    def authenticate_department(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a department and return session data.
        Returns department data with session token if successful.
        """
        if not self.client:
            logger.warning("Supabase not configured, cannot authenticate department")
            return None
        
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user and response.session:
                # Get department profile
                dept = self.get_department_by_id(response.user.id)
                
                if not dept:
                    logger.warning(f"Department profile not found for user: {response.user.id}")
                    return None
                
                return {
                    "department_id": response.user.id,
                    "email": response.user.email,
                    "session_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "department": dept
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error authenticating department: {e}")
            return None
    
    def get_department_by_id(self, department_id: str) -> Optional[Dict[str, Any]]:
        """Get department profile by ID."""
        if not self.client:
            return None
        
        try:
            response = self.client.table("departments").select("*").eq("id", department_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting department: {e}")
            return None
    
    def get_department_by_type(self, department_type: str) -> List[Dict[str, Any]]:
        """Get all departments of a specific type."""
        if not self.client:
            return []
        
        try:
            response = self.client.table("departments").select("*").eq("department_type", department_type).eq("is_active", True).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error getting departments by type: {e}")
            return []
    
    def get_all_departments(self) -> List[Dict[str, Any]]:
        """Get all active departments."""
        if not self.client:
            return []
        
        try:
            response = self.client.table("departments").select("*").eq("is_active", True).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error getting all departments: {e}")
            return []
    
    def update_department(
        self,
        department_id: str,
        name: Optional[str] = None,
        contact_phone: Optional[str] = None,
        address: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """Update department profile."""
        if not self.client:
            return None
        
        try:
            updates = {}
            if name:
                updates["name"] = name
            if contact_phone:
                updates["contact_phone"] = contact_phone
            if address:
                updates["address"] = address
            if jurisdiction:
                updates["jurisdiction"] = jurisdiction
            if is_active is not None:
                updates["is_active"] = is_active
            
            if not updates:
                return None
            
            updates["updated_at"] = "now()"
            
            response = self.client.table("departments").update(updates).eq("id", department_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error updating department: {e}")
            return None
    
    # ==================== TICKET-USER LINKING ====================
    
    def link_ticket_to_user(self, ticket_id: str, user_id: str) -> bool:
        """Link a ticket to a user (reporter)."""
        if not self.client:
            return False
        
        try:
            # This would update a tickets table if it exists in Supabase
            # For now, we'll store this relationship in a separate table
            link_data = {
                "ticket_id": ticket_id,
                "user_id": user_id,
                "created_at": "now()"
            }
            
            response = self.client.table("ticket_users").upsert(link_data).execute()
            return response.data is not None
            
        except Exception as e:
            logger.error(f"Error linking ticket to user: {e}")
            return False
    
    def link_ticket_to_department(self, ticket_id: str, department_id: str) -> bool:
        """Link a ticket to a department (responder)."""
        if not self.client:
            return False
        
        try:
            link_data = {
                "ticket_id": ticket_id,
                "department_id": department_id,
                "created_at": "now()"
            }
            
            response = self.client.table("ticket_departments").upsert(link_data).execute()
            return response.data is not None
            
        except Exception as e:
            logger.error(f"Error linking ticket to department: {e}")
            return False
    
    def get_user_tickets(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all tickets reported by a user."""
        if not self.client:
            return []
        
        try:
            response = self.client.table("ticket_users").select("ticket_id").eq("user_id", user_id).execute()
            ticket_ids = [row["ticket_id"] for row in (response.data or [])]
            return ticket_ids
        except Exception as e:
            logger.error(f"Error getting user tickets: {e}")
            return []
    
    def get_department_tickets(self, department_id: str) -> List[Dict[str, Any]]:
        """Get all tickets assigned to a department."""
        if not self.client:
            return []
        
        try:
            response = self.client.table("ticket_departments").select("ticket_id").eq("department_id", department_id).execute()
            ticket_ids = [row["ticket_id"] for row in (response.data or [])]
            return ticket_ids
        except Exception as e:
            logger.error(f"Error getting department tickets: {e}")
            return []


# Global service instance
supabase_service = SupabaseService()
