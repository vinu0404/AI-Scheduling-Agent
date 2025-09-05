from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Patient(Base):
    __tablename__ = "patients"
    
    # Primary identification
    patient_id = Column(String, primary_key=True, index=True)
    
    # Personal Information
    first_name = Column(String, nullable=False)
    middle_initial = Column(String)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String)  # Male, Female, Other
    
    # Contact Information
    email = Column(String, unique=True, nullable=False, index=True)
    home_phone = Column(String)
    cell_phone = Column(String)
    
    # Address Information
    street_address = Column(String)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)
    
    # Emergency Contact
    emergency_contact_name = Column(String)
    emergency_contact_relationship = Column(String)
    emergency_contact_phone = Column(String)
    
    # Insurance Information
    primary_insurance_company = Column(String)
    primary_member_id = Column(String)
    primary_group_number = Column(String)
    secondary_insurance_company = Column(String)
    secondary_member_id = Column(String)
    secondary_group_number = Column(String)
    
    # Chief Complaint & Symptoms
    primary_reason_for_visit = Column(Text)
    symptom_duration = Column(String)  # Less than 1 week, 1-4 weeks, etc.
    current_symptoms = Column(JSON)  # Array of symptoms
    
    # Allergy History
    has_known_allergies = Column(String)  # Yes, No, Not sure
    known_allergies_list = Column(Text)
    had_allergy_testing = Column(String)  # Yes - When, No
    allergy_testing_date = Column(String)
    had_severe_allergic_reaction = Column(String)  # Yes, No
    
    # Current Medications
    current_medications = Column(Text)
    current_allergy_medications = Column(JSON)  # Array of allergy medications
    
    # Medical History
    medical_conditions = Column(JSON)  # Array of conditions
    family_allergy_history = Column(Text)
    
    # Pre-visit Instructions Acknowledgment
    understands_medication_instructions = Column(String)  # Yes, Has questions
    
    # System fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    appointments = relationship("Appointment", back_populates="patient")

class Doctor(Base):
    __tablename__ = "doctors"
    doctor_id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_name = Column(String, nullable=False, unique=True)
    specialization = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    calendly_new_patient_url = Column(String)
    calendly_existing_patient_url = Column(String)
    is_active = Column(Boolean, default=True)
    appointments = relationship("Appointment", back_populates="doctor")

class Appointment(Base):
    __tablename__ = "appointments"
    appointment_id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, ForeignKey('patients.patient_id'))
    doctor_id = Column(Integer, ForeignKey('doctors.doctor_id'))
    
    calendly_event_uri = Column(String, unique=True, nullable=False)
    calendly_invitee_uri = Column(String, unique=True, nullable=False)
    
    appointment_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String, default='scheduled')
    reschedule_url = Column(String)
    cancel_url = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")