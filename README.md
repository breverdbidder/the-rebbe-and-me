# 🕯️ The Rebbe and Me

**Agentic AI Platform for Torah Study & The Rebbe's Teachings**

## Overview

The Rebbe and Me is an agentic AI ecosystem designed to help users prepare farbrengens (Chassidic gatherings), research the Rebbe's teachings, and connect Torah wisdom to current events through multi-agent orchestration.

## Purpose

- **Farbrengen Preparation:** Generate comprehensive content for Chassidic gatherings
- **Source Research:** Deep search through the Rebbe's sichos, letters, and teachings
- **Current Events Connection:** Link Torah/Chassidus to contemporary situations
- **Multi-Agent Orchestration:** LangGraph-powered workflows for complex Torah research

## Technology Stack

- **Backend:** Python + LangGraph
- **Database:** Supabase (PostgreSQL)
- **AI:** Claude Sonnet 4.5 (orchestration) + Smart Router V5
- **Deployment:** GitHub Actions + Cloudflare Pages
- **Version Control:** GitHub

## Features

### 1. Farbrengen Agent
- Generates structured farbrengen content
- Connects historical events to current situations
- Provides verified sources and citations
- Organizes content by time blocks (5min, 10min, etc.)

### 2. Source Research Agent
- Searches Igrot Kodesh, Sichos, Maamarim
- Provides direct links to chabad.org, hebrewbooks.org
- Cross-references halachic sources (Rambam, Shulchan Aruch)
- Verifies accuracy of citations

### 3. Current Events Agent
- Monitors world events through web search
- Connects to Rebbe's teachings and prophecies
- Identifies Torah perspectives on contemporary issues

### 4. Orchestrator Agent
- Coordinates multi-agent workflows
- Manages token budgets across agents
- Implements checkpointing for long tasks
- Handles parallel agent execution

## Repository Structure

```
the-rebbe-and-me/
├── agents/
│   ├── farbrengen_agent.py       # Farbrengen content generation
│   ├── source_research_agent.py  # Rebbe's teachings search
│   ├── current_events_agent.py   # News + Torah connection
│   └── orchestrator.py           # Multi-agent coordination
├── data/
│   ├── conversations/            # Stored chat history
│   ├── sources/                  # Curated source links
│   └── templates/                # Farbrengen templates
├── db/
│   ├── schema.sql               # Supabase tables
│   └── migrations/              # Database migrations
├── workflows/
│   ├── farbrengen_workflow.py   # LangGraph farbrengen flow
│   └── research_workflow.py     # LangGraph research flow
├── .github/
│   └── workflows/
│       ├── orchestrator.yml     # Auto-orchestration
│       └── deploy.yml           # Auto-deployment
└── docs/
    ├── FARBRENGEN_GUIDE.md     # How to use farbrengen agent
    ├── SOURCE_GUIDE.md         # Guide to source research
    └── API.md                  # API documentation

## First Farbrengen: Chanukah 5785

**Topic:** Nes HaHermon - The Miracle of the Hermon  
**Date:** December 19, 2024  
**Content:** Connection between Chanukah miracles and the capture of the Syrian Hermon without a single bullet

### Key Themes:
1. Historical comparison: 1967 (115 casualties), 1973 (772 casualties), 2024 (0 casualties)
2. Rebbe's doctrine: "Continue to Damascus" - fighting in enemy territory
3. Three Mitzvos: Shleimus HaAretz, Shleimus HaTorah, Shleimus HaAm
4. Annexation policy: Citizenship vs. Residency (East Jerusalem model)

## Database Schema

### Tables:
- `farbrengens` - Stored farbrengen content
- `sources` - Links to Rebbe's teachings
- `conversations` - Chat history with context
- `insights` - Key learnings and patterns
- `agents_logs` - Multi-agent execution logs

## Usage

### Prepare a Farbrengen
```python
from agents.orchestrator import FarbrengenOrchestrator

orchestrator = FarbrengenOrchestrator()
content = orchestrator.prepare_farbrengen(
    topic="Nes HaHermon",
    duration_minutes=10,
    audience="young_bochurim",
    include_sources=True
)
```

### Research a Topic
```python
from agents.source_research_agent import SourceResearchAgent

agent = SourceResearchAgent()
sources = agent.find_sources(
    topic="shleimus_haaretz annexation",
    date_range="1967-1987",
    source_types=["sichos", "igrot_kodesh"]
)
```

## Contributing

This is a personal project for Ariel Shapira, but the architecture can be adapted for other Torah study use cases.

## License

MIT License - Built with ❤️ for Torah study

---

**Created:** December 19, 2024  
**Author:** Ariel Shapira  
**AI Architect:** Claude Sonnet 4.5
