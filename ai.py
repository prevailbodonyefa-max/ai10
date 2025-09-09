# app.py
import streamlit as st
import openai
import hashlib

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(page_title="My AI Assistant", page_icon="🤖", layout="wide")

# ---------------------------
# Utility Functions
# ---------------------------
def make_hash(password: str) -> str:
    """Hash password with SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(username: str, password: str) -> bool:
    """Check login credentials against secrets.toml."""
    if "users" in st.secrets and username in st.secrets["users"]:
        stored_pw_hash = st.secrets["users"][username]
        return make_hash(password) == stored_pw_hash
    return False

def signup_user(username: str, password: str):
    """Show hashed password for adding to secrets.toml."""
    st.info(f"👉 Add this to your secrets.toml:\n\n[users]\n{username} = \"{make_hash(password)}\"")

def generate_ai_response(messages):
    """Call OpenAI API and return assistant reply."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        st.error(f"⚠️ API Error: {e}")
        return None

def render_chat():
    """Render the chat history."""
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        bubble_class = "user-bubble" if role == "user" else "ai-bubble"
        st.markdown(
            f"<div class='chat-bubble {bubble_class}'>{content}</div>",
            unsafe_allow_html=True
        )

# ---------------------------
# CSS Styling
# ---------------------------
st.markdown("""
    <style>
    body {
        background-color: #0D0D0D;
        color: #E6E6FA;
    }
    .chat-bubble {
        padding: 0.6rem 1rem;
        border-radius: 12px;
        margin-bottom: 0.6rem;
        font-size: 1rem;
        max-width: 80%;
        word-wrap: break-word;
    }
    .user-bubble {
        background-color: #5A189A;
        color: white;
        text-align: right;
        margin-left: auto;
    }
    .ai-bubble {
        background-color: #240046;
        color: #E0AAFF;
        text-align: left;
        margin-right: auto;
    }
    .stButton>button {
        background-color: #7B2CBF;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #9D4EDD;
        color: #fff;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------
# Authentication
# ---------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

auth_mode = st.sidebar.radio("🔐 Authentication", ["Login", "Sign Up"])

if not st.session_state.authenticated:
    st.title("🔐 Welcome to My AI Assistant")

    if auth_mode == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if check_password(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("✅ Login successful")
                st.experimental_rerun()
            else:
                st.error("❌ Invalid username or password")

    else:  # Sign Up
        username = st.text_input("Choose Username")
        password = st.text_input("Choose Password", type="password")
        if st.button("Sign Up"):
            if username and password:
                signup_user(username, password)
            else:
                st.error("❌ Please enter username & password")

# ---------------------------
# Main App (after login)
# ---------------------------
if st.session_state.authenticated:
    st.title(f"🤖 My AI Assistant — Hello, {st.session_state.username}!")

    # Load API Key
    try:
        openai.api_key = st.secrets["openai"]["api_key"]
    except Exception:
        st.error("⚠️ No API key found in secrets.")
        st.stop()

    # Initialize Chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Input Area
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input("💬 Type your message:", key="input", placeholder="Ask me anything...")
    with col2:
        send = st.button("Send")

    clear = st.button("🗑️ Clear Chat")
    logout = st.button("🚪 Log Out")

    # Actions
    if clear:
        st.session_state.messages = []
        st.experimental_rerun()

    if logout:
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.experimental_rerun()

    if send and user_input.strip():
        # Save user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        # AI reply
        ai_reply = generate_ai_response(st.session_state.messages)
        if ai_reply:
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})

        # Reset input
        st.session_state.input = ""

    # Render chat
    render_chat()
