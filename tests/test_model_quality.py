from src.sql_analysis.model_quality import analyze_model_quality


def test_model_quality_ignores_comments_and_accepts_explicit_forms():
    sql = """
        -- GRANT ALL ON depots TO PUBLIC;
        INSERT INTO depots (id, name) VALUES (1, 'ALTER TABLE depots ADD CHECK');
        ALTER TABLE depots ADD CONSTRAINT positive_id CHECK (id > 0);
        GRANT SELECT ON depots TO reader;
    """
    assert analyze_model_quality(sql) == ()


def test_model_quality_explains_each_advice_with_statement_number():
    findings = analyze_model_quality("""
        ALTER TABLE depots ADD CHECK (id > 0);
        GRANT ALL PRIVILEGES ON depots TO reader;
    """)

    assert [finding.code for finding in findings] == [
        "style.model_unnamed_constraint",
        "style.model_grant_all",
    ]
    assert [finding.details["statement_number"] for finding in findings] == [1, 2]
    assert not any(finding.blocks_execution for finding in findings)

