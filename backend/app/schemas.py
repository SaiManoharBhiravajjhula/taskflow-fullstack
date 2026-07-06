from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from .models import Priority, Role, TaskStatus


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: Role

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    description: str = ""
    status: TaskStatus = TaskStatus.todo
    priority: Priority = Priority.medium
    due_date: datetime | None = None
    assignee_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=180)
    description: str | None = None
    status: TaskStatus | None = None
    priority: Priority | None = None
    due_date: datetime | None = None
    assignee_id: int | None = None


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class CommentOut(BaseModel):
    id: int
    body: str
    created_at: datetime
    author: UserOut

    class Config:
        from_attributes = True


class AttachmentOut(BaseModel):
    id: int
    filename: str
    content_type: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    status: TaskStatus
    priority: Priority
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime
    assignee: UserOut | None
    creator: UserOut
    comments: list[CommentOut] = []
    attachments: list[AttachmentOut] = []

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    total_tasks: int
    overdue_tasks: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    due_this_week: int
