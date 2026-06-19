import json
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "worldcup.db"
MATCHES_PATH = DATA_DIR / "matches.json"


def get_connection():
    DATA_DIR.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def create_tables(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            student_class INTEGER,
            division TEXT,
            is_admin INTEGER DEFAULT 0,
            created_at DATETIME,
            last_login DATETIME
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY,
            team1 TEXT,
            team2 TEXT,
            group_name TEXT,
            stage TEXT,
            match_number INTEGER,
            kickoff DATETIME,
            score1 INTEGER,
            score2 INTEGER,
            status TEXT,
            processed INTEGER DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            match_id INTEGER,
            pred1 INTEGER,
            pred2 INTEGER,
            submitted_at DATETIME,
            points_awarded INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(match_id) REFERENCES matches(id),
            UNIQUE(user_id, match_id)
        )
        """
    )

    print("creating standings")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS standings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT,
            team TEXT,
            played INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            draws INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            gf INTEGER DEFAULT 0,
            ga INTEGER DEFAULT 0,
            gd INTEGER DEFAULT 0,
            points INTEGER DEFAULT 0,
            position integer,
            UNIQUE(group_name, team)
        )
        """
    )


def load_matches():
    with MATCHES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def insert_matches(conn, matches):
    rows = [
        (
            match["id"],
            match["team1"],
            match["team2"],
            match["group_name"],
            match["stage"],
            match["match_number"],
            match["kickoff"],
            match["score1"],
            match["score2"],
            match["status"],
            match["processed"],
        )
        for match in matches
    ]
    conn.executemany(
        """
        INSERT OR REPLACE INTO matches (
            id, team1, team2, group_name, stage, match_number,
            kickoff, score1, score2, status, processed
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def initialize_database():
    with get_connection() as conn:
        create_tables(conn)
        insert_matches(conn, load_matches())
        conn.commit()


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized at {DB_PATH}")
