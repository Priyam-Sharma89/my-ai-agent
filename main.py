from fastapi import FastAPI

# This creates your restaurant
app = FastAPI()

# This creates your first waiter route
@app.get("/")
def home():
    return {"message": "My AI Agent is Alive!"}


home()
                                                 