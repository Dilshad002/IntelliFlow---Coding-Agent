import os
import subprocess
from typing import TypedDict
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

class AgentState(TypedDict):
    user_prompt: str
    code: str
    output: str
    error: str
    attempts: int
    success: bool

def execute_code(code: str) -> dict:
    try:
        result = subprocess.run(['python', '-c', code], 
        capture_output=True, text=True, timeout=10)
    except subprocess.TimeoutExpired:
        return {"output": "", "error": "Code execution timed out after 10 seconds"}
    out = {"output": result.stdout, "error": result.stderr}
    return out

llm = ChatGroq(model="openai/gpt-oss-120b", api_key=os.getenv("GROQ_API_KEY"))
sm = '''Return only Python code. No markdown, no backticks, no explanation, no preamble, and
     only use standard built in libraries like sys, os, math, random, itertools, collections, string, re, datetime, etc'''

def write_code(state: AgentState) -> AgentState:
    user = state["user_prompt"]
    print(f"\nGenerating code for {user}")
    messages = [
        SystemMessage(content=sm),
        HumanMessage(content=user)
    ]
    response = llm.invoke(messages)
    state["code"] = response.content
    return state

def run_code(state: AgentState) -> AgentState:
    print(f"\n[Attempt {state['attempts'] + 1}] Running code...")
    result = execute_code(state["code"])
    state["output"] = result["output"]
    state["error"] = result["error"]
    state["attempts"] += 1
    return state

def evaluate(state: AgentState) -> AgentState:
    if state["error"] == "" and state["output"] != "":
        state["success"] = True
    else:
        state["success"] = False
    print(f"Output success: {state['success']}[Attend: {state['attempts']}]")
    return state

def fix_code(state: AgentState) -> AgentState:
    if "timed out" in state["error"]:
        print("Fixing code due to timeout error")
        user = f"i wanted to do {state['user_prompt']}, and you gave me the code {state['code']}, and it ran infinitely and timed out with  the error {state['error']}.Rewrite it without infinite loops or expensive recursive calls."
    else:
        print(f"Fixing code for error {state['error']}")
        user= f"i wanted to do {state['user_prompt']}, and you gave me the code {state['code']}, and it gave the error {state['error']}"
    messages = [
        SystemMessage(content=sm),
        HumanMessage(content=user)
    ]
    response = llm.invoke(messages)
    state["code"] = response.content
    return state

graph = StateGraph(AgentState)

graph.add_node("write_code", write_code)
graph.add_node("run_code", run_code)
graph.add_node("evaluate", evaluate)
graph.add_node("fix_code", fix_code)

graph.set_entry_point("write_code")

graph.add_edge("write_code", "run_code")
graph.add_edge("run_code", "evaluate")
graph.add_edge("fix_code", "run_code")

graph.add_conditional_edges("evaluate", lambda state: END if state['success'] else (END if state['attempts'] >= 5 else "fix_code"))

app = graph.compile()

if __name__ == "__main__":
    user_input = input("Enter a coding problem: ")
    result = app.invoke({
        "user_prompt": user_input,
        "code": "",
        "output": "",
        "error": "",
        "attempts": 0,
        "success": False
    })
    print("\n--- Final Code ---")
    print(result["code"])
    print("\n--- Output ---")
    print(result["output"])