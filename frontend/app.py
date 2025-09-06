import streamlit as st
import requests
import datetime
import uuid
import pandas as pd

st.set_page_config(page_title="MediCare Wellness Center", layout="wide")

API_BASE_URL = "http://localhost:8000/api"

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = "home"

if 'doctors' not in st.session_state:
    try:
        response = requests.get(f"{API_BASE_URL}/doctors")
        st.session_state.doctors = response.json() if response.status_code == 200 else []
    except requests.exceptions.ConnectionError:
        st.session_state.doctors = []
        st.error("Connection Error: Could not connect to the backend. Please ensure it is running.")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = str(uuid.uuid4())

if "verified_patient" not in st.session_state:
    st.session_state.verified_patient = None

def parse_datetime_flexible(date_string):
    """Parse datetime string with flexible format handling"""
    try:
        # Try ISO8601 format first
        return pd.to_datetime(date_string, format='ISO8601').strftime('%Y-%m-%d %I:%M %p')
    except:
        try:
            # Try mixed format parsing
            return pd.to_datetime(date_string, format='mixed').strftime('%Y-%m-%d %I:%M %p')
        except:
            # If all else fails, return the original string
            return date_string

def navigate_to(page):
    st.session_state.page = page

def home_page():
    st.title("🏥 Welcome to MediCare Wellness Center")
    st.write("Your partner in health. Please select an option below to get started.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📅 Book an Appointment", use_container_width=True, type="primary"):
            navigate_to("patient_type_selection")
            st.rerun()
    with col2:
        if st.button("💬 Chat with an AI Assistant", use_container_width=True):
            navigate_to("chat")
            st.rerun()
    with col3:
        if st.button("👨‍💼 Admin Dashboard", use_container_width=True):
            navigate_to("admin")
            st.rerun()

def patient_type_selection_page():
    st.title("📅 Book an Appointment")
    st.write("Are you a new or existing patient?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("I am a New Patient", use_container_width=True):
            navigate_to("new_patient_form")
            st.rerun()
    with col2:
        if st.button("I am an Existing Patient", use_container_width=True):
            navigate_to("existing_patient_verification")
            st.rerun()
    
    if st.button("⬅️ Go Back to Home"):
        navigate_to("home")
        st.rerun()

def existing_patient_verification_page():
    st.title("🔍 Existing Patient Verification")
    st.write("Please enter your information to verify you are an existing patient.")
    
    with st.form("patient_verification_form"):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name *", placeholder="Enter your first name")
            last_name = st.text_input("Last Name *", placeholder="Enter your last name")
        with col2:
            email = st.text_input("Email Address *", placeholder="your.email@example.com")
        
        submitted = st.form_submit_button("Verify Patient Information", type="primary")
    
    if submitted:
        if not all([first_name, last_name, email]):
            st.error("Please fill out all required fields.")
        else:
            with st.spinner("Verifying patient information..."):
                try:
                    verification_data = {
                        "first_name": first_name.strip(),
                        "last_name": last_name.strip(),
                        "email": email.strip().lower()
                    }
                    
                    response = requests.post(f"{API_BASE_URL}/verify-patient", json=verification_data)
                    
                    if response.status_code == 200:
                        patient_data = response.json()
                        st.session_state.verified_patient = patient_data
                        st.success(f"Welcome back, {patient_data['first_name']} {patient_data['last_name']}!")
                        st.info("Redirecting you to book your appointment...")
                        st.balloons()
                        navigate_to("existing_patient_form")
                        st.rerun()
                    elif response.status_code == 404:
                        st.error("Patient not found in our system.")
                        st.warning("It looks like you might be a new patient. Please use the 'I am a New Patient' option to register.")
                        
                    else:
                        st.error("There was an error verifying your information. Please try again.")
                        
                except requests.exceptions.ConnectionError:
                    st.error("Connection Error: Could not connect to the backend. Please ensure it is running.")

    if st.button("⬅️ Back to Appointment Type"):
        navigate_to("patient_type_selection")
        st.rerun()

def new_patient_form_page():
    st.title("📋 New Patient Registration")
    
    with st.form("new_patient_form"):
        st.header("PATIENT INFORMATION")
        col1, col2, col3 = st.columns([2, 0.5, 2])
        with col1:
            first_name = st.text_input("First Name *", placeholder="Enter your first name")
        with col2:
            middle_initial = st.text_input("Middle Initial", placeholder="M.I.", max_chars=1)
        with col3:
            last_name = st.text_input("Last Name *", placeholder="Enter your last name")
        
        col1, col2 = st.columns(2)
        with col1:
            date_of_birth = st.date_input("Date of Birth *", 
                                        min_value=datetime.date(1920, 1, 1),
                                        max_value=datetime.date.today(),
                                        help="MM/DD/YYYY")
        with col2:
            gender = st.selectbox("Gender *", ["", "Male", "Female", "Other"])
        col1, col2 = st.columns(2)
        with col1:
            home_phone = st.text_input("Home Phone", placeholder="(555) 123-4567")
        with col2:
            cell_phone = st.text_input("Cell Phone *", placeholder="(555) 123-4567")
        
        email = st.text_input("Email Address *", placeholder="your.email@example.com")
        street_address = st.text_input("Street Address *", placeholder="123 Main Street")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            city = st.text_input("City *", placeholder="Your City")
        with col2:
            state = st.text_input("State *", placeholder="CA", max_chars=2)
        with col3:
            zip_code = st.text_input("ZIP Code *", placeholder="12345")
        
        st.header("EMERGENCY CONTACT")
        
        col1, col2 = st.columns(2)
        with col1:
            emergency_contact_name = st.text_input("Emergency Contact Name *", 
                                                 placeholder="Full name of emergency contact")
        with col2:
            emergency_contact_relationship = st.text_input("Relationship *", 
                                                         placeholder="e.g., Spouse, Parent, Sibling")
        
        emergency_contact_phone = st.text_input("Emergency Contact Phone Number *", 
                                               placeholder="(555) 123-4567")
        
        st.header("INSURANCE INFORMATION")
        
        st.subheader("Primary Insurance")
        col1, col2 = st.columns(2)
        with col1:
            primary_insurance_company = st.text_input("Insurance Company *", 
                                                    placeholder="e.g., LIC")
            primary_member_id = st.text_input("Member ID *", placeholder="Member ID number")
        with col2:
            primary_group_number = st.text_input("Group Number", placeholder="Group number (if applicable)")
        
        st.subheader("Secondary Insurance (if applicable)")
        col1, col2 = st.columns(2)
        with col1:
            secondary_insurance_company = st.text_input("Secondary Insurance Company", 
                                                      placeholder="Optional")
            secondary_member_id = st.text_input("Secondary Member ID", placeholder="Optional")
        with col2:
            secondary_group_number = st.text_input("Secondary Group Number", placeholder="Optional")
        
        st.info("📋 Note: Please bring insurance cards and photo ID to your appointment.")
        
        st.header("CHIEF COMPLAINT & SYMPTOMS")
        
        primary_reason_for_visit = st.text_area("What is the primary reason for your visit today? *", 
                                              placeholder="Please describe your main concern or symptoms...",
                                              height=100)
        
        symptom_duration = st.selectbox("How long have you been experiencing these symptoms?", 
                                      ["", "Less than 1 week", "1-4 weeks", "1-6 months", "More than 6 months"])
        
        st.write("**Please check all symptoms you are currently experiencing:**")
        
        # Symptoms checkboxes
        symptoms_col1, symptoms_col2, symptoms_col3 = st.columns(3)
        
        current_symptoms = []
        
        with symptoms_col1:
            if st.checkbox("Sneezing"): current_symptoms.append("Sneezing")
            if st.checkbox("Runny nose"): current_symptoms.append("Runny nose")
            if st.checkbox("Shortness of breath"): current_symptoms.append("Shortness of breath")
            if st.checkbox("Itchy eyes"): current_symptoms.append("Itchy eyes")
            if st.checkbox("Chest tightness"): current_symptoms.append("Chest tightness")
        
        with symptoms_col2:
            if st.checkbox("Wheezing"): current_symptoms.append("Wheezing")
            if st.checkbox("Stuffy nose"): current_symptoms.append("Stuffy nose")
            if st.checkbox("Coughing"): current_symptoms.append("Coughing")
            if st.checkbox("Watery eyes"): current_symptoms.append("Watery eyes")
            if st.checkbox("Skin rash/hives"): current_symptoms.append("Skin rash/hives")
        
        with symptoms_col3:
            if st.checkbox("Sinus pressure"): current_symptoms.append("Sinus pressure")
            if st.checkbox("Headaches"): current_symptoms.append("Headaches")
        
        st.header("ALLERGY HISTORY")
        
        has_known_allergies = st.radio("Do you have any known allergies? *", 
                                     ["Yes", "No", "Not sure"])
        
        known_allergies_list = ""
        if has_known_allergies == "Yes":
            known_allergies_list = st.text_area("If yes, please list all known allergies and reactions:",
                                              placeholder="Include foods, medications, environmental allergens, etc.",
                                              height=80)
        
        had_allergy_testing = st.radio("Have you ever had allergy testing before?", 
                                     ["Yes", "No"])
        
        allergy_testing_date = ""
        if had_allergy_testing == "Yes":
            allergy_testing_date = st.text_input("When:", placeholder="e.g., January 2023")
        
        had_severe_allergic_reaction = st.radio("Have you ever used an EpiPen or had a severe allergic reaction?", 
                                              ["Yes", "No"])
        
        st.header("CURRENT MEDICATIONS")
        
        current_medications = st.text_area("Please list ALL current medications, vitamins, and supplements:",
                                         placeholder="Include prescription medications, over-the-counter drugs, vitamins, and herbal supplements. Include dosage if known.",
                                         height=100)
        
        st.write("**Are you currently taking any of these allergy medications?**")
        
        current_allergy_medications = []
        
        allergy_col1, allergy_col2 = st.columns(2)
        with allergy_col1:
            if st.checkbox("Claritin (loratadine)"): current_allergy_medications.append("Claritin (loratadine)")
            if st.checkbox("Zyrtec (cetirizine)"): current_allergy_medications.append("Zyrtec (cetirizine)")
            if st.checkbox("Allegra (fexofenadine)"): current_allergy_medications.append("Allegra (fexofenadine)")
        
        with allergy_col2:
            if st.checkbox("Flonase/Nasacort (nasal sprays)"): current_allergy_medications.append("Flonase/Nasacort (nasal sprays)")
            if st.checkbox("Benadryl (diphenhydramine)"): current_allergy_medications.append("Benadryl (diphenhydramine)")
        
        other_allergy_med = st.text_input("Other:", placeholder="Please specify")
        if other_allergy_med:
            current_allergy_medications.append(f"Other: {other_allergy_med}")
        
        st.header("MEDICAL HISTORY")
        
        st.write("**Please check any conditions you have or have had:**")
        
        medical_conditions = []
        
        medical_col1, medical_col2, medical_col3 = st.columns(3)
        
        with medical_col1:
            if st.checkbox("Asthma"): medical_conditions.append("Asthma")
            if st.checkbox("Eczema"): medical_conditions.append("Eczema")
            if st.checkbox("Sinus infections"): medical_conditions.append("Sinus infections")
            if st.checkbox("High blood pressure"): medical_conditions.append("High blood pressure")
        
        with medical_col2:
            if st.checkbox("Pneumonia"): medical_conditions.append("Pneumonia")
            if st.checkbox("Bronchitis"): medical_conditions.append("Bronchitis")
            if st.checkbox("Diabetes"): medical_conditions.append("Diabetes")
        
        with medical_col3:
            if st.checkbox("Heart disease"): medical_conditions.append("Heart disease")
        
        other_condition = st.text_input("Other:", placeholder="Please specify any other conditions")
        if other_condition:
            medical_conditions.append(f"Other: {other_condition}")
        
        family_allergy_history = st.text_area("Family history of allergies or asthma:",
                                            placeholder="Please describe any family history of allergies, asthma, or related conditions",
                                            height=80)
        
        st.header("IMPORTANT PRE-VISIT INSTRUCTIONS")
        
        st.warning("""
        **CRITICAL: If allergy testing is planned, you MUST stop the following medications 7 days before your appointment:**
        
        • All antihistamines (Claritin, Zyrtec, Allegra, Benadryl)
        • Cold medications containing antihistamines  
        • Sleep aids like Tylenol PM
        
        **You MAY continue:**
        • Nasal sprays (Flonase, Nasacort)
        • Asthma inhalers
        • Prescription medications
        """)
        
        understands_medication_instructions = st.radio("I understand the pre-visit medication instructions: *", 
                                                     ["Yes, I understand and will follow instructions", 
                                                      "I have questions about these instructions"])
        
        st.header("PATIENT ACKNOWLEDGMENT")
        
        acknowledgment = st.checkbox("I certify that the information provided is accurate and complete to the best of my knowledge. I understand that providing false information may affect my treatment. *")
        
        submitted = st.form_submit_button("Complete Registration & Find a Doctor", type="primary")

    if submitted:
        required_fields = [
            first_name, last_name, date_of_birth, gender, cell_phone, email,
            street_address, city, state, zip_code, emergency_contact_name,
            emergency_contact_relationship, emergency_contact_phone,
            primary_insurance_company, primary_member_id, primary_reason_for_visit,
            symptom_duration, has_known_allergies, had_allergy_testing,
            had_severe_allergic_reaction, understands_medication_instructions
        ]
        
        if not all(required_fields) or not acknowledgment:
            st.error("Please fill out all required fields (*) and accept the patient acknowledgment.")
        else:
            patient_data = {
                # Personal Information
                "first_name": first_name,
                "middle_initial": middle_initial or "",
                "last_name": last_name,
                "date_of_birth": str(date_of_birth),
                "gender": gender,
                
                # Contact Information
                "email": email,
                "home_phone": home_phone or "",
                "cell_phone": cell_phone,
                
                # Address Information
                "street_address": street_address,
                "city": city,
                "state": state.upper(),
                "zip_code": zip_code,
                
                # Emergency Contact
                "emergency_contact_name": emergency_contact_name,
                "emergency_contact_relationship": emergency_contact_relationship,
                "emergency_contact_phone": emergency_contact_phone,
                
                # Insurance Information
                "primary_insurance_company": primary_insurance_company,
                "primary_member_id": primary_member_id,
                "primary_group_number": primary_group_number or "",
                "secondary_insurance_company": secondary_insurance_company or "",
                "secondary_member_id": secondary_member_id or "",
                "secondary_group_number": secondary_group_number or "",
                
                # Chief Complaint & Symptoms
                "primary_reason_for_visit": primary_reason_for_visit,
                "symptom_duration": symptom_duration,
                "current_symptoms": current_symptoms,
                
                # Allergy History
                "has_known_allergies": has_known_allergies,
                "known_allergies_list": known_allergies_list,
                "had_allergy_testing": had_allergy_testing,
                "allergy_testing_date": allergy_testing_date,
                "had_severe_allergic_reaction": had_severe_allergic_reaction,
                
                # Current Medications
                "current_medications": current_medications or "",
                "current_allergy_medications": current_allergy_medications,
                
                # Medical History
                "medical_conditions": medical_conditions,
                "family_allergy_history": family_allergy_history or "",
                
                # Pre-visit Instructions Acknowledgment
                "understands_medication_instructions": understands_medication_instructions
            }
            
            with st.spinner("Processing your registration and finding the right doctor for you..."):
                try:
                    # Create patient
                    patient_response = requests.post(f"{API_BASE_URL}/patients", json=patient_data)
                    
                    if patient_response.status_code == 200:
                        symptoms_text = f"{primary_reason_for_visit}. Current symptoms: {', '.join(current_symptoms) if current_symptoms else 'None specified'}. Duration: {symptom_duration}."
                        
                        rec_response = requests.post(f"{API_BASE_URL}/recommend-doctor", 
                                                   json={"symptoms": symptoms_text})
                        
                        if rec_response.status_code == 200:
                            rec = rec_response.json()
                            st.session_state.recommendation = rec
                            st.session_state.patient_data = patient_data
                        else:
                            st.error("Could not get a doctor recommendation at this time.")
                    else:
                        st.error("There was an error processing your registration. Please try again.")
                        
                except requests.exceptions.ConnectionError:
                    st.error("Connection Error: Could not connect to the backend. Please ensure it is running.")

    # Display recommendation and booking
    if 'recommendation' in st.session_state and st.session_state.recommendation:
        rec = st.session_state.recommendation
        st.success(f"**AI Recommendation:** Based on your symptoms, we recommend **{rec['recommended_doctor_name']}**.")
        st.info(f"**Reasoning:** {rec['reasoning']}")
        
        doctor = next((d for d in st.session_state.doctors if d['doctor_name'] == rec['recommended_doctor_name']), None)
        if doctor:
            st.subheader(f"Book Your Consultation with {doctor['doctor_name']}")
            st.components.v1.html(f'<iframe src="{doctor["calendly_new_patient_url"]}" width="100%" height="700"></iframe>', height=710)
        else:
            st.error("The recommended doctor is not available for booking right now.")

    if st.button("⬅️ Back to Appointment Type"):
        if 'recommendation' in st.session_state:
            del st.session_state.recommendation
        if 'patient_data' in st.session_state:
            del st.session_state.patient_data
        navigate_to("patient_type_selection")
        st.rerun()

def existing_patient_form_page():
    st.title("👤 Existing Patient Welcome")
    
    # Check if patient is verified
    if not st.session_state.verified_patient:
        st.error("Access denied. Please verify your patient information first.")
        if st.button("Go to Patient Verification"):
            navigate_to("existing_patient_verification")
            st.rerun()
        return
    
    patient = st.session_state.verified_patient
    st.success(f"Welcome back, {patient['first_name']} {patient['last_name']}!")
    st.write("Please select your doctor to book a follow-up appointment.")
    
    for doctor in st.session_state.doctors:
        with st.expander(f"**{doctor['doctor_name']}** - {doctor['specialization']}"):
            st.write(f"Book a follow-up with {doctor['doctor_name']}:")
            st.components.v1.html(f'<iframe src="{doctor["calendly_existing_patient_url"]}" width="100%" height="700"></iframe>', height=710)

    if st.button("⬅️ Back to Appointment Type"):
        st.session_state.verified_patient = None 
        navigate_to("patient_type_selection")
        st.rerun()

def admin_page():
    st.title("👨‍💼 Admin Dashboard")
    st.write("Comprehensive view of appointments and patient data.")
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        with st.form("admin_login"):
            st.subheader("Admin Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Login")
            
            if login_submitted:
                if username == "admin" and password == "admin123":
                    st.session_state.admin_authenticated = True
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        return
    
    try:
        # Get appointments data
        appointments_response = requests.get(f"{API_BASE_URL}/admin/appointments")
        if appointments_response.status_code != 200:
            st.error("Failed to fetch appointments data")
            return
            
        appointments_data = appointments_response.json()
        
        # Get doctor statistics
        stats_response = requests.get(f"{API_BASE_URL}/admin/doctor-stats")
        if stats_response.status_code != 200:
            st.error("Failed to fetch doctor statistics")
            return
            
        doctor_stats = stats_response.json()
        
        # Display statistics
        st.header("📊 Doctor Statistics")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Doctors", len(doctor_stats))
        with col2:
            total_appointments = sum(stat['appointment_count'] for stat in doctor_stats)
            st.metric("Total Appointments", total_appointments)
        with col3:
            active_appointments = sum(1 for apt in appointments_data if apt['status'] == 'scheduled')
            st.metric("Active Appointments", active_appointments)
        
        st.subheader("👨‍⚕️ Doctor Appointment Summary")
        if doctor_stats:
            df_stats = pd.DataFrame(doctor_stats)
            df_stats = df_stats.rename(columns={
                'doctor_name': 'Doctor Name',
                'specialization': 'Specialization',
                'appointment_count': 'Total Appointments',
                'scheduled_count': 'Scheduled',
                'cancelled_count': 'Cancelled'
            })
            st.dataframe(df_stats, use_container_width=True)
        
        # Detailed Appointments View
        st.subheader("📅 All Appointments")
        
        if appointments_data:
            df_appointments = pd.DataFrame(appointments_data)
            
            # Enhanced datetime parsing with flexible handling
            if 'appointment_time' in df_appointments.columns:
                df_appointments['appointment_time'] = df_appointments['appointment_time'].apply(parse_datetime_flexible)
            if 'created_at' in df_appointments.columns:
                df_appointments['created_at'] = df_appointments['created_at'].apply(parse_datetime_flexible)
            
            display_columns = {
                'appointment_id': 'ID',
                'patient_name': 'Patient Name',
                'patient_email': 'Patient Email',
                'doctor_name': 'Doctor',
                'appointment_time': 'Appointment Time',
                'status': 'Status',
                'created_at': 'Booked On'
            }
            
            # Only include columns that exist in the DataFrame
            available_columns = {k: v for k, v in display_columns.items() if k in df_appointments.columns}
            df_display = df_appointments[list(available_columns.keys())].rename(columns=available_columns)
            
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                status_filter = st.selectbox("Filter by Status", ["All"] + df_appointments['status'].unique().tolist())
            with col2:
                doctor_filter = st.selectbox("Filter by Doctor", ["All"] + df_appointments['doctor_name'].unique().tolist())
            with col3:
                date_filter = st.date_input("Filter by Date", value=None)
            
            # Apply filters
            filtered_df = df_display.copy()
            
            if status_filter != "All":
                filtered_df = filtered_df[df_appointments['status'] == status_filter]
            
            if doctor_filter != "All":
                filtered_df = filtered_df[df_appointments['doctor_name'] == doctor_filter]
            
            if date_filter:
                date_str = date_filter.strftime('%Y-%m-%d')
                mask = df_appointments['appointment_time'].str.contains(date_str, na=False)
                filtered_df = filtered_df[mask]
            
            # Display filtered results
            st.dataframe(filtered_df, use_container_width=True)
            
            # Export functionality
            if st.button("📥 Export to CSV"):
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"appointments_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No appointments found.")
            
    except requests.exceptions.ConnectionError:
        st.error("Connection Error: Could not connect to the backend. Please ensure it is running.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    
    # Logout and navigation
    if st.button("🚪 Logout"):
        st.session_state.admin_authenticated = False
        st.rerun()
    
    if st.button("⬅️ Go Back to Home"):
        navigate_to("home")
        st.rerun()

def chat_page():
    st.title("💬 AI Assistant")
    st.write("Ask me questions about our services or doctors.")

    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("What would you like to know?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner("Thinking..."):
                try:
                    payload = {
                        "session_id": st.session_state.chat_session_id,
                        "query": prompt
                    }
                    response = requests.post(f"{API_BASE_URL}/chat", json=payload)
                    
                    if response.status_code == 200:
                        assistant_response = response.json()["response"]
                        message_placeholder.markdown(assistant_response)
                        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                    else:
                        error_message = "I'm having trouble connecting. Please try again later."
                        message_placeholder.markdown(error_message)
                        st.session_state.messages.append({"role": "assistant", "content": error_message})
                except requests.exceptions.ConnectionError:
                    st.error("Connection Error: Could not connect to the AI assistant.")

    if st.button("⬅️ Go Back to Home"):
        navigate_to("home")
        st.rerun()

# Main navigation
if st.session_state.page == "home":
    home_page()
elif st.session_state.page == "patient_type_selection":
    patient_type_selection_page()
elif st.session_state.page == "existing_patient_verification":
    existing_patient_verification_page()
elif st.session_state.page == "new_patient_form":
    new_patient_form_page()
elif st.session_state.page == "existing_patient_form":
    existing_patient_form_page()
elif st.session_state.page == "admin":
    admin_page()
elif st.session_state.page == "chat":
    chat_page()