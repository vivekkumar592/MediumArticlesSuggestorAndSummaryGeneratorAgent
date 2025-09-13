from fastapi import FastAPI
from agent import agent
app = FastAPI()
import logging

logger = logging.getLogger("uvicorn.error")
  # stream_graph_updates(user_input)

@app.get("/recommend/{user_input}")
async def read_user_input(user_input: str):
    agent_content = await agent(user_input)
    logger.info(f"recomment path hit by this user request{user_input}")
    return {"agent_content": agent_content}
