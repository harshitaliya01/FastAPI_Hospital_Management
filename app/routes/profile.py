from fastapi import Depends,APIRouter
from utils.utility import get_current_user
from db import db

router = APIRouter()

@router.get("/profile/")
async def my_profile(current_user: dict = Depends(get_current_user)):
    try:
        patient = await db.patient.find_one({"email":current_user["email"]})
        if patient:
            return {
            "name": patient["name"],
            "email": patient["email"],
            "medical_history":patient["medical_history"],
            "mobile_no" :patient["mobile_no"],
            "role": patient["role"],
            }
        
        doctor = await db.doctor.find_one({"email":current_user["email"]})
        if doctor:
            return {
            "name":doctor["name"],
            "email": doctor["email"],
            "mobile_no":doctor["mobile_no"],
            "experience_years" : doctor["experience_years"],
            "specialization":doctor["specialization"],
            "role": doctor["role"],
            }
        
        staff = await db.staff.find_one({"email":current_user["email"]})
        return {
                    "name":staff["name"],
                    "email": staff["email"],
                    "mobile_no":staff["mobile_no"],
        }
    except Exception as e:
        return str(e)