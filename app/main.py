from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Any, List, Dict, Optional
from pydantic import BaseModel, EmailStr, Field, validator
import uuid
from datetime import date, datetime
import logging
from app.database import models, database
from app.services.ai_service import MedicalAIService, DoctorRecommendation
from app.services.email_service import EmailService
from app.services.calendly_service import CalendlyService, verify_webhook_signature
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()
ai_service = MedicalAIService()
email_service = EmailService()
calendly_service = CalendlyService()
class PatientCreate(BaseModel):
    first_name: str
    middle_initial: str = ""
    last_name: str
    date_of_birth: str  
    gender: str
    
    # Contact Information
    email: str
    home_phone: str = ""
    cell_phone: str = ""
    
    # Address Information
    street_address: str
    city: str
    state: str
    zip_code: str
    
    # Emergency Contact
    emergency_contact_name: str
    emergency_contact_relationship: str
    emergency_contact_phone: str
    
    # Insurance Information
    primary_insurance_company: str
    primary_member_id: str
    primary_group_number: str = ""
    secondary_insurance_company: str = ""
    secondary_member_id: str = ""
    secondary_group_number: str = ""
    
    # Chief Complaint & Symptoms
    primary_reason_for_visit: str
    symptom_duration: str
    current_symptoms: list = []
    
    # Allergy History
    has_known_allergies: str
    known_allergies_list: str = ""
    had_allergy_testing: str
    allergy_testing_date: str = ""
    had_severe_allergic_reaction: str
    
    # Current Medications
    current_medications: str = ""
    current_allergy_medications: list = []
    
    # Medical History
    medical_conditions: list = []
    family_allergy_history: str = ""
    
    # Pre-visit Instructions Acknowledgment
    understands_medication_instructions: str
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()
    
    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        if isinstance(v, str):
            try:
                # Try to parse the date string
                from datetime import datetime
                parsed_date = datetime.strptime(v, '%Y-%m-%d').date()
                return parsed_date
            except ValueError:
                raise ValueError('Invalid date format. Expected YYYY-MM-DD')
        return v
    

class PatientVerification(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: EmailStr

class PatientResponse(BaseModel):
    patient_id: str
    first_name: str
    middle_initial: Optional[str]
    last_name: str
    email: str
    date_of_birth: date
    gender: str
    
    class Config:
        from_attributes = True

class DoctorResponse(BaseModel):
    doctor_name: str
    specialization: str
    calendly_new_patient_url: str
    calendly_existing_patient_url: str

class ChatRequest(BaseModel):
    session_id: str
    query: str

class AppointmentDetails(BaseModel):
    appointment_id: int
    patient_name: str
    patient_email: str
    doctor_name: str
    appointment_time: Optional[datetime]
    end_time: Optional[datetime]
    status: str
    created_at: datetime

class DoctorStats(BaseModel):
    doctor_name: str
    specialization: str
    appointment_count: int
    scheduled_count: int
    cancelled_count: int

# --- API Endpoints ---
@app.post("/api/patients")
def create_or_get_patient(patient_data: Dict[str, Any], db: Session = Depends(database.get_db)):
    try:
        logger.info(f"Received patient data: {patient_data}")
        
        # Clean and prepare the data
        cleaned_data = {}
        
        # Handle all string fields
        string_fields = [
            'first_name', 'middle_initial', 'last_name', 'gender', 'email',
            'home_phone', 'cell_phone', 'street_address', 'city', 'state', 'zip_code',
            'emergency_contact_name', 'emergency_contact_relationship', 'emergency_contact_phone',
            'primary_insurance_company', 'primary_member_id', 'primary_group_number',
            'secondary_insurance_company', 'secondary_member_id', 'secondary_group_number',
            'primary_reason_for_visit', 'symptom_duration', 'has_known_allergies',
            'known_allergies_list', 'had_allergy_testing', 'allergy_testing_date',
            'had_severe_allergic_reaction', 'current_medications', 'family_allergy_history',
            'understands_medication_instructions'
        ]
        
        for field in string_fields:
            cleaned_data[field] = str(patient_data.get(field, "")).strip()
        
        # Handle list fields
        list_fields = ['current_symptoms', 'current_allergy_medications', 'medical_conditions']
        for field in list_fields:
            value = patient_data.get(field, [])
            if isinstance(value, list):
                cleaned_data[field] = value
            else:
                cleaned_data[field] = []
        
        # Handle date field
        date_str = patient_data.get('date_of_birth', '')
        try:
            if isinstance(date_str, str):
                cleaned_data['date_of_birth'] = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                cleaned_data['date_of_birth'] = date_str
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid date format for date_of_birth")
        
        # Validate required fields
        required_fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender', 'email',
            'cell_phone', 'street_address', 'city', 'state', 'zip_code',
            'emergency_contact_name', 'emergency_contact_relationship', 'emergency_contact_phone',
            'primary_insurance_company', 'primary_member_id', 'primary_reason_for_visit',
            'symptom_duration', 'has_known_allergies', 'had_allergy_testing',
            'had_severe_allergic_reaction', 'understands_medication_instructions'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not cleaned_data.get(field) or cleaned_data[field] == "":
                missing_fields.append(field)
        
        if missing_fields:
            raise HTTPException(status_code=422, detail=f"Missing required fields: {missing_fields}")
        
        # Check if patient already exists by email
        db_patient = db.query(models.Patient).filter(models.Patient.email == cleaned_data['email']).first()
        if db_patient:
            for field, value in cleaned_data.items():
                if hasattr(db_patient, field):
                    setattr(db_patient, field, value)
            db_patient.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_patient)
            logger.info(f"Updated existing patient: {db_patient.email}")
            return db_patient
        
        # Create new patient
        cleaned_data['patient_id'] = str(uuid.uuid4())
        new_patient = models.Patient(**cleaned_data)
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)
        logger.info(f"Created new patient: {new_patient.email}")
        return new_patient
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating patient: {str(e)}")
        logger.error(f"Patient data was: {patient_data}")
        raise HTTPException(status_code=500, detail=f"Error creating patient: {str(e)}")


@app.get("/api/doctors", response_model=List[DoctorResponse])
def get_doctors(db: Session = Depends(database.get_db)):
    doctors = db.query(models.Doctor).filter(models.Doctor.is_active == True).all()
    return doctors

@app.post("/api/recommend-doctor", response_model=DoctorRecommendation)
def recommend_doctor_endpoint(request: Dict, db: Session = Depends(database.get_db)):
    symptoms = request.get("symptoms")
    if not symptoms:
        raise HTTPException(400, "Symptoms are required.")
    
    doctors = db.query(models.Doctor).filter(models.Doctor.is_active == True).all()
    doctor_list = [{"doctor_name": d.doctor_name, "specialization": d.specialization} for d in doctors]
    return ai_service.recommend_doctor(symptoms, doctor_list)

@app.post("/api/chat")
def chat_with_assistant(request: ChatRequest, db: Session = Depends(database.get_db)):
    if not request.query or not request.session_id:
        raise HTTPException(status_code=400, detail="Query and session_id cannot be empty.")
    
    doctors = db.query(models.Doctor).filter(models.Doctor.is_active == True).all()
    doctor_list = [{"doctor_name": d.doctor_name, "specialization": d.specialization} for d in doctors]
    
    response = ai_service.get_chat_response(request.session_id, request.query, doctor_list)
    return {"response": response}



@app.post("/api/verify-patient", response_model=PatientResponse)
def verify_existing_patient(verification: PatientVerification, db: Session = Depends(database.get_db)):
    """Verify if a patient exists in the database"""
    patient = db.query(models.Patient).filter(
        models.Patient.first_name.ilike(f"%{verification.first_name}%"),
        models.Patient.last_name.ilike(f"%{verification.last_name}%"),
        models.Patient.email.ilike(f"%{verification.email}%")
    ).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found in our system")
    
    return PatientResponse(
        patient_id=patient.patient_id,
        first_name=patient.first_name,
        middle_initial=patient.middle_initial,
        last_name=patient.last_name,
        email=patient.email,
        date_of_birth=patient.date_of_birth,
        gender=patient.gender
    )

@app.get("/api/admin/appointments", response_model=List[AppointmentDetails])
def get_all_appointments(db: Session = Depends(database.get_db)):
    """Get all appointments with patient and doctor details"""
    appointments = db.query(
        models.Appointment.appointment_id,
        models.Appointment.appointment_time,
        models.Appointment.end_time,
        models.Appointment.status,
        models.Appointment.created_at,
        models.Patient.first_name.label("patient_first_name"),
        models.Patient.last_name.label("patient_last_name"),
        models.Patient.email.label("patient_email"),
        models.Doctor.doctor_name
    ).join(
        models.Patient, models.Appointment.patient_id == models.Patient.patient_id
    ).join(
        models.Doctor, models.Appointment.doctor_id == models.Doctor.doctor_id
    ).order_by(
        models.Appointment.appointment_time.desc()
    ).all()
    
    result = []
    for apt in appointments:
        patient_name = f"{apt.patient_first_name} {apt.patient_last_name}".strip()
        result.append(AppointmentDetails(
            appointment_id=apt.appointment_id,
            patient_name=patient_name,
            patient_email=apt.patient_email,
            doctor_name=apt.doctor_name,
            appointment_time=apt.appointment_time,
            end_time=apt.end_time,
            status=apt.status,
            created_at=apt.created_at
        ))
    
    return result

@app.get("/api/admin/doctor-stats", response_model=List[DoctorStats])
def get_doctor_statistics(db: Session = Depends(database.get_db)):
    """Get appointment statistics for each doctor"""
    from sqlalchemy import func, case
    
    stats = db.query(
        models.Doctor.doctor_name,
        models.Doctor.specialization,
        func.count(models.Appointment.appointment_id).label("total_appointments"),
        func.sum(case(
            (models.Appointment.status == 'scheduled', 1),
            else_=0
        )).label("scheduled_count"),
        func.sum(case(
            (models.Appointment.status == 'canceled', 1),
            else_=0
        )).label("cancelled_count")
    ).outerjoin(
        models.Appointment, models.Doctor.doctor_id == models.Appointment.doctor_id
    ).group_by(
        models.Doctor.doctor_id,
        models.Doctor.doctor_name,
        models.Doctor.specialization
    ).all()
    
    result = []
    for stat in stats:
        result.append(DoctorStats(
            doctor_name=stat.doctor_name,
            specialization=stat.specialization,
            appointment_count=int(stat.total_appointments or 0),
            scheduled_count=int(stat.scheduled_count or 0),
            cancelled_count=int(stat.cancelled_count or 0)
        ))
    
    return result

@app.get("/api/admin/patients")
def get_all_patients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    """Get all patients with pagination"""
    patients = db.query(models.Patient).offset(skip).limit(limit).all()
    return patients

@app.get("/api/admin/patient/{patient_id}/appointments")
def get_patient_appointments(patient_id: str, db: Session = Depends(database.get_db)):
    """Get all appointments for a specific patient"""
    patient = db.query(models.Patient).filter(models.Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    appointments = db.query(
        models.Appointment.appointment_id,
        models.Appointment.appointment_time,
        models.Appointment.end_time,
        models.Appointment.status,
        models.Appointment.created_at,
        models.Doctor.doctor_name
    ).join(
        models.Doctor, models.Appointment.doctor_id == models.Doctor.doctor_id
    ).filter(
        models.Appointment.patient_id == patient_id
    ).order_by(
        models.Appointment.appointment_time.desc()
    ).all()
    
    return {
        "patient": {
            "patient_id": patient.patient_id,
            "name": f"{patient.first_name} {patient.last_name}",
            "email": patient.email
        },
        "appointments": appointments
    }
@app.post("/api/webhooks/calendly")
async def handle_calendly_webhook(request: Request, db: Session = Depends(database.get_db)):
    """Handle Calendly webhook events for appointment booking/cancellation"""
    
    logger.info("Received Calendly webhook")
    signature = request.headers.get("calendly-webhook-signature")
    body = await request.body()
    if not verify_webhook_signature(signature_header=signature, body=body):
        logger.error("Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    try:
        payload = await request.json()
        logger.info(f"Processing Calendly webhook: {payload}")
    except Exception as e:
        logger.error(f"Error parsing webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    event_type = payload.get("event")
    
    if event_type == "invitee.created":
        return await handle_invitee_created(payload, db)
    elif event_type == "invitee.canceled":
        return await handle_invitee_canceled(payload, db)
    else:
        logger.info(f"Unhandled event type: {event_type}")
        return {"status": "Event type not handled"}

async def handle_invitee_created(payload: dict, db: Session):
    """Handle when a new appointment is booked"""
    try:
        data = payload.get("payload", {})
        scheduled_event = data.get("scheduled_event", {})
        
        logger.info(f"Scheduled event: {scheduled_event}")
        patient_email = data.get("email")
        patient_name = data.get("name", "")
        event_type_uri = scheduled_event.get("event_type")
        event_uri = scheduled_event.get("uri")
        invitee_uri = data.get("uri")
        start_time_str = scheduled_event.get("start_time")
        end_time_str = scheduled_event.get("end_time")
        cancel_url = data.get("cancel_url", "")
        reschedule_url = data.get("reschedule_url", "")
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00')) if start_time_str else None
        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00')) if end_time_str else None
        
        logger.info(f"Appointment details - Email: {patient_email}, Event Type: {event_type_uri}")
        
        # Find the doctor based on event type URI
        doctor = None
        all_doctors = db.query(models.Doctor).filter(models.Doctor.is_active == True).all()
        
        # Get event type details from Calendly
        try:
            event_details = calendly_service.get_event_type_from_uri(event_type_uri)
            if event_details:
                scheduling_url = event_details.get("scheduling_url", "")
                
                # Find doctor by matching Calendly URLs
                for doc in all_doctors:
                    if (doc.calendly_new_patient_url == scheduling_url or 
                        doc.calendly_existing_patient_url == scheduling_url):
                        doctor = doc
                        break
        except Exception as e:
            logger.error(f"Error fetching event details: {e}")
        
        patient = db.query(models.Patient).filter(models.Patient.email == patient_email).first()
        
        if not patient:
            name_parts = patient_name.strip().split()
            first_name = name_parts[0] if name_parts else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            
            patient = models.Patient(
                patient_id=str(uuid.uuid4()),
                first_name=first_name,
                last_name=last_name,
                email=patient_email,
                date_of_birth=date(2000, 1, 1), 
                gender="Not specified",
                cell_phone="",
                street_address="To be updated",
                city="To be updated", 
                state="NA",
                zip_code="00000",
                emergency_contact_name="To be updated",
                emergency_contact_relationship="To be updated",
                emergency_contact_phone="To be updated",
                primary_insurance_company="To be updated",
                primary_member_id="To be updated",
                primary_reason_for_visit="Scheduled via Calendly",
                symptom_duration="Not specified",
                current_symptoms=[],
                has_known_allergies="Not specified",
                had_allergy_testing="Not specified",
                had_severe_allergic_reaction="Not specified",
                current_allergy_medications=[],
                medical_conditions=[],
                understands_medication_instructions="Not specified"
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)
            logger.info(f"Created minimal patient record: {patient_email}")
        
        if doctor and patient:
            new_appointment = models.Appointment(
                patient_id=patient.patient_id,
                doctor_id=doctor.doctor_id,
                calendly_event_uri=event_uri,
                calendly_invitee_uri=invitee_uri,
                appointment_time=start_time,
                end_time=end_time,
                reschedule_url=reschedule_url,
                cancel_url=cancel_url,
                status="scheduled"
            )
            db.add(new_appointment)
            db.commit()
            db.refresh(new_appointment)
            
            logger.info(f"Created appointment: {new_appointment.appointment_id}")
            try:
                appointment_date = start_time.strftime('%A, %B %d, %Y') if start_time else 'TBD'
                appointment_time_formatted = start_time.strftime('%I:%M %p') if start_time else 'TBD'
                end_time_formatted = end_time.strftime('%I:%M %p') if end_time else 'TBD'
                duration_minutes = 60 
                if start_time and end_time:
                    duration_minutes = int((end_time - start_time).total_seconds() / 60)
                patient_data = {
                    'first_name': patient.first_name,
                    'middle_initial': patient.middle_initial,
                    'last_name': patient.last_name,
                    'email': patient.email,
                    'date_of_birth': patient.date_of_birth.strftime('%B %d, %Y') if patient.date_of_birth else 'Not provided',
                    'cell_phone': patient.cell_phone,
                    'home_phone': patient.home_phone,
                    'street_address': patient.street_address,
                    'city': patient.city,
                    'state': patient.state,
                    'zip_code': patient.zip_code,
                    'primary_insurance_company': patient.primary_insurance_company,
                    'primary_member_id': patient.primary_member_id,
                    'primary_reason_for_visit': patient.primary_reason_for_visit,
                    'symptom_duration': patient.symptom_duration,
                    'current_symptoms': patient.current_symptoms or [],
                    'known_allergies_list': patient.known_allergies_list,
                    'had_severe_allergic_reaction': patient.had_severe_allergic_reaction,
                    'understands_medication_instructions': patient.understands_medication_instructions
                }
                
                appointment_details = {
                    'doctor_name': doctor.doctor_name,
                    'appointment_date': appointment_date,
                    'appointment_time': appointment_time_formatted,
                    'end_time': end_time_formatted,
                    'duration': duration_minutes,
                    'cancel_url': cancel_url,
                    'reschedule_url': reschedule_url
                }
                patient_type = 'new' if doctor.calendly_new_patient_url == scheduling_url else 'existing'
                
                email_service.send_appointment_confirmation(
                    patient_data=patient_data,
                    appointment_details=appointment_details,
                    patient_type=patient_type
                )
                
                logger.info(f"Comprehensive confirmation email sent to {patient_email}")
                
            except Exception as e:
                logger.error(f"Error sending confirmation email: {e}")
            
            return {"status": "Appointment created and comprehensive email sent"}
        else:
            logger.warning(f"Could not find doctor for event type: {event_type_uri}")
            return {"status": "Webhook received but doctor not found"}
            
    except Exception as e:
        logger.error(f"Error processing invitee.created webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")

async def handle_invitee_canceled(payload: dict, db: Session):
    """Handle when an appointment is canceled"""
    try:
        data = payload.get("payload", {})
        invitee_uri = data.get("uri")
        appointment = db.query(models.Appointment).filter(
            models.Appointment.calendly_invitee_uri == invitee_uri
        ).first()
        
        if appointment:
            appointment.status = 'canceled'
            db.commit()
            logger.info(f"Canceled appointment: {appointment.appointment_id}")
            return {"status": "Appointment canceled"}
        else:
            logger.warning(f"Could not find appointment for invitee URI: {invitee_uri}")
            return {"status": "Appointment not found"}
            
    except Exception as e:
        logger.error(f"Error processing invitee.canceled webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing cancellation: {str(e)}")