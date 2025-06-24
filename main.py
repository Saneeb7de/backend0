# main.py
import os
import uuid
import shutil
from fastapi import FastAPI, Form, UploadFile, File, HTTPException, Depends, Response
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

# These imports are now cleaner and more organized
import models
import schemas
import crud
import speech_service
from database import SessionLocal, engine

# Create database tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Meeting Recorder API",
    description="API for recording, transcribing, and managing meetings."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/meetings/", response_model=schemas.MeetingResponse, status_code=201)
async def create_meeting_endpoint(
    title: str = Form(...),
    duration: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not title.strip() or duration <= 0:
        raise HTTPException(status_code=400, detail="Invalid title or duration.")

    upload_dir = "audio_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_ext = os.path.splitext(file.filename)[1].lower()
    file_path = os.path.join(upload_dir, f"{uuid.uuid4()}{file_ext}")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    try:
        transcript = speech_service.transcribe_audio(file_path)
    except speech_service.SpeechServiceError as e:
        os.remove(file_path)  # Clean up the failed upload
        raise HTTPException(status_code=502, detail=f"Speech service error: {e}")
    
    meeting = crud.create_meeting(db, title=title, duration=duration, transcript=transcript, file_path=file_path)
    return meeting

@app.get("/meetings/", response_model=list[schemas.MeetingResponse])
def list_meetings_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.list_meetings(db, skip=skip, limit=limit)

@app.get("/meetings/{meeting_id}", response_model=schemas.MeetingResponse)
def get_meeting_endpoint(meeting_id: int, db: Session = Depends(get_db)):
    meeting = crud.get_meeting(db, meeting_id=meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting

@app.delete("/meetings/{meeting_id}", status_code=204)
def delete_meeting_endpoint(meeting_id: int, db: Session = Depends(get_db)):
    """Deletes a meeting and its associated audio file."""
    deleted_meeting = crud.delete_meeting(db, meeting_id=meeting_id)
    if not deleted_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    # A 204 response must not have a body
    return Response(status_code=204)

@app.get("/health", tags=["Monitoring"])
def health_check():
    """Returns the operational status of the API."""
    return {"status": "healthy"}