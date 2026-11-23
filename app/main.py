from fastapi import FastAPI

from app.routers import analytics, auth, tasks, topics, users

app = FastAPI(
    title="Трекер задач",
    version="1.0.0",
    description="Сервис учёта задач: CRUD, фильтрация, статусы, аналитика и графики.",
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(topics.router)
app.include_router(tasks.router)
app.include_router(analytics.router)


@app.get("/health", tags=["Служебное"], summary="Проверка работоспособности")
def health():
    return {"status": "ok"}
