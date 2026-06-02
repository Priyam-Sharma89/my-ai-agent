from fastapi import FastAPI
from groq import Groq
import os
from dotenv import load_dotenv

# load important data from .env file
load_dotenv()

#opening the Resturnat
app = FastAPI()

client = Groq(api_key=os.getenv("GROUQ_API_KEY")) # here we Give the Key 
# Soln- 1 - we build the what shape of data user must Enter , Other shape is not acceptable 

# so create A Class

from pydantic import BaseModel # Pydantic Provide A Base Model that is the SUPER Powered BluePrint (that have Sequroty Sysatem) Normal Class DOn't Have this
class QuestoinRequest(BaseModel): #BaseModel = The foundation structurethat Pydantic gives you to build YOUR structure on top of
    question:str
    user_id:str


#creating fucntion to make ai brain 
conversation_memory = {} #Dict we Created to Stored Conversation (it Stored in RAM) 

def brain_ai(question: str, user_id:str): #Problem 1 -  Write now We did't Define Shape of Data , input in Not in the Requrad Shape the API gose Crash 
    
    # If this user is new - give them a fresh notebook
    if user_id not in conversation_memory:
        conversation_memory[user_id] = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant."
            }
        ]

    # Add their new question to their notebook
    conversation_memory[user_id].append({
        "role": "user",
        "content": question
    })
    

    #making the sliding window - so it can remember only last 10 messages
    system_prompt = conversation_memory[user_id][0]
    recent_messages = conversation_memory[user_id][-10:]

    #message that sent to the LLM 
    augumented_message = [system_prompt]+recent_messages

    #sendig the full notbook to grouq   
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages = augumented_message
    )

    answer = response.choices[0].message.content

    #Also write the Answer in to the notbook 

    conversation_memory[user_id].append({"role":"assistant","content":answer}) # that also written in notbook
    return answer
 
#Creating a home route 
@app.get("/")
def home():
    return {"message": "My AI Agent is Alive and Also Working!"}

# # this is the Asking Rout
# @app.post("/ask")
# def ask_agent(question:str):
#     result = brain_ai(question)
#     return {"answer":result}

#Soln - 1 Change the Ask Route 

@app.post("/ask")
def ask_agent(request:QuestoinRequest):
    result = brain_ai(request.question, request.user_id)
    return {
        "user": request.user_id, # here We Go the Attribute bug - Then We saw 500 Status Code - in this Bug - the Attribute have different name 
        "question": request.question,
        "answer": result
    }

@app.get("/memory{user_id}")
def see_memory(user_id:str):
    memory = conversation_memory.get(user_id, [])
    return {
        "user_id": user_id,
        "total_messages": len(memory),
        "conversation": memory
    }