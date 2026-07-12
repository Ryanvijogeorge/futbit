import os
import psycopg2
from psycopg2.extras import DictCursor
from pathlib import Path
from datetime import datetime, timedelta
from time import perf_counter
from flask import g

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "worldcup.db"

# os.environ["DATABASE_URL"]
test_url = "postgresql://neondb_owner:npg_Ca5Me1dwFSXN@ep-summer-lake-ao8jq9hi-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
real_url = "postgresql://neondb_owner:npg_pEGv3DORh1Kn@ep-mute-breeze-aoykew70-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
DATABASE_URL = os.environ["DATABASE_URL"]
#DATABASE_URL = test_url



def get_connection():
    t = perf_counter()
    if "db" not in g:
        print("NEW CONNECTION")
        g.db = psycopg2.connect(DATABASE_URL)
        g.cur = g.db.cursor(cursor_factory=DictCursor)
        print("connect took", perf_counter() - t)
    return g.db, g.cur


def get_active_stage():
    return "Semi-finals"


def get_groups():
    conn, cur = get_connection()

    cur.execute("""
        SELECT DISTINCT group_name
        FROM matches
        WHERE stage='Group Stage'
        ORDER BY group_name
        """)

    groups = cur.fetchall()

    result = {}

    for group in groups:

        cur.execute(
            """
            SELECT DISTINCT team
            FROM (

                SELECT team1 AS team
                FROM matches
                WHERE group_name=%s

                UNION

                SELECT team2 AS team
                FROM matches
                WHERE group_name=%s

            )

            ORDER BY team
            """,
            (group["group_name"], group["group_name"]),
        )

        teams = cur.fetchall()

        result[group["group_name"]] = [t["team"] for t in teams]

    # conn.close()

    return result


def get_matches_by_group(group_name):

    conn, cur = get_connection()

    cur.execute(
        """
        SELECT *
        FROM matches
        WHERE group_name=%s
        ORDER BY kickoff
        """,
        (group_name,),
    )

    matches = cur.fetchall()

    # conn.close()

    return matches


def get_standings(group_name):

    conn, cur = get_connection()

    cur.execute(
        """
        SELECT *
        FROM standings
        WHERE group_name=%s
        ORDER BY
            position ASC
        """,
        (group_name,),
    )

    standings = cur.fetchall()

    # conn.close()

    return standings


def get_match(match_id):

    conn, cur = get_connection()

    cur.execute(
        """
        SELECT *

        FROM matches

        WHERE id = %s

        """,
        (match_id,),
    )

    match = cur.fetchone()

    # conn.close()

    return match


def get_prediction(user_id, match_id):

    conn, cur = get_connection()

    cur.execute(
        """

        SELECT *

        FROM predictions


        WHERE


        user_id = %s


        AND


        match_id = %s


        """,
        (user_id, match_id),
    )

    prediction = cur.fetchone()

    # conn.close()

    return prediction


def prediction_closed(match_id):

    match = get_match(match_id)

    kickoff = match["kickoff"]

    lock_time = kickoff - timedelta(minutes=10)

    now = datetime.now(kickoff.tzinfo)

    print("=" * 40)
    print(f"Match ID : {match_id}")
    print(f"Kickoff  : {kickoff}")
    print(f"Lock     : {lock_time}")
    print(f"Now      : {now}")
    print(f"Closed?  : {now >= lock_time}")

    return now >= lock_time


def save_prediction(user_id, match_id, pred1, pred2):

    conn, cur = get_connection()

    cur.execute(
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
            %s,
            %s,
            %s,
            %s,
            %s
        )

        ON CONFLICT (user_id, match_id)

        DO UPDATE SET

            pred1 = EXCLUDED.pred1,
            pred2 = EXCLUDED.pred2,
            submitted_at = EXCLUDED.submitted_at
        """,
        (user_id, match_id, pred1, pred2, datetime.now()),
    )

    conn.commit()
    # conn.close()


def get_match_predictions(match_id):

    conn, cur = get_connection()

    cur.execute(
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


        WHERE match_id = %s

        """,
        (match_id,),
    )

    predictions = cur.fetchall()

    # conn.close()

    return predictions


def get_predictions(match_ids):
    conn, cur = get_connection()

    cur.execute(
        """
        SELECT
            p.*,
            u.username
        FROM predictions p
        JOIN users u
            ON p.user_id = u.id
        WHERE p.match_id = ANY(%s)
    """,
        (match_ids,),
    )

    return cur.fetchall()


def get_all_matches():

    conn, cur = get_connection()

    cur.execute("""

        SELECT *

        FROM matches

        ORDER BY

        CASE status

            WHEN 'upcoming' THEN 0

            WHEN 'Completed' THEN 1

        END,

        kickoff ASC

        """)

    matches = cur.fetchall()

    return matches


def get_matches_by_stage(stage):

    conn, cur = get_connection()

    cur.execute(
        """

        SELECT *

        FROM matches

        WHERE stage = %s

        ORDER BY

        CASE status

            WHEN 'upcoming' THEN 0

            WHEN 'Completed' THEN 1

        END,

        kickoff ASC

        """,
        (stage,),
    )

    matches = cur.fetchall()

    return matches


def calculate_points(pred1, pred2, score1, score2):

    if pred1 == score1 and pred2 == score2:

        return 20

    # bools as ints for outcome
    pred_outcome = (pred1 > pred2) - (pred1 < pred2)

    actual_outcome = (score1 > score2) - (score1 < score2)

    if pred_outcome == actual_outcome:

        pred_gd = pred1 - pred2

        actual_gd = score1 - score2

        if (pred1 == score1) or (pred2 == score2):
            return 12

        if pred_gd == actual_gd:

            return 10
        

        return 5

    return 0


def recompute_match_points(match_id):

    conn, cur = get_connection()

    cur.execute(
        """

        SELECT score1,

               score2


        FROM matches


        WHERE id=%s

        """,
        (match_id,),
    )

    match = cur.fetchone()

    cur.execute(
        """

        SELECT *


        FROM predictions


        WHERE match_id=%s

        """,
        (match_id,),
    )

    predictions = cur.fetchall()

    for prediction in predictions:

        old_points = prediction["points_awarded"]

        new_points = calculate_points(
            prediction["pred1"], prediction["pred2"], match["score1"], match["score2"]
        )

        delta = new_points - old_points

        cur.execute(
            """

            UPDATE users


            SET points = points + %s


            WHERE id = %s

            """,
            (delta, prediction["user_id"]),
        )

        cur.execute(
            """

            UPDATE predictions


            SET points_awarded=%s


            WHERE id=%s

            """,
            (new_points, prediction["id"]),
        )

    conn.commit()

    # conn.close()


def process_match(match_id, score1, score2):

    conn, cur = get_connection()

    cur.execute(
        """

        UPDATE matches


        SET


        score1=%s,

        score2=%s,

        status='Completed',

        processed=1


        WHERE id=%s


        """,
        (score1, score2, match_id),
    )

    conn.commit()

    # conn.close()

    recompute_match_points(match_id)


def update_standing(group_name, team, position, points):

    conn, cur = get_connection()

    cur.execute(
        """

        UPDATE standings


        SET


            position = %s,


            points = %s


        WHERE


            group_name = %s


            AND team = %s

        """,
        (position, points, group_name, team),
    )

    conn.commit()

    # conn.close()


def get_leaderboard():

    conn, cur = get_connection()

    cur.execute("""

        SELECT

            username,

            points

        FROM users

        ORDER BY

            points DESC,

            username ASC

        """)

    leaderboard = cur.fetchall()

    # conn.close()

    return leaderboard


FLAGS = {
    "Algeria": "dz",
    "Argentina": "ar",
    "Australia": "au",
    "Austria": "at",
    "Belgium": "be",
    "Bosnia and Herzegovina": "ba",
    "Brazil": "br",
    "Canada": "ca",
    "Cape Verde": "cv",
    "Colombia": "co",
    "Croatia": "hr",
    "Curacao": "cw",
    "Czechia": "cz",
    "DR Congo": "cd",
    "Ecuador": "ec",
    "Egypt": "eg",
    "England": "gb-eng",
    "France": "fr",
    "Germany": "de",
    "Ghana": "gh",
    "Haiti": "ht",
    "Iran": "ir",
    "Iraq": "iq",
    "Ivory Coast": "ci",
    "Japan": "jp",
    "Jordan": "jo",
    "Mexico": "mx",
    "Morocco": "ma",
    "Netherlands": "nl",
    "New Zealand": "nz",
    "Norway": "no",
    "Panama": "pa",
    "Paraguay": "py",
    "Portugal": "pt",
    "Qatar": "qa",
    "Saudi Arabia": "sa",
    "Scotland": "gb-sct",
    "Senegal": "sn",
    "South Africa": "za",
    "South Korea": "kr",
    "Spain": "es",
    "Sweden": "se",
    "Switzerland": "ch",
    "Tunisia": "tn",
    "Turkey": "tr",
    "United States": "us",
    "Uruguay": "uy",
    "Uzbekistan": "uz",
}

