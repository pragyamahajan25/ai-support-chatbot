import sqlite3
from pathlib import Path

# Set path for SQLite database file
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "feedback.db"

# Connect to SQLite
conn = sqlite3.connect(DB_PATH, check_same_thread=False)

# Create feedback table if it doesn't exist
# Columns:
# - solution: unique identifier for a solution (e.g., "ticketID_solution1")
# - success_count: number of times this solution was confirmed as working
conn.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    solution TEXT PRIMARY KEY,
    success_count INTEGER DEFAULT 0
)
""")
conn.commit()

# Function to record user feedback
def record_feedback(solution: str):
    """
    Increment the success count for a solution.
    If solution does not exist in table, insert it with count 1.
    """
    try:
        conn.execute("""
        INSERT INTO feedback(solution, success_count)
        VALUES (?, 1)
        ON CONFLICT(solution)
        DO UPDATE SET success_count = success_count + 1
        """, (solution,))
        conn.commit()
    except Exception as e:
        print(f"[Feedback Error] Could not record feedback for {solution}: {e}")

# Function to get how many times a solution was confirmed
def get_success_count(solution: str) -> int:
    """
    Return the number of times this solution has been marked as successful.
    Returns 0 if no record exists.
    """
    try:
        row = conn.execute(
            "SELECT success_count FROM feedback WHERE solution=?",
            (solution,)
        ).fetchone()
        return int(row[0]) if row else 0
    except Exception as e:
        print(f"[Feedback Error] Could not get success count for {solution}: {e}")
        return 0
