from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.app.core.database import get_db
from backend.app.models.models import Task, User
from backend.app.schemas.schemas import TaskCreate, TaskOut, TaskStatusUpdate
from backend.app.api.deps import get_current_admin, get_current_user

router = APIRouter()

@router.get("", response_model=List[TaskOut])
def list_all_tasks(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    List all tasks in the system. (Admin/Manager only)
    """
    return db.query(Task).order_by(Task.date_created.desc()).all()

@router.get("/my", response_model=List[TaskOut])
def list_my_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List tasks assigned to the current logged-in user.
    """
    return db.query(Task).filter(Task.assigned_to_id == current_user.id).order_by(Task.date_created.desc()).all()

@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Create a new task and assign it to a user. (Admin/Manager only)
    """
    # Verify assignee exists
    assignee = db.query(User).filter(User.id == task_in.assigned_to_id).first()
    if not assignee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignee user not found."
        )

    task = Task(
        title=task_in.title,
        description=task_in.description,
        assigned_to_id=task_in.assigned_to_id,
        due_date=task_in.due_date,
        status="Pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.put("/{id}/status", response_model=TaskOut)
def update_task_status(
    id: int,
    status_in: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a task's status (Pending/Completed).
    Available to the assigned user or an Admin.
    """
    task = db.query(Task).filter(Task.id == id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found."
        )

    # Permission check: current user must be the assignee or an Admin
    is_admin = current_user.role.name == "Administrator"
    is_assignee = task.assigned_to_id == current_user.id

    if not is_admin and not is_assignee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this task's status."
        )

    if status_in.status not in ["Pending", "Completed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Allowed values: Pending, Completed."
        )

    task.status = status_in.status
    db.commit()
    db.refresh(task)
    return task
