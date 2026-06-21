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

    groups = conn.execute("""
        SELECT DISTINCT group_name
        FROM matches
        WHERE stage='Group Stage'
        ORDER BY group_name
        """).fetchall()

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
            (group["group_name"], group["group_name"]),
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
        (group_name,),
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
        (group_name,),
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
        (match_id,),
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
        (user_id, match_id),
    ).fetchone()

    conn.close()

    return prediction


def prediction_closed(match_id):

    match = get_match(match_id)

    kickoff = datetime.fromisoformat(match["kickoff"])

    lock_time = kickoff - timedelta(minutes=20)

    now = datetime.now(kickoff.tzinfo)

    return now >= lock_time


def save_prediction(user_id, match_id, pred1, pred2):

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
        (user_id, match_id),
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
            (pred1, pred2, submitted_at, user_id, match_id),
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
            (user_id, match_id, pred1, pred2, submitted_at),
        )

    conn.commit()

    conn.close()


def get_match_predictions(match_id):

    conn = get_connection()

    predictions = conn.execute(
        """

        SELECT

        users.username,

        predictions.pred1,

        predictions.pred2,

        predictions.points_awarded,

        predictions.submitted_at


        FROM predictions


        JOIN users


        ON users.id = predictions.user_id


        WHERE match_id = ?

        """,
        (match_id,),
    ).fetchall()

    conn.close()

    return predictions


def get_all_matches():

    conn = get_connection()

    matches = conn.execute("""

        SELECT *

        FROM matches


        ORDER BY kickoff

        """).fetchall()

    conn.close()

    return matches


def calculate_points(pred1, pred2, score1, score2):

    if pred1 == score1 and pred2 == score2:

        return 10

    # bools as ints for outcome
    pred_outcome = (pred1 > pred2) - (pred1 < pred2)

    actual_outcome = (score1 > score2) - (score1 < score2)

    if pred_outcome == actual_outcome:

        pred_gd = pred1 - pred2

        actual_gd = score1 - score2

        if pred_gd == actual_gd:

            return 5

        return 3

    return 0


def recompute_match_points(match_id):

    conn = get_connection()

    match = conn.execute(
        """

        SELECT score1,

               score2


        FROM matches


        WHERE id=?

        """,
        (match_id,),
    ).fetchone()

    predictions = conn.execute(
        """

        SELECT *


        FROM predictions


        WHERE match_id=?

        """,
        (match_id,),
    ).fetchall()

    for prediction in predictions:

        old_points = prediction["points_awarded"]

        new_points = calculate_points(
            prediction["pred1"], prediction["pred2"], match["score1"], match["score2"]
        )

        delta = new_points - old_points

        conn.execute(
            """

            UPDATE users


            SET points = points + ?


            WHERE id = ?

            """,
            (delta, prediction["user_id"]),
        )

        conn.execute(
            """

            UPDATE predictions


            SET points_awarded=?


            WHERE id=?

            """,
            (new_points, prediction["id"]),
        )

    conn.commit()

    conn.close()


def process_match(match_id, score1, score2):

    conn = get_connection()

    conn.execute(
        """

        UPDATE matches


        SET


        score1=?,

        score2=?,

        status='Completed',

        processed=1


        WHERE id=?


        """,
        (score1, score2, match_id),
    )

    conn.commit()

    conn.close()

    recompute_match_points(match_id)


def update_standing(group_name, team, position, points):

    conn = get_connection()

    conn.execute(
        """

        UPDATE standings


        SET


            position = ?,


            points = ?


        WHERE


            group_name = ?


            AND team = ?

        """,
        (position, points, group_name, team),
    )

    conn.commit()

    conn.close()


def get_leaderboard():

    conn = get_connection()

    leaderboard = conn.execute("""

        SELECT

            username,

            points

        FROM users

        ORDER BY

            points DESC,

            username ASC

        """).fetchall()

    conn.close()

    return leaderboard
