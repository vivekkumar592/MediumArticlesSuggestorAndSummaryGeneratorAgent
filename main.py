from fastapi import FastAPI, Request
from agent import agent
import logging
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Use "*" only, do not mix with other origins list
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=False,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

logger = logging.getLogger("uvicorn.error")

@app.middleware("https")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    return response

@app.get("/")
async def read_initial():
    return {"agent_content": "Hello User"}

@app.get("/recommend/{user_input}")
async def read_user_input(user_input: str):
    agent_content = await agent(user_input)
    logger.info(f"recommend path hit by user request: {user_input}")
    return {"agent_content": agent_content}

# Optional: explicit OPTIONS for debug
@app.options("/recommend/{user_input}")
async def options_handler(user_input: str):
    return {}
