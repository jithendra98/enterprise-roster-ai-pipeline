from typing import List
from .models import EmployeeRosterRecord, ComplianceViolation

class RosterComplianceValidator:
    """
    Validates enterprise commute policies and statutory guidelines
    (e.g., Night-shift female employee escort mandate, geofence validity).
    """

    def is_night_shift(self, shift_time: str) -> bool:
        """
        Flags shifts between 20:00 (8 PM) and 06:00 (6 AM).
        """
        try:
            parts = shift_time.split(":")
            hour = int(parts[0])
            return hour >= 20 or hour < 6
        except Exception:
            return False

    def validate_record(self, record: EmployeeRosterRecord) -> List[ComplianceViolation]:
        violations = []

        # Rule 1: Night-shift escort mandate for female employees (Statutory compliance)
        if record.gender == "F" and self.is_night_shift(record.shift_time):
            record.requires_escort = True
            violations.append(ComplianceViolation(
                policy_code="POL-NIGHT-ESCORT",
                severity="CRITICAL",
                employee_id=record.employee_id,
                employee_name=record.employee_name,
                description=f"Female employee scheduled for night shift ({record.shift_time}) requires mandatory security escort.",
                suggested_action="Auto-allocate verified security escort guard on assigned vehicle roster."
            ))

        # Rule 2: Address Completeness & Geofence Verification
        if len(record.pickup_address) < 8 or record.pickup_address == "DEFAULT_PICKUP":
            violations.append(ComplianceViolation(
                policy_code="POL-INVALID-GEO",
                severity="WARNING",
                employee_id=record.employee_id,
                employee_name=record.employee_name,
                description=f"Pickup address '{record.pickup_address}' appears truncated or missing specific landmark coordinates.",
                suggested_action="Trigger geocoding verification prompt to employee before dispatch generation."
            ))

        # Rule 3: Missing Emergency Contact
        if not record.contact_number or len(record.contact_number) < 10:
            violations.append(ComplianceViolation(
                policy_code="POL-CONTACT-MISSING",
                severity="WARNING",
                employee_id=record.employee_id,
                employee_name=record.employee_name,
                description="Valid 10-digit mobile contact number missing for live trip tracking.",
                suggested_action="Fetch verified contact from primary HRMS master sync."
            ))

        return violations

    def validate_batch(self, records: List[EmployeeRosterRecord]) -> List[ComplianceViolation]:
        all_violations = []
        for rec in records:
            all_violations.extend(self.validate_record(rec))
        return all_violations
