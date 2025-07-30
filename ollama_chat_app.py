import streamlit as st
import requests
import json
import os
import tempfile
from gtts import gTTS
from deep_translator import GoogleTranslator
import speech_recognition as sr
import re
import getpass
from pathlib import Path
from datetime import datetime
from pathlib import Path
import getpass

# Get user and chat storage paths
username = getpass.getuser()
history_dir = Path.home() / ".ollama_chat_history"
history_dir.mkdir(parents=True, exist_ok=True)

history_file = history_dir / f"{username}_chat_history.json"
archive_dir = history_dir / "archive"
archive_dir.mkdir(parents=True, exist_ok=True)
# --- Configuration ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:1b"

# --- Streamlit Setup ---
st.set_page_config(page_title="Ollama Voice Chat AI", page_icon="💬")
st.title("💬 Ollama Voice Chat AI (Multi-language)")
st.markdown("Interact with your local Ollama model via text or voice in any language!")

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- User Chat History Management ---
# Identify user
username = getpass.getuser()
history_dir = Path.home() / ".ollama_chat_history"
history_file = history_dir / f"{username}_chat_history.json"

# Ensure directory and file exist
history_dir.mkdir(parents=True, exist_ok=True)
if not history_file.exists():
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump([], f)

# Load existing messages
try:
    with open(history_file, "r", encoding="utf-8") as f:
        st.session_state.messages = json.load(f)
except json.JSONDecodeError:
    st.session_state.messages = []

# Function to save history
def save_history():
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(st.session_state.messages, f, ensure_ascii=False, indent=2)

# --- Language Code Mapping ---
gtts_lang_map = {
    "en-US": "en",
    "ar-SA": "ar",
    "el-GR": "el",
    "fr-FR": "fr",
    "es-ES": "es",
    "de-DE": "de",
    "it-IT": "it",
    "pt-PT": "pt",
    "ru-RU": "ru",
    "zh-CN": "zh-CN",
    "ja-JP": "ja",
    "he-IL": "he",
}

# --- Clean Text for TTS ---
def clean_text_for_tts(text):
    emoji_pattern = re.compile(
        "["  
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002700-\U000027BF"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub('', text)
    text = re.sub(r'[*_~`#@%^&+=|<>{}[\]\\]', '', text)
    return re.sub(r'\s+', ' ', text).strip()

# --- Ollama Call ---
def generate_ollama_response(prompt_text):
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"Your name is Eva and You are a friendly, helpful, and fun AI assistant. Respond in a casual and engaging manner. {prompt_text}",
        "stream": False,
    }
    try:
        response = requests.post(OLLAMA_API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        return result.get("response", "No response from Ollama.")
    except requests.exceptions.ConnectionError:
        return "❌ Could not connect to Ollama. Is it running?"
    except requests.exceptions.RequestException as e:
        return f"❌ Ollama request error: {e}"

# --- TTS ---
def text_to_speech(text, lang='en'):
    try:
        clean_text = clean_text_for_tts(text)
        tts = gTTS(text=clean_text, lang=lang)
        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        tts.save(temp_path)
        with open(temp_path, "rb") as f:
            st.audio(f.read(), format="audio/mp3", autoplay=True)
        os.remove(temp_path)
    except Exception as e:
        st.error(f"Could not generate speech: {e}")

# --- STT ---
def speech_to_text(lang='en-US'):
    r = sr.Recognizer()
    with st.spinner("🎙️ Listening..."):
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source)
                audio = r.listen(source, timeout=5, phrase_time_limit=20)
        except sr.WaitTimeoutError:
            st.warning("⏱️ No speech detected.")
            return None
        except Exception as e:
            st.error(f"Microphone error: {e}")
            return None

    try:
        text = r.recognize_google(audio, language=lang)
        st.success("Transcription: " + text)
        return text
    except sr.UnknownValueError:
        st.warning("Sorry, I couldn't understand the audio.")
        return None
    except sr.RequestError as e:
        st.error(f"Google Speech API error: {e}")
        return None

# --- Chat History Display ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Language Selector ---
lang_code = st.selectbox("🎙️ Choose language (for voice + reply)", list(gtts_lang_map.keys()))
tts_lang = gtts_lang_map.get(lang_code, "en")

# --- Text Input ---
if prompt := st.chat_input("Type your message here..."):
    # Translate to English if user selected a non-English language
    if tts_lang != "en":
        prompt_translated = GoogleTranslator(source='auto', target='en').translate(prompt)
    else:
        prompt_translated = prompt

    # Store user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_history()
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI Response
    with st.spinner("💡 AI is thinking..."):
        response_en = generate_ollama_response(prompt_translated)

        # Translate back if needed
        if tts_lang != "en":
            response_final = GoogleTranslator(source='en', target=tts_lang).translate(response_en)
        else:
            response_final = response_en

        st.session_state.messages.append({"role": "assistant", "content": response_final})
        save_history()
        with st.chat_message("assistant"):
            st.markdown(response_final)
        text_to_speech(response_final, lang=tts_lang)

# --- Voice Input ---
if st.button("🎤 Speak to AI"):
    spoken_text = speech_to_text(lang=lang_code)
    if spoken_text:
        # Translate input if needed
        if tts_lang != "en":
            spoken_translated = GoogleTranslator(source='auto', target='en').translate(spoken_text)
        else:
            spoken_translated = spoken_text

        st.session_state.messages.append({"role": "user", "content": f"_(Voice)_ {spoken_text}"})
        save_history()
        with st.chat_message("user"):
            st.markdown(f"_(Voice)_ {spoken_text}")

        with st.spinner("💡 AI is thinking..."):
            response_en = generate_ollama_response(spoken_translated)
            response_final = GoogleTranslator(source='en', target=tts_lang).translate(response_en) if tts_lang != "en" else response_en

            st.session_state.messages.append({"role": "assistant", "content": response_final})
            save_history()
            with st.chat_message("assistant"):
                st.markdown(response_final)
            text_to_speech(response_final, lang=tts_lang)

# --- Sidebar Instructions ---
st.sidebar.header("Setup Instructions")
st.sidebar.markdown("""
1. **Start Ollama server**  
   ```bash
   ollama run gemma3:1b```

    
    #streamlit run ollama_chat_app.py --server.port 8080 --server.address 0.0.0.0""")
def archive_current_chat():
    if st.session_state.messages:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        archive_file = archive_dir / f"chat_{timestamp}.json"
        with open(archive_file, "w", encoding="utf-8") as f:
            json.dump(st.session_state.messages, f, ensure_ascii=False, indent=2)

if st.sidebar.button("🆕 New Chat"):
    archive_current_chat()
    st.session_state.messages = []
    save_history()
    st.rerun()

st.sidebar.markdown("### 📂 Recent Chats")
archived_files = sorted(archive_dir.glob("chat_*.json"), reverse=True)

for file in archived_files[:5]:  # show last 5 chats
    label = file.stem.replace("chat_", "").replace("_", ":", 1).replace("_", "-")
    if st.sidebar.button(f"🕘 {label}"):
        with open(file, "r", encoding="utf-8") as f:
            st.session_state.messages = json.load(f)
        save_history()
        st.rerun()
#C:\Users\<your-username>\.ollama_chat_history\<your-username>_chat_history.json
#streamlit run ollama_chat_app.py --server.port 8080 --server.address 0.0.0.0
