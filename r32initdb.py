import json
from pathlib import Path

from init_db import get_connection, insert_matches

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
R32_PATH = DATA_DIR / "r32_matches.json"


def load_r32_matches():
    with R32_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def add_round_of_32():
    matches = load_r32_matches()

    with get_connection() as conn:
        cur = conn.cursor()

        insert_matches(conn, cur, matches)

        conn.commit()

    print(f"✅ Added {len(matches)} Round of 32 matches.")


if __name__ == "__main__":
    add_round_of_32()