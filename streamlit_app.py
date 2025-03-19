import streamlit as st
import requests
import random
import pandas as pd
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Set page configuration - MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title=">A/B",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Load environment variables
load_dotenv()

# Hide GitHub icon
hide_github_icon = """
<style>
#GithubIcon {
    visibility: hidden;
}
</style>
"""
st.markdown(hide_github_icon, unsafe_allow_html=True)

# Check for API keys
# Try multiple ways to get the API keys
OPENROUTER_API_KEY = None
SUPABASE_URL = None
SUPABASE_KEY = None

# First try Streamlit secrets
try:
    OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception as e:
    st.warning(f"Could not load from Streamlit secrets: {e}")
    # Then try environment variable
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    if OPENROUTER_API_KEY:
        st.success("Found OpenRouter API key in environment variables!")
    if SUPABASE_URL and SUPABASE_KEY:
        st.success("Found Supabase credentials in environment variables!")

# Final check if keys were found
missing_keys = []
if not OPENROUTER_API_KEY:
    missing_keys.append("OPENROUTER_API_KEY")
if not SUPABASE_URL:
    missing_keys.append("SUPABASE_URL")
if not SUPABASE_KEY:
    missing_keys.append("SUPABASE_KEY")

if missing_keys:
    st.error(f"Missing required keys: {', '.join(missing_keys)}")
    st.info("For Streamlit Cloud deployment, make sure to add these secrets in the app settings.")
    # Display more debug info
    st.write("Environment variables available:")
    env_vars = {k: "✓" for k in os.environ.keys()}
    st.json(env_vars)
    
    # Try to access all secrets
    try:
        st.write("Available secrets:")
        st.json({k: "✓" for k in st.secrets.keys()})
    except:
        st.error("No secrets available or couldn't access secrets")

# Initialize Supabase client if credentials are available
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        st.success("Successfully connected to Supabase!")
    except Exception as e:
        st.error(f"Failed to connect to Supabase: {str(e)}")

# Define CSS for retro styling
retro_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono&display=swap');
    
    /* Hide GitHub icon */
    #GithubIcon {
        visibility: hidden;
    }
    
    .retro-container {
        font-family: 'Space Mono', monospace;
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        background-color: #f5f3ef;
        border-radius: 8px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    
    .header {
        text-align: center;
        color: #FF6B6B;
        margin-bottom: 30px;
    }
    
    .answer-container {
        background-color: #ffffff;
        border-radius: 6px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #4ECDC4;
    }
    
    .answer-container.model-a {
        border-left: 4px solid #FF6B6B;
    }
    
    .answer-container.model-b {
        border-left: 4px solid #4ECDC4;
    }
    
    .vote-button {
        background-color: #FFE66D;
        color: #333;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        font-family: 'Space Mono', monospace;
        transition: background-color 0.3s;
    }
    
    .vote-button:hover {
        background-color: #FFC857;
    }
    
    .leaderboard {
        margin-top: 30px;
    }
    
    .prompt-input {
        border: 2px solid #4ECDC4;
        border-radius: 4px;
        padding: 10px;
        font-family: 'Space Mono', monospace;
    }
    
    .section-divider {
        height: 4px;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        margin: 30px 0;
        border-radius: 2px;
    }
    
    .retro-header {
        font-size: 32px;
        letter-spacing: 1px;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    
    .retro-subheader {
        font-size: 14px;
        color: #666;
        margin-bottom: 20px;
    }
</style>
"""

# Inject custom CSS
st.markdown(retro_css, unsafe_allow_html=True)

# Constants
MODELS = {
    "A": {
        "id": "openai/chatgpt-4o-latest",
        "system_message": "",
        "display_name": "Model A"
    },
    "B": {
        "id": "openai/gpt-4o-mini",
        "system_message": "Be terse. Use plain texts, no lists or bullet points. Make you answers engaging and interesting, but terse. Never lecture or patronize the user or give general advices everyone knows.",
        "display_name": "Model B"
    }
}

# Functions to interact with Supabase
def get_model_stats():
    if not supabase:
        return {"A": {"wins": 0, "total": 0}, "B": {"wins": 0, "total": 0}}
    
    try:
        # Get counts from votes table
        response = supabase.table('votes').select('winner').execute()
        votes = response.data
        
        # Calculate stats
        stats = {"A": {"wins": 0, "total": 0}, "B": {"wins": 0, "total": 0}}
        
        for vote in votes:
            winner = vote['winner']
            loser = 'B' if winner == 'A' else 'A'
            
            stats[winner]['wins'] += 1
            stats[winner]['total'] += 1
            stats[loser]['total'] += 1
            
        return stats
    except Exception as e:
        st.error(f"Error fetching model stats: {str(e)}")
        return {"A": {"wins": 0, "total": 0}, "B": {"wins": 0, "total": 0}}

def get_recent_votes(limit=5):
    if not supabase:
        return []
    
    try:
        response = supabase.table('votes').select('*').order('created_at', desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching recent votes: {str(e)}")
        return []

def record_vote_in_supabase(winner, prompt):
    if not supabase:
        st.error("Cannot record vote: No connection to Supabase")
        return False
    
    loser = "B" if winner == "A" else "A"
    
    try:
        # Record vote in Supabase
        supabase.table('votes').insert({
            'prompt': prompt,
            'winner': winner,
            'loser': loser,
            'winner_model': MODELS[winner]['id'],
            'loser_model': MODELS[loser]['id']
        }).execute()
        return True
    except Exception as e:
        st.error(f"Error recording vote: {str(e)}")
        return False

# Function to call API for LLM response
def get_llm_response(prompt, model_info):
    # Check if API key is available
    if not OPENROUTER_API_KEY:
        return "Error: OpenRouter API key is missing. Please add it to your environment variables or app secrets."
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.app",  # Add referer for OpenRouter tracking
        "X-Title": "A/B Testing App"  # Add title for OpenRouter tracking
    }
    
    payload = {
        "model": model_info["id"],
        "messages": [
            {"role": "system", "content": model_info["system_message"]},
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        st.write(f"Calling API with model: {model_info['id']}")
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60  # Add timeout
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            error_msg = f"Error calling LLM API: {response.status_code} - {response.reason}"
            st.error(error_msg)
            st.json(response.json())  # Show the full error response
            return f"Error: {response.status_code} - {response.reason}. Check console for details."
    except Exception as e:
        error_msg = f"Exception when calling API: {str(e)}"
        st.error(error_msg)
        return f"Error: Failed to connect to OpenRouter API. {str(e)}"

# App state in session state
if 'has_voted' not in st.session_state:
    st.session_state.has_voted = False

if 'responses' not in st.session_state:
    st.session_state.responses = {"A": "", "B": ""}

if 'display_order' not in st.session_state:
    # Randomize which model appears first (left) and second (right)
    st.session_state.display_order = random.sample(["A", "B"], 2)

# Helper functions
def record_vote(winner):
    success = record_vote_in_supabase(winner, st.session_state.prompt)
    if success:
        st.session_state.has_voted = True
        return True
    return False

def reset_test():
    st.session_state.has_voted = False
    st.session_state.prompt = ""
    st.session_state.responses = {"A": "", "B": ""}
    st.session_state.display_order = random.sample(["A", "B"], 2)

# Main app layout
st.markdown('<div class="retro-container">', unsafe_allow_html=True)
st.markdown('<div class="header">', unsafe_allow_html=True)
st.markdown('<h1 class="retro-header">>A/B</h1>', unsafe_allow_html=True)
st.markdown('<p class="retro-subheader">Compare AI responses. Vote for your favorite. See which model wins.</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Prompt input
with st.form("prompt_form"):
    st.text_area("Enter your prompt", key="prompt", height=100)
    submitted = st.form_submit_button("Get Responses")
    
    if submitted and st.session_state.prompt:
        # Check API key before making request
        if not OPENROUTER_API_KEY:
            st.error("Cannot proceed: API key is missing. Please add your OpenRouter API key.")
        else:
            with st.spinner("Getting responses from both models..."):
                # Get responses from both models
                try:
                    st.session_state.responses["A"] = get_llm_response(st.session_state.prompt, MODELS["A"])
                    st.session_state.responses["B"] = get_llm_response(st.session_state.prompt, MODELS["B"])
                    
                    # Check if responses contain error messages
                    if any(response.startswith("Error:") for response in st.session_state.responses.values()):
                        st.error("One or both models failed to respond. Please check error messages above.")
                    else:
                        st.session_state.has_voted = False
                except Exception as e:
                    st.error(f"Failed to get responses: {str(e)}")

# Display responses if available
if st.session_state.responses["A"] and st.session_state.responses["B"]:
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # Display in randomized order
    col1, col2 = st.columns(2)
    
    for i, pos in enumerate(["left", "right"]):
        model_key = st.session_state.display_order[i]
        display_name = f"Response {pos.capitalize()}"
        
        with col1 if pos == "left" else col2:
            st.markdown(f'<div class="answer-container model-{model_key.lower()}">', unsafe_allow_html=True)
            st.markdown(f"### {display_name}")
            st.markdown(st.session_state.responses[model_key])
            st.markdown('</div>', unsafe_allow_html=True)
            
            if not st.session_state.has_voted:
                if st.button(f"Vote for {display_name}", key=f"vote_{pos}"):
                    record_vote(model_key)
                    st.success(f"Vote recorded for {display_name}!")
                    st.rerun()

# After voting, allow user to start a new test
if st.session_state.has_voted:
    if st.button("Start New Test"):
        reset_test()
        st.rerun()

# Leaderboard section
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="leaderboard">', unsafe_allow_html=True)
st.markdown("## 📊 Leaderboard")

# Get stats from Supabase
stats = get_model_stats()
total_votes = stats["A"]["total"] + stats["B"]["total"]

if total_votes > 0:
    model_a_win_rate = (stats["A"]["wins"] / stats["A"]["total"]) * 100 if stats["A"]["total"] > 0 else 0
    model_b_win_rate = (stats["B"]["wins"] / stats["B"]["total"]) * 100 if stats["B"]["total"] > 0 else 0
    
    # Create DataFrame for leaderboard
    leaderboard_data = {
        "Model": [MODELS["A"]["id"], MODELS["B"]["id"]],
        "Wins": [stats["A"]["wins"], stats["B"]["wins"]],
        "Total Votes": [stats["A"]["total"], stats["B"]["total"]],
        "Win Rate": [f"{model_a_win_rate:.1f}%", f"{model_b_win_rate:.1f}%"]
    }
    
    leaderboard_df = pd.DataFrame(leaderboard_data)
    st.dataframe(leaderboard_df, use_container_width=True)
    
    # Visual representation of win rates
    st.markdown("### Win Rate Comparison")
    st.progress(model_a_win_rate / 100)
    st.write(f"Model A - {model_a_win_rate:.1f}%")
    st.progress(model_b_win_rate / 100)
    st.write(f"Model B - {model_b_win_rate:.1f}%")
    
    # Recent votes
    recent_votes = get_recent_votes()
    if recent_votes:
        st.markdown("### Recent Votes")
        
        for vote in recent_votes:
            prompt = vote.get('prompt', '')
            winner = vote.get('winner', '')
            st.markdown(f"**Prompt:** {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
            st.markdown(f"**Winner:** Model {winner} ({MODELS[winner]['id']})")
            st.markdown("---")
else:
    st.info("No votes recorded yet. Be the first to compare and vote!")

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
