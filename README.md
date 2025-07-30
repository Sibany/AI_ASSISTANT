
# 💬 Ollama Voice Chat AI (Multi-language)

A Streamlit-based chatbot app that lets you **talk to your local Ollama model** (e.g., `gemma3:1b`) using **text or voice** — with full **multi-language support**, including **translation, speech recognition**, and **TTS (Text-to-Speech)**.

---

## 🚀 Features

- ✅ Local LLM chatbot using Ollama (`gemma3:1b`)
- 🗣️ Voice input via microphone (Google Speech-to-Text)
- 🔈 Voice output via Google Text-to-Speech (gTTS)
- 🌍 Multi-language support:
  - Auto translation to/from English
  - Choose your preferred voice language (e.g., Arabic, Hebrew, French)
- 😃 Emoji support in chat (ignored in voice)
- 🧼 Strips special characters from voice output for cleaner TTS

---

## 🛠 Requirements

- Python `3.10.0`
- [Ollama](https://ollama.com/)
- `gemma3:1b` model (or any model you prefer)

---

## 📦 Installation

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/ollama-voice-chat-ai.git
cd ollama-voice-chat-ai
```

### 2. Install Ollama & Pull a Model

Make sure [Ollama](https://ollama.com/download) is installed and running:

```bash
ollama run gemma3:1b
```

> You can swap `gemma3:1b` with any other local LLM model (e.g., `mistral`, `llama2`).

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

If you're on **Windows** and get errors with `pyaudio`:

```bash
pip install pipwin
pipwin install pyaudio
```

---

## 🧠 How It Works

1. User types or speaks a message (in any language).
2. Message is translated to English (if needed).
3. Sent to your **local Ollama model**.
4. Response is translated back (if needed).
5. Shown in chat + played as voice using `gTTS`.

---

## 🌐 Supported Languages

You can select any of the following in the dropdown:

- English (en-US)
- Arabic (ar-SA)
- Greek (el-GR)
- French (fr-FR)
- Spanish (es-ES)
- German (de-DE)
- Italian (it-IT)
- Portuguese (pt-PT)
- Russian (ru-RU)
- Chinese (zh-CN)
- Japanese (ja-JP)
- Hebrew (he-IL)

---

## 📸 Screenshot

![Ollama Chat Multilingual UI](docs/screenshot.png)

---

## 🧪 Run the App

```bash
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501)

---

## 📁 File Structure

```
ollama-voice-chat-ai/
├── app.py               # Main Streamlit app
├── requirements.txt     # Python dependencies
├── README.md            # This file
└── docs/
    └── screenshot.png   # Optional image for GitHub preview
```

---

## 🤖 Example Models You Can Use

- `gemma3:1b`
- `llama2`
- `mistral`
- `phi`
- `dolphin-mixtral`

> Swap models by editing the `OLLAMA_MODEL` constant in `app.py`.

---

## 🙋 FAQ

**Q: Can I use this offline?**  
Yes — Ollama and `gTTS` both work locally, but `gTTS` needs internet to fetch audio.

**Q: Can I add more languages?**  
Yes — just update the `gtts_lang_map` dictionary in `app.py`.

**Q: Can I use my own model?**  
Yes — any Ollama-compatible model can be used by updating the `OLLAMA_MODEL`.

---

## 📝 License

MIT License — feel free to modify and use.

---

## 💡 Credits

Built with [Streamlit](https://streamlit.io), [Ollama](https://ollama.com), and ❤️
