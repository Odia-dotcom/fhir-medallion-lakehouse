# 🏥 FHIR Medallion Lakehouse: End-to-End Clinical Data Pipeline

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![DuckDB](https://img.shields.io/badge/DuckDB-OLAP%20Engine-yellow.svg)](https://duckdb.org/)
[![Storage](https://img.shields.io/badge/Storage-Apache%20Parquet-green.svg)](https://parquet.apache.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Medallion%20%28Bronze%2FSilver%2FGold%29-orange.svg)]()

An automated, local data lakehouse pipeline built with **Python**, **DuckDB**, and **Apache Parquet**. This repository ingests raw, unstructured Fast Healthcare Interoperability Resources (**FHIR**) JSON patient bundles generated via **Synthea**—transforming them into structured Silver tables, a Gold **Patient 360** star schema, and an **NLP Clinical Feature Store**—executing end-to-end in under 50 seconds.

---

## 📐 Architecture & Data Flow

This project follows the **Medallion Architecture** pattern to progressively clean, enrich, and transform healthcare data for high-performance analytical processing.

```text
               ┌────────────────────────────────────────────────────────┐
               │              RAW INGESTION (Synthea Synthetic FHIR)    │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ BRONZE LAYER (data/bronze/)                                                   │
│ Raw, immutable synthetic FHIR patient bundles generated via Synthea           │
└──────────────────────────────────────────┬────────────────────────────────────┘
                                           │ parse_patient.py
                                           ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ SILVER LAYER (data/silver/)                                                   │
│ Cleansed, normalized columnar Parquet tables                                  │
│ • patients.parquet  • encounters.parquet  • conditions.parquet  • notes.parquet│
└──────────────────────────────────────────┬────────────────────────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    │ gold_patient_360.py                         │gold_clinical_nlp.py
                    ▼                                             ▼
┌───────────────────────────────────────┐   ┌───────────────────────────────────┐
│ GOLD LAYER: Patient 360               │   │ GOLD LAYER: Clinical NLP          │
│ Single-source-of-truth star schema    │   │ Extracted features & terms across │
│ (gold_patient_360.parquet)            │   │ 6,947 clinical progress notes     │
└───────────────────┬───────────────────┘   └─────────────────┬─────────────────┘
                    │                                         │
                    └───────────────────┬─────────────────────┘
                                        │ analyze_nlp_keywords.py
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ ANALYTICS & VALIDATION REPORTING                                              │
│ In-memory DuckDB SQL queries for data quality smoke testing & population risk │
└───────────────────────────────────────────────────────────────────────────────┘
Important Note: Although GitHub rendered directories alphabetically (bronze --> gold --> silver), execution strictly follows the sequential order: Bronze --> Silver --> Gold.
```
---

## 🛠️ Key Data Engineering Features

**Zero-Copy OLAP with DuckDB:** Executes fast, in-memory SQL queries directly against compressed Parquet files without requiring external database servers.

**Modular Pipeline Design:** Production-grade Python scripts using function-encapsulated logic and if __name__ == "__main__": entry points to prevent accidental import execution and optimize memory management.

**Custom Master Orchestration:** Single-command orchestration (run_pipeline.py) utilizing process isolation (subprocess), error handling circuit-breakers, and execution timing logs.

**Data Governance & Security:** Configured with .gitignore rules preventing raw dataset leaks and .gitkeep placeholders to enforce directory hierarchy across GitHub clones.

---

## 📂 Repository Structure

```text
fhir-medallion-lakehouse/
├── .gitignore                      # Environment, IDE, and data asset exclusion rules
├── README.md                       # Comprehensive project documentation
├── run_pipeline.py                 # Master pipeline orchestrator (Stages 1-4)
├── parse_patient.py                # Stage 1: Bronze -> Silver parsing & schema                                             enforcement
├── gold_patient_360.py             # Stage 2: Silver -> Gold Patient 360 star schema
├── gold_clinical_nlp.py            # Stage 3: Silver -> Gold Clinical NLP feature                                           extraction
├── analyze_nlp_keywords.py         # Stage 4: Gold DuckDB keyword analytics report
└── data/
    ├── bronze/                     # Raw FHIR JSON bundles (.gitkeep tracked)
    ├── silver/                     # Cleansed Parquet tables (.gitkeep tracked)
    └── gold/                       # Final analytical models (.gitkeep tracked)
```
---

## 📊 Sample Pipeline Output

Upon running the orchestrator, DuckDB processes 118 patients and 6,947 clinical notes, producing structured analytics in terminal as shown below:
```text
============================================================
  FHIR MEDALLION LAKEHOUSE: MASTER PIPELINE ORCHESTRATOR  
============================================================

[STARTING] Stage 1: Silver Data Ingestion & Cleansing (parse_patient.py)...
==========================================
STARTING ETL PROCESS...
==========================================
[OK] Silver Directory Created/Verified: ...\data\silver
[OK] Bronze Directory Path: ...\data\bronze
[OK] Found 122 JSON bundle files.
------------------------------------------
SUCCESS! Created silver_patients.parquet, silver_conditions.parquet, silver_notes.parquet
------------------------------------------
[SUCCESS] Stage 1: Silver Data Ingestion & Cleansing completed in 31.00 seconds.

[STARTING] Stage 2: Gold Patient 360 Aggregation (gold_patient_analytics.py)...
==========================================
STARTING GOLD PATIENT 360 TRANSFORMATION...
==========================================
[OK] Executing Multi-Table DuckDB SQL Query...
------------------------------------------
SUCCESS! Gold Patient 360 Table Created: ...\data\gold\gold_patient_360.parquet
Total Patient Records: 118
------------------------------------------

Updated Gold Patient 360 Sample:
                                           patient_id  total_conditions  total_clinical_notes
0  8b93b5f545d946a3b2a326976d70dfc267503d2e11bd7f...               225                   214
1  fcb9a3e332532a334afc0948b944e843f0a0189dfb69c7...               159                   140
2  fb963f82322f3c7d87184b4c84034f5c5d41579ffb17a0...               147                   154
3  5292ebb60a867299c10c8b646a8a364104e18bc171ec1b...               127                   101
4  9d6e5eb377af18c4024226aeb9cc10d281ec57693bd8db...               118                   195
[SUCCESS] Stage 2: Gold Patient 360 Aggregation completed in 5.63 seconds.

[STARTING] Stage 3: Gold Clinical NLP Feature Store (gold_clinical_nlp.py)...
==========================================
STARTING GOLD CLINICAL NLP EXTRACTION...
==========================================
[OK] Loaded 6947 raw clinical notes.
------------------------------------------
SUCCESS! Created Gold NLP Table: ...\data\gold\gold_clinical_notes_nlp.parquet
Processed Notes: 6947
------------------------------------------

Gold Clinical NLP Sample:
                                  note_id      category  word_count detected_keywords
0  72c36a2a-2e3d-ed95-1647-9285149e2686  General Note          73                  
1  e44eaf41-968d-e3ad-146b-279358a21121  General Note          83      hypertension
2  4eb577dc-083e-bed3-507c-fcf829819606  General Note          83          diabetes
3  c3887a80-dfdc-62cc-48a4-9bc3b70f6494  General Note          79        prescribed
4  bf6b7167-f761-a0c6-7fdd-52aeffb25e93  General Note          73                  
[SUCCESS] Stage 3: Gold Clinical NLP Feature Store completed in 6.40 seconds.

[STARTING] Stage 4: Gold Clinical Keyword Frequency Analytics (analyze_nlp_keywords.py)...
============================================================
  GOLD CLINICAL NLP: KEYWORD FREQUENCY ANALYSIS  
============================================================

Top Clinical Keywords Detected Across 6,947 Notes:

     keyword  total_occurrences  unique_patients_affected  pct_patient_population
  prescribed               3147                       110                    93.2
      normal               1268                        47                    39.8
    abnormal                575                        31                    26.3
        pain                426                        32                    27.1
       cough                327                         9                     7.6
       fever                237                         7                     5.9
    diabetes                106                        55                    46.6
hypertension                 33                        32                    27.1
     glucose                 31                        15                    12.7

============================================================
Total Unique Keywords Analyzed: 9
============================================================
[SUCCESS] Stage 4: Gold Clinical Keyword Frequency Analytics completed in 3.84 seconds.

============================================================
  PIPELINE EXECUTION COMPLETE! Total Time: 46.92s  
============================================================
```

---

## 🚀 Quickstart & Usage

1. **Prerequisites**
Python 3.10 or higher
Recommended: Conda / Miniconda or Python virtual environment

2. **Environment Setup**
# Clone the repository
git clone [https://github.com/Odia-dotcom/fhir-medallion-lakehouse.git](https://github.com/odia-dotcom/fhir-medallion-lakehouse.git)
cd fhir-medallion-lakehouse

# Install required dependencies
pip install duckdb pandas pyarrow

3. **Place Raw Data**
Place your raw synthetic FHIR JSON patient bundles (generated via [Synthea](https://github.com/synthetichealth/synthea)) into the Bronze directory:
`data/bronze/`

4. **Execute Master Orchestrator**
Run the entire 4-stage pipeline with a single command:
     python run_pipeline.py

---

## 🤖 AI-Assisted Development Workflow

This project was built leveraging Generative AI (Gemini) as a pair-programming partner and technical advisor.

1. **System Design & Architecture:** The 3-layer Medallion architecture (Bronze/Silver/Gold) and 4-stage pipeline orchestration, data models, folder structures, and zero-copy OLAP pipeline flow were independently designed and structured to meet healthcare data standards.

2. **Code Generation & Optimization:** AI was utilized to draft core ETL functions, optimize DuckDB SQL joins, and design the subprocess-based master orchestrator.

3. **Architecture Design:** Collaborated with AI to enforce production-grade software patterns, including entry-point guards (if __name__ == "__main__":), circuit-breaker error handling, and Medallion governance (.gitignore / .gitkeep rules).

4. **Code Testing & Debugging:** Independently tested, debugged, and validated all generated scripts, fixing path mismatches and schema edge cases during local execution.

---

## 📈 Future Roadmap

* [ ] **Live API Ingestion:** Integrate real-time FHIR data ingestion by connecting to live healthcare APIs (e.g., HAPI FHIR server or SMART on FHIR endpoints) via Python `requests`/`httpx`.
* [ ] **Automated Testing:** Add unit and integration tests using `pytest` to validate FHIR JSON parsing boundary conditions and schema integrity.
* [ ] **Containerization:** Package the environment using **Docker** for seamless, reproducible local or cloud deployments.
* [ ] **Workflow Orchestration:** Migrate the custom master orchestrator to **Apache Airflow** or **Prefect** DAGs for scheduled batch processing and automated retries.
