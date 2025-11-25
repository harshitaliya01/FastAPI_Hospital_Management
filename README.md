🏥 Hospital Management Backend — FastAPI + MongoDB

A fully asynchronous Hospital Management Backend built with FastAPI and MongoDB.
Supports Patients, Doctors, and Staff with role-based access, JWT authentication, appointment workflows, queue numbers, CRUD operations, and proper validations.

🚀 Features
🔐 Authentication & Authorization

JWT Authentication

Role-based access: patient, doctor, staff

Secure password hashing (bcrypt)

🧑‍⚕️ Appointment Management

Book appointments with conflict-free slot checking

Auto queue number generation

Cancel, complete, or list appointments

Doctor availability logic

Prevent double-booking

👤 User Management

Register patient/doctor/staff

Login with JWT

Update profile

Get all doctors/patients

Proper type validation & ObjectId serializer

⚙️ Backend Highlights

Fully asynchronous FastAPI routes

Motor (async MongoDB driver)

Clean folder structure

Centralized error handling

CORS enabled