from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class DoctorBase(BaseModel):
    id: str
    first_name: str
    last_name: str
    title: str
    languages_spoken: List[str]
    specialties: Optional[List[Dict[str, Any]]] = None

class Availability(BaseModel):
    id: str
    doctor_id: str
    day_of_week: Any # Can be string or int per docs
    start_time: str
    end_time: str
    is_available: bool

class PatientSummary(BaseModel):
    id: str
    firstName: str
    lastName: str
    lastAppointment: Optional[str]
    nextAppointment: Optional[str]