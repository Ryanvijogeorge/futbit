from flask import Flask, render_template

from helpers import (
    get_groups,
    get_matches_by_group,
    get_standings,
    get_connection
)

app = Flask(__name__)


@app.route("/")
def home():

    groups = get_groups()

    return render_template(
        "home.html",
        groups=groups
    )


@app.route("/group/<group_name>")
def group(group_name):

    matches = get_matches_by_group(group_name)

    standings = get_standings(group_name)

    return render_template(
        "group.html",
        group_name=group_name,
        matches=matches,
        standings=standings
    )


if __name__ == "__main__":
    app.run(debug=True)