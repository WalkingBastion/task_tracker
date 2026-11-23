from enum import StrEnum


class TaskStatus(StrEnum):
    NEW = "новая"
    IN_PROGRESS = "в работе"
    REVIEW = "на проверке"
    DONE = "выполнена"
    CANCELLED = "отменена"


class TaskPriority(StrEnum):
    LOW = "низкий"
    MEDIUM = "средний"
    HIGH = "высокий"


class GroupBy(StrEnum):
    STATUS = "status"
    TOPIC = "topic"
    ASSIGNEE = "assignee"


class SortField(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    DUE_DATE = "due_date"
    TITLE = "title"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


NO_TOPIC_LABEL = "Без темы"
NO_ASSIGNEE_LABEL = "Не назначен"
CLOSED_STATUSES = (TaskStatus.DONE.value, TaskStatus.CANCELLED.value)
