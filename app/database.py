import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "predictions.db")


# -----------------------------
# INIT DATABASE
# -----------------------------
def init_db():
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            error_count          INTEGER,
            warning_count        INTEGER,
            dependency_downloads INTEGER,
            install_steps        INTEGER,
            has_git_clone        INTEGER,
            prediction           INTEGER,
            probability          REAL,
            timestamp            TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(predictions)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    if "timestamp" not in existing_columns:
        cursor.execute("ALTER TABLE predictions ADD COLUMN timestamp TEXT")
        cursor.execute(
            "UPDATE predictions SET timestamp = datetime('now') WHERE timestamp IS NULL"
        )

    conn.commit()
    conn.close()


# -----------------------------
# INSERT DATA
# ✅ FIX: explicitly pass datetime('now') so timestamp is never NULL
# -----------------------------
def insert_prediction(error_count, warning_count, dependency_downloads,
                      install_steps, has_git_clone, prediction, probability):
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO predictions
        (error_count, warning_count, dependency_downloads,
         install_steps, has_git_clone, prediction, probability, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (error_count, warning_count, dependency_downloads,
          install_steps, has_git_clone, prediction, probability))
    conn.commit()
    conn.close()


# -----------------------------
# FETCH RECENT 10 (dashboard)
# -----------------------------
def get_predictions():
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(predictions)")
    cols = [r[1] for r in cursor.fetchall()]
    ts   = "timestamp" if "timestamp" in cols else "'N/A'"

    cursor.execute(f"""
        SELECT id, error_count, warning_count, dependency_downloads,
               install_steps, has_git_clone, prediction, probability, {ts}
        FROM predictions
        ORDER BY id DESC
        LIMIT 10
    """)
    data = cursor.fetchall()
    conn.close()
    return data


# -----------------------------
# FETCH ALL (history analyser)
# -----------------------------
def get_all_predictions():
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(predictions)")
    cols = [r[1] for r in cursor.fetchall()]
    ts   = "timestamp" if "timestamp" in cols else "'N/A'"

    cursor.execute(f"""
        SELECT id, error_count, warning_count, dependency_downloads,
               install_steps, has_git_clone, prediction, probability, {ts}
        FROM predictions
        ORDER BY id DESC
    """)
    data = cursor.fetchall()
    conn.close()
    return data


# -----------------------------
# FETCH SUMMARY STATS
# -----------------------------
def get_summary_stats():
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM predictions")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE prediction = 1")
    failures = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(probability) FROM predictions")
    avg_prob = cursor.fetchone()[0] or 0

    cursor.execute("SELECT AVG(probability) FROM predictions WHERE prediction = 1")
    avg_fail_prob = cursor.fetchone()[0] or 0

    cursor.execute("SELECT AVG(probability) FROM predictions WHERE prediction = 0")
    avg_safe_prob = cursor.fetchone()[0] or 0

    conn.close()

    return {
        "total":         total,
        "failures":      failures,
        "safe":          total - failures,
        "failure_rate":  round((failures / total * 100) if total > 0 else 0, 2),
        "avg_prob":      round(avg_prob      * 100, 2),
        "avg_fail_prob": round(avg_fail_prob * 100, 2),
        "avg_safe_prob": round(avg_safe_prob * 100, 2),
    }