"""The 17 API-level evaluation scenarios (eval/scenarios.py) must all pass with the mock model."""
import pytest

from eval.scenarios import SCENARIOS, run_one


@pytest.mark.parametrize("sc", SCENARIOS, ids=[s[0] for s in SCENARIOS])
def test_scenario(client, sc):
    result = run_one(client, sc)
    assert result["pass"], result
