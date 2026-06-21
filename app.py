import sqlite3
import secrets
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

from werkzeug.security import generate_password_hash, check_password_hash

from helpers import (
    get_groups,
    get_matches_by_group,
    get_standings,
    get_connection,
    get_prediction,
    save_prediction,
    prediction_closed,
    get_match_predictions,
    get_all_matches,
    process_match,
    update_standing,
    get_leaderboard,
)

app = Flask(__name__)
app.jinja_env.globals.update(prediction_closed=prediction_closed)

app.secret_key = secrets.token_hex(16)


def admin_required():

    return session.get("user_id") == 1


@app.route("/")
def home():

    groups = get_groups()

    return render_template("home.html", groups=groups)


@app.route("/group/<group_name>")
def group(group_name):

    matches = get_matches_by_group(group_name)

    standings = get_standings(group_name)

    predictions = {}
    prediction_visibility = {}

    for match in matches:

        preds = get_match_predictions(match["id"])

        if prediction_closed(match["id"]):

            preds.sort(key=lambda p: (-p["points_awarded"], p["submitted_at"]))

        else:

            preds.sort(key=lambda p: p["submitted_at"])
        prediction_visibility[match["id"]] = preds

    if "user_id" in session:
        for match in matches:
            pred = get_prediction(session["user_id"], match["id"])

            predictions[match["id"]] = pred

    return render_template(
        "group.html",
        group_name=group_name,
        matches=matches,
        standings=standings,
        predictions=predictions,
        prediction_visibility=prediction_visibility,
        predict_match=request.args.get("predict", type=int),
    )


@app.route("/predict/<int:match_id>", methods=["POST"])
def predict(match_id):

    if "user_id" not in session:
        group_name = request.form["group_name"]
        session["next_url"] = (
            url_for("group", group_name=group_name)
            + f"?predict={match_id}#match-{match_id}"
        )

        return redirect(url_for("login"))

    if prediction_closed(match_id):
        flash("Predictions closed.")

        return redirect(request.referrer)

    pred1 = int(request.form["pred1"])

    pred2 = int(request.form["pred2"])

    save_prediction(session["user_id"], match_id, pred1, pred2)

    flash("Prediction saved.")

    group_name = request.form["group_name"]

    return redirect(url_for("group", group_name=group_name) + f"#match-{match_id}")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form["username"]

        password = request.form["password"]

        conn = get_connection()

        user = conn.execute(
            """

            SELECT *

            FROM users

            WHERE username = ?

            """,
            (username,),
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]

            session["username"] = user["username"]

            return redirect(session.pop("next_url", url_for("home")))

        flash("Invalid username or password")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form["username"]

        password = request.form["password"]

        student_class = int(request.form["student_class"])

        division = request.form["division"]

        password_hash = generate_password_hash(password)

        conn = get_connection()

        try:
            conn.execute(
                """

                INSERT INTO users


                (


                username,


                password_hash,


                student_class,


                division


                )


                VALUES


                (


                ?,


                ?,


                ?,


                ?


                )


                """,
                (username, password_hash, student_class, division),
            )

            conn.commit()

            user = conn.execute(
                """

                SELECT id

                FROM users


                WHERE username = ?

                """,
                (username,),
            ).fetchone()

            session["user_id"] = user["id"]

            session["username"] = username

            conn.close()

            return redirect(session.pop("next_url", url_for("home")))

        except sqlite3.IntegrityError:
            flash("Username already exists.")

            conn.close()

    return render_template("register.html")


@app.route("/admin")
def admin():

    if not admin_required():
        return redirect(url_for("home"))

    conn = get_connection()

    matches = get_all_matches()

    standings = conn.execute("""

        SELECT *

        FROM standings

        ORDER BY

            group_name,

            position

        """).fetchall()

    return render_template("admin.html", matches=matches, standings=standings)


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


@app.route("/process_match", methods=["POST"])
def process_match_route():

    if not admin_required():

        return redirect(url_for("home"))

    match_id = int(request.form["match_id"])

    score1 = int(request.form["score1"])

    score2 = int(request.form["score2"])

    process_match(match_id, score1, score2)

    return redirect(url_for("admin"))


@app.post("/update-standing")
def update_standing_route():

    admin_required()

    update_standing(
        request.form["group_name"],
        request.form["team"],
        int(request.form["position"]),
        int(request.form["points"]),
    )

    return redirect(url_for("admin"))


@app.route("/leaderboard")
def leaderboard():

    leaderboard = get_leaderboard()

    return render_template("leaderboard.html", leaderboard=leaderboard)


if __name__ == "__main__":
    app.run(debug=True)
