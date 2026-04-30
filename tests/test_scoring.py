from skylimpiadas.scoring import software_score


def test_software_score_matches_regulation_formula():
    assert round(software_score(4, 6, 1), 2) == 40.60


def test_software_score_allows_zero_progress():
    assert software_score(0, 0, 0) == 0
