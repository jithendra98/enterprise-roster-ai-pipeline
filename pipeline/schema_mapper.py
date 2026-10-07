import csv
import re
from typing import List, Dict, Tuple, Any
from .models import EmployeeRosterRecord

class DynamicSchemaMapper:
    """
    Intelligently maps heterogeneous enterprise HRMS roster exports
    (Workday, SAP SuccessFactors, Darwinbox, etc.) into canonical MoveInSync records.
    """

    # Field synonyms across enterprise systems
    SYNONYM_MAP = {
        "employee_id": ["emp_id", "empid", "employee_id", "staff_id", "user_id", "id", "emp_no", "badge_no"],
        "employee_name": ["name", "emp_name", "employee_name", "full_name", "staff_name", "user_name"],
        "gender": ["gender", "sex", "emp_gender"],
        "shift_time": ["shift", "shift_time", "login_time", "timing", "shift_start", "roster_time", "schedule"],
        "pickup_address": ["pickup", "pickup_address", "pickup_point", "source", "origin", "from_location", "home_address"],
        "drop_address": ["drop", "drop_address", "drop_point", "destination", "to_location", "office_address", "site"],
        "contact_number": ["phone", "contact", "mobile", "contact_no", "cell", "phone_number"],
        "cost_center": ["cost_center", "department", "dept", "business_unit", "bu", "division"]
    }

    def infer_header_mapping(self, headers: List[str]) -> Dict[str, str]:
        """
        Maps raw input column names to canonical schema keys.
        """
        cleaned_headers = {h: re.sub(r'[^a-zA-Z0-9_]', '', h.strip().lower().replace(" ", "_")) for h in headers}
        mapping = {}

        for canonical_field, synonyms in self.SYNONYM_MAP.items():
            for orig_header, cleaned in cleaned_headers.items():
                if cleaned in synonyms or any(syn in cleaned for syn in synonyms):
                    mapping[canonical_field] = orig_header
                    break

        return mapping

    def clean_shift_time(self, raw_time: str) -> str:
        """
        Normalizes variations like '9:00 PM', '2100', '21:00:00' to standard 'HH:MM'.
        """
        if not raw_time:
            return "00:00"
        raw = raw_time.strip().upper()
        # Handle 12-hour format with AM/PM
        match_12 = re.match(r'(\d{1,2}):?(\d{2})?\s*(AM|PM)', raw)
        if match_12:
            hrs = int(match_12.group(1))
            mins = int(match_12.group(2) or 0)
            meridiem = match_12.group(3)
            if meridiem == "PM" and hrs < 12:
                hrs += 12
            elif meridiem == "AM" and hrs == 12:
                hrs = 0
            return f"{hrs:02d}:{mins:02d}"
        
        # Handle 24-hour format
        match_24 = re.match(r'(\d{1,2}):(\d{2})', raw)
        if match_24:
            hrs = int(match_24.group(1))
            mins = int(match_24.group(2))
            return f"{hrs:02d}:{mins:02d}"

        return raw

    def process_file(self, filepath: str) -> Tuple[List[EmployeeRosterRecord], List[Dict[str, Any]]]:
        valid_records: List[EmployeeRosterRecord] = []
        parse_errors: List[Dict[str, Any]] = []

        with open(filepath, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return [], [{"error": "Empty or headerless CSV"}]

            header_map = self.infer_header_mapping(reader.fieldnames)

            for idx, row in enumerate(reader, start=1):
                try:
                    emp_id = row.get(header_map.get("employee_id", ""), "").strip()
                    emp_name = row.get(header_map.get("employee_name", ""), "").strip()
                    gender = row.get(header_map.get("gender", ""), "U").strip().upper()
                    raw_shift = row.get(header_map.get("shift_time", ""), "").strip()
                    pickup = row.get(header_map.get("pickup_address", ""), "").strip()
                    drop = row.get(header_map.get("drop_address", ""), "").strip()
                    contact = row.get(header_map.get("contact_number", ""), "").strip()
                    cost_center = row.get(header_map.get("cost_center", ""), "GENERAL").strip()

                    if not emp_id or not emp_name:
                        parse_errors.append({"row": idx, "reason": "Missing mandatory Emp ID or Name", "data": row})
                        continue

                    # Standardize gender
                    clean_gender = "F" if gender.startswith("F") or gender == "FEMALE" else ("M" if gender.startswith("M") or gender == "MALE" else "O")
                    clean_shift = self.clean_shift_time(raw_shift)

                    record = EmployeeRosterRecord(
                        employee_id=emp_id,
                        employee_name=emp_name,
                        gender=clean_gender,
                        shift_time=clean_shift,
                        pickup_address=pickup or "DEFAULT_PICKUP",
                        drop_address=drop or "OFFICE_HQ",
                        contact_number=contact,
                        cost_center=cost_center,
                        requires_escort=False  # evaluated in compliance validator
                    )
                    valid_records.append(record)
                except Exception as e:
                    parse_errors.append({"row": idx, "reason": str(e), "data": row})

        return valid_records, parse_errors
