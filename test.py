from helpers_bonus import create_bonus_question
''' 
create sql table row test
qid = create_bonus_question(
    question="Who will win the World Cup?",
    question_type="team",
    options_source="teams.json",
    stage="Tournament",
    lock_time="2026-07-10T15:00:00+00:00",
    points=50,
)

print(qid)

'''

'''
getting one question test

from helpers_bonus import get_bonus_question

print(get_bonus_question(1))
'''


'''
get all questions
from helpers_bonus import get_bonus_questions

questions = get_bonus_questions()

for q in questions:
    print(q)
'''

'''
update q test
from helpers_bonus import update_bonus_question

update_bonus_question(
    question_id=1,
    question="Who will become World Champion?",
    question_type="team",
    options_source="teams.json",
    stage="Tournament",
    lock_time="2026-07-11T15:00:00+00:00",
    points=75,
)

print("updated")
'''

# test_bonus.py

from helpers_bonus import *

USER_ID = 1


def test_bonus_system():

    # =====================================================
    # QUESTION CRUD
    # =====================================================

    # ---------- CREATE ----------

    question_id = create_bonus_question(
        question="Unit Test Question",
        question_type="team",
        options_source="teams.json",
        stage="Tournament",
        lock_time="2026-07-20T15:00:00+00:00",
        points=25,
    )

    assert question_id is not None

    # ---------- GET ----------

    question = get_bonus_question(question_id)

    assert question is not None
    assert question["question"] == "Unit Test Question"
    assert question["question_type"] == "team"
    assert question["options_source"] == "teams.json"
    assert question["points"] == 25

    # ---------- UPDATE ----------

    update_bonus_question(
        question_id=question_id,
        question="Updated Unit Test Question",
        question_type="player",
        options_source="players.json",
        stage="Final",
        lock_time="2026-07-21T15:00:00+00:00",
        points=50,
    )

    question = get_bonus_question(question_id)

    assert question["question"] == "Updated Unit Test Question"
    assert question["question_type"] == "player"
    assert question["options_source"] == "players.json"
    assert question["stage"] == "Final"
    assert question["points"] == 50

    # =====================================================
    # PREDICTION CRUD
    # =====================================================

    save_bonus_prediction(USER_ID, 1, "Brazil")
    save_bonus_prediction(USER_ID, 2, "Mbappe")
    save_bonus_prediction(USER_ID, 3, "Yes")

    pred1 = get_bonus_prediction(USER_ID, 1)
    pred2 = get_bonus_prediction(USER_ID, 2)
    pred3 = get_bonus_prediction(USER_ID, 3)

    assert pred1 is not None
    assert pred2 is not None
    assert pred3 is not None

    assert pred1["answer"] == "Brazil"
    assert pred2["answer"] == "Mbappe"
    assert pred3["answer"] == "Yes"

    # ---------- UPDATE PREDICTION ----------

    save_bonus_prediction(USER_ID, 1, "France")

    pred1 = get_bonus_prediction(USER_ID, 1)

    assert pred1["answer"] == "France"

    # ---------- GET PREDICTIONS ----------

    predictions = get_bonus_predictions(1)

    assert any(
        p["user_id"] == USER_ID and p["answer"] == "France"
        for p in predictions
    )

    # ---------- ADMIN VIEW ----------

    # =====================================================
# ADMIN VIEW
# =====================================================

    rows = get_bonus_predictions_for_questions(
        USER_ID,
        [1, 2, 3],
    )

    print(type(rows))
    print(rows) 

    assert len(rows) == 3

    assert any(
        r["question_id"] == 1 and r["answer"] == "France"
        for r in rows
    )

    assert any(
        r["question_id"] == 2 and r["answer"] == "Mbappe"
        for r in rows
    )

    assert any(
        r["question_id"] == 3 and r["answer"] == "Yes"
        for r in rows
    )

    # =====================================================
    # DELETE PREDICTIONS
    # =====================================================

    delete_bonus_prediction(USER_ID, 1)
    delete_bonus_prediction(USER_ID, 2)
    delete_bonus_prediction(USER_ID, 3)

    assert get_bonus_prediction(USER_ID, 1) is None
    assert get_bonus_prediction(USER_ID, 2) is None
    assert get_bonus_prediction(USER_ID, 3) is None

    # =====================================================
    # DELETE QUESTION
    # =====================================================

    delete_bonus_question(question_id)

    assert get_bonus_question(question_id) is None