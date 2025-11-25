from fastapi import APIRouter,HTTPException
from models.models import Patient,PatientLogin
from utils.utility import hash_password,create_access_token,verify_password

from db import db

router = APIRouter()

@router.post("/patient/register/")
async def register(user:Patient):
    try:
        existing = await db.patient.find_one({"email":user.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email Already Registered")
        hashed_pw = hash_password(user.password)

        doc = {
                "name":user.name,
                "mobile_no":user.mobile_no,
                "email": user.email,
                "password": hashed_pw,
                "medical_history": user.medical_history,
                "role":"patient"
            }
       
        res = await db.patient.insert_one(doc)
        created = await db.patient.find_one({"_id":res.inserted_id})
        user_data = {
                "id":str(created["_id"]),
                "name":created["name"],
                "mobile_no":created["mobile_no"],
                "email":created["email"],
                "medical_history":created["medical_history"]
            }
        token = create_access_token({"email": user.email})
        return {"msg": "registered","user": user_data,"access_token": token, "token_type": "bearer"}
    except Exception as e:
        return str(e)
    

@router.post("/patient/login/")
async def login(usertry:PatientLogin):
    try:
        user = await db.patient.find_one({"email":usertry.email})
        if not user or not verify_password(usertry.password, user["password"]):
            raise HTTPException(status_code=400, detail="Incorrect credentials-password")
        token = create_access_token({"email": usertry.email})
        return {"message":"Success Login","access_token": token, "token_type": "bearer"}
    except Exception as e:
        return str(e)