ACTIVITY_COEFFICIENTS = {
    "low": 1.2,
    "medium": 1.375,
    "high": 1.55,
}

GOAL_DEFICIT = {
    "-2": 500,
    "-5": 700,
    "-10": 900,
    "-15": 1000,
}

GOAL_LABELS = {
    "-2": "−2 кг",
    "-5": "−5 кг",
    "-10": "−10 кг",
    "-15": "−15 кг и более",
}

ACTIVITY_LABELS = {
    "low": "Малоподвижный",
    "medium": "Умеренно активный",
    "high": "Активный",
}


def calc_target_calories(
    weight: float,
    height: float,
    age: int,
    gender: str,
    activity: str,
    goal: str,
) -> int:
    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    tdee = bmr * ACTIVITY_COEFFICIENTS[activity]
    deficit = GOAL_DEFICIT[goal]
    target = max(1200, round(tdee - deficit))
    return target
