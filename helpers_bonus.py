import json
from pathlib import Path
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import DictCursor

# from helpers import get_connection


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

TEAMS_JSON = DATA_DIR / "teams.json"
PLAYERS_JSON = DATA_DIR / "players.json"

# os.environ["DATABASE_URL"]
test_url = "postgresql://neondb_owner:npg_Ca5Me1dwFSXN@ep-summer-lake-ao8jq9hi-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
real_url = "postgresql://neondb_owner:npg_pEGv3DORh1Kn@ep-mute-breeze-aoykew70-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
# DATABASE_URL = os.environ["DATABASE_URL"]
DATABASE_URL = test_url


def get_test_connection():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=DictCursor)
    return conn, cur


QUESTION_TYPES = [
    "team",
    "player",
    "binary",
    "number",
]


def bonus_locked(lock_time):
    """
    Generic lock checker.
    Returns True once lock_time has passed.
    """

    if lock_time.tzinfo is None:
        lock_time = lock_time.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)

    return now >= lock_time


def get_bonus_questions():
    """
    Returns all bonus questions ordered by creation time.
    """

    conn, cur = get_test_connection()

    cur.execute("""
        SELECT *

        FROM bonus_questions

        ORDER BY created_at DESC
        """)

    questions = cur.fetchall()

    conn.close()

    return questions


def get_bonus_question(question_id):
    """
    Returns one bonus question.
    """

    conn, cur = get_test_connection()

    cur.execute(
        """
        SELECT *

        FROM bonus_questions

        WHERE id = %s
        """,
        (question_id,),
    )

    question = cur.fetchone()

    conn.close()

    return question


def create_bonus_question(
    question,
    question_type,
    options_source,
    stage,
    lock_time,
    points,
):
    """
    Creates a new bonus question.
    """

    conn, cur = get_test_connection()
    cur.execute(
        """
    INSERT INTO bonus_questions
    (
        question,
        question_type,
        stage,
        lock_time,
        points,
        options_source
    )

    VALUES
    (
        %s,%s,%s,%s,%s,%s
    )

    RETURNING id
    """,
        (
            question,
            question_type,
            stage,
            lock_time,
            points,
            options_source,
        ),
    )

    question_id = cur.fetchone()["id"]

    conn.commit()

    conn.close()

    return question_id


def update_bonus_question(
    question_id,
    question,
    question_type,
    options_source,
    stage,
    lock_time,
    points,
):
    """
    Updates an existing question.
    """

    conn, cur = get_test_connection()
    cur.execute(
        """
    UPDATE bonus_questions

    SET

        question = %s,
        question_type = %s,
        stage = %s,
        lock_time = %s,
        points = %s,
        options_source = %s

    WHERE id = %s
    """,
        (
            question,
            question_type,
            stage,
            lock_time,
            points,
            options_source,
            question_id,
        ),
    )

    conn.commit()

    conn.close()


def delete_bonus_question(question_id):
    """
    Deletes a question.
    Predictions cascade automatically because of FK.
    """

    conn, cur = get_test_connection()

    cur.execute(
        """
        DELETE

        FROM bonus_questions

        WHERE id = %s
        """,
        (question_id,),
    )

    conn.commit()

    conn.close()


def get_bonus_prediction(user_id, question_id):
    """
    Returns a user's prediction for a question.
    """

    conn, cur = get_test_connection()

    cur.execute(
        """
        SELECT *

        FROM bonus_predictions

        WHERE

            user_id = %s

        AND

            question_id = %s
        """,
        (user_id, question_id),
    )

    prediction = cur.fetchone()

    conn.close()

    return prediction


def get_bonus_predictions(question_id):
    """
    Returns every prediction for one question.
    """

    conn, cur = get_test_connection()

    cur.execute(
        """
        SELECT *

        FROM bonus_predictions

        WHERE question_id = %s

        ORDER BY submitted_at
        """,
        (question_id,),
    )

    predictions = cur.fetchall()

    conn.close()

    return predictions


def get_bonus_predictions_for_questions(user_id, question_ids):
    """
    Returns all predictions made by one user for the given questions.
    Returns a dictionary:
        {question_id: prediction_row}
    """

    if not question_ids:
        return {}

    conn, cur = get_test_connection()

    cur.execute(
        """
        SELECT *

        FROM bonus_predictions

        WHERE

            user_id = %s

        AND

            question_id = ANY(%s)
        """,
        (
            user_id,
            question_ids,
        ),
    )

    predictions = cur.fetchall()

    conn.close()

    return {prediction["question_id"]: prediction for prediction in predictions}


def save_bonus_prediction(
    user_id,
    question_id,
    answer,
):
    """
    Creates or updates a prediction until the question locks.
    """

    question = get_bonus_question(question_id)

    if bonus_locked(question["lock_time"]):
        return False

    conn, cur = get_test_connection()

    cur.execute(
        """
        INSERT INTO bonus_predictions
        (
            user_id,
            question_id,
            answer,
            submitted_at
        )

        VALUES
        (
            %s,%s,%s,NOW()
        )

        ON CONFLICT
        (
            user_id,
            question_id
        )

        DO UPDATE SET

            answer = EXCLUDED.answer,

            submitted_at = NOW()
        """,
        (
            user_id,
            question_id,
            answer,
        ),
    )

    conn.commit()

    conn.close()

    return True
