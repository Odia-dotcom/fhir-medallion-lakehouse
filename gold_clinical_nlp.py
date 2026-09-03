import re
from pathlib import Path
import pandas as pd

print("==========================================", flush=True)
print("STARTING GOLD CLINICAL NLP EXTRACTION...", flush=True)
print("==========================================", flush=True)

project_root = Path(__file__).resolve().parent

# Path setup
silver_dir = project_root / "data" / "silver"
if not silver_dir.exists():
    silver_dir = project_root / "Data" / "silver"

gold_dir = project_root / "data" / "gold"
gold_dir.mkdir(parents=True, exist_ok=True)

note_files = list(silver_dir.rglob("*note*.parquet"))
if not note_files:
    print("[ERROR] Could not find silver notes Parquet file!", flush=True)
    sys.exit(1)

notes_path = note_files[0]
df_notes = pd.read_parquet(notes_path)
print(f"[OK] Loaded {len(df_notes)} raw clinical notes.", flush=True)

# Common clinical terms to detect in note text
CLINICAL_KEYWORDS = [
    "fever", "cough", "hypertension", "diabetes", "pain", 
    "blood pressure", "glucose", "normal", "abnormal", "prescribed"
]

def extract_nlp_features(text: str) -> dict:
    if not text or not isinstance(text, str):
        return {
            "word_count": 0,
            "char_count": 0,
            "detected_keywords": "",
            "keyword_count": 0
        }
    
    clean_text = text.lower()
    words = re.findall(r'\b\w+\b', clean_text)
    
    # Keyword extraction matching
    found_keywords = [kw for kw in CLINICAL_KEYWORDS if kw in clean_text]
    
    return {
        "word_count": len(words),
        "char_count": len(text),
        "detected_keywords": "; ".join(found_keywords),
        "keyword_count": len(found_keywords)
    }

# Apply NLP extraction across clinical notes
nlp_results = df_notes["note_text"].apply(extract_nlp_features)
df_nlp_features = pd.DataFrame(list(nlp_results))

# Combine original note metadata with newly extracted NLP features
df_gold_nlp = pd.concat([df_notes[["note_id", "patient_id", "date", "category"]], df_nlp_features], axis=1)

# Save to Gold NLP Parquet table
gold_nlp_file = gold_dir / "gold_clinical_notes_nlp.parquet"
df_gold_nlp.to_parquet(gold_nlp_file, index=False)

print("------------------------------------------", flush=True)
print(f"SUCCESS! Created Gold NLP Table: {gold_nlp_file.absolute()}", flush=True)
print(f"Processed Notes: {len(df_gold_nlp)}", flush=True)
print("------------------------------------------", flush=True)

print("\nGold Clinical NLP Sample:")
print(df_gold_nlp[["note_id", "category", "word_count", "detected_keywords"]].head(5))
