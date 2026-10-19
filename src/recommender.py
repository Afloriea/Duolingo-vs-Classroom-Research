"""The decision framework from the final recommendation.

A learner picks their top three priorities out of six. Each priority is mapped to the
method the research found stronger on it; the method with the majority of picks wins.

    python src/recommender.py flexibility time proficiency
"""
import sys

# priority -> (recommended method, evidence behind the mapping)
PRIORITIES = {
    "prestige": ("Classroom", "Interview themes: interaction, cultural comprehension, oversimplification"),
    "proficiency": ("Classroom", "Survey: designated courses most often named most effective"),
    "interaction": ("Classroom", "Interview theme: interactive learning and participation"),
    "time": ("Duolingo", "Case study: a lesson fits in about 5 minutes on a busy day"),
    "flexibility": ("Duolingo", "Survey: flexibility ranked top-2 by the most respondents"),
    "entertainment": ("Duolingo", "Case study: gamified lessons kept daily practice going"),
}


def recommend(picks: list[str]) -> tuple[str, dict[str, int]]:
    picks = [p.lower() for p in picks]
    if len(picks) != 3 or len(set(picks)) != 3:
        raise ValueError("Pick exactly three different priorities.")
    unknown = [p for p in picks if p not in PRIORITIES]
    if unknown:
        raise ValueError(f"Unknown priority: {', '.join(unknown)}. Choose from {', '.join(PRIORITIES)}.")
    votes = {"Classroom": 0, "Duolingo": 0}
    for p in picks:
        votes[PRIORITIES[p][0]] += 1
    # Three picks over two methods can never tie, so the majority is always defined.
    return max(votes, key=votes.get), votes


def main(argv: list[str]) -> None:
    if len(argv) != 3:
        print(__doc__)
        print("Priorities:", ", ".join(PRIORITIES))
        return
    method, votes = recommend(argv)
    print(f"Recommendation: {method}  (Classroom {votes['Classroom']} : Duolingo {votes['Duolingo']})")
    for p in argv:
        m, why = PRIORITIES[p.lower()]
        print(f"  {p:<13} -> {m:<9} {why}")


if __name__ == "__main__":
    main(sys.argv[1:])
