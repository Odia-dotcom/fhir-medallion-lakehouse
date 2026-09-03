import sys
from pathlib import Path
import duckdb
import pandas as pd

print("==========================================", flush=True)
print("STARTING GOLD PATIENT 360 TRANSFORMATION...", flush=True)
print("==========================================", flush=True)

project_root = Path(__file__).resolve().parent

# 1. Resolve Pathing
silver_dir = project_root / "data" / "silver"
if not silver_dir.exists():
    silver_dir = project_root / "Data" / "silver"

gold_dir = project_root / "data" / "gold"
gold_dir.mkdir(parents=True, exist_ok=True)

# 2. Dynamic Parquet Discovery
patient_files = list(silver_dir.rglob("*patient*.parquet"))
condition_files = list(silver_dir.rglob("*condition*.parquet"))
note_files = list(silver_dir.rglob("*note*.parquet"))

if not patient_files or not condition_files or not note_files:
    print("[ERROR] Missing required Parquet files in silver directory!", flush=True)
    sys.exit(1)

patients_path = str(patient_files[0].absolute()).replace("\\", "/")
conditions_path = str(condition_files[0].absolute()).replace("\\", "/")
notes_path = str(note_files[0].absolute()).replace("\\", "/")

# 3. Multi-Table SQL Join with DuckDB
con = duckdb.connect()

gold_query = f"""
    SELECT 
        p.patient_id,
        p.gender,
        p.birth_date,
        COUNT(DISTINCT c.condition_id) AS total_conditions,
        STRING_AGG(DISTINCT c.display, '; ') AS condition_list,
        COUNT(DISTINCT n.note_id) AS total_clinical_notes
    FROM '{patients_path}' p
    LEFT JOIN '{conditions_path}' c
        ON p.patient_id = c.patient_id
    LEFT JOIN '{notes_path}' n
        ON p.patient_id = n.patient_id
    GROUP BY 
        p.patient_id, 
        p.gender, 
        p.birth_date
    ORDER BY total_conditions DESC
"""

print("[OK] Executing Multi-Table DuckDB SQL Query...", flush=True)
df_gold = con.execute(gold_query).df()

# 4. Save Output
gold_file = gold_dir / "gold_patient_360.parquet"
df_gold.to_parquet(gold_file, index=False)

print("------------------------------------------", flush=True)
print(f"SUCCESS! Gold Patient 360 Table Created: {gold_file.absolute()}", flush=True)
print(f"Total Patient Records: {len(df_gold)}", flush=True)
print("------------------------------------------", flush=True)

print("\nUpdated Gold Patient 360 Sample:")
print(df_gold[['patient_id', 'total_conditions', 'total_clinical_notes']].head(5))