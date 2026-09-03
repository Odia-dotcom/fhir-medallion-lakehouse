import subprocess
import sys
import time
from pathlib import Path


def run_stage(script_name: str, stage_label: str) -> None:
    """Executes a pipeline script as a subprocess and tracks execution timing."""
    print(f"\n[STARTING] {stage_label} ({script_name})...")
    start_time = time.time()

    script_path = Path(script_name)
    if not script_path.exists():
        print(f"[ERROR] Script not found: {script_name}")
        sys.exit(1)

    result = subprocess.run([sys.executable, script_name], capture_output=False)

    if result.returncode != 0:
        print(
            f"[FAILED] Stage '{stage_label}' encountered an error. Stopping pipeline execution."
        )
        sys.exit(result.returncode)

    elapsed = time.time() - start_time
    print(
        f"[SUCCESS] {stage_label} completed in {elapsed:.2f} seconds."
    )


def main():
    print("=" * 60)
    print("  FHIR MEDALLION LAKEHOUSE: MASTER PIPELINE ORCHESTRATOR  ")
    print("=" * 60)

    total_start = time.time()

    # Stage 1: Bronze -> Silver (Parsing & Normalization)
    run_stage("parse_patient.py", "Stage 1: Silver Data Ingestion & Cleansing")

    # Stage 2: Silver -> Gold (Patient 360 Star Schema)
    run_stage("gold_patient_analytics.py", "Stage 2: Gold Patient 360 Aggregation")

    # Stage 3: Silver -> Gold (Clinical NLP Feature Store)
    run_stage("gold_clinical_nlp.py", "Stage 3: Gold Clinical NLP Feature Store")

    # Stage 4: Gold Analytics & Validation Report
    run_stage("analyze_nlp_keywords.py", "Stage 4: Gold Clinical Keyword Frequency Analytics")
    
    total_elapsed = time.time() - total_start
    print("\n" + "=" * 60)
    print(
        f"  PIPELINE EXECUTION COMPLETE! Total Time: {total_elapsed:.2f}s  "
    )
    print("=" * 60)


if __name__ == "__main__":
    main()