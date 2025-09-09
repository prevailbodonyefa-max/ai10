import streamlit as st
import openai
import os
import time
from typing import List, Dict

# Page configuration
st.set_page_config(
    page_title="My AI Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Application title and description
st.title("My AI Assistant")
st.caption("Powered by OpenAI GPT API")

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
    </style>
    """, unsafe_allow_html=True)

apply_custom_theme()

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Function to initialize OpenAI client with error handling
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
def get_ai_response(client, messages: List[Dict], model: str = "gpt-3.5-turbo") -> str:
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

# Main chat interface
def main():
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

# Run the main function
if __name__ == "__main__":
    main()
