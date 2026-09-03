import duckdb


def analyze_keywords():
    print("=" * 60)
    print("  GOLD CLINICAL NLP: KEYWORD FREQUENCY ANALYSIS  ")
    print("=" * 60)

    con = duckdb.connect()

    # Query Gold NLP Feature Store using DuckDB
    query = """
    WITH exploded_keywords AS (
        SELECT 
            patient_id,
            UNNEST(STRING_SPLIT(detected_keywords, '; ')) AS keyword
        FROM 'data/gold/gold_clinical_notes_nlp.parquet'
        WHERE detected_keywords IS NOT NULL AND detected_keywords != ''
    )
    SELECT 
        keyword,
        COUNT(*) AS total_occurrences,
        COUNT(DISTINCT patient_id) AS unique_patients_affected,
        ROUND((COUNT(DISTINCT patient_id) * 100.0 / 118), 1) AS pct_patient_population
    FROM exploded_keywords
    GROUP BY keyword
    ORDER BY total_occurrences DESC;
    """

    results = con.execute(query).df()

    print("\nTop Clinical Keywords Detected Across 6,947 Notes:\n")
    print(results.to_string(index=False))

    print("\n" + "=" * 60)
    print(f"Total Unique Keywords Analyzed: {len(results)}")
    print("=" * 60)


if __name__ == "__main__":
    analyze_keywords()