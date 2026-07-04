import psycopg2
from psycopg2.extras import DictCursor

test_url = "postgresql://neondb_owner:npg_Ca5Me1dwFSXN@ep-summer-lake-ao8jq9hi-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
real_url = "postgresql://neondb_owner:npg_pEGv3DORh1Kn@ep-mute-breeze-aoykew70-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
#DATABASE_URL = os.environ["DATABASE_URL"]
DATABASE_URL = test_url


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def create_bonus_tables(conn, cur):

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bonus_questions (

            id SERIAL PRIMARY KEY,

            question TEXT NOT NULL,

            question_type TEXT NOT NULL,

            stage TEXT NOT NULL,

            lock_time TIMESTAMPTZ NOT NULL,

            points INTEGER NOT NULL,

            options_source TEXT,

            correct_answer TEXT,

            created_at TIMESTAMPTZ DEFAULT NOW()

        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bonus_predictions (

            id SERIAL PRIMARY KEY,

            user_id INTEGER NOT NULL,

            question_id INTEGER NOT NULL,

            answer TEXT NOT NULL,

            submitted_at TIMESTAMPTZ DEFAULT NOW(),

            points_awarded INTEGER DEFAULT 0,

            FOREIGN KEY (user_id)
                REFERENCES users(id),

            FOREIGN KEY (question_id)
                REFERENCES bonus_questions(id),

            UNIQUE(user_id, question_id)

        )
    """)


def initialize_bonus_database():

    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)

    create_bonus_tables(conn, cur)

    conn.commit()

    cur.close()
    conn.close()

    print("Bonus question tables created successfully.")


if __name__ == "__main__":
    initialize_bonus_database()