from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.models.models import User, Role, Employee, Sale, Task
from backend.app.schemas.schemas import Token, UserCreate, UserOut, UserLogin, RoleOut, StaffOverviewOut
from backend.app.api.deps import get_current_user, get_current_admin

router = APIRouter()

@router.post("/login", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Retrieve user
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login-json", response_model=Token)
def login_json(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserOut)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    # Check email uniqueness
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists."
        )
    
    # Check role exists
    role = db.query(Role).filter(Role.id == user_in.role_id).first()
    if not role:
        raise HTTPException(
            status_code=400,
            detail="Invalid role ID."
        )

    db_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role_id=user_in.role_id,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Automatically seed an Employee detail entry
    dept = "Management" if role.name == "Administrator" else "Retail Store"
    pos = "Manager" if role.name == "Administrator" else "Store Associate"
    emp = Employee(user_id=db_user.id, department=dept, position=pos, salary=3000.0)
    db.add(emp)
    db.commit()

    return db_user

@router.get("/me", response_model=UserOut)
def read_users_me(
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.get("/roles", response_model=List[RoleOut])
def read_roles(
    db: Session = Depends(get_db)
):
    return db.query(Role).all()


@router.get("/staff", response_model=List[StaffOverviewOut])
def read_staff_overview(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Get detailed overview of all employees, their sales stats, assigned tasks, and last activity. (Admin/Manager only)
    """
    users = db.query(User).all()
    overview = []
    for u in users:
        role_name = u.role.name
        
        # Pull Employee record details if exists
        dept = u.employee.department if u.employee else None
        pos = u.employee.position if u.employee else None
        salary = u.employee.salary if u.employee else None
        hire_date = u.employee.hire_date if u.employee else None
        
        # Calculate sales count & total amount
        sales_count = 0
        total_sales_amount = 0.0
        last_sale_date = None
        
        if u.employee:
            sales = db.query(Sale).filter(Sale.employee_id == u.employee.id).all()
            sales_count = len(sales)
            total_sales_amount = sum(s.total_amount for s in sales)
            if sales:
                last_sale_date = max(s.date_created for s in sales)
        
        # Get tasks assigned to this user
        tasks = db.query(Task).filter(Task.assigned_to_id == u.id).all()
        pending_tasks = sum(1 for t in tasks if t.status == "Pending")
        completed_tasks = sum(1 for t in tasks if t.status == "Completed")
        
        # Determine last activity
        last_activity = last_sale_date
        if not last_activity and tasks:
            last_activity = max(t.date_created for t in tasks)
        if not last_activity:
            last_activity = u.date_created

        overview.append(StaffOverviewOut(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=role_name,
            department=dept,
            position=pos,
            salary=salary,
            hire_date=hire_date,
            sales_count=sales_count,
            total_sales_amount=round(total_sales_amount, 2),
            pending_tasks_count=pending_tasks,
            completed_tasks_count=completed_tasks,
            tasks=tasks,
            last_activity=last_activity
        ))
    return overview
