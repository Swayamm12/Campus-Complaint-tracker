# Campus Complaint Tracker

A small FastAPI app built for the ASDD (Agile Software Development) mini project.
Students submit complaints; staff view, filter, and update their status.

## Features
- Submit a complaint (title, category, description) - starts as `Open`
- List complaints, filter by `status` and/or `category`
- View one complaint by id
- Update status: `Open -> In Progress -> Resolved` (anything else returns 400)

## Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| POST | /complaints | Submit a complaint |
| GET | /complaints?status=&category= | List / filter |
| GET | /complaints/{id} | View one |
| PATCH | /complaints/{id}/status | Update status |

Categories: hostel, academics, infrastructure, canteen, other

## Run locally
```
pip install -r requirements.txt
uvicorn main:app --reload
```
Open http://localhost:8000/docs

## Run tests
```
pytest -v
```

## Run with Docker
```
docker build -t complaint-tracker .
docker run -p 8000:8000 complaint-tracker
```

## Notes
Data is stored in memory, so it resets when the server restarts.
