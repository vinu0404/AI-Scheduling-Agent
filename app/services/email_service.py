import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = os.getenv("SMTP_PORT")
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL")
        self.env = Environment(loader=FileSystemLoader('templates/'))

    def send_appointment_confirmation(self, patient_data: dict, appointment_details: dict, patient_type: str):
        if not all([self.smtp_server, self.smtp_port, self.smtp_username, self.smtp_password, self.from_email]):
            print("Email configuration is incomplete. Skipping email.")
            return

        to_email = patient_data.get('email')
        subject = f"Appointment Confirmation - {appointment_details['doctor_name']}"
        
        template_name = 'new_patient_email.html' if patient_type == 'new' else 'existing_patient_email.html'
        template = self.env.get_template(template_name)
        html_content = template.render(patient=patient_data, appointment=appointment_details)

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.from_email
        msg['To'] = to_email
        msg.attach(MIMEText(html_content, 'html'))
        
        try:
            with smtplib.SMTP(self.smtp_server, int(self.smtp_port)) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                print(f"Email sent successfully to {to_email}")
        except Exception as e:
            print(f"Failed to send email to {to_email}. Error: {e}")
