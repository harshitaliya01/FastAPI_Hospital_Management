from fastapi import APIRouter,HTTPException,Depends
from models.models import Doctor,DoctorLogin
from bson import ObjectId
from utils.utility import hash_password,create_access_token,verify_password,get_current_user
from db import db

router = APIRouter()

@router.post("/doctor/register/")
async def register(user:Doctor,current_user: dict = Depends(get_current_user)):
    try:
        staff = await db.staff.find_one({"email":current_user["email"]})
        if staff:
            existing = await db.doctor.find_one({"email":user.email})
            if existing:
                raise HTTPException(status_code=400, detail="Email Already Registered")
            hashed_pw = hash_password(user.password)

            doc = {
                    "name":user.name,
                    "experience_years":user.experience_years,
                    "specialization":user.specialization,
                    "mobile_no":user.mobile_no,
                    "email": user.email,
                    "password": hashed_pw,
                    "role":"doctor"
                }

            res = await db.doctor.insert_one(doc)
            created = await db.doctor.find_one({"_id":res.inserted_id})
            user_data = {
                    "id":str(created["_id"]),
                    "name":created["name"],
                    "experience_years":created["experience_years"],
                    "specialization":created["specialization"],
                    "mobile_no":created["mobile_no"],
                    "email":created["email"],
                }
            return {"msg": "registered","user": user_data}
        else:
            raise HTTPException(status_code=400, detail="You Are Not Able To Create Doctor Please Login In Staff")
    except Exception as e:
        return str(e)
    

@router.post("/doctor/login/")
async def login(usertry:DoctorLogin):
    try:
        user = await db.doctor.find_one({"email":usertry.email})
        if not user or not verify_password(usertry.password, user["password"]):
            raise HTTPException(status_code=400, detail="Incorrect credentials-password")
        token = create_access_token({"email": usertry.email})
        return {"message":"Success Login","access_token": token, "token_type": "bearer"}
    except Exception as e:
        return str(e)
    

@router.get("/doctors/")
async def get_all_doctors():
    try:
        doctors_cursor = db.doctor.find({}, {"password": 0})
        doctors = []
        async for doc in doctors_cursor:
            doctors.append({
                "id": str(doc["_id"]),
                "name": doc.get("name"),
                "specialization": doc.get("specialization"),
                "experience_years": doc.get("experience_years"),
                "mobile_no": doc.get("mobile_no"),
                "email": doc.get("email")
            })
        if not doctors:
            return {"msg": "No doctors found."}

        return {"total": len(doctors), "doctors": doctors}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    



@router.delete("/doctor/{doctor_id}/")
async def register(doctor_id:str,current_user: dict = Depends(get_current_user)):
    try:
        staff = await db.staff.find_one({"email":current_user["email"]})
        if staff:
            doctor = await db.doctor.find_one({"_id": ObjectId(doctor_id)})
            if not doctor:
                raise HTTPException(status_code=400, detail="Doctor Not Found.")
            
            await db.doctor.delete_one({"_id": ObjectId(doctor_id)})
           
            return {"msg": "Doctor deleted successfully", "doctor_id": doctor_id}
        
        else:
            raise HTTPException(status_code=400, detail="Not Delete A Doctor Because You Are Not Staff.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))