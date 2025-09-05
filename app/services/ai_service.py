import os
from typing import List, Dict
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain
from langchain_core.prompts import MessagesPlaceholder, HumanMessagePromptTemplate, ChatPromptTemplate
load_dotenv()
class DoctorRecommendation(BaseModel):
    """The name and reasoning for a recommended doctor."""
    recommended_doctor_name: str = Field(description="The full name of the single most suitable doctor from the provided list.")
    reasoning: str = Field(description="A brief explanation for why this specific doctor was recommended based on the patient's symptoms.")

class MedicalAIService:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.1)
        self.conversations: Dict[str, ConversationChain] = {}

    def recommend_doctor(self, symptoms: str, doctors: List[Dict]) -> DoctorRecommendation:
        """
        Uses the modern LangChain .with_structured_output() method for reliable,
        Pydantic-based recommendations.
        """
        doctor_list_str = "\n".join([f"- {d['doctor_name']}, Specialization: {d['specialization']}" for d in doctors])
        
        system_prompt = "You are a helpful medical assistant. Your task is to analyze the patient's symptoms and recommend the single most suitable doctor from the provided list."
        
        human_prompt = """
        Please recommend a doctor from the following list based on the patient's symptoms.

        **Available Doctors:**
        {doctors}

        **Patient Symptoms:**
        {symptoms}
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])
        structured_llm = self.llm.with_structured_output(DoctorRecommendation)
        
        chain = prompt | structured_llm
        
        try:
            result = chain.invoke({
                "doctors": doctor_list_str,
                "symptoms": symptoms,
            })
            return result
        except Exception as e:
            print(f"CRITICAL ERROR in LangChain recommendation chain: {e}")
            raise

    def get_chat_response(self, session_id: str, query: str, doctors: List[Dict]) -> str:
        """
        Uses LangChain's ConversationChain with memory to provide contextual chat responses.
        """
        if session_id not in self.conversations:
            doctor_list_str = "\n".join([f"- {d['doctor_name']} specializes in {d['specialization']}." for d in doctors])
            
            system_prompt = f"""
            You are a friendly and helpful AI assistant for the 'MediCare Wellness Center'.
            Your goal is to answer patient questions about our services, doctors, and general hospital information.
            You must not give medical advice. If asked for medical advice, politely refuse and recommend booking an appointment.

            Here is information about our hospital:
            - Hospital Name: MediCare Wellness Center
            - Our Doctors:
            {doctor_list_str}
            - Our Services:
            - General Checkups
            - Pediatrics
            - Dermatology
            - Emergency Care
            - Location: 123 Health St, Wellness City
            """

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="history"),
                HumanMessagePromptTemplate.from_template("{input}")
            ])
            
            memory = ConversationBufferWindowMemory(k=4, return_messages=True)
            
            self.conversations[session_id] = ConversationChain(
                llm=ChatOpenAI(model="gpt-4", temperature=0.5),
                prompt=prompt,
                memory=memory,
                verbose=False
            )

        try:
            chain = self.conversations[session_id]
            response = chain.predict(input=query)
            return response
        except Exception as e:
            print(f"CRITICAL ERROR in LangChain conversation chain: {e}")
            raise