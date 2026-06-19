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


# test
if __name__ == "__main__":

    print(get_groups())

    print()

    conn = get_connection()

    conn.execute("""
    INSERT INTO standings
    (
        group_name,
        team,
        played,
        wins,
        draws,
        losses,
        gf,
        ga,
        gd,
        points,
        position
    )
    VALUES
    ('A','Mexico',3,2,1,0,5,2,3,7,4)
    """)

    conn.execute("""
    INSERT INTO standings
    (
        group_name,
        team,
        played,
        wins,
        draws,
        losses,
        gf,
        ga,
        gd,
        points,
        position
    )
    VALUES
    ('A','USA',3,1,2,0,4,3,1,5,2)
    """)

    conn.execute("""
    INSERT INTO standings
    (
        group_name,
        team,
        played,
        wins,
        draws,
        losses,
        gf,
        ga,
        gd,
        points,
        position
    )
    VALUES
    ('A','Korea',3,1,0,2,3,5,-2,3, 3)
    """)

    conn.execute("""
    INSERT INTO standings
    (
        group_name,
        team,
        played,
        wins,
        draws,
        losses,
        gf,
        ga,
        gd,
        points,
        position
    )
    VALUES
    ('A','Switzerland',3,0,1,2,2,4,-2,1, 1)
    """)

    conn.commit()

    print("Inserted dummy standings")

    for row in get_standings("A"):
        print(dict(row))

    conn.close()