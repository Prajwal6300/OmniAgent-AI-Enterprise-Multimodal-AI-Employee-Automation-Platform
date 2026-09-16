import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Machine(Base):
    __tablename__ = "machines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    machine_code = Column(String(50), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="OPERATIONAL", nullable=False)  # OPERATIONAL, MAINTENANCE, FAILED, OFFLINE
    failure_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    production_records = relationship("ProductionRecord", back_populates="machine", cascade="all, delete-orphan")
    maintenance_requests = relationship("MaintenanceRequest", back_populates="machine", cascade="all, delete-orphan")


class ProductionRecord(Base):
    __tablename__ = "production_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    machine_id = Column(UUID(as_uuid=True), ForeignKey("machines.id", ondelete="SET NULL"), nullable=True)
    batch_number = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="PASSED")  # PASSED, FAILED, COMPLETED, PENDING_INSPECTION
    defect_count = Column(Integer, default=0, nullable=False)
    production_time_hours = Column(Numeric(10, 2), default=0.0, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    machine = relationship("Machine", back_populates="production_records")


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    order_number = Column(String(100), nullable=False)
    customer_name = Column(String(255), nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, PROCESSING, COMPLETED, CANCELLED
    total_amount = Column(Numeric(12, 2), default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    sku = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), default=0.0, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=True)
    total_purchases = Column(Numeric(14, 2), default=0.0, nullable=False)
    rating = Column(Numeric(3, 2), default=5.0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    machine_id = Column(UUID(as_uuid=True), ForeignKey("machines.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    status = Column(String(50), default="OPEN", nullable=False)  # OPEN, IN_PROGRESS, RESOLVED, CLOSED
    priority = Column(String(20), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    machine = relationship("Machine", back_populates="maintenance_requests")
