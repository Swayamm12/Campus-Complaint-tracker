from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Campus Complaint Tracker")


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


@app.get("/complaints", response_model=list[Complaint])
def list_complaints(status: Optional[Status] = None, category: Optional[Category] = None):
    result = list(complaints.values())
    if status:
        result = [c for c in result if c.status == status]
    if category:
        result = [c for c in result if c.category == category]
    return result


@app.get("/complaints/{complaint_id}", response_model=Complaint)
def get_complaint(complaint_id: int):
    if complaint_id not in complaints:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaints[complaint_id]


@app.patch("/complaints/{complaint_id}/status", response_model=Complaint)
def update_status(complaint_id: int, update: StatusUpdate):
    complaint = get_complaint(complaint_id)
    if update.status not in ALLOWED_TRANSITIONS[complaint.status]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition: {complaint.status.value} -> {update.status.value}",
        )
    complaint.status = update.status
    return complaint
