from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    role_id: UUID
    organization_id: UUID
    department_id: UUID | None = None

class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    department_id: UUID | None = None
    role_id: UUID
    is_verified: bool
    created_at: datetime
