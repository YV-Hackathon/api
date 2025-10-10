from inference_service import get_model_service


JSON_INPUT = {
    "trait_choices": [
        "Gender::Female pastor",
        "Preaching method::Topical",
        "Theological tradition::Mixed",
        "Women in leadership::Egalitarian",
    ],
    "swipes": [
        {"pastorName": "AndyStanley,", "pastorId": 44, "rating": 5},
        {"pastorName": "RickWarren", "pastorId": 45, "rating": 4},
        {"pastorName": "JohnPiper", "pastorId": 48, "rating": 2},
    ],
}


def main() -> None:
    svc = get_model_service()
    user_preferences = {"trait_choices": JSON_INPUT.get("trait_choices", [])}
    user_swipes = [
        {"speaker_id": s.get("pastorId"), "rating": float(s.get("rating", 0))}
        for s in JSON_INPUT.get("swipes", [])
    ]
    recs = svc.generate_recommendations(
        user_preferences=user_preferences,
        user_swipes=user_swipes,
        limit=2,
    )
    print("Basic:", recs)

    detailed = svc.generate_recommendations_detailed(
        user_preferences=user_preferences,
        user_swipes=user_swipes,
        limit=2,
    )
    print("Detailed:", detailed)


if __name__ == "__main__":
    main()
