import base64
import hashlib
import json
import logging
import sys
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

SALT = "HEALTH_ETL_PIPELINE_V1_"

def clean_raw_id(raw_id: str) -> str:
    """Strips all FHIR URN and resource prefixes."""
    if not raw_id:
        return ""
    clean = str(raw_id).strip()
    prefixes = ["urn:uuid:", "urn:passthrough:", "Patient/", "Condition/"]
    for prefix in prefixes:
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
    return clean.strip().lower()

def hash_identifier(raw_id: str) -> str:
    """Generates deterministic SHA-256 pseudonymized ID."""
    clean_id = clean_raw_id(raw_id)
    if not clean_id:
        return None
    salted_input = f"{SALT}{clean_id}".encode("utf-8")
    return hashlib.sha256(salted_input).hexdigest()

def parse_bundle(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    patients, conditions, notes = [], [], []

    # Ensure bundle is a valid dictionary
    if not isinstance(bundle, dict):
        return patients, conditions, notes

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")

        if resource_type == "Patient":
            patients.append({
                "patient_id": hash_identifier(resource.get("id")),
                "gender": resource.get("gender"),
                "birth_date": resource.get("birthDate"),
            })

        elif resource_type == "Condition":
            coding = resource.get("code", {}).get("coding", [{}])[0]
            conditions.append({
                "condition_id": resource.get("id"),
                "patient_id": hash_identifier(resource.get("subject", {}).get("reference", "")),
                "code": coding.get("code"),
                "display": coding.get("display"),
                "system": coding.get("system"),
                "recorded_date": resource.get("recordedDate")
            })

        elif resource_type == "DocumentReference":
            content_list = resource.get("content", [])
            note_text = None
            if content_list:
                b64_data = content_list[0].get("attachment", {}).get("data")
                if b64_data:
                    try:
                        note_text = base64.b64decode(b64_data).decode("utf-8")
                    except Exception:
                        pass

            notes.append({
                "note_id": resource.get("id"),
                "patient_id": hash_identifier(resource.get("subject", {}).get("reference", "")),
                "date": resource.get("date"),
                "category": resource.get("type", {}).get("text", "General Note"),
                "note_text": note_text
            })

    return patients, conditions, notes

def main():
    print("==========================================", flush=True)
    print("STARTING ETL PROCESS...", flush=True)
    print("==========================================", flush=True)

    project_root = Path(__file__).resolve().parent
    bronze_dir = project_root / "data" / "bronze"
    silver_dir = project_root / "data" / "silver"

    # Step 1: Force Silver directory creation right away
    silver_dir.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Silver Directory Created/Verified: {silver_dir.absolute()}", flush=True)

    # Step 2: Use recursive glob (rglob) to catch JSON files in subdirectories
    json_files = list(bronze_dir.rglob("*.json"))
    print(f"[OK] Bronze Directory Path: {bronze_dir.absolute()}", flush=True)
    print(f"[OK] Found {len(json_files)} JSON bundle files.", flush=True)

    if not json_files:
        print("[ERROR] No JSON files found inside data/bronze or its subfolders!", flush=True)
        return

    all_patients, all_conditions, all_notes = [], [], []

    for json_file in json_files:
        try:
            patients, conditions, notes = parse_bundle(json_file)
            all_patients.extend(patients)
            all_conditions.extend(conditions)
            all_notes.extend(notes)
        except Exception as e:
            print(f"[WARN] Failed to parse {json_file.name}: {e}", flush=True)

    if not all_patients:
        print("[ERROR] No patient records were extracted. Check FHIR bundle contents.", flush=True)
        return

    df_patients = pd.DataFrame(all_patients).drop_duplicates(subset=["patient_id"])
    df_conditions = pd.DataFrame(all_conditions)
    df_notes = pd.DataFrame(all_notes)

    # Step 3: Write outputs
    df_patients.to_parquet(silver_dir / "silver_patients.parquet", index=False)
    df_conditions.to_parquet(silver_dir / "silver_conditions.parquet", index=False)
    df_notes.to_parquet(silver_dir / "silver_notes.parquet", index=False)

    print("------------------------------------------", flush=True)
    print("SUCCESS! Created silver_patients.parquet, silver_conditions.parquet, silver_notes.parquet", flush=True)
    print("------------------------------------------", flush=True)

if __name__ == "__main__":
    main()