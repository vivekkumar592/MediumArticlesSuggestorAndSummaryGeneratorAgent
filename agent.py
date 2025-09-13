from typing import Annotated
from langgraph.graph import StateGraph, END, START
import os
from langgraph.graph.message import add_messages
import http.client
from urllib.parse import quote
#from google.colab import userdata
import asyncio
import aiohttp
import re
import json
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import ToolNode, tools_condition,InjectedState
from langchain_core.messages import HumanMessage, AIMessage


from dotenv import load_dotenv
api_key=os.environ.get("OPENAPI_API_KEY")
rapid_key = os.environ.get("RAPIDAPI_KEY")





class State(TypedDict):
  messages:Annotated[list, add_messages]
  articlesDetails:Annotated[list, add_messages]
  articlesContents:Annotated[list, add_messages]

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.json()

async def recommended_articles_searching_Node(state : State):
  '''This node generates the recommended articles'''
  

  query = quote(state["messages"][-1].content)
  headers = {
    'x-rapidapi-key': rapid_key,
    'x-rapidapi-host': "medium2.p.rapidapi.com"
    }
  url = f"https://medium2.p.rapidapi.com/search/articles?query={query}&count=3"
  
  async with aiohttp.ClientSession(headers=headers) as session:
    res = await fetch(session, url)
  
  data = res
  print(data)
  connections =[];
  articles_id = data["articles"][:10];
  urls = [f"https://medium2.p.rapidapi.com/article/{article_id}" for article_id in articles_id]
  
  result = [];
  async with aiohttp.ClientSession(headers=headers) as session:
      tasks = [fetch(session, url) for url in urls]
      results = await asyncio.gather(*tasks, return_exceptions=True)
      
      result.append(results)
  
  llm_message = AIMessage (content=str(result))
  state["articlesDetails"].append(llm_message)
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

def article_recommender_node(state : State):
  ''' In this node the llm takes the articles details and try to find the 3 most suitable articles to show to the user from articleDetails.'''

  user_message = state["messages"][-1].content if state["messages"] else ""
  system_template = '''You are a precise article recommender
                    Your sole task is to select exactly 3 articles from the provided articleDetails array that best match the user's query based on relevance to title, subtitle, topics, tags, and other metadata.
                    Do not summarize, explain, or add any text beyond the output format."

                    Input:

                    User query: {query}

                    articleDetails: {articlesDetails}

                    Output ONLY in this exact format as a JSON array, nothing else—no introductions, no explanations, no summaries, no additional fields, no markdown, no questions:
                    
                    example_id,another_id,third_id
                    

                    Return exact 3. Extract 'id'  without changes. Strictly adhere to this;"
                    any deviation means failure.'''
  user_template = f"{user_message}"
  prompt = ChatPromptTemplate.from_messages([
    ("system", system_template),
    ("user", user_template)
  ])

  formatted_prompt = prompt.invoke({"query" : state["messages"][1].content, "articlesDetails":state["articlesDetails"]})
  
  llm = ChatOpenAI(model="gpt-4.1")
  llm_response = llm.invoke(formatted_prompt)
  llm_message = HumanMessage (content=llm_response.content)
  state["messages"].append(llm_message)

  print("In third node, LLM output:")
  return state  # RETURN the updated st

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
  
  llm = ChatOpenAI(model="gpt-4.1")
  llm_response = llm.invoke(formatted_prompt)
  llm_message = AIMessage (content=llm_response.content)
  state["messages"].append(llm_message)

  
  return state  # RETURN the updated st


async def medium_article_api_node(state: State):
  ''' In this node the api is called for contents of the articles that is recommended for the user.'''
  articles_id = state["messages"][-1].content.split(",")
  headers = {
    'x-rapidapi-key': rapid_key,
    'x-rapidapi-host': "medium2.p.rapidapi.com"
    }
  urls = [f"https://medium2.p.rapidapi.com/article/{article_id}/content" for article_id in articles_id]
  
  result = [];
  async with aiohttp.ClientSession(headers=headers) as session:
      tasks = [fetch(session, url) for url in urls]
      results = await asyncio.gather(*tasks, return_exceptions=True)
      
      for res in results:
        result.append(res["content"])
  
  
  article_content = HumanMessage (content=str(result))
  state["articlesContents"].append(article_content)
  return state

def llm_node_to_summarize_articles_content_Node(state: State):
  ''' In this node the llm takes the articles content and return the proper summary along witht the main points of the articles.'''

  user_message = state["messages"][-1].content if state["messages"] else ""
  system_template = '''You are a precise summarization expert. Your task is to take a list of article contents provided as input (e.g., [{{article1content}}, {{article2content}}, ...]) and generate a structured summary for each article.

      Each summary must capture the main ideas, key points, and conclusions without adding external information or opinions. Keep technical accuracy intact, maintain objectivity, and provide the summary in the following JSON object format:
      
      text
      {{
        "title": "...",
        "introduction": "...", 
        "bodyHighlights": "...", 
        "conclusion": "...",
        "url": "..." 
      }}
      Input format:
      articles: {{articlesContents}}
      
      Output requirements:
      
      Output strictly a JSON array of such objects, one per article, in the same order.
      
      If an article is empty or invalid, output an object with all fields as "No content to summarize" and "url" as an empty string.
      
      Include a first array element exactly as:
      {{ "summaryCount": N }}
      where N is the number of valid (non-empty) articles summarized.
      
      The entire output must be valid JSON, parsable by json.loads() with no extra text, explanation, or formatting outside this array.'''
  user_template = f"{user_message}"
  prompt = ChatPromptTemplate.from_messages([
    ("system", system_template),
    ("user", user_template)
  ])

  formatted_prompt = prompt.invoke({ "articlesContents":state["articlesContents"]})
  
  llm = ChatOpenAI(model="gpt-4.1")
  llm_response = llm.invoke(formatted_prompt)
  llm_message = HumanMessage (content=llm_response.content)
  state["messages"].append(llm_message)

  print("In summarizer node, LLM output:")
  return state  # RETURN the updated st

graph_builder.add_node("user_Input_understander_llm_node",user_Input_understander_llm_node)
graph_builder.add_node("recommended_articles_searching_Node", recommended_articles_searching_Node)
# graph_builder.add_node("tools", tools_node)
graph_builder.add_edge(START,"user_Input_understander_llm_node")
# graph_builder.add_conditional_edges("agent", tools_condition)
graph_builder.add_edge("user_Input_understander_llm_node","recommended_articles_searching_Node")
# graph_builder.add_edge("agent","tools")
graph_builder.add_edge("recommended_articles_searching_Node","article_recommender_node")
graph_builder.add_node("article_recommender_node",article_recommender_node)
graph_builder.add_edge("article_recommender_node","medium_article_api_node")
graph_builder.add_node("medium_article_api_node",medium_article_api_node)
graph_builder.add_edge("medium_article_api_node","llm_node_to_summarize_articles_content_Node")
graph_builder.add_node("llm_node_to_summarize_articles_content_Node",llm_node_to_summarize_articles_content_Node)
graph_builder.add_edge("llm_node_to_summarize_articles_content_Node", END)

graph = graph_builder.compile()

# def stream_graph_updates(user_input: str):
#     for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
#         for value in event.values():
#             print("Assistant:", value["messages"][-1].content)

async def agent(user_input):
  value = ""
  async for event in graph.astream({"messages": [HumanMessage(content=user_input)]}):
    for value in event.values():
        print("Output state messages:", value["messages"][-1].content)
        value = value["messages"][-1].content
  articles:any = json.loads(value)

# Step 2: Extract title and content for each item
  structured = []
  for i, article in enumerate(articles, start=1):
      # Split by custom `$$` separator
      
      
      structured.append({
          "id": i,
          "title": article.get("title", "No title"),
          "introduction": article.get("introduction", "No introduction"),
          "bodyHighlights": article.get("bodyHighlights", "No bodyHighlights"),
          "conclusion": article.get("conclusion","No Conclusion"),
          "url":article.get("url","No url")
      })
  return structured




