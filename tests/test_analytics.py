def make_task(client, headers, **payload):
    response = client.post("/tasks", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def seed(client, headers, assignee_id):
    dev = client.post("/topics", json={"name": "Разработка"}, headers=headers).json()
    qa = client.post("/topics", json={"name": "Тестирование"}, headers=headers).json()
    make_task(client, headers, title="1", status="новая", topic_id=dev["id"])
    make_task(client, headers, title="2", status="в работе", topic_id=dev["id"], assignee_id=assignee_id)
    make_task(client, headers, title="3", status="выполнена", topic_id=qa["id"], assignee_id=assignee_id)
    make_task(client, headers, title="4", status="выполнена", priority="высокий")
    make_task(
        client,
        headers,
        title="5",
        status="новая",
        due_date="2020-01-01T00:00:00+00:00",
    )


def as_map(items):
    return {item["name"]: item["count"] for item in items}


def test_group_by_status(client, alice, bob):
    _, headers = alice
    bob_user, _ = bob
    seed(client, headers, bob_user["id"])
    body = client.get("/analytics/group", params={"group_by": "status"}, headers=headers).json()
    assert body["group_by"] == "status"
    assert as_map(body["items"]) == {
        "новая": 2,
        "в работе": 1,
        "на проверке": 0,
        "выполнена": 2,
        "отменена": 0,
    }


def test_group_by_topic_and_assignee(client, alice, bob):
    _, headers = alice
    bob_user, _ = bob
    seed(client, headers, bob_user["id"])
    topics = client.get("/analytics/group", params={"group_by": "topic"}, headers=headers).json()
    assert as_map(topics["items"]) == {"Разработка": 2, "Тестирование": 1, "Без темы": 2}
    assignees = client.get("/analytics/group", params={"group_by": "assignee"}, headers=headers).json()
    assert as_map(assignees["items"]) == {"Bob": 2, "Не назначен": 3}


def test_group_invalid_value(client, alice):
    _, headers = alice
    assert client.get("/analytics/group", params={"group_by": "priority"}, headers=headers).status_code == 422


def test_summary(client, alice, bob):
    _, headers = alice
    bob_user, _ = bob
    seed(client, headers, bob_user["id"])
    body = client.get("/analytics/summary", headers=headers).json()
    assert body["total"] == 5
    assert body["completed"] == 2
    assert body["completion_rate"] == 40.0
    assert body["overdue"] == 1
    assert body["avg_completion_hours"] is not None
    assert as_map(body["by_priority"]) == {"низкий": 0, "средний": 4, "высокий": 1}
    assert as_map(body["by_status"])["выполнена"] == 2


def test_summary_empty(client, alice):
    _, headers = alice
    body = client.get("/analytics/summary", headers=headers).json()
    assert body["total"] == 0
    assert body["completion_rate"] == 0.0
    assert body["overdue"] == 0
    assert body["avg_completion_hours"] is None
    assert body["by_topic"] == []


def test_chart_png(client, alice, bob):
    _, headers = alice
    bob_user, _ = bob
    seed(client, headers, bob_user["id"])
    for group_by in ("status", "topic", "assignee"):
        response = client.get("/analytics/chart", params={"group_by": group_by}, headers=headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_chart_empty_database(client, alice):
    _, headers = alice
    response = client.get("/analytics/chart", headers=headers)
    assert response.status_code == 200
    assert response.content.startswith(b"\x89PNG")


def test_analytics_requires_auth(client):
    assert client.get("/analytics/group").status_code == 401
    assert client.get("/analytics/chart").status_code == 401
