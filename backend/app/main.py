import os
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from .auth import create_access_token, get_current_user, hash_password, require_admin, verify_password
from .database import Base, engine, get_db
from .models import Attachment, Comment, Priority, Role, Task, TaskStatus, User
from .schemas import (
    AttachmentOut,
    CommentCreate,
    CommentOut,
    DashboardSummary,
    LoginRequest,
    TaskCreate,
    TaskOut,
    TaskUpdate,
    Token,
    UserCreate,
    UserOut,
)


app = FastAPI(title="TaskFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def seed_data(db: Session) -> None:
    if db.query(User).count() > 0:
        return

    admin = User(
        name="Admin User",
        email="admin@taskflow.dev",
        hashed_password=hash_password("Admin123!"),
        role=Role.admin,
    )
    user = User(
        name="Demo User",
        email="user@taskflow.dev",
        hashed_password=hash_password("User123!"),
        role=Role.user,
    )
    db.add_all([admin, user])
    db.flush()

    db.add_all(
        [
            Task(
                title="Launch onboarding checklist",
                description="Create a repeatable checklist for new client setup.",
                status=TaskStatus.in_progress,
                priority=Priority.high,
                due_date=datetime.utcnow() + timedelta(days=3),
                assignee_id=user.id,
                created_by_id=admin.id,
            ),
            Task(
                title="Review overdue notification copy",
                description="Polish the notification text before release.",
                status=TaskStatus.todo,
                priority=Priority.medium,
                due_date=datetime.utcnow() - timedelta(days=1),
                assignee_id=user.id,
                created_by_id=admin.id,
            ),
        ]
    )
    db.commit()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        seed_data(db)
    finally:
        db.close()


def task_query(db: Session):
    return db.query(Task).options(
        joinedload(Task.assignee),
        joinedload(Task.creator),
        joinedload(Task.comments).joinedload(Comment.author),
        joinedload(Task.attachments),
    )


def get_visible_task(task_id: int, db: Session, current_user: User) -> Task:
    task = task_query(db).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role != Role.admin and task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only access assigned tasks")
    return task


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/register", response_model=UserOut, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=Role.user,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return Token(access_token=create_access_token(user))


@app.get("/users/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@app.get("/admin/users", response_model=list[UserOut])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> list[User]:
    return db.query(User).order_by(User.name).all()


@app.get("/tasks", response_model=list[TaskOut])
def list_tasks(
    search: str | None = None,
    status: TaskStatus | None = None,
    priority: Priority | None = None,
    assigned_to_me: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Task]:
    query = task_query(db)
    if current_user.role != Role.admin or assigned_to_me:
        query = query.filter(Task.assignee_id == current_user.id)
    if search:
        term = f"%{search}%"
        query = query.filter(or_(Task.title.ilike(term), Task.description.ilike(term)))
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    return query.order_by(Task.due_date.is_(None), Task.due_date.asc()).all()


@app.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(
    payload: TaskCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Task:
    if payload.assignee_id and not db.get(User, payload.assignee_id):
        raise HTTPException(status_code=404, detail="Assignee not found")
    task = Task(**payload.model_dump(), created_by_id=current_user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return get_visible_task(task.id, db, current_user)


@app.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    task = get_visible_task(task_id, db, current_user)
    changes = payload.model_dump(exclude_unset=True)
    if current_user.role != Role.admin:
        changes = {key: value for key, value in changes.items() if key in {"status"}}
    if "assignee_id" in changes and changes["assignee_id"] and not db.get(User, changes["assignee_id"]):
        raise HTTPException(status_code=404, detail="Assignee not found")
    for key, value in changes.items():
        setattr(task, key, value)
    task.updated_at = datetime.utcnow()
    db.commit()
    return get_visible_task(task.id, db, current_user)


@app.post("/tasks/{task_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(
    task_id: int,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Comment:
    task = get_visible_task(task_id, db, current_user)
    comment = Comment(body=payload.body, task_id=task.id, author_id=current_user.id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@app.post("/tasks/{task_id}/attachments", response_model=AttachmentOut, status_code=201)
async def upload_attachment(
    task_id: int,
    upload: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Attachment:
    task = get_visible_task(task_id, db, current_user)
    upload_dir = Path(os.getenv("UPLOAD_DIR", "uploads"))
    upload_dir.mkdir(exist_ok=True)
    safe_name = Path(upload.filename or "attachment").name
    target = upload_dir / f"task-{task.id}-{int(datetime.utcnow().timestamp())}-{safe_name}"
    target.write_bytes(await upload.read())
    attachment = Attachment(
        filename=safe_name,
        content_type=upload.content_type or "application/octet-stream",
        path=str(target),
        task_id=task.id,
        uploaded_by_id=current_user.id,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


@app.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardSummary:
    query = db.query(Task)
    if current_user.role != Role.admin:
        query = query.filter(Task.assignee_id == current_user.id)
    tasks = query.all()
    now = datetime.utcnow()
    week_end = now + timedelta(days=7)
    return DashboardSummary(
        total_tasks=len(tasks),
        overdue_tasks=sum(1 for task in tasks if task.due_date and task.due_date < now and task.status != TaskStatus.done),
        by_status={status.value: sum(1 for task in tasks if task.status == status) for status in TaskStatus},
        by_priority={priority.value: sum(1 for task in tasks if task.priority == priority) for priority in Priority},
        due_this_week=sum(1 for task in tasks if task.due_date and now <= task.due_date <= week_end),
    )


@app.get("/reports/tasks")
def task_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    tasks = list_tasks(current_user=current_user, db=db)
    completion_rate = 0 if not tasks else round(sum(task.status == TaskStatus.done for task in tasks) / len(tasks), 2)
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "completion_rate": completion_rate,
        "open_high_priority": sum(task.priority in {Priority.high, Priority.urgent} and task.status != TaskStatus.done for task in tasks),
        "tasks": [{"id": task.id, "title": task.title, "status": task.status, "priority": task.priority} for task in tasks],
    }


@app.get("/notifications")
def notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    now = datetime.utcnow()
    tasks = list_tasks(current_user=current_user, db=db)
    return [
        {"task_id": task.id, "message": f"{task.title} is overdue", "priority": task.priority}
        for task in tasks
        if task.due_date and task.due_date < now and task.status != TaskStatus.done
    ]
