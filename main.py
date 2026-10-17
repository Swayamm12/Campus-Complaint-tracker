import os
import secrets
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field

app = FastAPI(title="Campus Complaint Tracker")
BASE = Path(__file__).parent

# Staff login (change these with environment variables)
STAFF_USERNAME = os.getenv("STAFF_USERNAME", "staff")
STAFF_PASSWORD = os.getenv("STAFF_PASSWORD", "staff123")
security = HTTPBasic(auto_error=False)


def require_staff(credentials: Optional[HTTPBasicCredentials] = Depends(security)):
    """Only staff can pass. Students have no login, so they get 401."""
    ok = credentials is not None and (
        secrets.compare_digest(credentials.username, STAFF_USERNAME)
        and secrets.compare_digest(credentials.password, STAFF_PASSWORD)
    )
    if not ok:
        raise HTTPException(status_code=401, detail="Staff login required")


class Category(str, Enum):
    hostel = "hostel"
    academics = "academics"
    infrastructure = "infrastructure"
    canteen = "canteen"
    other = "other"


class Status(str, Enum):
    open = "Open"
    in_progress = "In Progress"
    resolved = "Resolved"


# Allowed status changes: Open -> In Progress -> Resolved
ALLOWED_TRANSITIONS = {
    Status.open: [Status.in_progress],
    Status.in_progress: [Status.resolved],
    Status.resolved: [],
}


class ComplaintCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    category: Category
    description: str = Field(min_length=5, max_length=1000)


class StatusUpdate(BaseModel):
    status: Status


class Complaint(BaseModel):
    id: int
    title: str
    category: Category
    description: str
    status: Status
    created_at: datetime


# In-memory storage (resets when the server restarts)
complaints: dict[int, Complaint] = {}
next_id = 1


# ---------- Pages ----------
@app.get("/", include_in_schema=False)
def student_page():
    return FileResponse(BASE / "index.html")


@app.get("/staff", include_in_schema=False)
def staff_page():
    return FileResponse(BASE / "staff.html")  # the page itself only shows a login form


# ---------- API ----------
# Students: open to everyone
@app.post("/complaints", response_model=Complaint, status_code=201)
def submit_complaint(data: ComplaintCreate):
    global next_id
    complaint = Complaint(
        id=next_id,
        title=data.title,
        category=data.category,
        description=data.description,
        status=Status.open,
        created_at=datetime.now(),
    )
    complaints[next_id] = complaint
    next_id += 1
    return complaint


# Staff only
@app.get("/complaints", response_model=list[Complaint], dependencies=[Depends(require_staff)])
def list_complaints(status: Optional[Status] = None, category: Optional[Category] = None):
    result = list(complaints.values())
    if status:
        result = [c for c in result if c.status == status]
    if category:
        result = [c for c in result if c.category == category]
    return result


@app.get("/complaints/{complaint_id}", response_model=Complaint, dependencies=[Depends(require_staff)])
def get_complaint(complaint_id: int):
    if complaint_id not in complaints:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaints[complaint_id]


@app.patch("/complaints/{complaint_id}/status", response_model=Complaint,
           dependencies=[Depends(require_staff)])
def update_status(complaint_id: int, update: StatusUpdate):
    complaint = get_complaint(complaint_id)
    if update.status not in ALLOWED_TRANSITIONS[complaint.status]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition: {complaint.status.value} -> {update.status.value}",
        )
    complaint.status = update.status
    return complaint
