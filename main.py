from fastapi import FastAPI
from agent import agent

import logging
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",   # Frontend local dev URL
    "https://your-frontend-domain.com",  # Production frontend URL
    "*",  # Use "*" to allow all origins but not recommended for production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Or ["*"] to allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)





logger = logging.getLogger("uvicorn.error")
  # stream_graph_updates(user_input)

@app.get("/")
async def read_initial():
    return {"agent_content": "Hello User"}
@app.get("/recommend/{user_input}")
async def read_user_input(user_input: str):
    agent_content = await agent(user_input)
    logger.info(f"recomment path hit by this user request{user_input}")
    return {"agent_content": agent_content}
