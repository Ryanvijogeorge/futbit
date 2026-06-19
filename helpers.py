import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "worldcup.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_groups():
    conn = get_connection()

    groups = conn.execute(
        """
        SELECT DISTINCT group_name
        FROM matches
        WHERE stage='Group Stage'
        ORDER BY group_name
        """
    ).fetchall()

    result = {}

    for group in groups:

        teams = conn.execute(
            """
            SELECT DISTINCT team
            FROM (

                SELECT team1 AS team
                FROM matches
                WHERE group_name=?

                UNION

                SELECT team2 AS team
                FROM matches
                WHERE group_name=?

            )

            ORDER BY team
            """,
            (group["group_name"], group["group_name"])
        ).fetchall()

        result[group["group_name"]] = [t["team"] for t in teams]

    conn.close()

    return result


def get_matches_by_group(group_name):

    conn = get_connection()

    matches = conn.execute(
        """
        SELECT *
        FROM matches
        WHERE group_name=?
        ORDER BY kickoff
        """,
        (group_name,)
    ).fetchall()

    conn.close()

    return matches


def get_standings(group_name):

    conn = get_connection()

    standings = conn.execute(
        """
        SELECT *
        FROM standings
        WHERE group_name=?
        ORDER BY
            position ASC
        """,
        (group_name,)
    ).fetchall()

    conn.close()

    return standings

