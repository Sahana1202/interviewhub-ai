def test_dashboard_requires_authentication(client):
    assert client.get("/api/dashboard").status_code == 401


def test_dashboard_aggregates_saved_profile_without_fabricated_progress(client, registered_user):
    headers = registered_user["headers"]
    initial = client.get("/api/dashboard", headers=headers)
    assert initial.status_code == 200
    assert initial.json()["name"] == "Test Candidate"
    assert initial.json()["profile_completion"] == 0
    assert initial.json()["progress"] == {"technical": None, "aptitude": None, "english": None, "interview": None}
    assert initial.json()["recent_activity"] == []
    assert initial.json()["recommended_topics"] == []

    saved = client.put("/api/profile", headers=headers, json={
        "college": "Example College", "degree": "B.E.", "department": "CSE", "graduation_year": 2027,
        "experience_level": "Fresher", "target_role": "Backend Developer", "target_industry": "Software", "location": "Chennai",
    })
    assert saved.status_code == 200
    dashboard = client.get("/api/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["profile"] == {"target_role": "Backend Developer", "target_industry": "Software", "experience_level": "Fresher"}
    assert dashboard.json()["profile_completion"] == 100
    assert "REST API design" in dashboard.json()["recommended_topics"]
