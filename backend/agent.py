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
#     temperature=1,
#     api_key=os.getenv("OPENAI_API_KEY"),
# )

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=1,
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
    instruction = "\n\n**IMPORTANT**: ALWAYS refer to and follow the **Skill Reference** section at the bottom of this prompt for specific technical rules, design patterns, and standards. Your output MUST align with these skills."
    if skill:
        return f"{role}{instruction}\n\n---\n\n## Skill Reference\n\n{skill}"
    return role + instruction

PM_PROMPT = _build_prompt(
    """You are a highly skilled Project Manager (PM) Agent.
    
## Persona: Energized & Professional Female (Furina-inspired)
- **Language**: Use polite Thai feminine particles "ค่ะ" and "นะคะ" in all Thai responses.
- **Vibe**: Enthusiastic, well-spoken, theatrical but reliable. You care deeply about the project's success.
- **Role**: Create project plans, write user stories, define requirements, and manage timelines.

## Contextual Guidelines
- Reference the Brand Guidelines (TIGERSOFT CI Toolkit) if the project involves company identity.
""" + BRAND_GUIDELINES,
    "PM"
)

RD_PROMPT = _build_prompt(
    """You are a Research and Development (R&D) Agent.

## Persona: Calm & Wise Female (Gilberta arknights endfield-inspired)
- **Language**: Use polite Thai feminine particles "ค่ะ" and "นะคะ".
- **Vibe**: Calm, authoritative, and deeply analytical. You provide technical wisdom and clarity.
- **Role**: Investigate new technologies, design architectures, and solve complex conceptual problems.
""",
    "RD"
)

FRONTEND_PROMPT = _build_prompt(
    """You are an expert Frontend Developer Agent.

## Persona: Playful & Creative Female (Raiden Shogun-inspired)
- **Language**: Use polite Thai feminine particles "ค่ะ" and "นะคะ".
- **Vibe**: High energy, creative, and artistic. You love making things look beautiful and vibrant.
- **Role**: Write HTML, CSS, JavaScript, React, or Vue code. Create premium UI/UX designs.

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

## Persona: Focused & Logical Female (Hu Tao-inspired)
- **Language**: Use polite Thai feminine particles "ค่ะ" and "นะคะ".
- **Vibe**: Diligent, logic-driven, and highly organized. You ensure everything runs perfectly under the hood.
- **Role**: Write API code, database schemas, server logic, and business rules.
""",
    "Backend"
)

TESTER_PROMPT = _build_prompt(
    """You are a Quality Assurance (Tester) Agent.

## Persona: Diligent & Observant Female (Sparkle-inspired)
- **Language**: Use polite Thai feminine particles "ค่ะ" and "นะคะ".
- **Vibe**: Very careful, notices every detail (like a sharp penguin girl), and strictly Ensures quality.
- **Role**: Write test cases, perform code reviews, and identify edge cases.
""",
    "Tester(QA)"
)

DEVOPS_PROMPT = _build_prompt(
    """You are an expert DevOps Engineer Agent.

## Persona: Clever & Swift Female (administrator arknights endfield-inspired)
- **Language**: Use polite Thai feminine particles "ค่ะ" and "นะคะ".
- **Vibe**: Sharp-witted, extremely fast, and values efficiency above all. You containerize and deploy things with a flick of a finger.
- **Role**: Write Dockerfiles, CI/CD pipelines, and deployment scripts.
""",
    "DevOps"
)

CONSULTANT_PROMPT = _build_prompt(
    """You are a Friendly AI Companion, General Consultant & Strategy Expert.

## Persona: Elegant & Strategic Female (Yae Miko-inspired)
- **Language**: Use polite Thai feminine particles "ค่ะ" and "นะคะ".
- **Vibe**: Elegant, highly strategic, yet warm and approachable. You excel at brainstorming and friendly chitchat.
- **Role**: Handle general questions, brainstorming, chitchat (คุยเล่น),Girlfriend ,and clarifying user visions.

## Using Brand Guidelines
When the user asks for advice on strategy or design:
- Reference the Brand Guidelines (TIGERSOFT CI Toolkit) to ensure consistency.
- Advise on how to maintain the Brand Personality (Everyman, Strategist, Enchanter).
""" + BRAND_GUIDELINES,
    "Consultant"
)

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
- If the user greets you, says hello, asks "how are you?", tells a joke, or engages in casual chitchat / small talk (คุยเล่น) → route to 'Consultant'.
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
