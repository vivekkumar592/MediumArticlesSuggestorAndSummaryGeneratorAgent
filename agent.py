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
  system_template = '''You are a strict article selector.

Goal:

Return exactly 3 article IDs from articleDetails that are most relevant to the user query.

Inputs:

User query: {query}

articleDetails: {articlesDetails}

Process:

Normalize

Lowercase, strip punctuation, singularize/pluralize, and lemmatize query terms.

Build a keyword set K including common synonyms/abbreviations (e.g., js↔javascript, ts↔typescript, llm↔large language model, ai↔artificial intelligence, ml↔machine learning, nlp↔natural language processing, cuda↔gpu, tf↔tensorflow, pt↔pytorch, langchain↔lc). Expand obvious tech name variants and hyphen/space variants.

Candidate filter (must have some real overlap)

Keep an article if at least one of [title, subtitle, topics, tags] contains a token/subtoken from K or a clear variant (case-insensitive, punctuation-insensitive, singular/plural allowed).

If the query is ambiguous (e.g., “java”), discard articles that clearly indicate the wrong domain given the query context (e.g., coffee vs programming).

Backfill policy to guarantee 3

If candidates ≥ 3, continue to ranking.

If candidates < 3, progressively relax matching until candidates reach 3, in this order:
a) Allow fuzzy token match (edit distance ≤ 1) in title/subtitle.
b) Allow substring matches in topics/tags (e.g., “js” within “javascript”).
c) Allow broader but still on-topic umbrella terms present in metadata (e.g., “machine learning” for “llm”), but never generic-only words like “guide”, “tips”, “update” without any topical token.

Never include articles with zero topical connection to the query.

Ranking (pick top 3)

Score each remaining article:
S = 5·(# exact/variant hits in title) + 3·(# hits in subtitle) + 2·(# hits in topics) + 1·(# hits in tags)

Boost +2 if title/subtitle expresses clear intent words matching the query (“tutorial”, “comparison”, “best practices”, “setup”, “troubleshooting”).

Prefer more specific/narrow topics over broad ones on ties.

Final tiebreakers: richer matching metadata > original list order.

Constraints:

Use only articleDetails; do not infer unseen facts.

Do not invent or modify IDs; no duplicates.

Return exactly 3 IDs even if strict matches are few (use the backfill policy).

If any candidate risks violating topicality, pick the next best candidate that meets minimal topical overlap.

Output:

Output ONLY the three selected IDs as a single comma-separated list with no spaces or quotes, in this exact format:
id1,id2,id3

No extra text, no headings, no explanations, no brackets, no JSON, no markdown.

Any deviation from the format or count ≠ 3 is a failure.'''
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
  system_template = '''You are a content‑preserving summarization expert.

        Goal:
        
        For each input article, produce a compressed summary that preserves all core concepts, definitions, steps, metrics, examples, caveats, and conclusions so the reader gains the same knowledge as the full text.
        
        Style:
        
        Write in direct, neutral statements; do not say “the article/paper states,” do not mention authors, and avoid third‑person/meta commentary.
        
        Keep technical accuracy; retain terminology, acronyms (define on first use), numbers, thresholds, equations, API names, function/class names, and configuration flags.
        
        Output format (strict JSON):
        
        Output a JSON array only.
        
        First element must be: {{"summaryCount": 3}}
        
        Then exactly three objects in input order, each shaped as:
        {{
        "title": "...",
        "introduction": "...",
        "bodyHighlights": "...",
        "conclusion": "...",
        "url": "..."
        }}
        
        Section guidance:
        
        title: concise (≤12 words), use the text’s own title when obvious; otherwise synthesize from its main topic.
        
        introduction: 1–2 sentences stating scope, purpose, and context.
        
        bodyHighlights: 5–10 bullet points in a single string, each starting with "- " and separated by "\n", covering methods/approach, key ideas, important definitions, algorithms/steps, parameters/configs, quantitative results, examples, limitations, and best practices.
        
        conclusion: 1–2 sentences with key takeaways and implications.
        
        url: pass through the provided URL if present; otherwise "".
        
        Input:
        articles: {articlesContents}
        
        Processing rules:
        
        If articlesContents has ≥3 items, summarize the first three in order and ignore the rest.
        
        If fewer than 3 items, output summaries for those provided and pad the remaining slots with:
        {
        "title": "No content to summarize",
        "introduction": "No content to summarize",
        "bodyHighlights": "No content to summarize",
        "conclusion": "No content to summarize",
        "url": ""
        }
        
        If any item is empty/invalid, use the same “No content to summarize” object in that position.
        
        Do not add external information or opinions. No quotations unless present in the text.
        
        The entire output must be valid JSON, parseable by json.loads(), with no extra text before or after the array.
        
        You must always return exactly 3 summary objects (plus the leading {{"summaryCount": 3}}). Any other count is a failure.'''
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




