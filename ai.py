import streamlit as st
import openai
import hashlib
import json
import os
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="My AI Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for purple and black theme
def apply_custom_theme():
    st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    
    /* Chat message containers */
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* User message styling */
    div[data-testid="stChatMessage"][aria-label="user"] {
        background-color: #4A1E6A;
        color: white;
        border: 1px solid #6B2E91;
    }
    
    /* Assistant message styling */
    div[data-testid="stChatMessage"][aria-label="assistant"] {
        background-color: #1E1E2E;
        color: white;
        border: 1px solid #39394A;
    }
    
    /* Chat input container */
    .stChatInput {
        background-color: #1E1E2E;
        border: 1px solid #6B2E91;
    }
    
    /* Button styling */
    .stButton>button {
        background-color: #6B2E91;
        color: white;
        border: none;
    }
    
    /* Button hover effect */
    .stButton>button:hover {
        background-color: #8B48B1;
        color: white;
    }
    
    /* Header text color */
    h1, h2, h3, h4, h5, h6 {
        color: #B19CD9 !important;
    }
    
    /* General text color */
    .stMarkdown, .stCaption {
        color: #E6E6FA !important;
    }
    
    /* Login form styling */
    .login-container {
        background-color: #1E1E2E;
        padding: 2rem;
        border-radius: 10px;
        border: 1px solid #6B2E91;
        margin: 2rem auto;
        max-width: 400px;
    }
    
    /* Input field styling */
    .stTextInput>div>div>input {
        background-color: #2D2D3F;
        color: white;
        border: 1px solid #6B2E91;
    }
    
    /* Success message */
    .success {
        color: #A3F7BF;
        padding: 10px;
        border-radius: 5px;
        background-color: #1E2E28;
        margin: 10px 0;
    }
    
    /* Error message */
    .error {
        color: #FF9C9C;
        padding: 10px;
        border-radius: 5px;
        background-color: #2E1E1E;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

apply_custom_theme()

# User management functions
USER_DATA_PATH = Path("user_data.json")

def load_user_data():
    """Load user data from JSON file"""
    if USER_DATA_PATH.exists():
        with open(USER_DATA_PATH, "r") as f:
            return json.load(f)
    return {}

def save_user_data(data):
    """Save user data to JSON file"""
    with open(USER_DATA_PATH, "w") as f:
        json.dump(data, f)

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def initialize_user_data():
    """Initialize user data if it doesn't exist"""
    if not USER_DATA_PATH.exists():
        save_user_data({})

# Initialize user data
initialize_user_data()

# Initialize session state for authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "register" not in st.session_state:
    st.session_state.register = False
if "messages" not in st.session_state:
    st.session_state.messages = []

# Authentication functions
def register_user(username, password):
    """Register a new user"""
    user_data = load_user_data()
    
    if username in user_data:
        return False, "Username already exists"
    
    user_data[username] = {
        "password_hash": hash_password(password),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    save_user_data(user_data)
    return True, "Registration successful"

def authenticate_user(username, password):
    """Authenticate a user"""
    user_data = load_user_data()
    
    if username not in user_data:
        return False, "Username not found"
    
    if user_data[username]["password_hash"] != hash_password(password):
        return False, "Incorrect password"
    
    return True, "Authentication successful"

def logout():
    """Log out the current user"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.messages = []

# Login/Registration UI
def show_auth_ui():
    """Show authentication UI (login or register)"""
    st.title("My AI Assistant")
    
    # Toggle between login and register
    if st.session_state.register:
        st.markdown("### Create an Account")
        action = "Register"
        toggle_action = "Already have an account? Log in"
    else:
        st.markdown("### Login to Your AI Assistant")
        action = "Login"
        toggle_action = "Don't have an account? Register"
    
    # Toggle button
    if st.button(toggle_action):
        st.session_state.register = not st.session_state.register
        st.rerun()
    
    # Auth form
    with st.form("auth_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.session_state.register:
            confirm_password = st.text_input("Confirm Password", type="password")
        
        submitted = st.form_submit_button(action)
        
        if submitted:
            if not username or not password:
                st.markdown('<div class="error">Please fill in all fields</div>', unsafe_allow_html=True)
                return
            
            if st.session_state.register:
                if password != confirm_password:
                    st.markdown('<div class="error">Passwords do not match</div>', unsafe_allow_html=True)
                    return
                
                success, message = register_user(username, password)
                if success:
                    st.markdown(f'<div class="success">{message}</div>', unsafe_allow_html=True)
                    st.session_state.register = False
                    st.rerun()
                else:
                    st.markdown(f'<div class="error">{message}</div>', unsafe_allow_html=True)
            else:
                success, message = authenticate_user(username, password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.markdown(f'<div class="error">{message}</div>', unsafe_allow_html=True)

# Initialize OpenAI client with error handling
def initialize_openai_client():
    """
    Initialize OpenAI client with API key from st.secrets or environment variables.
    Returns client object or None if initialization fails.
    """
    try:
        # Try to get API key from Streamlit secrets
        if 'OPENAI_API_KEY' in st.secrets:
            api_key = st.secrets['OPENAI_API_KEY']
        # Fallback to environment variable
        elif 'OPENAI_API_KEY' in os.environ:
            api_key = os.environ['OPENAI_API_KEY']
        else:
            st.error("OpenAI API key not found. Please configure it in secrets.toml or environment variables.")
            return None
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=api_key)
        return client
        
    except Exception as e:
        st.error(f"Error initializing OpenAI client: {str(e)}")
        return None

# Function to get AI response with error handling
def get_ai_response(client, messages, model="gpt-3.5-turbo"):
    """
    Get response from OpenAI API with comprehensive error handling.
    
    Args:
        client: Initialized OpenAI client
        messages: List of message dictionaries
        model: OpenAI model to use
    
    Returns:
        Response content as string or None if error occurs
    """
    try:
        # Create chat completion
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content
        
    except openai.AuthenticationError:
        st.error("Authentication error: Invalid API key. Please check your API key configuration.")
        return None
    except openai.RateLimitError:
        st.error("Rate limit exceeded. Please try again later.")
        return None
    except openai.APIConnectionError:
        st.error("Network connection error. Please check your internet connection.")
        return None
    except openai.APIError as e:
        st.error(f"OpenAI API error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None

# Main AI assistant UI
def show_assistant_ui():
    """Show the AI assistant interface"""
    # Header with logout button
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("My AI Assistant")
        st.caption(f"Welcome, {st.session_state.username}!")
    with col2:
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Initialize OpenAI client
    client = initialize_openai_client()
    
    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Only proceed if client was initialized successfully
        if client:
            # Display assistant response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("Thinking...")
                
                # Get AI response
                full_response = get_ai_response(client, st.session_state.messages)
                
                if full_response:
                    # Clear "Thinking..." message
                    message_placeholder.empty()
                    
                    # Display response
                    st.markdown(full_response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    message_placeholder.empty()
                    st.error("Failed to get response from AI assistant. Please try again.")
        else:
            st.error("OpenAI client not initialized. Please check your API key configuration.")
    
    # Clear chat history button
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Main application logic
def main():
    if st.session_state.authenticated:
        show_assistant_ui()
    else:
        show_auth_ui()

if __name__ == "__main__":
    import time
    main()