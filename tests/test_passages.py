import pytest

from passages import PASSAGES, get_passage

PASSAGE_IDS = sorted(PASSAGES)


def test_expected_passage_ids():
    assert PASSAGE_IDS == [
        "academic",
        "financial",
        "legal",
        "medical",
        "scientific",
    ]


@pytest.mark.parametrize("passage_id", PASSAGE_IDS)
def test_passage_has_required_fields(passage_id):
    passage = PASSAGES[passage_id]

    assert passage["title"].strip()
    assert passage["control_text"].strip()
    assert passage["treatment_text"].strip()
    assert passage["quiz1_questions"]
    assert passage["quiz2_questions"]


@pytest.mark.parametrize("passage_id", PASSAGE_IDS)
@pytest.mark.parametrize("quiz_key", ["quiz1_questions", "quiz2_questions"])
def test_quiz_questions_are_well_formed(passage_id, quiz_key):
    for question in PASSAGES[passage_id][quiz_key]:
        options = question["options"]

        assert question["question"].strip()
        assert len(options) >= 2
        assert len(set(options)) == len(options)
        assert isinstance(question["answer"], int)
        assert 0 <= question["answer"] < len(options)


@pytest.mark.parametrize("passage_id", PASSAGE_IDS)
def test_get_passage_returns_matching_passage(passage_id):
    assert get_passage(passage_id) is PASSAGES[passage_id]


@pytest.mark.parametrize("passage_id", ["unknown", "", None, 0])
def test_get_passage_defaults_to_medical(passage_id):
    assert get_passage(passage_id) is PASSAGES["medical"]
