#here we apply the Expcetion Hadaling , So our API don't crash - 
#1 Appy- user Question limit 
#2 try except block to handle erro related to groq server 
from fastapi import FastAPI,HTTPException,Header,Request,Depends
from groq import Groq
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
import os
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from slowapi import Limiter
from slowapi.util import get_remote_address
from jose import JWTError, jwt
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import uuid # To generate random unique numbers for session 
from datetime import datetime,timedelta # Adding for token expired at set time 



# load important data from .env file
load_dotenv()
#Rate limiter Setup 
#ger_remote_address = this identifies the user by the IP Address

#----Creating secrete key 
SECRET_KEY = os.getenv("SECRET_KEY","fallback-secret-change-this")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30

limiter = Limiter(key_func=get_remote_address)

#opening the Resturnat
app = FastAPI()
#connecting limiter to your app
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

client = Groq(api_key=os.getenv("GROQ_API_KEY")) # here we Give the Key 

# Add Sequrity 
security =HTTPBearer()

#creating fucntion to make ai brain 
conversation_memory = {} #Dict we Created to Stored Conversation (it Stored in RAM) 

#----Storing now RAM LAter I use DB 
# In here a big problem we will solve further - password in plain text
fake_users_db={
    'rahul':"password123",
    'priyam':"maypassword"
}

# active_sessions ={} # Creating the Session # Remove the session for JWT

# so create A Class

from pydantic import BaseModel # Pydantic Provide A Base Model that is the SUPER Powered BluePrint (that have Sequroty Sysatem) Normal Class DOn't Have this

class LoginRequest(BaseModel):
    username:str
    password:str
class QuestionRequest(BaseModel): #BaseModel = The foundation structurethat Pydantic gives you to build YOUR structure on top of
    question:str
    
##_____Adding JWP Setup 

def create_token(username:str):
    payload = {
    "username": username,
    "exp": datetime.utcnow()+timedelta(minutes=TOKEN_EXPIRE_MINUTES)
}

    #Sign in awith that key 

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return token

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        #Decode that signature

        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username = payload.get("username")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="invalid token,login again"
        )

# def ask_agent(request: Request,body: QuestionRequest,session_token: str = Header(None)):

def brain_ai(question: str, username:str): #Problem 1 -  Write now We did't Define Shape of Data , input in Not in the Requrad Shape the API gose Crash 
        
    # Adding the nmumbers limit
    if (len(question)) >1000:
        raise HTTPException(
            status_code= 400,
            detail="Question is Too Long , Maximum 1000 Characters"
        )
    # If this user is new - give them a fresh notebook

    if username not in conversation_memory:
        conversation_memory[username] = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant."
            }
        ]

    # Add their new question to their notebook
    conversation_memory[username].append({
        "role": "user",
        "content":question
    })
    

    #making the sliding window - so it can remember only last 10 messages

    system_prompt = conversation_memory[username][0]
    recent_messages = conversation_memory[username][-10:]

    #message that sent to the LLM 
    augumented_message = [system_prompt]+recent_messages

    #sendig the full notbook to grouq   
    try:
        response = client.chat.completions.create(
         model="llama-3.1-8b-instant",
            messages = augumented_message
        )

        answer = response.choices[0].message.content
    except Exception as e:
        # Groq is down? Internet cut? Key expired?
        # Don't crash. Tell user politely.
        raise HTTPException(
            status_code=503,
            detail="Ai Server is Down try After Some time"
        )

    #Also write the Answer in to the notbook 

    conversation_memory[username].append({"role":"assistant","content":answer}) # that also written in notbook
    return answer
 
#Creating a home route 
@app.get("/")
def home():
    return RedirectResponse(url="/docs") # So User Can Directly Lands in Swagger UI and test 

# # this is the Asking Rout
# @app.post("/ask")
# def ask_agent(question:str):
#     result = brain_ai(question)
#     return {"answer":result}

@app.post("/login")
def login(request:LoginRequest):
    if request.username not in fake_users_db:
        raise HTTPException(
            status_code=401,
            detail="Username not found."
        )
    if fake_users_db[request.username] != request.password:
        raise HTTPException(
            status_code=401,
            detail="Wrong password"
        )
    
    #Creating jwt token
    token = create_token(request.username)
    return {
        "message": f"Welcome {request.username}!",
        "access_token": token,
        "token_type": "bearer",
        "expires_in": f"{TOKEN_EXPIRE_MINUTES} minutes"
    }
    return {
        "message": f"Welcome {request.username}!",
        "session_token": session_token
    }
#Soln - 1 Change the Ask Route 

@app.post("/ask")
@limiter.limit("5/minute") # Reduced limit for deployment
# def ask_agent(request: Request, body: QuestionRequest, session_token: str = Header(None)): # change the session to jwt tokens
def ask_agent(request: Request, body: QuestionRequest,  username: str = Depends(verify_token)):
    result = brain_ai(body.question,username)
    return {
        "user": username,
        "question": body.question,
        "answer": result
    }
    
@app.get("/memory") # here i decrese the resuseability to define new rote also the loop hole is - session if change and lost the covrsation 
# so in future we will use the databases 
def see_memory(username:str= Depends(verify_token)):
    memory = conversation_memory.get(username, [])
    return {
        "user": username,
        "total_messages": len(memory),
        "conversation": memory
    }