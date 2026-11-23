from datetime import datetime, timedelta, timezone

import pandas as pd

from app.analytics import build_dataframe, build_summary, group_counts, render_chart
from app.constants import GroupBy


def sample_rows():
    now = datetime.now(timezone.utc)
    return [
        (1, "новая", "средний", now - timedelta(days=1), now - timedelta(days=5), None, "Разработка", None),
        (2, "выполнена", "высокий", None, now - timedelta(days=3), now - timedelta(days=2), None, "Иван"),
        (3, "выполнена", "низкий", None, now - timedelta(days=2), now - timedelta(days=1), "Разработка", "Иван"),
        (4, "отменена", "средний", now - timedelta(days=1), now - timedelta(days=4), None, "Дизайн", "Пётр"),
    ]


def test_group_counts_status_includes_all_statuses():
    df = build_dataframe(sample_rows())
    counts = {item["name"]: item["count"] for item in group_counts(df, GroupBy.STATUS)}
    assert counts["новая"] == 1
    assert counts["выполнена"] == 2
    assert counts["в работе"] == 0
    assert len(counts) == 5


def test_group_counts_topic_sorted_desc():
    df = build_dataframe(sample_rows())
    items = group_counts(df, GroupBy.TOPIC)
    assert items[0] == {"name": "Разработка", "count": 2}
    assert {"name": "Без темы", "count": 1} in items


def test_summary_values():
    summary = build_summary(build_dataframe(sample_rows()))
    assert summary["total"] == 4
    assert summary["completed"] == 2
    assert summary["completion_rate"] == 50.0
    assert summary["overdue"] == 1
    assert summary["avg_completion_hours"] == 24.0


def test_summary_empty_dataframe():
    summary = build_summary(build_dataframe([]))
    assert summary["total"] == 0
    assert summary["by_topic"] == []
    assert isinstance(pd.DataFrame(), pd.DataFrame)


def test_render_chart_returns_png():
    df = build_dataframe(sample_rows())
    for group_by in GroupBy:
        assert render_chart(df, group_by).startswith(b"\x89PNG")
    assert render_chart(build_dataframe([]), GroupBy.STATUS).startswith(b"\x89PNG")
