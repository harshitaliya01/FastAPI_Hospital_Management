from fastapi import FastAPI
from routes import staff,doctor,patient,appointment,profile
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Hospital Management System")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
  CORSMiddleware,
#   allow_origins=["http://localhost:5500","http://127.0.0.1:5500","http://localhost:3000"], # or ["*"] for quick test
  allow_origins=["*"], # or ["*"] for quick test
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


app.include_router(patient.router, tags=["Patients"])
app.include_router(doctor.router, tags=["Doctors"])
app.include_router(staff.router, tags=["Staff"])
app.include_router(profile.router, tags=["Profile"])
app.include_router(appointment.router, tags=["Appointment"])

@app.get("/",)
def home():
    return {"message": "Hospital API Running"}