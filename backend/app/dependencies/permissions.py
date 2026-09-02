from typing import List
from fastapi import Depends, HTTPException, status
from app.models.user import User
from app.dependencies.auth import get_current_user

def require_role(allowed_roles: List[str]):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.role or current_user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted for role: {current_user.role.name if current_user.role else 'None'}"
            )
        return current_user
    return role_checker
