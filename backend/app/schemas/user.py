from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    role_id: UUID
    organization_id: UUID
    department_id: Optional[UUID] = None

class UserRead(UserBase):
    id: UUID
    organization_id: UUID
    department_id: Optional[UUID] = None
    role_id: UUID
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True
