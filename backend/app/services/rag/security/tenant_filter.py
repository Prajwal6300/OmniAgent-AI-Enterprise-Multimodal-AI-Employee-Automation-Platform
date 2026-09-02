from uuid import UUID
from sqlalchemy import Select

class TenantFilter:
    @staticmethod
    def apply(stmt: Select, model_cls, org_id: UUID) -> Select:
        return stmt.where(model_cls.organization_id == org_id)
