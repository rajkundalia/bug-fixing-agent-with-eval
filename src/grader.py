"""src/grader.py"""


def get_grade(score: int) -> str:
    """Return the letter grade for a numeric score."""
    if score > 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"
