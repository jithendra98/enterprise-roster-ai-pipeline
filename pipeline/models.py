from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class EmployeeRosterRecord(BaseModel):
    employee_id: str = Field(..., description="Unique employee identifier")
    employee_name: str = Field(..., description="Full name of employee")
    gender: str = Field(..., description="Gender (M/F/O)")
    shift_time: str = Field(..., description="Shift time format e.g. 21:00 or 06:00")
    pickup_address: str = Field(..., description="Origin pickup location")
    drop_address: str = Field(..., description="Destination office or home location")
    contact_number: Optional[str] = Field(None, description="Phone number")
    cost_center: Optional[str] = Field(None, description="Client cost center / BU")
    requires_escort: bool = Field(False, description="Whether security escort is mandated")

class ComplianceViolation(BaseModel):
    policy_code: str
    severity: str  # CRITICAL, WARNING, INFO
    employee_id: str
    employee_name: str
    description: str
    suggested_action: str
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DispatchAlert(BaseModel):
    alert_id: str
    title: str
    severity: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    violations: List[ComplianceViolation]
    metadata: Dict[str, Any] = Field(default_factory=dict)
