from models.models import Staff,StaffLogin
from fastapi import APIRouter,HTTPException,Depends
from utils.utility import hash_password,create_access_token,verify_password,get_current_user

import os
from db import db

router = APIRouter()

@router.post("/staff/register/{admin}")
async def register(user:Staff,admin:str):
    try:
        if admin==os.getenv("ADMIN_KEY"):
            existing = await db.staff.find_one({"email":user.email})
            if existing:
                raise HTTPException(status_code=400, detail="Email Already Registered")
            hashed_pw = hash_password(user.password)

            doc = {
                    "name":user.name,
                    "mobile_no":user.mobile_no,
                    "email": user.email,
                    "password": hashed_pw,
                }

            res = await db.staff.insert_one(doc)
            created = await db.staff.find_one({"_id":res.inserted_id})
            user_data = {
                    "id":str(created["_id"]),
                    "name":created["name"],
                    "mobile_no":created["mobile_no"],
                    "email":created["email"],
                }
            return {"msg": "registered","user": user_data}
        else:
            print("true")
    except Exception as e:
        return str(e)


@router.post("/staff/login/")
async def login(usertry:StaffLogin):
    try:
        user = await db.staff.find_one({"email":usertry.email})
        if not user or not verify_password(usertry.password, user["password"]):
            raise HTTPException(status_code=400, detail="Incorrect credentials-password")
        token = create_access_token({"email": usertry.email})
        return {"message":"Success Login","access_token": token, "token_type": "bearer"}
    except Exception as e:
        return str(e)
    

