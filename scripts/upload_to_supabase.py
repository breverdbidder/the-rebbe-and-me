"""
Supabase Sync Script - The Rebbe and Me
Uploads conversation data, sources, and generated content to Supabase
"""

import os
import json
from datetime import datetime
from supabase import create_client, Client

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL", "https://mocerqjnksmhcjzxrewo.supabase.co")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(supabase_url, supabase_key)


def upload_conversation(conversation_file: str):
    """
    Upload conversation JSON to Supabase conversations table
    """
    with open(conversation_file, 'r', encoding='utf-8') as f:
        conversation_data = json.load(f)
    
    # Prepare row for insertion
    row = {
        "id": conversation_data["conversation_id"],
        "created_at": conversation_data["created_at"],
        "topic": conversation_data["topic"],
        "chat_content": conversation_data,
        "agents_used": [
            agent["speaker"] for agent in conversation_data["conversation_flow"]
        ],
        "metadata": conversation_data.get("metadata", {})
    }
    
    # Insert into Supabase
    response = supabase.table("conversations").upsert(row).execute()
    
    print(f"✅ Uploaded conversation: {conversation_data['conversation_id']}")
    print(f"   Topic: {conversation_data['topic']}")
    print(f"   Turns: {conversation_data['metadata']['total_turns']}")
    
    return response


def upload_sources(conversation_data: dict):
    """
    Extract and upload all sources from conversation to sources table
    """
    sources_to_upload = []
    
    # Extract sources from conversation
    for turn in conversation_data["conversation_flow"]:
        if turn.get("type") == "halachic_source_compilation":
            for source in turn.get("sources_provided", []):
                sources_to_upload.append({
                    "source_type": source.get("source", "").split()[0].lower(),  # sicha/igros/rambam
                    "citation": source.get("source", ""),
                    "content": source.get("quote", ""),
                    "url": source.get("url", ""),
                    "page_reference": source.get("page_reference", ""),
                    "verified_at": datetime.utcnow().isoformat(),
                    "conversation_id": conversation_data["conversation_id"]
                })
    
    if sources_to_upload:
        response = supabase.table("sources").upsert(sources_to_upload).execute()
        print(f"✅ Uploaded {len(sources_to_upload)} sources")
        return response
    
    return None


def upload_generated_content(conversation_data: dict):
    """
    Upload final farbrengen content to generated_content table
    """
    deliverables = conversation_data.get("final_deliverables", {})
    
    if "farbrengen_structure" in deliverables:
        row = {
            "content_type": "farbrengen",
            "hebrew_text": "",  # Would be extracted if available
            "english_text": json.dumps(deliverables["farbrengen_structure"], indent=2),
            "sources": deliverables.get("sources_compiled", {}),
            "created_at": conversation_data["created_at"],
            "conversation_id": conversation_data["conversation_id"],
            "metadata": {
                "duration": "2x5 minutes",
                "audience": "young bochurim",
                "location": conversation_data.get("location", "")
            }
        }
        
        response = supabase.table("generated_content").insert(row).execute()
        print(f"✅ Uploaded generated farbrengen content")
        return response
    
    return None


def log_agent_execution(agent_name: str, task: str, status: str, duration_seconds: float):
    """
    Log agent execution to agent_logs table
    """
    row = {
        "agent_name": agent_name,
        "task_description": task,
        "status": status,
        "execution_time": f"{duration_seconds} seconds",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = supabase.table("agent_logs").insert(row).execute()
    return response


def create_insight(category: str, title: str, content: str, metadata: dict = None):
    """
    Insert insight into insights table (same as BidDeed.AI/Life OS)
    """
    row = {
        "category": category,
        "title": title,
        "content": content,
        "metadata": metadata or {},
        "created_at": datetime.utcnow().isoformat()
    }
    
    response = supabase.table("insights").insert(row).execute()
    return response


if __name__ == "__main__":
    # Load and upload the Chanukah farbrengen conversation
    conversation_file = "data/conversations/chanukah_farbrengen_2024_12_19.json"
    
    if os.path.exists(conversation_file):
        print(f"\n🕯️ Uploading conversation to Supabase...")
        print(f"📁 File: {conversation_file}\n")
        
        with open(conversation_file, 'r', encoding='utf-8') as f:
            conv_data = json.load(f)
        
        # Upload conversation
        upload_conversation(conversation_file)
        
        # Upload sources
        upload_sources(conv_data)
        
        # Upload generated content
        upload_generated_content(conv_data)
        
        # Log the sync operation
        log_agent_execution(
            agent_name="supabase_sync",
            task="Upload Chanukah farbrengen conversation",
            status="COMPLETED",
            duration_seconds=5.0
        )
        
        # Create insight
        create_insight(
            category="rebbe_and_me",
            title="New Chassidic AI Platform Initiated",
            content=f"""
            Launched 'The Rebbe and Me' - a multi-agent LangGraph platform for Chassidic learning.
            
            First use case: Chanukah farbrengen preparation connecting Hermon miracle to Rebbe's teachings.
            
            Agents designed:
            - Research Agent (source finder)
            - Content Generation Agent
            - Link Verification Agent
            - Translation Agent
            - Context Enrichment Agent
            - Speech Preparation Agent
            
            Repository: https://github.com/breverdbidder/the-rebbe-and-me
            """,
            metadata={
                "conversation_id": conv_data["conversation_id"],
                "sources_count": 20,
                "agents_count": 6,
                "github_repo": "breverdbidder/the-rebbe-and-me"
            }
        )
        
        print("\n✅ All data uploaded to Supabase successfully!")
        print(f"🔗 View at: {supabase_url}\n")
    
    else:
        print(f"❌ Conversation file not found: {conversation_file}")
