def make_task(client, headers, **overrides):
    payload = {"title": "Подготовить отчёт"}
    payload.update(overrides)
    response = client.post("/tasks", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_task_defaults(client, alice):
    user, headers = alice
    task = make_task(client, headers)
    assert task["status"] == "новая"
    assert task["priority"] == "средний"
    assert task["author"]["id"] == user["id"]
    assert task["completed_at"] is None


def test_create_task_with_relations(client, alice, bob):
    _, headers = alice
    bob_user, _ = bob
    topic = client.post("/topics", json={"name": "Разработка"}, headers=headers).json()
    task = make_task(
        client,
        headers,
        topic_id=topic["id"],
        assignee_id=bob_user["id"],
        priority="высокий",
        due_date="2030-01-01T10:00:00+00:00",
    )
    assert task["topic"]["name"] == "Разработка"
    assert task["assignee"]["username"] == "bob"
    assert task["priority"] == "высокий"


def test_create_task_validation(client, alice):
    _, headers = alice
    assert client.post("/tasks", json={"title": "   "}, headers=headers).status_code == 422
    assert client.post("/tasks", json={"title": "x", "status": "unknown"}, headers=headers).status_code == 422
    assert client.post("/tasks", json={"title": "x", "priority": "срочный"}, headers=headers).status_code == 422


def test_create_task_unknown_relations(client, alice):
    _, headers = alice
    assert client.post("/tasks", json={"title": "x", "topic_id": 999}, headers=headers).status_code == 404
    assert client.post("/tasks", json={"title": "x", "assignee_id": 999}, headers=headers).status_code == 404


def test_get_task_and_not_found(client, alice):
    _, headers = alice
    task = make_task(client, headers)
    assert client.get(f"/tasks/{task['id']}", headers=headers).json()["title"] == "Подготовить отчёт"
    assert client.get("/tasks/9999", headers=headers).status_code == 404


def test_update_task(client, alice):
    _, headers = alice
    task = make_task(client, headers)
    response = client.put(
        f"/tasks/{task['id']}",
        json={"title": "Новый заголовок", "priority": "низкий", "description": "Описание"},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Новый заголовок"
    assert body["priority"] == "низкий"
    assert body["description"] == "Описание"


def test_update_task_rejects_null_title(client, alice):
    _, headers = alice
    task = make_task(client, headers)
    response = client.put(f"/tasks/{task['id']}", json={"title": None}, headers=headers)
    assert response.status_code == 422


def test_update_task_can_clear_assignee(client, alice, bob):
    _, headers = alice
    bob_user, _ = bob
    task = make_task(client, headers, assignee_id=bob_user["id"])
    response = client.put(f"/tasks/{task['id']}", json={"assignee_id": None}, headers=headers)
    assert response.status_code == 200
    assert response.json()["assignee"] is None


def test_status_transitions_set_completed_at(client, alice):
    _, headers = alice
    task = make_task(client, headers)
    url = f"/tasks/{task['id']}/status"
    in_progress = client.patch(url, json={"status": "в работе"}, headers=headers).json()
    assert in_progress["status"] == "в работе"
    assert in_progress["completed_at"] is None
    done = client.patch(url, json={"status": "выполнена"}, headers=headers).json()
    assert done["status"] == "выполнена"
    assert done["completed_at"] is not None
    reopened = client.patch(url, json={"status": "в работе"}, headers=headers).json()
    assert reopened["completed_at"] is None


def test_status_invalid_value(client, alice):
    _, headers = alice
    task = make_task(client, headers)
    response = client.patch(f"/tasks/{task['id']}/status", json={"status": "done"}, headers=headers)
    assert response.status_code == 422


def test_delete_only_by_author(client, alice, bob):
    _, alice_headers = alice
    _, bob_headers = bob
    task = make_task(client, alice_headers)
    assert client.delete(f"/tasks/{task['id']}", headers=bob_headers).status_code == 403
    assert client.delete(f"/tasks/{task['id']}", headers=alice_headers).status_code == 204
    assert client.get(f"/tasks/{task['id']}", headers=alice_headers).status_code == 404


def test_list_filters(client, alice, bob):
    _, headers = alice
    bob_user, _ = bob
    topic = client.post("/topics", json={"name": "Тестирование"}, headers=headers).json()
    make_task(client, headers, title="Первая", status="новая", priority="низкий")
    make_task(client, headers, title="Вторая", status="в работе", priority="высокий", topic_id=topic["id"])
    make_task(client, headers, title="Третья", status="выполнена", assignee_id=bob_user["id"])

    assert client.get("/tasks", headers=headers).json()["total"] == 3
    by_status = client.get("/tasks", params={"status": "в работе"}, headers=headers).json()
    assert [t["title"] for t in by_status["items"]] == ["Вторая"]
    by_priority = client.get("/tasks", params={"priority": "низкий"}, headers=headers).json()
    assert [t["title"] for t in by_priority["items"]] == ["Первая"]
    by_topic = client.get("/tasks", params={"topic_id": topic["id"]}, headers=headers).json()
    assert by_topic["total"] == 1
    by_assignee = client.get("/tasks", params={"assignee_id": bob_user["id"]}, headers=headers).json()
    assert [t["title"] for t in by_assignee["items"]] == ["Третья"]


def test_list_search(client, alice):
    _, headers = alice
    make_task(client, headers, title="Купить молоко")
    make_task(client, headers, title="Написать код", description="нужно молоко для кофе")
    make_task(client, headers, title="Скидка 50% на всё")
    found = client.get("/tasks", params={"search": "молоко"}, headers=headers).json()
    assert found["total"] == 2
    percent = client.get("/tasks", params={"search": "%"}, headers=headers).json()
    assert [t["title"] for t in percent["items"]] == ["Скидка 50% на всё"]
    underscore = client.get("/tasks", params={"search": "_"}, headers=headers).json()
    assert underscore["total"] == 0


def test_list_search_sql_injection(client, alice):
    _, headers = alice
    make_task(client, headers, title="Обычная задача")
    payloads = ["'; DROP TABLE tasks; --", "' OR '1'='1", "\" OR 1=1 --", "1; DELETE FROM tasks"]
    for payload in payloads:
        response = client.get("/tasks", params={"search": payload}, headers=headers)
        assert response.status_code == 200
        assert response.json()["total"] == 0
    assert client.get("/tasks", headers=headers).json()["total"] == 1


def test_list_rejects_injection_in_typed_params(client, alice):
    _, headers = alice
    assert client.get("/tasks", params={"topic_id": "1 OR 1=1"}, headers=headers).status_code == 422
    assert client.get("/tasks", params={"status": "новая'; --"}, headers=headers).status_code == 422
    assert client.get("/tasks", params={"sort_by": "id; DROP TABLE tasks"}, headers=headers).status_code == 422


def test_list_pagination_and_sorting(client, alice):
    _, headers = alice
    for title in ("Б", "А", "В"):
        make_task(client, headers, title=title)
    page = client.get(
        "/tasks",
        params={"sort_by": "title", "order": "asc", "limit": 2, "offset": 0},
        headers=headers,
    ).json()
    assert [t["title"] for t in page["items"]] == ["А", "Б"]
    assert page["total"] == 3
    rest = client.get(
        "/tasks",
        params={"sort_by": "title", "order": "asc", "limit": 2, "offset": 2},
        headers=headers,
    ).json()
    assert [t["title"] for t in rest["items"]] == ["В"]
    assert client.get("/tasks", params={"limit": 0}, headers=headers).status_code == 422
    assert client.get("/tasks", params={"limit": 1000}, headers=headers).status_code == 422


def test_list_overdue_and_due_filters(client, alice):
    _, headers = alice
    make_task(client, headers, title="Просрочена", due_date="2020-01-01T00:00:00+00:00")
    make_task(
        client,
        headers,
        title="Просрочена, но выполнена",
        due_date="2020-01-01T00:00:00+00:00",
        status="выполнена",
    )
    make_task(client, headers, title="В будущем", due_date="2999-01-01T00:00:00+00:00")
    overdue = client.get("/tasks", params={"overdue_only": True}, headers=headers).json()
    assert [t["title"] for t in overdue["items"]] == ["Просрочена"]
    before = client.get(
        "/tasks", params={"due_before": "2021-01-01T00:00:00+00:00"}, headers=headers
    ).json()
    assert before["total"] == 2
    after = client.get(
        "/tasks", params={"due_after": "2900-01-01T00:00:00+00:00"}, headers=headers
    ).json()
    assert [t["title"] for t in after["items"]] == ["В будущем"]


def test_topics_crud(client, alice):
    _, headers = alice
    topic = client.post("/topics", json={"name": "Дизайн", "description": "Макеты"}, headers=headers)
    assert topic.status_code == 201
    assert client.post("/topics", json={"name": "Дизайн"}, headers=headers).status_code == 409
    assert [t["name"] for t in client.get("/topics", headers=headers).json()] == ["Дизайн"]
    task = make_task(client, headers, topic_id=topic.json()["id"])
    assert client.delete(f"/topics/{topic.json()['id']}", headers=headers).status_code == 204
    assert client.get(f"/tasks/{task['id']}", headers=headers).json()["topic"] is None
    assert client.delete("/topics/9999", headers=headers).status_code == 404


def test_users_list(client, alice, bob):
    _, headers = alice
    usernames = {u["username"] for u in client.get("/users", headers=headers).json()}
    assert usernames == {"alice", "bob"}
