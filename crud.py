# crud.py
from sqlalchemy.orm import Session
from datetime import datetime
import models
import schemas
import os

def get_meeting(db: Session, meeting_id: int):
    return db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()

def list_meetings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Meeting).offset(skip).limit(limit).all()

def create_meeting(db: Session, title: str, duration: int, transcript: str, file_path: str):
    db_meeting = models.Meeting(
        title=title,
        duration=duration,
        transcript=transcript,
        audio_path=file_path,
        created_at=datetime.now()
    )
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting

def delete_meeting(db: Session, meeting_id: int):
    db_meeting = get_meeting(db, meeting_id)
    if not db_meeting:
        return None
    
    if db_meeting.audio_path and os.path.exists(db_meeting.audio_path):
        os.remove(db_meeting.audio_path)
    
    db.delete(db_meeting)
    db.commit()
    return db_meeting