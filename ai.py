import streamlit as st
import openai
import hashlib
import json
import os
import time
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Nexus AI Assistant",
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

# AI Assistant name
AI_NAME = "Nexus"

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

# Enhanced OpenAI client initialization with better error handling
def initialize_openai_client():
    """
    Initialize OpenAI client with API key from Streamlit secrets with robust error handling.
    Returns client object or None if initialization fails.
    """
    try:
        # Check if secrets are available
        if not hasattr(st, 'secrets'):
            st.error("Secrets management is not available in this environment.")
            return None
        
        # Try to get API key from Streamlit secrets with multiple access methods
        api_key = None
        
        # Method 1: Direct key access
        if 'OPENAI_API_KEY' in st.secrets:
            api_key = st.secrets['OPENAI_API_KEY']
        # Method 2: Nested key access
        elif 'openai' in st.secrets and 'api_key' in st.secrets.openai:
            api_key = st.secrets.openai.api_key
        # Method 3: Environment variable fallback
        elif 'OPENAI_API_KEY' in os.environ:
            api_key = os.environ['OPENAI_API_KEY']
            st.info("Using OpenAI API key from environment variable.")
        else:
            st.error("""
            OpenAI API key not found. Please configure it in one of these ways:
            
            1. **Streamlit Community Cloud**: Add to your app's secrets in the dashboard
            2. **Local development**: Create a `.streamlit/secrets.toml` file with:
               ```
               OPENAI_API_KEY = "your-openai-api-key-here"
               ```
            3. **Environment variable**: Set OPENAI_API_KEY in your environment
            """)
            return None
        
        if not api_key or api_key.strip() == "":
            st.error("OpenAI API key is empty. Please provide a valid key.")
            return None
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Test the connection with a simple request
        try:
            client.models.list()
        except Exception as test_error:
            st.error(f"API key test failed: {str(test_error)}")
            return None
        
        return client
        
    except Exception as e:
        st.error(f"Error initializing OpenAI client: {str(e)}")
        return None

# Function to get AI response with enhanced error handling
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
        # Show typing indicator
        with st.status("Thinking...", expanded=False) as status:
            # Create chat completion
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            status.update(label="Response ready", state="complete")
        
        return response.choices[0].message.content
        
    except openai.AuthenticationError:
        st.error("""
        Authentication error: Invalid API key. 
        Please check your API key configuration in Streamlit Community Cloud secrets.
        """)
        return None
    except openai.RateLimitError:
        st.error("""
        Rate limit exceeded. Please try again later.
        You might have reached your OpenAI API quota or the rate limit for your account.
        """)
        return None
    except openai.APIConnectionError:
        st.error("""
        Network connection error. Please check your internet connection.
        If this persists, check OpenAI's status page for any ongoing issues.
        """)
        return None
    except openai.APIError as e:
        st.error(f"OpenAI API error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None

# Login/Registration UI
def show_auth_ui():
    """Show authentication UI (login or register)"""
    st.title(f"My {AI_NAME} AI Assistant")
    
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
                if len(password) < 6:
                    st.markdown('<div class="error">Password must be at least 6 characters</div>', unsafe_allow_html=True)
                    return
                
                success, message = register_user(username, password)
                if success:
                    st.markdown(f'<div class="success">{message}</div>', unsafe_allow_html=True)
                    st.session_state.register = False
                    time.sleep(1)  # Brief delay for user to read success message
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

# Main AI assistant UI
def show_assistant_ui():
    """Show the AI assistant interface"""
    # Header with logout button
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title(f"My {AI_NAME} AI Assistant")
        st.caption(f"Welcome, {st.session_state.username}!")
    with col2:
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Initialize OpenAI client with enhanced error handling
    client = initialize_openai_client()
    
    # Show warning if client couldn't be initialized
    if client is None:
        st.warning("""
        The AI assistant functionality is currently unavailable due to missing or invalid API configuration.
        Please check your secrets configuration and try again.
        """)
        
        with st.expander("Secrets Configuration Help"):
            st.markdown("""
            ### Setting Up Secrets on Streamlit Community Cloud
            
            1. Go to your app's dashboard on [Streamlit Community Cloud](https://share.streamlit.io/)
            2. Click on **⋮** (three dots) next to your app
            3. Select **Settings** → **Secrets**
            4. Add your OpenAI API key in the following format:
            
            ```toml
            OPENAI_API_KEY = "your-openai-api-key-here"
            ```
            
            5. Click **Save** to update your secrets
            
            ### Local Development Setup
            
            For local development, create a file `.streamlit/secrets.toml` with:
            
            ```toml
            OPENAI_API_KEY = "your-openai-api-key-here"
            ```
            
            **Important**: Add `.streamlit/secrets.toml` to your `.gitignore` file to prevent accidentally committing secrets to version control.
            """)
    
    # Chat input (only show if client is available)
    if client and (prompt := st.chat_input("What would you like to know?")):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
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
    main()
