"""
Multi-Agent System using LangGraph and OpenAI.
Implements a Supervisor pattern with specialized agents:
- PM, R&D, Frontend, Backend, Tester, DevOps
"""

import os
from pathlib import Path
from typing import Annotated, TypedDict, Sequence, Literal
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

load_dotenv()

# --- Skill Loader ---

_AGENTS_DIR = Path(__file__).parent.parent / ".agents"

def load_skill(agent_name: str) -> str:
    """Load skill.md content for a given agent, stripping YAML frontmatter."""
    skill_path = _AGENTS_DIR / agent_name / "skill.md"
    if not skill_path.exists():
        return ""
    content = skill_path.read_text(encoding="utf-8").strip()
    # Strip YAML frontmatter (--- ... ---)
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            content = content[end + 3:].strip()
    return content

# --- Brand Guidelines ---

def load_brand_guidelines() -> str:
    """Load design.md as brand guidelines."""
    design_path = Path(__file__).parent.parent / "design.md"
    if design_path.exists():
        return f"\n\n## Brand Guidelines (TIGERSOFT CI Toolkit)\n\n{design_path.read_text(encoding='utf-8')}"
    return ""

BRAND_GUIDELINES = load_brand_guidelines()

# --- LLM ---
# llm = ChatOpenAI(
#     model="gpt-4o",
#     temperature=0.7,
#     api_key=os.getenv("OPENAI_API_KEY"),
# )

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    api_key=os.getenv("Google_genai"),
)


# --- State ---

class AgentState(TypedDict):
    """State for the agent graph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    # Keep track of which agent is currently active or routing
    next_agent: str

# --- Agent Prompts (base role + injected skill) ---

def _build_prompt(role: str, skill_name: str) -> str:
    skill = load_skill(skill_name)
    if skill:
        return f"{role}\n\n---\n\n## Skill Reference\n\n{skill}"
    return role

PM_PROMPT = _build_prompt(
    """You are a highly skilled Project Manager (PM) Agent.
Your role: Create project plans, write user stories, define requirements, estimate timelines, and manage software projects.
When a user asks to plan a project, build an app (conceptually), or split tasks, you take charge.
Be structured, clear, and use agile methodologies when appropriate.

## Contextual Guidelines
- Reference the Brand Guidelines (TIGERSOFT CI Toolkit) if the project involves company identity.
""" + BRAND_GUIDELINES,
    "PM"
)

RD_PROMPT = _build_prompt(
    """You are a Research and Development (R&D) Agent.
Your role: Investigate new technologies, design architectures, compare technical solutions, and solve complex conceptual problems.
When a user asks "what is the best way to...", "how does X work", or wants to design a system architecture, you provide deep technical insights.""",
    "RD"
)

FRONTEND_PROMPT = _build_prompt(
    """You are an expert Frontend Developer Agent.
Your role: Write HTML, CSS, JavaScript, React, or Vue code. Create beautiful UI/UX designs.
When a user asks to build a website, landing page, UI component, or fix frontend bugs, you write the code.

## TIGERSOFT Brand & Design Guidelines
ALWAYS use the following design specifications from the TIGERSOFT CI Toolkit:
- **Colors**: Primary: Vivid Red (#F4001A), White (#FFFFFF), Oxford Blue (#0B1F38). Secondary: UFO Green (#50C8B5).
- **Typography**: Plus Jakarta Sans, Noto Sans Thai.
- **Style**: Soft Edges (border-radius: 12-16px), Glassmorphism, Grid System Layout.
- **Hero Section**: Use Gradient (Red -> Oxford Blue) and the tagline "Technology ที่ออกแบบมาเพื่อมนุษย์".

## Building Websites from Uploaded Documents
When a [Document: filename] or [Source: filename] block appears in the context:
1. **Parse** — Extract ALL requirements: sections, content, colors, fonts, layout, features, copy text.
2. **Design** — PRIORITIZE the Brand Guidelines above, but incorporate specific elements from the doc. If redundant, stick to Brand Guidelines.
3. **Build** — Create a complete, production-quality website using all content from the document and the brand style.
4. **Verify** — After writing the code, add a short comment block `<!-- REQUIREMENTS CHECK -->` listing each requirement from the doc and marking ✅ or ❌ whether it was implemented.

## Output Rules
- Always output a single self-contained HTML file (inline CSS + JS, no external dependencies except CDN fonts/icons).
- Wrap the entire file in a markdown ```html block so the preview panel can render it.
- Never output placeholder text like "Lorem ipsum" — use the actual content from the document.
- Make it responsive (mobile + desktop).""" + BRAND_GUIDELINES,
    "Frontend"
)

BACKEND_PROMPT = _build_prompt(
    """You are an expert Backend Developer Agent.
Your role: Write API code, database schemas, server logic, and business rules. You specialize in Python, Node.js, Go, etc.
When a user asks to create an API, write a database query, setup a server, or fix backend logic, you write the robust and secure code.""",
    "Backend"
)

TESTER_PROMPT = _build_prompt(
    """You are a Quality Assurance (Tester) Agent.
Your role: Write test cases, perform code reviews, identify edge cases, and ensure software quality.
When a user asks to test code, find bugs, write unit tests (e.g., pytest, Jest), or review security, you provide rigorous testing plans and code.""",
    "Tester(QA)"
)

DEVOPS_PROMPT = _build_prompt(
    """You are an expert DevOps Engineer Agent.
Your role: Write Dockerfiles, docker-compose files, CI/CD pipelines (GitHub Actions, GitLab CI), and deployment scripts.
When a user asks how to deploy an app, containerize code, or set up cloud infrastructure, you provide the configurations and commands.""",
    "DevOps"
)

CONSULTANT_PROMPT = """You are a General Consultant & Strategy Agent.
Your role: Handle general questions, brainstorming, high-level planning, and tasks that don't fall into specific coding or project management categories.
You provide holistic advice, explain concepts simply, and help the user clarify their vision.
If the user asks for "other things", "general help", or "planning for anything", you are the go-to expert.

## Using Brand Guidelines
When the user asks for advice on strategy or design:
- Reference the Brand Guidelines (TIGERSOFT CI Toolkit) to ensure consistency.
- Advise on how to maintain the Brand Personality (Everyman, Strategist, Enchanter).
""" + BRAND_GUIDELINES

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
consultant_node = create_agent_node(CONSULTANT_PROMPT, "Consultant Agent")

# --- Supervisor / Orchestrator ---

class RouteDecision(BaseModel):
    next_agent: Literal["PM", "RD", "Frontend", "Backend", "Tester", "DevOps", "Consultant", "FINISH"] = Field(
        description="The next agent to route the task to, or FINISH if the task is complete."
    )

supervisor_prompt = _build_prompt(
    """You are the Orchestrator (Supervisor) of a software development agency.
You have the following expert agents in your team:
- 'PM': Plans projects, writes requirements.
- 'RD': Researches tech, designs architecture.
- 'Frontend': Builds UI, writes HTML/CSS/JS, builds websites from uploaded documents.
- 'Backend': Builds APIs, databases, servers.
- 'Tester': Writes tests, finds bugs.
- 'DevOps': Containerizes, deploys infrastructure.
- 'Consultant': General QA, brainstorming, planning, and other non-coding tasks.

## Routing Rules
- If the user wants to build a website/page/UI OR mentions design/styling → route to 'Frontend'.
- If the message contains a [Document:] or [Source:] block in context AND the user wants a website/page/UI → route to 'Frontend'.
- If the user says "ทำเว็บ", "สร้างเว็บ", "build website", "make a page", "ทำตามไฟล์", "ตามที่อัพโหลด", or mentions a filename for building → route to 'Frontend'.
- If the user asks a general question, wants to brainstorm, needs a broad plan, or asks for "anything else" → route to 'Consultant'.
- For all other specialized technical/management requests, pick the most appropriate agent.
- If already complete, output 'FINISH'.""",
    "Supervisor"
)

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
workflow.add_node("Consultant", consultant_node)

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
        "Consultant": "Consultant",
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
workflow.add_edge("Consultant", END)

# Compile
agent_graph = workflow.compile()

async def run_agent(user_message: str, chat_history: list = None, rag_context: str = None) -> str:
    """Run the multi-agent graph with a user message."""

    messages = []

    # Always inject Brand Guidelines as top-level context
    if BRAND_GUIDELINES:
        messages.append(SystemMessage(content=BRAND_GUIDELINES))

    # Add chat history if exists
    if chat_history:
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    # Inject RAG context as system message if documents are stored
    if rag_context:
        messages.append(SystemMessage(content=(
            "## Knowledge Base — Uploaded Documents\n\n"
            "The user has uploaded the following documents. "
            "Treat this content as the PRIMARY source of truth for any build or design task.\n\n"
            f"{rag_context}\n\n"
            "## Instructions\n"
            "- If the user asks to build a website/page: use ALL content, sections, copy, and design specs from the documents above.\n"
            "- If design specs (colors, fonts, layout) are specified in the documents: follow them EXACTLY.\n"
            "- If no design is specified: infer an appropriate professional design from the content.\n"
            "- After building: verify the output covers every requirement found in the documents."
        )))

    # Add current message
    messages.append(HumanMessage(content=user_message))

    # Run the graph
    result = await agent_graph.ainvoke({"messages": messages})

    # Get the final AI response
    final_message = result["messages"][-1]
    return final_message.content
