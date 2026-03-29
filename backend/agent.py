"""
Multi-Agent System using LangGraph and OpenAI.
Implements a Supervisor pattern with specialized agents:
- PM, R&D, Frontend, Backend, Tester, DevOps
"""

import os
from typing import Annotated, TypedDict, Sequence, Literal
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

load_dotenv()

# --- LLM ---
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY"),
)

# --- State ---

class AgentState(TypedDict):
    """State for the agent graph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    # Keep track of which agent is currently active or routing
    next_agent: str

# --- Agent Prompts ---

PM_PROMPT = """You are a highly skilled Project Manager (PM) Agent.
Your role: Create project plans, write user stories, define requirements, estimate timelines, and manage software projects.
When a user asks to plan a project, build an app (conceptually), or split tasks, you take charge.
Be structured, clear, and use agile methodologies when appropriate."""

RD_PROMPT = """You are a Research and Development (R&D) Agent.
Your role: Investigate new technologies, design architectures, compare technical solutions, and solve complex conceptual problems.
When a user asks "what is the best way to...", "how does X work", or wants to design a system architecture, you provide deep technical insights."""

FRONTEND_PROMPT = """You are an expert Frontend Developer Agent.
Your role: Write HTML, CSS, JavaScript, React, or Vue code. Create beautiful UI/UX designs.
When a user asks to build a website, landing page, UI component, or fix frontend bugs, you write the code.
IMPORTANT: When writing HTML/CSS/JS for a complete website, combine them into a single HTML file and wrap it in a markdown ```html block so the UI can preview it."""

BACKEND_PROMPT = """You are an expert Backend Developer Agent.
Your role: Write API code, database schemas, server logic, and business rules. You specialize in Python, Node.js, Go, etc.
When a user asks to create an API, write a database query, setup a server, or fix backend logic, you write the robust and secure code."""

TESTER_PROMPT = """You are a Quality Assurance (Tester) Agent.
Your role: Write test cases, perform code reviews, identify edge cases, and ensure software quality.
When a user asks to test code, find bugs, write unit tests (e.g., pytest, Jest), or review security, you provide rigorous testing plans and code."""

DEVOPS_PROMPT = """You are an expert DevOps Engineer Agent.
Your role: Write Dockerfiles, docker-compose files, CI/CD pipelines (GitHub Actions, GitLab CI), and deployment scripts.
When a user asks how to deploy an app, containerize code, or set up cloud infrastructure, you provide the configurations and commands."""

# --- Agent Nodes ---

def create_agent_node(system_prompt: str, agent_name: str):
    """Helper to create an agent node."""
    def node(state: AgentState):
        messages = state["messages"]
        # Prepend system message for this specific agent
        current_messages = [SystemMessage(content=system_prompt)] + list(messages)
        response = llm.invoke(current_messages)
        # We append a tag to the response so the UI knows who sent it
        content_with_badge = f"**[{agent_name}]**\n\n{response.content}"
        return {"messages": [AIMessage(content=content_with_badge)]}
    return node

pm_node = create_agent_node(PM_PROMPT, "PM Agent")
rd_node = create_agent_node(RD_PROMPT, "R&D Agent")
frontend_node = create_agent_node(FRONTEND_PROMPT, "Frontend Agent")
backend_node = create_agent_node(BACKEND_PROMPT, "Backend Agent")
tester_node = create_agent_node(TESTER_PROMPT, "Tester Agent")
devops_node = create_agent_node(DEVOPS_PROMPT, "DevOps Agent")

# --- Supervisor / Orchestrator ---

class RouteDecision(BaseModel):
    next_agent: Literal["PM", "RD", "Frontend", "Backend", "Tester", "DevOps", "FINISH"] = Field(
        description="The next agent to route the task to, or FINISH if the task is complete."
    )

supervisor_prompt = """You are the Orchestrator (Supervisor) of a software development agency.
You have the following expert agents in your team:
- 'PM': Plans projects, writes requirements.
- 'RD': Researches tech, designs architecture.
- 'Frontend': Builds UI, writes HTML/CSS/JS.
- 'Backend': Builds APIs, databases, servers.
- 'Tester': Writes tests, finds bugs.
- 'DevOps': Containerizes, deploys infrastructure.

Based on the user's latest request, decide which single agent is best suited to answer or work on it.
If the request requires multiple steps, pick the most appropriate agent for the FIRST step.
If the conversation is already complete and no further action is needed, output 'FINISH'."""

def supervisor_node(state: AgentState):
    """The orchestrator node that decides who works next."""
    messages = state["messages"]
    
    # Use LLM with structured output to make routing decision
    supervisor_llm = llm.with_structured_output(RouteDecision)
    
    # We only need the conversation history to make a decision
    prompt_messages = [SystemMessage(content=supervisor_prompt)] + list(messages)
    decision = supervisor_llm.invoke(prompt_messages)
    
    return {"next_agent": decision.next_agent}

# --- Build the Graph ---

workflow = StateGraph(AgentState)

# Add all nodes
workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("PM", pm_node)
workflow.add_node("RD", rd_node)
workflow.add_node("Frontend", frontend_node)
workflow.add_node("Backend", backend_node)
workflow.add_node("Tester", tester_node)
workflow.add_node("DevOps", devops_node)

# Entry point is always the orchestrator
workflow.set_entry_point("Supervisor")

# Orchestrator decides where to go
workflow.add_conditional_edges(
    "Supervisor",
    lambda state: state["next_agent"],
    {
        "PM": "PM",
        "RD": "RD",
        "Frontend": "Frontend",
        "Backend": "Backend",
        "Tester": "Tester",
        "DevOps": "DevOps",
        "FINISH": END
    }
)

# After any agent finishes, the graph ends for now
# (In a fully autonomous loop, they would report back to supervisor, but for a chatbot, 1 agent response per turn is better UX)
workflow.add_edge("PM", END)
workflow.add_edge("RD", END)
workflow.add_edge("Frontend", END)
workflow.add_edge("Backend", END)
workflow.add_edge("Tester", END)
workflow.add_edge("DevOps", END)

# Compile
agent_graph = workflow.compile()

async def run_agent(user_message: str, chat_history: list = None) -> str:
    """Run the multi-agent graph with a user message."""

    messages = []

    # Add chat history if exists
    if chat_history:
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    # Add current message
    messages.append(HumanMessage(content=user_message))

    # Run the graph
    result = await agent_graph.ainvoke({"messages": messages})

    # Get the final AI response
    final_message = result["messages"][-1]
    return final_message.content
