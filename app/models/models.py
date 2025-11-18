from typing import Optional, List
from datetime import datetime
from pydantic import EmailStr
from beanie import Document, Link
from pydantic import BaseModel,Field
from typing_extensions import Annotated
from dotenv import load_dotenv
load_dotenv()

class Patient(BaseModel):
    name: str
    mobile_no: str
    email: EmailStr
    password:Annotated[str,Field(min_length=6)]
    medical_history: str


class PatientLogin(BaseModel):
    email:str
    password:str

class Doctor(BaseModel):
    name: str    
    experience_years : int
    mobile_no: str
    specialization: str
    email: Optional[EmailStr] = None
    password:Annotated[str,Field(min_length=6)]

class DoctorLogin(BaseModel):
    email:str
    password:str

class Staff(BaseModel):
    name : Annotated[str,Field(min_length=3)]
    mobile_no : Annotated[str,Field(min_length=10,max_length=10)]
    email:Optional[EmailStr] = None
    password:Annotated[str,Field(min_length=6)]

class StaffLogin(BaseModel):
    email:str
    password:str


class Appointment(BaseModel):
    doctor_id :str
    reason:str



class Report(BaseModel):
    patient: Link[Patient]
    summary: Optional[str] = None
    summarized: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

