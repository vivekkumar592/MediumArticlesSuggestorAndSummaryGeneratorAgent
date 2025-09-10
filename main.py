from fastapi import FastAPI
from agent import agent
app = FastAPI()



  # stream_graph_updates(user_input)

@app.get("/recommend/{user_input}")
async def read_user_input(user_input: str):
    agent_content = await agent(user_input)
    return {"agent_content": agent_content}
