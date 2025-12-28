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


class PatientBase(BaseModel):
    id: str
    first_name: str
    last_name: str
    date_of_birth: str
    gender: Optional[str] = None
    phoneNumber: Optional[str] = Field(None, alias="phoneNumber") # Handles API variations
    email: Optional[str] = None
    insurance_provider: Optional[str] = None
    reliability_score: float = 0.0

class PatientCreate(BaseModel):
    firstName: str
    lastName: str
    email: str
    phoneNumber: str
    dateOfBirth: str # YYYY-MM-DD

class AppointmentBase(BaseModel):
    id: str
    clinic_id: str
    patient_id: str
    doctor_id: str
    appointment_date: str
    start_time: str
    end_time: str
    status: str
    notes: Optional[str] = None

class AppointmentCreate(BaseModel):
    clinic_id: str
    patient_id: str
    doctor_id: str
    appointment_date: str
    start_time: str
    end_time: str
    notes: Optional[str] = ""

class AppointmentType(BaseModel):
    id: str
    name: str
    default_duration: int
# tools/models.py (Add these to the bottom)

class RevenueBreakdown(BaseModel):
    totalRevenue: float
    averageRevenuePerAppointment: float
    breakdown: Optional[Dict[str, float]] = None

class DashboardSummary(BaseModel):
    activePatients: int
    newPatientsThisMonth: int
    upcomingAppointments: int
    totalRevenue: Optional[float] = None

class DoctorPerformance(BaseModel):
    doctor_id: str
    name: str
    revenue: float
    appointmentCount: int

class SpecialtyPerformance(BaseModel):
    specialty: str
    revenue: float
    appointments: int

class ReminderBase(BaseModel):
    id: str
    patient_id: str
    type: str
    message: str
    send_at: str
    status: str
    channel: str
    metadata: Optional[Dict[str, Any]] = None

class MedicationReminderCreate(BaseModel):
    userId: str
    medicationName: str
    dosage: str
    frequency: str
    timingContext: str
    scheduledTimes: List[str]
    endDate: str

class PreparationReminderCreate(BaseModel):
    userId: str
    appointmentId: str
    procedureType: str
    instructions: List[str]
    scheduledTime: str
class MedicationCreate(BaseModel):
    medicationName: str
    dosage: str
    frequency: str
    startDate: str
    endDate: Optional[str] = None
    instructions: Optional[str] = None

class MedicationUpdate(BaseModel):
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    endDate: Optional[str] = None
    instructions: Optional[str] = None

class MedicationRefill(BaseModel):
    refillDate: str
    quantity: int
    pharmacy: str


class VitalSigns(BaseModel):
    bloodPressure: Optional[str] = None
    heartRate: Optional[int] = None
    temperature: Optional[float] = None
    respiratoryRate: Optional[int] = None
    oxygenSaturation: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None

class SoapNoteCreate(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str
    vitalSigns: Optional[VitalSigns] = None
    createdBy: Optional[str] = None

class SoapNoteUpdate(BaseModel):
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None

class Intervention(BaseModel):
    type: str  # medication, lifestyle, referral
    description: str
    status: str = "pending"
    priority: str = "medium"

class TreatmentPlanCreate(BaseModel):
    patientId: str
    appointmentId: str
    diagnosis: str
    status: str = "active"
    interventions: List[Intervention]

class PreVisitResponseCreate(BaseModel):
    appointment_id: str
    responses: Dict[str, Any]
    notes: Optional[str] = None
    is_complete: bool = True

class Clinic(BaseModel):
    id: str
    name: str
    address: str
    city: str
    phone: str
    email: str