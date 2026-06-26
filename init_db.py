import json
import psycopg2
from psycopg2.extras import DictCursor
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "worldcup.db"
MATCHES_PATH = DATA_DIR / "matches.json"

DATABASE_URL = "postgresql://neondb_owner:npg_Ca5Me1dwFSXN@ep-summer-lake-ao8jq9hi-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"


def get_connection():
    #os.environ["DATABASE_URL"]
    return psycopg2.connect(DATABASE_URL) 


def create_tables(conn, cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            student_class INTEGER,
            division TEXT,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ,
            last_login TIMESTAMPTZ,
            points INTEGER DEFAULT 0
        )
        """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY,
            team1 TEXT,
            team2 TEXT,
            group_name TEXT,
            stage TEXT,
            match_number INTEGER,
            kickoff TIMESTAMPTZ,
            score1 INTEGER,
            score2 INTEGER,
            status TEXT,
            processed INTEGER DEFAULT 0
        )
        """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            match_id INTEGER,
            pred1 INTEGER,
            pred2 INTEGER,
            submitted_at TIMESTAMPTZ,
            points_awarded INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(match_id) REFERENCES matches(id),
            UNIQUE(user_id, match_id)
        )
        """)

    print("creating standings")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS standings (
            id SERIAL PRIMARY KEY,
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
        """)


def load_matches():
    with MATCHES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def insert_matches(conn, cur, matches):
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
    cur.executemany(
        """
        INSERT INTO matches (
        id, team1, team2, group_name,
        stage, match_number,
        kickoff, score1, score2,
        status, processed
    )

    VALUES (
        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
    )

    ON CONFLICT (id)

    DO UPDATE SET

    team1 = EXCLUDED.team1,
    team2 = EXCLUDED.team2,
    group_name = EXCLUDED.group_name,
    stage = EXCLUDED.stage,
    match_number = EXCLUDED.match_number,
    kickoff = EXCLUDED.kickoff,
    score1 = EXCLUDED.score1,
    score2 = EXCLUDED.score2,
    status = EXCLUDED.status,
    processed = EXCLUDED.processed
        """,
        rows,
    )


def initialize_standings(conn, cur):
    cur.execute("""
        SELECT DISTINCT
            group_name,
            team
        FROM
        (
            SELECT
                group_name,
                team1 AS team
            FROM matches

            UNION

            SELECT
                group_name,
                team2 AS team
            FROM matches
        )

        ORDER BY
            group_name,
            team
        """)

    teams = cur.fetchall()

    for group_name, team in teams:

        cur.execute(
            """
        INSERT INTO standings
        (
            group_name,
            team
        )

        VALUES
        (
            %s,
            %s
        )

        ON CONFLICT
        (
            group_name,
            team
        )

        DO NOTHING
            """,
            (group_name, team),
        )


def initialize_database():
    with get_connection() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)
        create_tables(conn, cur)
        insert_matches(conn, cur, load_matches())
        initialize_standings(conn, cur)
        conn.commit()


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized at {DATABASE_URL}")
