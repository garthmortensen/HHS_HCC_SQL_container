#!/usr/bin/env python3
"""
Generate ACA-like synthetic seed data as CSVs using Faker and scenarios.json.

Outputs:
  - transform/seeds/Enrollment.csv
  - transform/seeds/MedicalClaims.csv
  - transform/seeds/PharmacyClaims.csv
  - transform/seeds/Supplemental.csv

Run: python scripts/generate_seed_data.py
"""
import csv
import json
import os
import random
import shutil
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from faker import Faker

# User-configurable parameters
DBT_SEEDS_DIR = "transform/seeds/"
YEARS = [2025]
MEMBERS = 200
SCENARIO_PROBABILITY = 0.8  # Probability a member gets assigned scenarios

# ICD-11 to ICD-10 Mapping (Simplified for demo purposes)
# Maps the codes found in scenarios.json to valid ICD-10-CM codes (no dots)
ICD_MAPPING = {
    # format "ICD-11": "ICD-10"
    # Infectious
    "1A00": "A000", "1A01": "A001", "1A02": "A009", "1B11": "J101", 
    "2A00": "B20", "2B20": "A150", "1D60": "A984",
    # Neoplasms
    "2B30": "C859", "2C60": "C61", "2D10": "C3490", "8A20": "C50919",
    # Blood
    "3A00": "D509", "3B60": "D619",
    # Endocrine
    "4A00": "E109", "4A01": "E119", "5A10": "F329", "5A11": "F319",
    # Nervous
    "6A40": "G40909", "8A00": "G20",
    # Circulatory
    "BA00": "I10", "BA41": "I219", "BA42": "I2510", "BC20": "I509",
    # Respiratory
    "CA22": "J449", "CA40": "J45909", "CB00": "J189",
    # Digestive
    "DA00": "K219", "DA40": "K5090",
    # Musculoskeletal
    "FA00": "M069", "FA20": "M179",
    # Genitourinary
    "GA00": "N189", "GA10": "N390",
    # Pregnancy
    "JA00": "O80",
    # Perinatal
    "KA00": "P0730", "KB00": "P0700",
    # Injury
    "NA00": "S069X9A", "ND90": "T3150",
    # Factors
    "QA00": "Z0000",
    # Default fallback
    "DEFAULT": "R69"
}

def get_icd10(icd11_code):
    """Convert ICD-11 to ICD-10, stripping dots."""
    code = ICD_MAPPING.get(icd11_code, ICD_MAPPING["DEFAULT"])
    return code.replace(".", "")

def generate_hios_id():
    """Generate a 16-digit HIOS ID."""
    state = random.choice(["VA", "MD", "DC", "CA", "TX", "FL"])
    issuer = f"{random.randint(10000, 99999)}"
    product = f"{state}{issuer}" # 7 chars
    # HIOS ID format: 5 digit issuer + 2 digit state + 4 digit product + 2 digit variant
    # Actually usually: 12345XX0010001
    # Let's stick to the README example format: 12345XX0010001
    return f"{random.randint(10000,99999)}{state}001{random.randint(1,99):04d}01"

def generate_ndc(drug_name):
    """Generate a consistent 11-digit NDC based on drug name hash."""
    # Simple hash to get a number
    h = abs(hash(drug_name))
    return f"{h % 100000:05d}{(h // 100000) % 10000:04d}{(h // 1000000000) % 100:02d}"

def main():
    fake = Faker()
    Faker.seed(0)
    random.seed(0)

    # Load scenarios
    with open("scripts/scenarios.json", "r") as f:
        scenarios_data = json.load(f)
    
    # Flatten scenarios list
    all_scenarios = []
    for category, scenarios in scenarios_data.items():
        all_scenarios.extend(scenarios)

    # Prepare outputs
    os.makedirs(DBT_SEEDS_DIR, exist_ok=True)
    
    enrollment_rows = []
    medical_claims_rows = []
    pharmacy_claims_rows = []
    supplemental_rows = []

    print(f"Generating data for {MEMBERS} members...")

    for i in range(1, MEMBERS + 1):
        member_id = f"MEM{i:05d}"
        
        # 1. Enrollment
        gender = random.choice(["M", "F"])
        dob = fake.date_of_birth(minimum_age=0, maximum_age=85)
        plan_id = generate_hios_id()
        
        # Create 1 or 2 spans per year
        for year in YEARS:
            # Simple logic: Full year enrollment for most
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            
            metal = random.choice(["Bronze", "Silver", "Gold", "Platinum", "Catastrophic"])
            market = random.choice(["1", "2"]) # 1=Indiv, 2=Small Group

            enrollment_rows.append({
                "MemberID": member_id,
                "Gender": gender,
                "DOB": dob,
                "PlanID": plan_id,
                "EnrollmentStart": start_date,
                "EnrollmentEnd": end_date,
                "MetalLevel": metal,
                "Market": market
            })

            # 2. Claims Generation based on Scenarios
            # Assign 0-3 scenarios to this member for this year
            num_scenarios = 0
            if random.random() < SCENARIO_PROBABILITY:
                num_scenarios = random.randint(1, 3)
            
            member_scenarios = random.sample(all_scenarios, k=min(num_scenarios, len(all_scenarios)))

            for s_idx, scenario in enumerate(member_scenarios):
                # Generate Medical Claims (Diagnoses & Procedures)
                # We'll create one claim per scenario for simplicity, or split them
                claim_id = f"CLM{i:05d}{year}{s_idx:03d}"
                dos = fake.date_between(start_date=start_date, end_date=end_date)
                
                # Get Diagnoses (mapped to ICD-10)
                diags = [get_icd10(d) for d in scenario.get("diagnoses", [])]
                primary_dx = diags[0] if diags else "R69"
                
                # Cost
                cost_range = scenario.get("cost_range", [100.0, 500.0])
                total_cost = round(random.uniform(cost_range[0], cost_range[1]), 2)
                
                # Medical Claim Row
                medical_claims_rows.append({
                    "MemberID": member_id,
                    "ClaimID": claim_id,
                    "LineNumber": 1,
                    "ServiceFromDate": dos,
                    "ServiceToDate": dos,
                    "FormType": "I" if scenario.get("service_category") == "Inpatient" else "P",
                    "DX1": primary_dx,
                    "BilledAmount": total_cost,
                    "AllowedAmount": total_cost,
                    "PaidAmount": total_cost
                })

                # Supplemental (Chance to add extra diagnoses)
                if len(diags) > 1:
                    for extra_dx in diags[1:]:
                        supplemental_rows.append({
                            "MemberID": member_id,
                            "ClaimID": claim_id,
                            "DX": extra_dx,
                            "AddDeleteFlag": "A"
                        })

                # Pharmacy Claims
                drugs = scenario.get("drugs", [])
                for d_idx, drug in enumerate(drugs):
                    rx_claim_id = f"RX{i:05d}{year}{s_idx:03d}{d_idx:02d}"
                    ndc = generate_ndc(drug)
                    rx_cost = round(random.uniform(10.0, 200.0), 2)
                    
                    pharmacy_claims_rows.append({
                        "MemberID": member_id,
                        "ClaimID": rx_claim_id,
                        "NDC": ndc,
                        "FilledDate": dos,
                        "PaidDate": dos,
                        "BilledAmount": rx_cost,
                        "AllowedAmount": rx_cost,
                        "PaidAmount": rx_cost
                    })

    # Write CSVs
    print("Writing CSVs...")
    
    # Enrollment
    with open(os.path.join(DBT_SEEDS_DIR, "enrollment.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["MemberID", "Gender", "DOB", "PlanID", "EnrollmentStart", "EnrollmentEnd", "MetalLevel", "Market"])
        writer.writeheader()
        writer.writerows(enrollment_rows)

    # MedicalClaims
    with open(os.path.join(DBT_SEEDS_DIR, "medicalclaims.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["MemberID", "ClaimID", "LineNumber", "ServiceFromDate", "ServiceToDate", "FormType", "DX1", "BilledAmount", "AllowedAmount", "PaidAmount"])
        writer.writeheader()
        writer.writerows(medical_claims_rows)

    # PharmacyClaims
    with open(os.path.join(DBT_SEEDS_DIR, "pharmacyclaims.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["MemberID", "ClaimID", "NDC", "FilledDate", "PaidDate", "BilledAmount", "AllowedAmount", "PaidAmount"])
        writer.writeheader()
        writer.writerows(pharmacy_claims_rows)

    # Supplemental
    with open(os.path.join(DBT_SEEDS_DIR, "supplemental.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["MemberID", "ClaimID", "DX", "AddDeleteFlag"])
        writer.writeheader()
        writer.writerows(supplemental_rows)

    print(f"Done. Generated {len(enrollment_rows)} enrollment spans, {len(medical_claims_rows)} medical claims, {len(pharmacy_claims_rows)} rx claims.")

if __name__ == "__main__":
    main()
