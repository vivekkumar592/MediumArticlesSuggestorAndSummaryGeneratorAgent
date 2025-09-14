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

@app.get("/recommend")
async def recommend(q: str = Query(..., min_length=1, description="Search text")):
    agent_content = await agent(q)
    logger.info(f"recommend query hit: {q}")
    return {"agent_content": agent_content}

# Optional: explicit OPTIONS for debug
@app.options("/recommend/{user_input}")
async def options_handler(user_input: str):
    return {}
