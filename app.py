import os
import streamlit as st
from datetime import datetime
from groq_client import get_chat_completion
from config import load_config
import pyttsx3
import speech_recognition as sr
import emoji
from googlesearch import search
from PIL import Image
import io
import PyPDF2 
import time  

# Load the environment variables
load_config()

# Set page configuration at the top
st.set_page_config(page_title="LLM Copilot", page_icon="🤖", layout="wide")

# Initialize session state for authentication and app data
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
if 'feedback' not in st.session_state:
    st.session_state['feedback'] = []
if 'rating' not in st.session_state:
    st.session_state['rating'] = None
if 'theme' not in st.session_state:
    st.session_state['theme'] = 'Dark'
if 'speech_input' not in st.session_state:
    st.session_state['speech_input'] = None
if 'user_input' not in st.session_state:
    st.session_state['user_input'] = None
if 'response_in_progress' not in st.session_state:
    st.session_state['response_in_progress'] = False

# Function to apply the theme
def apply_theme(theme):
    if theme == 'Dark':
        st.markdown(
            """
            <style>
            .main {background-color: #0e1117; color: #cfcfcf;}
            .css-1d391kg {background-color: #0e1117; color: #cfcfcf;}
            .st-bd {color: #cfcfcf;}
            .st-az {color: #cfcfcf;}
            .st-cy {color: #cfcfcf;}
            .css-17eq0hr {color: #cfcfcf;}
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            .main {background-color: #ffffff; color: #000000;}
            .css-1d391kg {background-color: #ffffff; color: #000000;}
            .st-bd {color: #000000;}
            .st-az {color: #000000;}
            .st-cy {color: #000000;}
            .css-17eq0hr {color: #000000;}
            </style>
            """,
            unsafe_allow_html=True,
        )

# Authentication
if not st.session_state['authenticated']:
    st.title('Login')
    st.header("Please enter your credentials")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    # Dummy credentials for demonstration purposes
    correct_username = "user"
    correct_email = "user@example.com"
    correct_password = "password123"

    if st.button("Login"):
        if username == correct_username and email == correct_email and password == correct_password:
            st.session_state['authenticated'] = True
            st.success("Login successful!")
        else:
            st.error("Invalid username, email, or password")

# Main app content
if st.session_state['authenticated']:
    # Sidebar for settings
    st.sidebar.title("Settings")
    model_choice = st.sidebar.selectbox('Choose Model', (
        'LLaMA3 8b', 'LLaMA3 70b', 'Mixtral 8x7b', 'Gemma 7b'
    ))

    model_map = {
        'LLaMA3 8b': 'llama3-8b-8192',
        'LLaMA3 70b': 'llama3-70b-8192',
        'Mixtral 8x7b': 'mixtral-8x7b-32768',
        'Gemma 7b': 'gemma-7b-it'
    }

    model = model_map.get(model_choice, 'llama3-8b-8192')

    # Theme selection
    theme_choice = st.sidebar.selectbox('Choose Theme', ['Dark', 'Light'], index=0 if st.session_state['theme'] == 'Dark' else 1)
    st.session_state['theme'] = theme_choice

    # Apply theme
    apply_theme(st.session_state['theme'])

    # Initialize TTS engine
    engine = pyttsx3.init()

    # Speech-to-Text
    if st.sidebar.button("Start Speech Input"):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.sidebar.text("Listening...")
            audio = recognizer.listen(source)
            try:
                text = recognizer.recognize_google(audio)
                st.session_state['speech_input'] = text
                st.sidebar.success(f"Recognized: {text}")
            except sr.UnknownValueError:
                st.sidebar.error("Could not understand audio")
            except sr.RequestError:
                st.sidebar.error("Could not request results")

    # Title and description
    st.title('LLM Copilot with Groq API and Streamlit')
    st.write("This is your AI-powered copilot. Start typing or speak to chat with the model.")

    # Welcome message
    if not st.session_state['user_input'] and len(st.session_state['messages']) == 0:
        st.title('Hello there 👋')
        st.write("I'm here to assist you. Start typing or speaking to chat with the model.")

    # Display the conversation history with timestamps and markdown support
    for message in st.session_state['messages']:
        if message['role'] == 'user':
            st.write(f"**User ({message['timestamp']}):** {message['content']}")
        elif message['role'] == 'assistant':
            st.write(f"**Assistant ({message['timestamp']}):** {message['content']}")
        elif message['role'] == 'rating':
            st.write(f"**Rating ({message['timestamp']}):** {message['content']}")
        elif message['role'] == 'system':
            st.write(f"**System ({message['timestamp']}):** {message['content']}")

    # Handle user input and generate response
    if st.session_state['user_input'] and not st.session_state['response_in_progress']:
        st.session_state['response_in_progress'] = True
        with st.spinner('Generating response...'):
            try:
                # Get response from the model
                response = get_chat_completion(st.session_state['user_input'], model)

                # Add user message to the conversation history
                st.session_state['messages'].append({
                    'role': 'user', 
                    'content': emoji.emojize(st.session_state['user_input']), 
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

                # Fetch reference links related to the query
                search_results = search(st.session_state['user_input'], num_results=3)
                reference_links = "\n\n**Related References:**\n"
                for link in search_results:
                    reference_links += f"- {link}\n"

                # Append search results to response
                response += reference_links

                # Simulate typing effect by displaying the response incrementally
                full_response = emoji.emojize(response)
                response_placeholder = st.empty()
                previous_text = ""

                # Simulating a typing effect
                for sentence in full_response.split('. '):
                    previous_text += f"{sentence}. "
                    response_placeholder.write(f"**Assistant ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):** {previous_text}")
                    time.sleep(0.30)  # Adjust typing speed as needed

                # Ensure the full response is added after typing effect
                st.session_state['messages'].append({
                    'role': 'assistant', 
                    'content': emoji.emojize(response), 
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

                # Clear user input after generating response
                st.session_state['user_input'] = None

            except Exception as e:
                st.error(f"Error: {e}")

            st.session_state['response_in_progress'] = False

    # Create a single row of columns for the query buttons (optional)
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("What's the weather like?"):
            st.session_state['user_input'] = "What's the weather like?"

    with col2:
        if st.button("Tell me a joke"):
            st.session_state['user_input'] = "Tell me a joke"

    with col3:
        if st.button("How do I make a cake?"):
            st.session_state['user_input'] = "How do I make a cake?"

    # Rich Media Support
    st.write("Upload media files (PDFs, audio, or video) to interact with:")
    uploaded_file = st.file_uploader("Upload a file", type=["pdf", "mp3", "mp4"])

    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            # Handle PDF files
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            num_pages = len(pdf_reader.pages)
            text = ""
            for page in range(num_pages):
                text += pdf_reader.pages[page].extract_text()
            st.text_area("PDF Content", text, height=200)

        elif uploaded_file.type == "audio/mpeg":
            # Handle audio files (could include audio analysis or transcription)
            st.audio(uploaded_file)

        elif uploaded_file.type == "video/mp4":
            # Handle video files
            st.video(uploaded_file)
    else:
        st.write("No file uploaded yet.")

    # Feedback and rating settings
    st.sidebar.write("### Feedback and Ratings")
    feedback_text = st.sidebar.text_area("Provide your feedback on the response", key="feedback_text")
    
    # Submit Feedback Button
    if st.sidebar.button("Submit Feedback"):
        if feedback_text:
            st.session_state['feedback'].append({
                'feedback': feedback_text,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            st.sidebar.success("Feedback submitted!")
        else:
            st.sidebar.error("Please enter feedback before submitting.")

    # Rating Slider
    rating = st.sidebar.slider("Rate the response", 1, 5, 3, key="rating_slider")

    # Submit Rating Button
    if st.sidebar.button("Submit Rating"):
        st.session_state['rating'] = rating
        st.sidebar.success("Rating submitted!")

    # Ask a question box at the end
    #st.write("## Ask a question")
    user_input = st.text_input('Ask a question', key="chat_input", value='')

    if user_input:
        st.session_state['user_input'] = user_input   
