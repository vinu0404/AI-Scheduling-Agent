import os
import uuid
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
from app.database.database import SessionLocal
from app.database.models import Doctor, Patient, Appointment

def seed_database():
    """
    Populates the database with initial doctors, detailed dummy patients, and dummy appointments.
    """
    load_dotenv()
    db = SessionLocal()
    
    try:
        # --- 1. Add Doctors ---
        print("--- Seeding Doctors ---")
        doctors_data = [
             {
                "doctor_name": "Dr. Sarah Smith", "specialization": "Allergy & Immunology,Asthma,Respiratory Medicine,Pulmonology,Chronic Cough,Wheezing,Shortness of Breath,Environmental Allergies,Food Allergies,Drug Allergies,Anaphylaxis,Immunodeficiency,Sinus Infections,Rhinitis",
                "email": "sarah.smith@medicare.com", "phone": "(555) 123-4567",
                "calendly_new_patient_url": os.getenv('DR_SARAH_SMITH_NEW_PATIENT_URL'),
                "calendly_existing_patient_url": os.getenv('DR_SARAH_SMITH_EXISTING_PATIENT_URL'),
            },
            {
                "doctor_name": "Dr. Michael Johnson", "specialization": "Dermatology,Dermatopathology,General Surgery,Skin Conditions,Eczema,Skin Rash,Hives,Allergic Skin Reactions,Psoriasis,Skin Cancer,Acne,Wound Care,Surgical Procedures,Mole Removal,Skin Allergies",
                "email": "michael.johnson@medicare.com", "phone": "(555) 234-5678",
                "calendly_new_patient_url": os.getenv('DR_MICHAEL_JOHNSON_NEW_PATIENT_URL'),
                "calendly_existing_patient_url": os.getenv('DR_MICHAEL_JOHNSON_EXISTING_PATIENT_URL'),
            },
            {
                "doctor_name": "Dr. Emily Williams","specialization": "Internal Medicine,Pediatrics,Family Medicine,Primary Care,Preventive Care,Chronic Disease Management,Diabetes,High Blood Pressure,Heart Disease,General Health,Wellness Exams,Vaccinations,Health Screenings,Medication Management",
                "email": "emily.williams@medicare.com", "phone": "(555) 345-6789",
                "calendly_new_patient_url": os.getenv('DR_EMILY_WILLIAMS_NEW_PATIENT_URL'),
                "calendly_existing_patient_url": os.getenv('DR_EMILY_WILLIAMS_EXISTING_PATIENT_URL'),
            }
        ]
        for doc_data in doctors_data:
            if not db.query(Doctor).filter(Doctor.doctor_name == doc_data["doctor_name"]).first():
                db.add(Doctor(**doc_data))
                print(f"Adding Doctor: {doc_data['doctor_name']}")
        db.commit()

        # --- 2. Add Fully Detailed Dummy Patients ---
        print("\n--- Seeding Patients ---")
        patients_data = [
            {
                "patient_id": str(uuid.uuid4()), "first_name": "John", "last_name": "Doe", "date_of_birth": date(1985, 5, 20),
                "email": "john.doe@example.com", "cell_phone": "555-0101", "street_address": "123 Maple St", "city": "Wellness City", "state": "CA", "zip_code": "90210",
                "primary_reason_for_visit": "Seasonal allergies and persistent cough.", "current_symptoms": ["coughing", "sneezing", "itchy eyes"],
                "has_known_allergies": "Yes", "known_allergies_list": "Pollen, Penicillin", "medical_conditions": ["Asthma"],
            },
            {
                "patient_id": str(uuid.uuid4()), "first_name": "Jane", "last_name": "Smith", "date_of_birth": date(1992, 8, 15),
                "email": "jane.smith@example.com", "cell_phone": "555-0102", "street_address": "456 Oak Ave", "city": "Wellness City", "state": "CA", "zip_code": "90211",
                "primary_reason_for_visit": "Skin rash on arms and back.", "current_symptoms": ["itchy rash", "redness"],
                "has_known_allergies": "No", "medical_conditions": [],
            },
            {
                "patient_id": str(uuid.uuid4()), "first_name": "Peter", "last_name": "Jones", "date_of_birth": date(1978, 1, 10),
                "email": "peter.jones@example.com", "cell_phone": "555-0103", "street_address": "789 Pine Ln", "city": "Metroburg", "state": "NY", "zip_code": "10001",
                "primary_reason_for_visit": "Annual physical and check-up.", "current_symptoms": ["general fatigue"],
                "has_known_allergies": "Not sure", "medical_conditions": ["High Blood Pressure"],
            },
            {
                "patient_id": str(uuid.uuid4()), "first_name": "Mary", "last_name": "Williams", "date_of_birth": date(2001, 11, 30),
                "email": "mary.williams@example.com", "cell_phone": "555-0104", "street_address": "101 Birch Rd", "city": "Metroburg", "state": "NY", "zip_code": "10002",
                "primary_reason_for_visit": "Severe acne breakout.", "current_symptoms": ["acne", "oily skin"],
                "has_known_allergies": "No", "medical_conditions": [],
            },
            {
                "patient_id": str(uuid.uuid4()), "first_name": "David", "last_name": "Brown", "date_of_birth": date(1965, 3, 25),
                "email": "david.brown@example.com", "cell_phone": "555-0105", "street_address": "212 Cedar Blvd", "city": "Wellness City", "state": "CA", "zip_code": "90212",
                "primary_reason_for_visit": "Difficulty breathing, especially at night.", "current_symptoms": ["shortness of breath", "wheezing"],
                "has_known_allergies": "Yes", "known_allergies_list": "Dust Mites", "medical_conditions": ["Asthma", "Sleep Apnea"],
            },
            {
                "patient_id": str(uuid.uuid4()), "first_name": "Linda", "last_name": "Davis", "date_of_birth": date(1988, 7, 12),
                "email": "linda.davis@example.com", "cell_phone": "555-0106", "street_address": "333 Elm St", "city": "Metroburg", "state": "NY", "zip_code": "10003",
                "primary_reason_for_visit": "Follow-up for diabetes management.", "current_symptoms": [],
                "has_known_allergies": "No", "medical_conditions": ["Diabetes Type 2"],
            },
            {
                "patient_id": str(uuid.uuid4()), "first_name": "James", "last_name": "Miller", "date_of_birth": date(1995, 9, 5),
                "email": "james.miller@example.com", "cell_phone": "555-0107", "street_address": "444 Spruce Way", "city": "Wellness City", "state": "CA", "zip_code": "90213",
                "primary_reason_for_visit": "Eczema flare-up.", "current_symptoms": ["dry skin", "itchiness", "red patches"],
                "has_known_allergies": "Yes", "known_allergies_list": "Fragrances in soaps", "medical_conditions": ["Eczema"],
            },
            {
                "patient_id": str(uuid.uuid4()), "first_name": "Patricia", "last_name": "Wilson", "date_of_birth": date(1972, 12, 18),
                "email": "patricia.wilson@example.com", "cell_phone": "555-0108", "street_address": "555 Willow Creek", "city": "Metroburg", "state": "NY", "zip_code": "10004",
                "primary_reason_for_visit": "Checking on heart health and blood pressure.", "current_symptoms": [],
                "has_known_allergies": "No", "medical_conditions": ["High Blood Pressure", "High Cholesterol"],
            },
            {
                "patient_id": str(uuid.uuid4()), "first_name": "Robert", "last_name": "Moore", "date_of_birth": date(1980, 4, 22),
                "email": "robert.moore@example.com", "cell_phone": "555-0109", "street_address": "666 Redwood Pkwy", "city": "Wellness City", "state": "CA", "zip_code": "90214",
                "primary_reason_for_visit": "Suspected food allergy after eating shellfish.", "current_symptoms": ["hives", "swelling"],
                "has_known_allergies": "Not sure", "medical_conditions": [],
            },
            {
                "patient_id": str(uuid.uuid4()), "first_name": "Jennifer", "last_name": "Taylor", "date_of_birth": date(1999, 6, 8),
                "email": "jennifer.taylor@example.com", "cell_phone": "555-0110", "street_address": "777 Sequoia Ave", "city": "Metroburg", "state": "NY", "zip_code": "10005",
                "primary_reason_for_visit": "Mole check and general skin screening.", "current_symptoms": [],
                "has_known_allergies": "No", "medical_conditions": [],
            },
        ]
        for patient_data in patients_data:
            if not db.query(Patient).filter(Patient.email == patient_data["email"]).first():
                db.add(Patient(**patient_data))
                print(f"Adding Patient: {patient_data['first_name']} {patient_data['last_name']}")
        db.commit()

        # --- 3. Add Dummy Appointments ---
        print("\n--- Seeding Appointments ---")
        
        doctors = {d.doctor_name: d.doctor_id for d in db.query(Doctor).all()}
        patients = {p.email: p.patient_id for p in db.query(Patient).all()}
        
        if doctors and patients:
            appointments_data = [
                {
                    "patient_id": patients["john.doe@example.com"], "doctor_id": doctors["Dr. Sarah Smith"],
                    "appointment_time": datetime.now() + timedelta(days=3, hours=2), "status": "scheduled",
                },
                {
                    "patient_id": patients["jane.smith@example.com"], "doctor_id": doctors["Dr. Michael Johnson"],
                    "appointment_time": datetime.now() + timedelta(days=4, hours=6), "status": "scheduled",
                },
                {
                    "patient_id": patients["peter.jones@example.com"], "doctor_id": doctors["Dr. Emily Williams"],
                    "appointment_time": datetime.now() + timedelta(days=5, hours=3), "status": "scheduled",
                },
                {
                    "patient_id": patients["mary.williams@example.com"], "doctor_id": doctors["Dr. Michael Johnson"],
                    "appointment_time": datetime.now() - timedelta(days=10, hours=4), "status": "canceled",
                },
                {
                    "patient_id": patients["john.doe@example.com"], "doctor_id": doctors["Dr. Sarah Smith"],
                    "appointment_time": datetime.now() + timedelta(days=10), "status": "scheduled",
                },
            ]

            for i, appt_data in enumerate(appointments_data):
                appt_data['end_time'] = appt_data['appointment_time'] + timedelta(minutes=30)
                appt_data['calendly_event_uri'] = f"https://api.calendly.com/scheduled_events/FAKE_EVENT_{uuid.uuid4()}"
                appt_data['calendly_invitee_uri'] = f"https://api.calendly.com/scheduled_events/FAKE_INVITEE_{uuid.uuid4()}"
                
                if not db.query(Appointment).filter(Appointment.calendly_event_uri == appt_data['calendly_event_uri']).first():
                    db.add(Appointment(**appt_data))
                    print(f"Adding Appointment for Patient ID: {appt_data['patient_id'][:8]}... at {appt_data['appointment_time'].strftime('%Y-%m-%d %H:%M')}")
            db.commit()
        else:
            print("Could not seed appointments because no doctors or patients were found.")

        print("\nDatabase seeded successfully!")
    
    except Exception as e:
        db.rollback()
        print(f"\nAn error occurred: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()