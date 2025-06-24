# models.py
from sqlalchemy import Column, Integer, String, Text, DateTime
# Change from relative to absolute import
from database import Base

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    duration = Column(Integer)
    transcript = Column(Text)
    audio_path = Column(String(255))
    created_at = Column(DateTime)