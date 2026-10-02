"""Small educational phishing classifier trained on URL/page feature examples.

For a real deployment, replace the sample data with a versioned, audited phishing
dataset and retrain the model offline.
"""

from sklearn.ensemble import RandomForestClassifier


# Features: HTTP, IP host, many hyphens, risky TLD, long URL, credential terms,
# password field, external form action, brand word in domain.
TRAINING_ROWS = [
    ([0, 0, 0, 0, 0, 0, 0, 0, 0], 0), ([0, 0, 0, 0, 0, 1, 1, 0, 0], 0),
    ([0, 0, 0, 0, 1, 0, 0, 0, 0], 0), ([1, 0, 1, 1, 1, 1, 1, 1, 1], 1),
    ([1, 1, 0, 0, 0, 1, 1, 1, 0], 1), ([0, 0, 1, 1, 0, 1, 1, 0, 1], 1),
    ([1, 0, 0, 1, 1, 1, 1, 1, 0], 1), ([0, 1, 1, 0, 1, 0, 1, 1, 0], 1),
    ([0, 0, 0, 0, 0, 0, 1, 0, 0], 0), ([0, 0, 1, 0, 0, 0, 0, 0, 0], 0),
]

MODEL = RandomForestClassifier(n_estimators=80, max_depth=4, random_state=42)
MODEL.fit([row for row, _ in TRAINING_ROWS], [label for _, label in TRAINING_ROWS])


def phishing_probability(features: list[int]) -> float:
    return float(MODEL.predict_proba([features])[0][1])
