import random
from datetime import datetime, timedelta, timezone

from app.constants import TaskPriority, TaskStatus
from app.database import SessionLocal
from app.models import Task, Topic, User
from app.security import hash_password

DEMO_PASSWORD = "demo12345"

USERS = [
    ("ivanov", "Иван Иванов"),
    ("petrova", "Мария Петрова"),
    ("sidorov", "Алексей Сидоров"),
]

TOPICS = ["Разработка", "Тестирование", "Дизайн", "Документация"]

TITLES = [
    "Подготовить отчёт",
    "Исправить ошибку авторизации",
    "Обновить зависимости",
    "Согласовать макет",
    "Написать тесты для API",
    "Провести ревью кода",
    "Настроить резервное копирование",
    "Обновить инструкцию",
    "Оптимизировать запросы",
    "Подготовить демонстрацию",
]


def main() -> None:
    random.seed(42)
    db = SessionLocal()
    try:
        if db.query(User).count():
            print("База данных уже содержит данные")
            return
        users = [
            User(username=username, full_name=full_name, hashed_password=hash_password(DEMO_PASSWORD))
            for username, full_name in USERS
        ]
        topics = [Topic(name=name) for name in TOPICS]
        db.add_all(users + topics)
        db.commit()
        now = datetime.now(timezone.utc)
        for index in range(60):
            created = now - timedelta(days=random.randint(1, 45), hours=random.randint(0, 23))
            status = random.choice(list(TaskStatus))
            completed = None
            if status == TaskStatus.DONE:
                completed = created + timedelta(hours=random.randint(2, 120))
            due = created + timedelta(days=random.randint(3, 30)) if random.random() < 0.7 else None
            db.add(
                Task(
                    title=f"{random.choice(TITLES)} №{index + 1}",
                    status=status.value,
                    priority=random.choice(list(TaskPriority)).value,
                    topic_id=random.choice(topics).id if random.random() < 0.9 else None,
                    assignee_id=random.choice(users).id if random.random() < 0.85 else None,
                    author_id=random.choice(users).id,
                    due_date=due,
                    created_at=created,
                    updated_at=completed or created,
                    completed_at=completed,
                )
            )
        db.commit()
        print(f"Демо-данные созданы. Пользователи: {', '.join(u for u, _ in USERS)}, пароль: {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
