import streamlit as st
import requests
import json
import tempfile
from gtts import gTTS
from deep_translator import GoogleTranslator
import speech_recognition as sr
import re
import getpass
from pathlib import Path
from datetime import datetime
import geocoder
from bs4 import BeautifulSoup
from urllib.parse import quote
import subprocess
import pyautogui
import time
import math
import mutagen.mp3

# === Setup ===
username = getpass.getuser()
history_dir = Path.home() / ".ollama_chat_history"
history_dir.mkdir(parents=True, exist_ok=True)
history_file = history_dir / f"{username}_chat_history.json"
archive_dir = history_dir / "archive"
archive_dir.mkdir(parents=True, exist_ok=True)

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:1b"

# === Streamlit Setup ===
st.set_page_config(
    page_title="Ollama Voice Chat AI",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===== Global CSS + Reopen Arrow (only shows when sidebar is hidden) =====
st.markdown("""
<style>
/* ===== Base + background ===== */
html, body, [data-testid="stAppViewContainer"] {
  background: radial-gradient(80% 60% at 50% 30%, #1e2742 0%, #0b1221 45%, #070d18 100%) !important;
  color: #e7eaf3;
}
[data-testid="stAppViewContainer"] { padding-top: 0rem; }

/* keep menu + footer hidden, but leave header visible so the native toggle works */
#MainMenu, footer { visibility: hidden; height: 0; }

/* slim, transparent header; keep the hamburger visible */
header[data-testid="stHeader"]{
  visibility: visible;
  background: transparent;
  border-bottom: 0;
  height: 48px;
}
header [data-testid="baseButton-headerNoPadding"],
button[title="Collapse sidebar"], button[title="Expand sidebar"]{
  opacity: 1 !important;
  pointer-events: auto !important;
  z-index: 1000 !important;
}

/* ===== Center column ===== */
.block-container { max-width: 980px; padding-top: 2.2rem; }

/* ===== Hero (no search input) ===== */
.hero-wrap { display:flex; align-items:center; justify-content:center; min-height:70vh; text-align:center; }
.hero h1 { font-weight:700; letter-spacing:.3px; font-size:38px; margin:0 0 .6rem 0; }
.hero p { color:#98a2b3; margin:.2rem 0 2.2rem; }

/* ===== Chat bubbles ===== */
[data-testid="stChatMessageContainer"] > div { width: 100%; display: flex; justify-content: center; }
[data-testid="stChatMessage"] {
  width: 100%; max-width: 880px; border-radius: 18px; padding: 16px 18px; border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.05);
  backdrop-filter: blur(8px);
}
[data-testid="stChatMessage"][data-testid*="user"] {
  background: rgba(40,169,255,0.10);
  border-color: rgba(40,169,255,0.20);
}

/* ===== Chat input (bottom) ===== */
[data-testid="stChatInput"] {
  max-width: 880px; margin: 0 auto 14px auto;
}
textarea[aria-label="Type your message here..."] {
  color: #e7eaf3 !important;
  border-radius: 16px !important;
}

/* ===== Sidebar ===== */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg,#0c1324,#0a1020);
  border-right: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] * { color: #cbd5e1; }
section[data-testid="stSidebar"] .stButton>button {
  width: 100%;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px; padding: 8px 10px;
}

/* ===== Floating reopen arrow (only visible when sidebar is hidden) ===== */
#reopenSidebar {
  position: fixed;
  top: 12px; left: 12px;
  z-index: 2000;
  display: none; /* JS toggles this */
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.15);
  backdrop-filter: blur(8px);
  border-radius: 10px;
  padding: 6px 10px;
  cursor: pointer; user-select: none;
  font-size: 18px; line-height: 1;
}
#reopenSidebar:hover{ background: rgba(255,255,255,0.14); }
</style>

<!-- the arrow »« appears only when sidebar is hidden -->
<div id="reopenSidebar">≪</div>

<script>
(function(){
  function nativeToggle(){
    const btn = Array.from(document.querySelectorAll('button')).find(b=>{
      const t = (b.title || '');
      return t.includes('Collapse sidebar') || t.includes('Expand sidebar');
    });
    if(btn){ btn.click(); return true; }
    return false;
  }

  function isSidebarVisible(){
    const sb = document.querySelector('section[data-testid="stSidebar"]');
    if(!sb){ return false; }
    const style = window.getComputedStyle(sb);
    return style.display !== 'none' && sb.offsetWidth > 0 && sb.offsetHeight > 0;
  }

  function refreshArrow(){
    const arrow = document.getElementById('reopenSidebar');
    if(!arrow) return;
    arrow.style.display = isSidebarVisible() ? 'none' : 'block';
  }

  // Click handler on the arrow
  const arrow = document.getElementById('reopenSidebar');
  if(arrow){
    arrow.addEventListener('click', function(e){
      e.stopPropagation();
      if(!nativeToggle()){
        let tries = 0;
        const iv = setInterval(()=>{
          if(nativeToggle() || ++tries > 20){ clearInterval(iv); }
        }, 150);
      }
    }, true);
  }

  // Observe DOM changes to show/hide arrow correctly when sidebar changes
  const obs = new MutationObserver(refreshArrow);
  obs.observe(document.body, {subtree:true, childList:true, attributes:true});

  // Initial check
  window.addEventListener('load', refreshArrow);
  setTimeout(refreshArrow, 500);
})();
</script>
""", unsafe_allow_html=True)

# Hide default title and render our own hero when needed
st.title("")

# === Session State ===
default_session_state = {
    "messages": [],
    "voice_mode": False,
    "input_used": False,
    "lang_code": "en-US",
    "tts_lang": "en",
    "rename_states": {},
    "browser_open": False,
    "processing_voice": False,
    "speech_failed_count": 0,
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# === History Load ===
if not history_file.exists():
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump([], f)

try:
    with open(history_file, "r", encoding="utf-8") as f:
        st.session_state.messages = json.load(f)
except json.JSONDecodeError:
    st.session_state.messages = []

def save_history():
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(st.session_state.messages, f, ensure_ascii=False, indent=2)

# === Helper Functions ===
def clean_text_for_tts(text):
    emoji_pattern = re.compile(
        "[" +
        u"\U0001F600-\U0001F64F" +
        u"\U0001F300-\U0001F5FF" +
        u"\U0001F680-\U0001F6FF" +
        u"\U0001F1E0-\U0001F1FF" +
        u"\u2700-\u27BF" +
        u"\u24C2-\U0001F251" +
        "]+", flags=re.UNICODE
    )
    return re.sub(r'\s+', ' ', emoji_pattern.sub('', text)).strip()

def build_conversation_prompt():
    now = datetime.now().strftime('%A, %d %B %Y %I:%M %p')
    location = geocoder.ip('me')
    loc_str = f"{location.country}" if getattr(location, "ok", False) else "Unknown Location"

    system_prompt = (
        f"You are a smart, self-aware assistant named Gemma. You know the current date and time is {now} and you are located in {loc_str}.\n"
        "You use real web data, add hyperlinks in a markdown format when possible, and always aim to provide fresh and concise information. Do not prefix responses with 'Assistant'."
    )
    history = ""
    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "assistant"
        content_clean = re.sub(r"^(User|Assistant):\\s*", "", msg["content"])
        history += f"{role}: {content_clean}\n"
    return f"{system_prompt}\n\n{history}user:"

def perform_web_search(query):
    try:
        url = f"https://www.google.com/search?q={quote(query)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        snippets = [
            result.get_text(strip=True)
            for result in soup.select("div.VwiC3b, div.BNeawe.s3v9rd.AP7Wnd")
        ][:3]
        if snippets:
            return "Web search results:\n" + "\n".join(f"- {s}" for s in snippets)
        return "Web search found no results."
    except Exception as e:
        return f"Web search failed: {e}"

def generate_ollama_response(prompt_text, search_results=None):
    if search_results:
        prompt_text = (
            f"Using the following information from a web search:\n{search_results}\n\n"
            f"Based on this, answer the following question: {prompt_text}. "
            f"Format any links in markdown like this: [text](url)."
        )
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{build_conversation_prompt()} {prompt_text}\n",
        "stream": False,
    }
    try:
        response = requests.post(OLLAMA_API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        return result.get("response", "No response from Ollama.")
    except Exception as e:
        return f"❌ Error: {e}"

def get_local_news_summary():
    try:
        location = geocoder.ip('me')
        city = getattr(location, "city", None) or "your city"
        country = getattr(location, "country", None) or "your country"
        location_str = f"{city}, {country}"

        query = f"{city} news site:news.google.com"
        url = f"https://www.google.com/search?q={quote(query)}&tbm=nws"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        articles = []
        for item in soup.select("div.dbsr")[:3]:
            a = item.select_one("a")
            title = item.get_text(strip=True)
            link = a['href'] if a else None
            if title and link:
                articles.append(f"- [{title}]({link})")

        if not articles:
            return f"Couldn't find news for {location_str}."
        return f"Here’s what I learned from today’s local news in {location_str}:\n\n" + "\n".join(articles)
    except Exception as e:
        return f"News fetch error: {e}"

def text_to_speech(text, lang='en'):
    try:
        lines = text.split("\n")
        clean_lines = [line for line in lines if "[" not in line and "http" not in line]
        clean_text = clean_text_for_tts(" ".join(clean_lines))
        tts = gTTS(text=clean_text, lang=lang)
        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        tts.save(temp_path)

        audio_info = mutagen.mp3.MP3(temp_path)
        duration = math.ceil(audio_info.info.length)

        with open(temp_path, "rb") as f:
            st.audio(f.read(), format="audio/mp3", autoplay=True)

        time.sleep(duration + 0.3)
    except Exception as e:
        st.error(f"TTS error: {e}")

def speech_to_text(lang='en-US'):
    r = sr.Recognizer()
    r.pause_threshold = 4  # stop after 4 seconds of silence
    with st.status("🎧 Listening...", expanded=True) as status:
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source)
                audio = r.listen(source, timeout=10)
            status.update(label="✅ Listening complete.", state="complete")
            return r.recognize_google(audio, language=lang)
        except sr.WaitTimeoutError:
            status.update(label="🎧 Listening timed out (no speech detected).", state="complete")
            return None
        except Exception:
            status.update(label="❌ Speech recognition failed.", state="error")
            return None

def open_browser_with_query(query):
    url = f"https://www.google.com/search?q={quote(query)}"
    subprocess.Popen(["start", "chrome", url], shell=True)
    st.session_state.browser_open = True

def close_browser():
    subprocess.call(["taskkill", "/F", "/IM", "chrome.exe"], shell=True)
    st.session_state.browser_open = False

# === Chat history rendering ===
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

def clean_ai_response(text):
    return re.sub(r'^(Assistant|assistant):\s*', '', text).strip()

def handle_input(user_input, from_voice=False):
    original = user_input.strip()
    if not original:
        if from_voice:
            st.session_state.processing_voice = False
        return
    if len(original) > 4900:
        st.warning("Your message is too long. Please shorten it.")
        if from_voice:
            st.session_state.processing_voice = False
        return

    if "what did you learn today" in original.lower():
        news = get_local_news_summary()
        st.session_state.messages.append({"role": "assistant", "content": news})
        with st.chat_message("assistant"):
            st.markdown(news)
        text_to_speech(news, lang=st.session_state.tts_lang)
        if from_voice:
            st.session_state.processing_voice = False
        st.rerun()
        return

    if "open browser" in original.lower():
        query = original.lower().replace("open browser", "").strip()
        open_browser_with_query(query or "")
        message = f"🧭 Opening browser{' and searching for: **' + query + '**' if query else '.'}"
        st.session_state.messages.append({"role": "assistant", "content": message})
        with st.chat_message("assistant"):
            st.markdown(message)
        text_to_speech(message, lang=st.session_state.tts_lang)
        if from_voice:
            st.session_state.processing_voice = False
        st.rerun()
        return

    if "close browser" in original.lower():
        close_browser()
        message = "❌ Browser closed."
        st.session_state.messages.append({"role": "assistant", "content": message})
        with st.chat_message("assistant"):
            st.markdown(message)
        text_to_speech(message, lang=st.session_state.tts_lang)
        if from_voice:
            st.session_state.processing_voice = False
        st.rerun()
        return

    with st.spinner("🔍 Performing web search..."):
        search_results = perform_web_search(original)

    try:
        translated = GoogleTranslator(source='auto', target='en').translate(original)
    except Exception as e:
        st.error(f"Translation error: {e}")
        if from_voice:
            st.session_state.processing_voice = False
        return

    role_input = f"🎤 {original}" if from_voice else original
    st.session_state.messages.append({"role": "user", "content": role_input})
    save_history()

    with st.chat_message("user"):
        st.markdown(role_input)

    with st.spinner("💡 AI is thinking..."):
        response_en = clean_ai_response(
            generate_ollama_response(translated, search_results=search_results)
        )
        try:
            response_final = GoogleTranslator(source='en', target=st.session_state.tts_lang).translate(response_en)
        except Exception:
            response_final = response_en

        st.session_state.messages.append({"role": "assistant", "content": response_final})
        save_history()

        with st.chat_message("assistant"):
            st.markdown(response_final)

        text_to_speech(response_final, lang=st.session_state.tts_lang)

    if from_voice:
        st.session_state.processing_voice = False

    st.rerun()

# === Empty-state hero (centered, no input) ===
def render_home():
    st.markdown(
        """
        <div class="hero-wrap">
          <div class="hero">
            <h1>Introducing GPT-style Chat</h1>
            <p>Smart, fast, and helpful — with thinking built in so you get better answers, every time.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return None

# === Main Application Logic ===
new_query = None
if not st.session_state.messages:
    new_query = render_home()

if new_query:
    handle_input(new_query)

if prompt := st.chat_input("Type your message here..."):
    if prompt.strip():
        st.session_state.voice_mode = False
        handle_input(prompt)

# === Voice loop ===
if st.session_state.voice_mode and not st.session_state.processing_voice:
    st.session_state.processing_voice = True
    speech = speech_to_text(lang=st.session_state.lang_code)
    if speech:
        handle_input(speech, from_voice=True)
        st.session_state.speech_failed_count = 0
    else:
        st.session_state.processing_voice = False
        st.session_state.speech_failed_count += 1
        if st.session_state.speech_failed_count > 3:
            st.warning("Speech recognition failed. Please try again.")
            st.session_state.speech_failed_count = 0
        st.rerun()

# === Sidebar ===
st.sidebar.header("📈 Voice Settings")
lang_map = {
    "en-US": "en", "ar-SA": "ar", "el-GR": "el", "fr-FR": "fr",
    "es-ES": "es", "de-DE": "de", "it-IT": "it", "pt-PT": "pt",
    "ru-RU": "ru", "zh-CN": "zh-CN", "ja-JP": "ja", "he-IL": "iw",
}
st.session_state.lang_code = st.sidebar.selectbox("Speech Recognition Language", list(lang_map.keys()), index=0)
st.session_state.tts_lang = lang_map.get(st.session_state.lang_code, "en")

if st.sidebar.button("🎤 Start Voice Chat"):
    st.session_state.voice_mode = True
    st.session_state.processing_voice = False
    st.rerun()

if st.sidebar.button("🛑 Stop Voice Chat"):
    st.session_state.voice_mode = False
    st.session_state.processing_voice = False
    st.rerun()

def archive_chat():
    if st.session_state.messages:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with open(archive_dir / f"chat_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(st.session_state.messages, f, ensure_ascii=False, indent=2)

if st.sidebar.button("🆕 New Chat"):
    archive_chat()
    st.session_state.messages = []
    save_history()
    st.rerun()

st.sidebar.markdown("### 📁 Recent Chats")
archive_files = sorted(archive_dir.glob("chat_*.json"), reverse=True)[:10]

for file in archive_files:
    file_id = file.stem.replace("chat_", "")
    display_name = file_id.replace("_", " ")
    with st.sidebar.container():
        col1, col2, col3 = st.columns([6, 1, 1])
        with col1:
            if st.button(f"🕘 {display_name}", key=f"load_{file_id}"):
                with open(file, "r", encoding="utf-8") as f:
                    st.session_state.messages = json.load(f)
                save_history()
                st.rerun()
        with col2:
            if st.button("✏️", key=f"rename_btn_{file_id}"):
                st.session_state.rename_states[file_id] = not st.session_state.rename_states.get(file_id, False)
        with col3:
            if st.button("🗑️", key=f"delete_{file_id}"):
                file.unlink()
                st.rerun()

        if st.session_state.rename_states.get(file_id, False):
            new_name = st.text_input("Rename chat", value=file_id, key=f"input_{file_id}")
            clean_name = new_name.strip().replace(" ", "_").replace(":", "-")
            if clean_name and clean_name != file_id:
                new_path = archive_dir / f"chat_{clean_name}.json"
                file.rename(new_path)
                st.success(f"Renamed to {clean_name}")
                st.session_state.rename_states[file_id] = False
                st.rerun()
