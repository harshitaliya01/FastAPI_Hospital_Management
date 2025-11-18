from datetime import datetime, date, time, timedelta
from fastapi import HTTPException
from bson import ObjectId
from db import db

# --- Config / constants (same as original) ---
MORNING_START = time(9, 0)
MORNING_END = time(12, 0)
AFTERNOON_START = time(15, 0)
AFTERNOON_END = time(18, 0)
APPOINTMENT_DURATION = timedelta(minutes=20)


# --- Utilities ---
def next_working_day(current_date: date) -> date:
    """Return the next non-Sunday date (same logic as original)."""
    next_day = current_date + timedelta(days=1)
    while next_day.weekday() == 6:  # Sunday (weekday() == 6)
        next_day += timedelta(days=1)
    return next_day


def _round_up_to_next_slot(t: time) -> time:

    # compute minute bucket
    total_minutes = t.hour * 60 + t.minute
    # Add 1 second margin so exact boundaries behave same as original rounding-up logic
    # (original used integer division then +1)
    # We'll compute next boundary:
    remainder = total_minutes % 20
    if remainder == 0:
        next_total = total_minutes + 20
    else:
        next_total = total_minutes + (20 - remainder)
    next_hour = next_total // 60
    next_min = next_total % 60
    # normalize hour to 0-23 (if it becomes 24+ we wrap to hour value >23 but
    # callers will treat times outside sessions)
    next_hour = next_hour % 24
    return time(next_hour, next_min)


# --- Slot-finding (merged and simplified) ---
async def find_next_free_slot(doctor_id, start_date: date, start_time: time):

    candidate_date = start_date
    candidate_time = start_time
    increments = 0

    # safety loop to avoid infinite loops
    for _ in range(500):
        # Snap candidate_time into the next valid session if it's outside sessions
        if MORNING_START <= candidate_time < MORNING_END:
            session_end = MORNING_END
        elif AFTERNOON_START <= candidate_time < AFTERNOON_END:
            session_end = AFTERNOON_END
        else:
            # Not in any session — move forward to nearest session start (preserve original snapping logic)
            if candidate_time < MORNING_START:
                candidate_time = MORNING_START
            elif candidate_time < AFTERNOON_START:
                candidate_time = AFTERNOON_START
            else:
                # after AFTERNOON_END -> next working day morning
                candidate_date = next_working_day(candidate_date)
                candidate_time = MORNING_START
            # continue to re-evaluate with snapped time
            continue

        # If Saturday afternoon or later, move to next working day's morning
        if candidate_date.weekday() == 5 and candidate_time >= AFTERNOON_START:
            candidate_date = next_working_day(candidate_date)
            candidate_time = MORNING_START
            continue

        # Check DB for occupancy
        slot = await db.appointments.find_one({
            "doctor_id": ObjectId(doctor_id),
            "date": candidate_date.isoformat(),
            "time": candidate_time.strftime("%H:%M:%S")
        })
        if not slot:
            # free slot found
            return candidate_date, candidate_time, increments

        # otherwise move to next 20-minute slot
        dt = datetime.combine(candidate_date, candidate_time) + APPOINTMENT_DURATION
        candidate_date, candidate_time = dt.date(), dt.time()
        increments += 1

    # if we exit loop, we couldn't find a slot
    raise HTTPException(status_code=500, detail="Unable to find free slot (too many attempts).")


def get_next_slot_time(current_time: time) -> time:

    # before morning -> start of morning
    if current_time < MORNING_START:
        return MORNING_START

    # in morning session
    if MORNING_START <= current_time < MORNING_END:
        candidate = _round_up_to_next_slot(current_time)
        return candidate if candidate < MORNING_END else AFTERNOON_START

    # in afternoon session
    if AFTERNOON_START <= current_time < AFTERNOON_END:
        candidate = _round_up_to_next_slot(current_time)
        return candidate if candidate < AFTERNOON_END else MORNING_START

    # fallback (e.g. between MORNING_END and AFTERNOON_START or after AFTERNOON_END)
    return MORNING_START


async def get_first_available_slot(doctor_id, current_time: time):

    now_date = datetime.now().date()

    if now_date.weekday() == 6:
        now_date = next_working_day(now_date)

    now_time = get_next_slot_time(current_time)

    if now_time == MORNING_START and current_time >= AFTERNOON_END:
        now_date = next_working_day(now_date)

    appointment_date, appointment_time, increments = await find_next_free_slot(
        doctor_id, now_date, now_time
    )

    # original returned 1 + increments
    return appointment_date, appointment_time, 1 + increments


def get_session(t: time):
    """Return 'morning' or 'afternoon' depending on time, otherwise None."""
    if MORNING_START <= t < MORNING_END:
        return "morning"
    if AFTERNOON_START <= t < AFTERNOON_END:
        return "afternoon"
    return None


async def book_slot(last_appointment, doctor_id, patient_id):
    now = datetime.now()
    today = now.date()

    #     # Prevent same-day double booking for patient

    last_date = None
    last_time = None
    last_qnum = 0
    last_session = None

    if last_appointment:
        last_date = datetime.fromisoformat(last_appointment["date"]).date()
        last_time = datetime.strptime(last_appointment["time"], "%H:%M:%S").time()
        last_qnum = int(last_appointment.get("qnumber", 0))
        last_session = get_session(last_time)

    # CASE A: No previous appointment
    if not last_appointment:
        appointment_date, appointment_time, qnumber = await get_first_available_slot(doctor_id, now.time())

    # CASE B: Doctor has previous appointments
    else:
        proposed_dt = datetime.combine(last_date, last_time) + APPOINTMENT_DURATION
        candidate_date, candidate_time = proposed_dt.date(), proposed_dt.time()

        if last_date >= today:
            appointment_date, appointment_time, increments = await find_next_free_slot(
                doctor_id, candidate_date, candidate_time
            )

            # Determine session of the newly found appointment
            new_session = get_session(appointment_time)

            # If same day AND same session as last appointment, continue numbering from last_qnum
            if appointment_date == last_date and last_session and new_session and last_session == new_session:
                qnumber = last_qnum + 1 + increments
            else:
                # Different session or different day -> session numbering resets
                qnumber = 1 + increments
        else:
            appointment_date, appointment_time, qnumber = await get_first_available_slot(doctor_id, now.time())

    # Ensure final appointment is strictly in the future
    final_dt = datetime.combine(appointment_date, appointment_time)
    if final_dt <= now:
        appointment_date = next_working_day(now.date())
        appointment_time = MORNING_START
        appointment_date, appointment_time, inc = await find_next_free_slot(
            doctor_id, appointment_date, appointment_time
        )
        qnumber = 1 + inc

    # Prevent same-day double booking for patient
    if await db.appointments.find_one({
        "patient_id": patient_id,
        "date": appointment_date.isoformat()
    }):
        raise HTTPException(status_code=400, detail="You already have an appointment on this day.")

    # Defensive re-check: if intended slot is taken, advance to next free slot and update qnumber accordingly
    if await db.appointments.find_one({
        "doctor_id": ObjectId(doctor_id),
        "date": appointment_date.isoformat(),
        "time": appointment_time.strftime("%H:%M:%S")
    }):
        # search starting at next slot
        next_start_time = (datetime.combine(appointment_date, appointment_time) + APPOINTMENT_DURATION).time()
        appointment_date, appointment_time, inc = await find_next_free_slot(
            doctor_id,
            appointment_date,
            next_start_time
        )

        # Decide base for qnumber when we advance:
        # If we have a last appointment on the same date and the new slot is in the same session -> continue numbering,
        # otherwise start session numbering from 1.
        new_session = get_session(appointment_time)
        if last_appointment and appointment_date == last_date and last_session and new_session and last_session == new_session:
            base = last_qnum
        else:
            base = 0

        qnumber = base + 1 + inc


    if await db.appointment.find_one({
        "patient_id": patient_id,
        "date": appointment_date.isoformat()
    }):
        raise HTTPException(status_code=400, detail="You already have an appointment on this day.")

    return appointment_date, appointment_time, qnumber