import io

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.ticker import MaxNLocator

from app.constants import (
    CLOSED_STATUSES,
    NO_ASSIGNEE_LABEL,
    NO_TOPIC_LABEL,
    GroupBy,
    TaskPriority,
    TaskStatus,
)

COLUMNS = [
    "id",
    "status",
    "priority",
    "due_date",
    "created_at",
    "completed_at",
    "topic",
    "assignee",
]

GROUP_COLUMNS = {
    GroupBy.STATUS: "status",
    GroupBy.TOPIC: "topic",
    GroupBy.ASSIGNEE: "assignee",
}

STATUS_ORDER = [item.value for item in TaskStatus]
PRIORITY_ORDER = [item.value for item in TaskPriority]

CHART_TITLES = {
    GroupBy.STATUS: "Задачи по статусам",
    GroupBy.TOPIC: "Задачи по темам",
    GroupBy.ASSIGNEE: "Задачи по исполнителям",
}

CHART_X_LABELS = {
    GroupBy.STATUS: "Статус",
    GroupBy.TOPIC: "Тема",
    GroupBy.ASSIGNEE: "Исполнитель",
}


def build_dataframe(rows: list[tuple]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=COLUMNS)
    df["topic"] = df["topic"].fillna(NO_TOPIC_LABEL)
    df["assignee"] = df["assignee"].fillna(NO_ASSIGNEE_LABEL)
    return df


def count_by(df: pd.DataFrame, column: str, order: list[str] | None = None) -> list[dict]:
    if df.empty:
        counts = pd.Series(dtype="int64")
    else:
        counts = df.groupby(column).size()
    if order is not None:
        counts = counts.reindex(order, fill_value=0)
    items = [{"name": str(name), "count": int(count)} for name, count in counts.items()]
    if order is None:
        items.sort(key=lambda item: (-item["count"], item["name"]))
    return items


def group_counts(df: pd.DataFrame, group_by: GroupBy) -> list[dict]:
    order = STATUS_ORDER if group_by == GroupBy.STATUS else None
    return count_by(df, GROUP_COLUMNS[group_by], order)


def build_summary(df: pd.DataFrame) -> dict:
    total = int(len(df))
    completed = int((df["status"] == TaskStatus.DONE.value).sum()) if total else 0
    overdue = 0
    avg_hours = None
    if total:
        now = pd.Timestamp.now(tz="UTC")
        due = pd.to_datetime(df["due_date"], utc=True)
        active = ~df["status"].isin(CLOSED_STATUSES)
        overdue = int(((due < now) & active).sum())
        created = pd.to_datetime(df["created_at"], utc=True)
        finished = pd.to_datetime(df["completed_at"], utc=True)
        hours = ((finished - created).dt.total_seconds() / 3600).dropna()
        if not hours.empty:
            avg_hours = round(float(hours.mean()), 2)
    return {
        "total": total,
        "completed": completed,
        "completion_rate": round(completed / total * 100, 1) if total else 0.0,
        "overdue": overdue,
        "avg_completion_hours": avg_hours,
        "by_status": count_by(df, "status", STATUS_ORDER),
        "by_priority": count_by(df, "priority", PRIORITY_ORDER),
        "by_topic": count_by(df, "topic"),
        "by_assignee": count_by(df, "assignee"),
    }


def render_chart(df: pd.DataFrame, group_by: GroupBy) -> bytes:
    frame = pd.DataFrame(group_counts(df, group_by), columns=["name", "count"])
    with sns.axes_style("whitegrid"):
        fig, ax = plt.subplots(figsize=(9, 5))
        if frame.empty:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", fontsize=16)
            ax.set_axis_off()
        else:
            sns.barplot(
                data=frame,
                x="name",
                y="count",
                hue="name",
                palette="viridis",
                legend=False,
                ax=ax,
            )
            for container in ax.containers:
                ax.bar_label(container, fontsize=10)
            ax.set_xlabel(CHART_X_LABELS[group_by])
            ax.set_ylabel("Количество задач")
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        ax.set_title(CHART_TITLES[group_by], fontsize=14)
        fig.tight_layout()
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=120)
        plt.close(fig)
    return buffer.getvalue()
