from typing import Annotated
from langgraph.graph import StateGraph, END, START
import os
from langgraph.graph.message import add_messages
import http.client
from urllib.parse import quote
from google.colab import userdata
import asyncio
import aiohttp
import os
import json
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import ToolNode, tools_condition,InjectedState
from langchain_core.messages import HumanMessage, AIMessage
import nest_asyncio

nest_asyncio.apply()
api_key=userdata.get("OPENAI_API_KEY")
rapid_key = userdata.get("RAPIDAPI_KEY")

os.environ["OPENAI_API_KEY"] = api_key
os.environ["RAPIDAPI_KEY"] = rapid_key

print(f"api key is {api_key}")
print(f"rapid key is {rapid_key}")

class State(TypedDict):
  messages:Annotated[list, add_messages]

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.json()

async def recommended_articles_searching_Node(state : State):
  '''This node generates the recommended articles'''
  print("Messages length entering tool node:")
  
  query = quote(state["messages"][-1].content)
  headers = {
    'x-rapidapi-key': rapid_key,
    'x-rapidapi-host': "medium2.p.rapidapi.com"
    }
  url = f"https://medium2.p.rapidapi.com/search/articles?query={query}&count=3"
  print(f"url is {url}")
  async with aiohttp.ClientSession(headers=headers) as session:
    res = await fetch(session, url)
  print(f"res is {res}")
  data = res
  print(data)
  connections =[];
  articles_id = data["articles"][:10];
  urls = [f"https://medium2.p.rapidapi.com/article/{article_id}" for article_id in articles_id]
  print(f"urls are {urls}")
  async with aiohttp.ClientSession(headers=headers) as session:
      tasks = [fetch(session, url) for url in urls]
      results = await asyncio.gather(*tasks, return_exceptions=True)
      print(f"results ",results)
      llm_message = AIMessage (content=str(results))
      state["messages"].append(llm_message)
  return state



graph_builder = StateGraph(State)

# tools_node = ToolNode(tools = [recommended_articles_searching_tool])

# def tool_agent_node(state: State):
#   ''' In this node the llm the tool recommended articles searching tools is called '''

#   user_message = state["messages"][-1].content if state["messages"] else ""
#   system_template = "You are a helpful assistant. call 'recommended_articles_searching_tool using this query '".format(user_message)
#   user_template = f"{user_message}"
#   prompt = ChatPromptTemplate.from_messages([
#     ("system", system_template),
#     ("user", user_template)
#   ])

#   formatted_prompt = prompt.invoke({"message": state["messages"][-1].content})
#   print(f"formatted prompt {formatted_prompt}")
#   llm = ChatOpenAI(model="gpt-4.1").bind_tools([recommended_articles_searching_tool]) 
#   llm_response = llm.invoke(formatted_prompt)
#   llm_message = AIMessage (content=llm_response.content)
#   state["messages"].append(llm_message)

#   print("In first node, LLM output:", llm_response.content)
#   return state  # RETURN the updated st


def user_Input_understander_llm_node(state: State):
  ''' In this node the llm takes the input from the user and analyse the topic or main crux to search in medium for this input'''

  user_message = state["messages"][-1].content if state["messages"] else ""
  system_template = "You are a helpful assistant that can easily deduce the crux of any conversation. from the given user message you have to find the topic or preferred sentence that will be useful for us to search. This search should give the knowledge that the user is looking for. Only return the exact sentence that you framed. Nothing else."
  user_template = f"{user_message}"
  prompt = ChatPromptTemplate.from_messages([
    ("system", system_template),
    ("user", user_template)
  ])

  formatted_prompt = prompt.invoke({"message": state["messages"][-1].content})
  print(f"formatted prompt {formatted_prompt}")
  llm = ChatOpenAI(model="gpt-4.1")
  llm_response = llm.invoke(formatted_prompt)
  llm_message = AIMessage (content=llm_response.content)
  state["messages"].append(llm_message)

  print("In first node, LLM output:", llm_response.content)
  return state  # RETURN the updated st


graph_builder.add_node("user_Input_understander_llm_node",user_Input_understander_llm_node)
graph_builder.add_node("recommended_articles_searching_Node", recommended_articles_searching_Node)
# graph_builder.add_node("tools", tools_node)
graph_builder.add_edge(START,"user_Input_understander_llm_node")
# graph_builder.add_conditional_edges("agent", tools_condition)
graph_builder.add_edge("user_Input_understander_llm_node","recommended_articles_searching_Node")
# graph_builder.add_edge("agent","tools")
graph_builder.add_edge("recommended_articles_searching_Node",END)

graph = graph_builder.compile()

# def stream_graph_updates(user_input: str):
#     for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
#         for value in event.values():
#             print("Assistant:", value["messages"][-1].content)

async def main():
  user_input = input("What's in your mind :")

  async for event in graph.astream({"messages": [HumanMessage(content=user_input)]}):
    print(event)
    for value in event.values():
        print("Output state messages:", value["messages"])

await main()

  # stream_graph_updates(user_input)
