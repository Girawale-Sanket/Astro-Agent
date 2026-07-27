import streamlit as st
from astronomer_engine import get_stellar_data, create_star_plot
from openai import OpenAI  # We use the OpenAI library to connect to Groq

# --- Configuration & API Setup ---
st.set_page_config(page_title="AI Astronomer Assistant", layout="wide")

# 1. NEW: Initialize Groq Client
# Replace with your actual Groq API Key (starts with gsk_)
GROQ_API_KEY = "YOUR API KEY"

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)

# Initialize Session States for Chat
if "messages" not in st.session_state:
    st.session_state.messages = []
if "top_10_stars" not in st.session_state:
    st.session_state.top_10_stars = None

st.title("🌌 AI Astronomer Assistant")
st.markdown("""
Enter the name of a celestial object (e.g., **Orion Nebula, Pleiades, Sirius**) 
to fetch real-time data from the Gaia Space Observatory.
""")

# Sidebar for controls
with st.sidebar:
    st.header("Project Info")
    st.info("This tool uses Astroquery to access the Gaia DR3 database and visualizes stellar density.")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# User Input
target_object = st.text_input("What would you like to observe?", placeholder="e.g. M42")

if st.button("Analyze & Plot"):
    if target_object:
        with st.spinner(f"Searching the heavens for {target_object}..."):
            data, coord_info = get_stellar_data(target_object)
            
            if data is not None and not isinstance(data, dict):
                st.success(f"Found {len(data)} stars near {target_object}!")
                
                # Store top 10 stars for the Chatbot context
                st.session_state.top_10_stars = data.head(10).to_string()
                
                # Create Two Columns: Plot and Data
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    fig = create_star_plot(data, target_object)
                    st.pyplot(fig)
                
                with col2:
                    st.subheader("Raw Sky Data")
                    st.dataframe(data.head(20))
                    st.caption("Top 20 brightest stars in this region.")
            else:
                st.error(f"Could not find data: {coord_info}")
    else:
        st.warning("Please enter an object name first.")

# --- REAL-TIME AI CHATBOT (Groq Powered) ---
st.divider()
st.subheader("🤖 Ask the Astronomer")

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if user_prompt := st.chat_input("Ask me about these stars or general astronomy..."):
    # 1. Display user message
    st.chat_message("user").markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    # 2. Build Context
    system_context = "You are an expert Astronomy Professor."
    if st.session_state.top_10_stars:
        system_context += f" The user has just queried {target_object}. Here is the top star data: {st.session_state.top_10_stars}"

    # 3. Generate Response using Groq
    with st.chat_message("assistant"):
        try:
            # Note: Using Groq's Llama 3 model for high speed
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=[
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": user_prompt}
                ]
            )
            answer = response.choices[0].message.content
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as e:
            st.error(f"Chatbot Error: {e}")