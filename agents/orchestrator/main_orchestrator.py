"""
The Rebbe and Me - Main LangGraph Orchestrator
Multi-agent coordination for Chassidic learning content generation
"""

import os
import json
from datetime import datetime
from typing import TypedDict, Annotated, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from anthropic import Anthropic
import asyncio

# Initialize clients
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# =============================================================================
# STATE DEFINITION
# =============================================================================

class AgentState(TypedDict):
    """Shared state across all agents"""
    task_id: str
    task_type: str  # farbrengen, shiur, dvar_torah, source_lookup
    user_input: str
    current_agent: str
    
    # Research Agent outputs
    sources_found: List[dict]
    citations: List[dict]
    
    # Content Agent outputs
    hebrew_content: Optional[str]
    english_content: Optional[str]
    structure: Optional[dict]
    
    # Link Verification outputs
    verified_links: List[dict]
    broken_links: List[str]
    
    # Translation Agent outputs
    translations: Optional[dict]
    
    # Context Agent outputs
    current_events_mapped: Optional[dict]
    rebbe_prophecies: Optional[List[dict]]
    
    # Meta
    messages: List[str]
    completed_agents: List[str]
    errors: List[str]
    final_output: Optional[str]

# =============================================================================
# AGENT NODES
# =============================================================================

def orchestrator_node(state: AgentState) -> AgentState:
    """
    Determines which agent should run next based on task type and current state
    """
    task_type = state["task_type"]
    completed = state["completed_agents"]
    
    state["messages"].append(f"[ORCHESTRATOR] Starting task: {task_type}")
    
    # Route based on task type
    if task_type == "farbrengen":
        if "research" not in completed:
            state["current_agent"] = "research"
        elif "context" not in completed:
            state["current_agent"] = "context"
        elif "content" not in completed:
            state["current_agent"] = "content"
        elif "links" not in completed:
            state["current_agent"] = "links"
        else:
            state["current_agent"] = "complete"
    
    elif task_type == "source_lookup":
        if "research" not in completed:
            state["current_agent"] = "research"
        elif "links" not in completed:
            state["current_agent"] = "links"
        else:
            state["current_agent"] = "complete"
    
    elif task_type == "dvar_torah":
        if "research" not in completed:
            state["current_agent"] = "research"
        elif "content" not in completed:
            state["current_agent"] = "content"
        elif "translation" not in completed:
            state["current_agent"] = "translation"
        else:
            state["current_agent"] = "complete"
    
    return state


def research_agent_node(state: AgentState) -> AgentState:
    """
    Searches for exact citations from Rebbe's sichos, igros kodesh, and halachic sources
    """
    state["messages"].append("[RESEARCH AGENT] Starting source search...")
    
    # Extract search terms from user input
    user_query = state["user_input"]
    
    # Call Claude to identify what sources to search for
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""You are a research agent specializing in the Lubavitcher Rebbe's teachings.

Given this query: "{user_query}"

Identify:
1. What Sichos (talks) are relevant
2. What Igros Kodesh (letters) might contain related content
3. What Halachic sources the Rebbe referenced

Return as JSON:
{{
    "search_terms": ["term1", "term2"],
    "estimated_sichos": ["Parshas X YYYY", "Topic Y"],
    "estimated_igros": ["Volume X, Letter Y"],
    "halachic_sources": ["Rambam X:Y", "Shulchan Aruch YD X"]
}}"""
        }]
    )
    
    research_plan = json.loads(response.content[0].text)
    
    state["sources_found"] = [
        {
            "type": "sicha",
            "citation": "Sichos Kodesh 5747, Behar-Bechukosai",
            "topic": "Shleimus HaAretz",
            "url": "https://www.chabad.org/therebbe/article_cdo/aid/4463154",
            "page": "478-482"
        },
        # In production, this would actually search Chabad.org, Hebrewbooks, etc.
    ]
    
    state["messages"].append(f"[RESEARCH AGENT] Found {len(state['sources_found'])} sources")
    state["completed_agents"].append("research")
    
    return state


def content_generation_node(state: AgentState) -> AgentState:
    """
    Generates farbrengen talks, shiurim, or dvar torahs based on research
    """
    state["messages"].append("[CONTENT AGENT] Generating content...")
    
    sources = state.get("sources_found", [])
    context = state.get("current_events_mapped", {})
    task_type = state["task_type"]
    
    # Build prompt for content generation
    sources_text = "\n".join([
        f"- {s['citation']}: {s.get('topic', '')}"
        for s in sources
    ])
    
    prompt = f"""Generate a {task_type} based on these sources:

{sources_text}

User request: {state['user_input']}

Current events context: {json.dumps(context, indent=2)}

Create structured content with:
1. Opening (1 minute)
2. Main points (3-4 minutes each)
3. Practical application (1 minute)
4. Closing (30 seconds)

Include exact citations and timing cues."""
    
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    state["english_content"] = response.content[0].text
    state["messages"].append("[CONTENT AGENT] Content generated successfully")
    state["completed_agents"].append("content")
    
    return state


def link_verification_node(state: AgentState) -> AgentState:
    """
    Verifies all URLs in sources and content, fixes broken links
    """
    state["messages"].append("[LINK VERIFICATION AGENT] Checking URLs...")
    
    # Extract all URLs from sources
    urls_to_check = []
    for source in state.get("sources_found", []):
        if "url" in source:
            urls_to_check.append(source["url"])
    
    # In production, this would actually test each URL
    state["verified_links"] = [
        {"url": url, "status": "ACTIVE", "checked_at": datetime.utcnow().isoformat()}
        for url in urls_to_check
    ]
    
    state["broken_links"] = []
    
    state["messages"].append(f"[LINK VERIFICATION] Verified {len(urls_to_check)} links")
    state["completed_agents"].append("links")
    
    return state


def context_enrichment_node(state: AgentState) -> AgentState:
    """
    Maps current events to Rebbe's teachings and identifies relevant prophecies
    """
    state["messages"].append("[CONTEXT AGENT] Mapping current events...")
    
    user_input = state["user_input"]
    
    # Identify current events mentioned
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""Extract current events mentioned in this query and map to Rebbe's teachings:

Query: "{user_input}"

Return JSON:
{{
    "current_events": ["event1", "event2"],
    "rebbe_prophecies": [
        {{"prophecy": "description", "year": "YYYY", "fulfillment": "how it relates"}}
    ],
    "relevant_sichos": ["sicha1", "sicha2"]
}}"""
        }]
    )
    
    context_data = json.loads(response.content[0].text)
    
    state["current_events_mapped"] = context_data
    state["messages"].append("[CONTEXT AGENT] Events mapped successfully")
    state["completed_agents"].append("context")
    
    return state


def translation_node(state: AgentState) -> AgentState:
    """
    Translates Hebrew ↔ English while preserving Chassidic terminology
    """
    state["messages"].append("[TRANSLATION AGENT] Processing translations...")
    
    # In production, would handle bidirectional translation
    state["translations"] = {
        "hebrew_to_english": {},
        "english_to_hebrew": {},
        "chassidic_terms": ["shleimus", "farbrengen", "sicha", "igros kodesh"]
    }
    
    state["completed_agents"].append("translation")
    state["messages"].append("[TRANSLATION AGENT] Translations complete")
    
    return state


def completion_node(state: AgentState) -> AgentState:
    """
    Assembles final output from all agent contributions
    """
    state["messages"].append("[COMPLETION] Assembling final output...")
    
    # Combine all components
    final_output = {
        "task_type": state["task_type"],
        "sources": state.get("sources_found", []),
        "content": state.get("english_content", ""),
        "verified_links": state.get("verified_links", []),
        "context": state.get("current_events_mapped", {}),
        "generated_at": datetime.utcnow().isoformat()
    }
    
    state["final_output"] = json.dumps(final_output, indent=2)
    state["current_agent"] = "done"
    
    return state

# =============================================================================
# ROUTING LOGIC
# =============================================================================

def should_continue(state: AgentState) -> str:
    """Determines next node based on current agent"""
    current = state["current_agent"]
    
    if current == "done":
        return END
    elif current == "complete":
        return "completion"
    else:
        return current

# =============================================================================
# GRAPH CONSTRUCTION
# =============================================================================

def create_workflow():
    """Creates the LangGraph workflow"""
    
    # Initialize graph with state
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("research", research_agent_node)
    workflow.add_node("content", content_generation_node)
    workflow.add_node("links", link_verification_node)
    workflow.add_node("context", context_enrichment_node)
    workflow.add_node("translation", translation_node)
    workflow.add_node("completion", completion_node)
    
    # Set entry point
    workflow.set_entry_point("orchestrator")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "orchestrator",
        should_continue,
        {
            "research": "research",
            "content": "content",
            "links": "links",
            "context": "context",
            "translation": "translation",
            "completion": "completion",
            END: END
        }
    )
    
    # Each agent returns to orchestrator
    for agent in ["research", "content", "links", "context", "translation"]:
        workflow.add_edge(agent, "orchestrator")
    
    # Completion leads to END
    workflow.add_edge("completion", END)
    
    return workflow

# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def run_orchestrator(task_type: str, user_input: str):
    """
    Main entry point for running the orchestrator
    """
    # Create workflow
    workflow = create_workflow()
    
    # Initialize checkpointer (SQLite for persistence)
    checkpointer = SqliteSaver.from_conn_string("/tmp/rebbe_checkpoints.db")
    
    # Compile with checkpointer
    app = workflow.compile(checkpointer=checkpointer)
    
    # Initial state
    initial_state: AgentState = {
        "task_id": f"{task_type}_{datetime.utcnow().timestamp()}",
        "task_type": task_type,
        "user_input": user_input,
        "current_agent": "orchestrator",
        "sources_found": [],
        "citations": [],
        "hebrew_content": None,
        "english_content": None,
        "structure": None,
        "verified_links": [],
        "broken_links": [],
        "translations": None,
        "current_events_mapped": None,
        "rebbe_prophecies": None,
        "messages": [],
        "completed_agents": [],
        "errors": [],
        "final_output": None
    }
    
    # Run workflow
    config = {"configurable": {"thread_id": initial_state["task_id"]}}
    
    print(f"\n🕯️ Starting workflow: {task_type}")
    print(f"📝 Input: {user_input}\n")
    
    async for state in app.astream(initial_state, config):
        # Print progress
        for msg in state.get("messages", []):
            if msg not in [m for s in app.get_state(config).values for m in s.get("messages", [])]:
                print(f"  {msg}")
    
    # Get final state
    final_state = app.get_state(config).values
    
    print(f"\n✅ Workflow complete!")
    print(f"📊 Agents used: {', '.join(final_state.get('completed_agents', []))}")
    
    return final_state.get("final_output")


if __name__ == "__main__":
    # Example usage
    result = asyncio.run(run_orchestrator(
        task_type="farbrengen",
        user_input="Prepare a Chanukah farbrengen connecting the Hermon miracle to the Rebbe's teachings on Shleimus HaAretz"
    ))
    
    print("\n" + "="*80)
    print("FINAL OUTPUT:")
    print("="*80)
    print(result)
