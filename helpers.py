import sqlite3
from pathlib import Path
from datetime import datetime, timedelta


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "worldcup.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
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


def get_match(match_id):

    conn = get_connection()

    match = conn.execute(

        """
        SELECT *

        FROM matches

        WHERE id = ?

        """,

        (match_id,)

    ).fetchone()

    conn.close()

    return match


def get_prediction(user_id, match_id):

    conn = get_connection()


    prediction = conn.execute(

        """

        SELECT *

        FROM predictions


        WHERE


        user_id = ?


        AND


        match_id = ?


        """,


        (

            user_id,

            match_id

        )


    ).fetchone()



    conn.close()



    return prediction


def prediction_closed(match_id):


    match = get_match(

        match_id

    )



    kickoff = datetime.fromisoformat(

        match["kickoff"]

    )



    lock_time = kickoff - timedelta(

        minutes=20

    )



    now = datetime.now(

        kickoff.tzinfo

    )



    return now >= lock_time


def save_prediction(

        user_id,

        match_id,

        pred1,

        pred2

):



    conn = get_connection()



    existing = conn.execute(

        """

        SELECT id


        FROM predictions


        WHERE


        user_id = ?


        AND


        match_id = ?


        """,



        (

            user_id,

            match_id

        )


    ).fetchone()



    submitted_at = datetime.now().isoformat()




    if existing:



        conn.execute(

            """

            UPDATE predictions


            SET


            pred1 = ?,


            pred2 = ?,


            submitted_at = ?



            WHERE


            user_id = ?


            AND


            match_id = ?



            """,



            (

                pred1,

                pred2,

                submitted_at,

                user_id,

                match_id

            )



        )



    else:



        conn.execute(

            """

            INSERT INTO predictions


            (



            user_id,

            match_id,

            pred1,

            pred2,

            submitted_at



            )



            VALUES



            (


            ?,


            ?,


            ?,


            ?,


            ?



            )



            """,



            (


                user_id,


                match_id,


                pred1,


                pred2,


                submitted_at


            )



        )



    conn.commit()


    conn.close()


if __name__ == "__main__":

    save_prediction(

        2,

        3,

        5,

        7

    )


    print(

        get_prediction(

            2,

            3

        )

    )


    print(

        prediction_closed(

            1

        )

    )