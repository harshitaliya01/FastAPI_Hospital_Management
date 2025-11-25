from fastapi import APIRouter,Depends,HTTPException
from models.models import Appointment
from bson import ObjectId
from utils.utility import get_current_user
from datetime import datetime
from utils.slot import book_slot
from db import db

router = APIRouter()

@router.post("/create/appointment/")
async def create_appointment(appointment:Appointment,current_user :dict=Depends(get_current_user)):
    try:
        patient = await db.patient.find_one({"email":current_user["email"]})
        if patient["role"] !="patient":
            raise HTTPException(status_code=400, detail="You must be logged in as a patient to book")
        
        if not patient:
            raise HTTPException(status_code=400, detail="Patient not found")     

        doctor = await db.doctor.find_one({"_id": ObjectId(appointment.doctor_id)})
        if not doctor:
            raise HTTPException(status_code=400, detail="Doctor not found")
        
        datetime.now()
        last_appointment = await db.appointment.find_one(
            {"doctor_id": ObjectId(appointment.doctor_id)},
            sort=[("date", -1), ("time", -1)]
        )
        patient_name = patient["name"]
        doctor_name = doctor["name"]
        appointment_date,appointment_time,qnumber = await book_slot(last_appointment,appointment.doctor_id,patient["_id"])

        doc = {
            "doctor_id": ObjectId(appointment.doctor_id),
            "date": appointment_date.isoformat(),
            "time": appointment_time.strftime("%H:%M:%S"),
            "patient_id": patient["_id"],
            "doctor_name": doctor_name,
            "patient_name": patient_name,
            "qnum":qnumber,
            "reason": appointment.reason,
            "created_at": datetime.utcnow(),
            "status": "pending"
        }
        
        
        await db.appointment.insert_one(doc)
        return {
            "msg": "booked",
            "patient_name": patient_name,
            "doctor_name": doctor_name,
            "date": appointment_date.isoformat(),
            "time": appointment_time.strftime("%H:%M:%S"),
            "qnumber": int(qnumber),
        }
    
    except Exception as e:
        return str(e)


@router.get("/my_appointments/")
async def list_appointments(current_user: dict = Depends(get_current_user)):
    patient = await db.patient.find_one({"email":current_user["email"]})       
    if patient:
        query = {"patient_id": patient["_id"]}

        appointments = await db.appointment.find(query).to_list(length=None)

        for a in appointments:
            a["_id"] = str(a["_id"])
            if "patient_id" in a: a["patient_id"] = str(a["patient_id"])
            if "doctor_id" in a: a["doctor_id"] = str(a["doctor_id"])

        return {"count": len(appointments), "appointments": appointments}

    doctor = await db.doctor.find_one({"email":current_user["email"]})       
    
    if doctor:
        query = {"doctor_id": doctor["_id"]}

        appointments = await db.appointment.find(query).to_list(length=None)

        for a in appointments:
            a["_id"] = str(a["_id"])
            if "patient_id" in a: a["patient_id"] = str(a["patient_id"])
            if "doctor_id" in a: a["doctor_id"] = str(a["doctor_id"])

        return {"count": len(appointments), "appointments": appointments}


    staff = await db.staff.find_one({"email":current_user["email"]}) 
    
    if staff:
        appointments = await db.appointment.find({}).sort([
            ("date", 1),
            ("time", 1)]).to_list(length=None)
        for a in appointments:
            a["_id"] = str(a["_id"])
            if "patient_id" in a: a["patient_id"] = str(a["patient_id"])
            if "doctor_id" in a: a["doctor_id"] = str(a["doctor_id"])

        return {"count": len(appointments), "appointments": appointments}
    



#    ===>>>>> CANCEL <<<<<======    
@router.put("/cancel/appointment/{appointment_id}/")
async def cancel_appointment(appointment_id: str, current_user: dict = Depends(get_current_user)):
    try:
        appointment = await db.appointment.find_one({"_id": ObjectId(appointment_id)})
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        patient = await db.patient.find_one({"email":current_user["email"]}) 
        doctor = await db.doctor.find_one({"email":current_user["email"]}) 
        staff = await db.staff.find_one({"email":current_user["email"]}) 
        
        if patient:
            if str(appointment["patient_id"]) != str(patient["_id"]):
                raise HTTPException(status_code=403, detail="You can cancel only your own appointments")
            
            elif appointment["status"] == "completed":
                raise HTTPException(status_code=400, detail="Appointment already completed by staff now you can not cancel")
            else:
                if appointment["status"] == "cancelled":
                    raise HTTPException(status_code=400, detail="Appointment already cancelled")
                
            await db.appointment.update_one(
                {"_id": ObjectId(appointment_id)},
                {"$set": {"status": "cancelled by patient"}}
            )
        
        if doctor:
            if str(appointment["doctor_id"]) != str(doctor["_id"]):
                raise HTTPException(status_code=403, detail="You can cancel only your own appointments")
            else:
                if appointment["status"] == "cancelled":
                    raise HTTPException(status_code=400, detail="Appointment already cancelled")
                
            await db.appointment.update_one(
                {"_id": ObjectId(appointment_id)},
                {"$set": {"status": "cancelled"}}
            )
                
        if staff:
            if appointment["status"] == "cancelled":
                    raise HTTPException(status_code=400, detail="Appointment already cancelled")

            await db.appointment.update_one(
                {"_id": ObjectId(appointment_id)},
                {"$set": {"status": "cancelled"}}
            )

        return {"msg": "Appointment cancelled successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


#    ===>>>>> COMPLETE <<<<<======    
@router.put("/complete/appointment/{appointment_id}/")
async def complete_appointment(appointment_id: str, current_user: dict = Depends(get_current_user)):
    try:
        appointment = await db.appointment.find_one({"_id": ObjectId(appointment_id)})
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        
        patient = await db.patient.find_one({"email":current_user["email"]}) 
        doctor = await db.doctor.find_one({"email":current_user["email"]}) 
        staff = await db.staff.find_one({"email":current_user["email"]}) 
        
        if patient:
            raise HTTPException(status_code=403, detail="You can not complete your appointments")
        
        if doctor:
            if str(appointment["doctor_id"]) != str(doctor["_id"]):
                raise HTTPException(status_code=403, detail="You can complete only your own appointments")
            
            elif appointment["status"] == "cancelled by patient":
                raise HTTPException(status_code=400, detail="Appointment already cancelled by patient now you can not complete")
            
            else:
                if appointment["status"] == "completed":
                    raise HTTPException(status_code=400, detail="Appointment already completed")

                
        if staff:
            if appointment["status"] == "completed":
                    raise HTTPException(status_code=400, detail="Appointment already completed")

        await db.appointment.update_one(
            {"_id": ObjectId(appointment_id)},
            {"$set": {"status": "completed"}}
        )

        return {"msg": "Appointment completed successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))