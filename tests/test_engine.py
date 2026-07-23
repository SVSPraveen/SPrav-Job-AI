import pytest
from engine.tailor import validate_selection, construct_prompt

@pytest.fixture
def sample_kb():
    # validate_selection calls flatten_bullets(), which reads work_history and projects.
    # The KB must use those keys, not the pre-flattened 'resume_bullets' key.
    return {
        "work_history": [
            {
                "id": "work_1",
                "company": "Acme",
                "role": "Engineer",
                "bullets": [
                    {"id": "bullet_1", "text": "Did a thing."},
                ]
            }
        ],
        "projects": [
            {
                "id": "proj_1",
                "name": "Side project",
                "bullets": [
                    {"id": "bullet_2", "text": "Built a thing."},
                ]
            }
        ]
    }

def test_validate_selection_filters_invalid_ids(sample_kb):
    selected_ids = ["bullet_1", "bullet_fake", "bullet_2"]
    valid_ids = validate_selection(selected_ids, sample_kb)
    
    assert "bullet_1" in valid_ids
    assert "bullet_2" in valid_ids
    assert "bullet_fake" not in valid_ids
    assert len(valid_ids) == 2

def test_construct_prompt_contains_jd_and_kb(sample_kb):
    jd_text = "Looking for someone to do things."
    prompt = construct_prompt(jd_text, sample_kb)
    
    assert jd_text in prompt
    assert "bullet_1" in prompt
    assert "Did a thing" in prompt
