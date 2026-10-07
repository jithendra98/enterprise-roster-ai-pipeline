import unittest
import os
from pipeline.schema_mapper import DynamicSchemaMapper
from pipeline.compliance_validator import RosterComplianceValidator
from pipeline.models import EmployeeRosterRecord

class TestRosterPipeline(unittest.TestCase):

    def test_dynamic_schema_mapping_workday(self):
        mapper = DynamicSchemaMapper()
        records, errors = mapper.process_file("data/sample_raw_roster_workday.csv")
        self.assertGreater(len(records), 0)
        self.assertEqual(len(errors), 0)
        self.assertEqual(records[0].employee_id, "E-10021")
        self.assertEqual(records[0].shift_time, "09:00")

    def test_dynamic_schema_mapping_sap(self):
        mapper = DynamicSchemaMapper()
        records, errors = mapper.process_file("data/sample_raw_roster_sap.csv")
        self.assertEqual(len(records), 4)
        self.assertEqual(records[0].employee_id, "B-9011")
        self.assertEqual(records[0].gender, "F")
        self.assertEqual(records[0].shift_time, "21:30")

    def test_compliance_validator_night_escort(self):
        validator = RosterComplianceValidator()
        night_female_record = EmployeeRosterRecord(
            employee_id="TEST-001",
            employee_name="Jane Doe",
            gender="F",
            shift_time="22:00",
            pickup_address="Electronic City Phase 1",
            drop_address="Campus Gate 3",
            contact_number="9900112233"
        )
        violations = validator.validate_record(night_female_record)
        self.assertTrue(any(v.policy_code == "POL-NIGHT-ESCORT" for v in violations))
        self.assertTrue(night_female_record.requires_escort)

    def test_compliance_validator_day_shift_clean(self):
        validator = RosterComplianceValidator()
        day_record = EmployeeRosterRecord(
            employee_id="TEST-002",
            employee_name="John Smith",
            gender="M",
            shift_time="10:00",
            pickup_address="Koramangala 80ft Road",
            drop_address="Campus Gate 3",
            contact_number="9900112233"
        )
        violations = validator.validate_record(day_record)
        self.assertEqual(len(violations), 0)

if __name__ == "__main__":
    unittest.main()
