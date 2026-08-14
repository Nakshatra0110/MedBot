# 🩺 MedBot — AI Health Chatbot

An intelligent desktop medical assistant that combines **skin disease detection** 
using a trained deep learning model with **LLM-powered medical Q&A**, 
multilingual support, and voice interaction — all in a unified ChatGPT-style interface.

---

## ✨ Features

- 💬 **Medical Chatbot** — Ask any health or symptom question, get detailed AI responses
- 🔬 **Skin Disease Detection** — Upload a photo; MobileNetV2 classifies 46 skin conditions
- 🌍 **50+ Languages** — Speak or type in Hindi, Urdu, Tamil, Telugu, Arabic, and more
- 🎤 **Voice Input** — Speak in your native language; auto-translated to English for the LLM
- 🔊 **Voice Output** — Hear responses read aloud with Stop/Auto-Speak controls
- 💾 **Chat History** — All conversations saved locally and reloadable from the sidebar
- 🖼️ **Image Upload in Chat** — Attach skin images directly in the chat input
- ⚡ **Fast LLM** — Powered by Groq API (Llama-3.3-70B) — free and extremely fast

---

## 🖥️ Interface

- ChatGPT-style dark theme UI built with Python Tkinter
- Left sidebar: New Chat, Chat History, Language Selector, Username
- Chat bubbles with **bold markdown** rendering
- Prominent voice toolbar: 🎤 Speak to Type | 🔊 Speak Response | ⏹ Stop Speaking

---

## 🧠 AI Models

| Model | Purpose |
|---|---|
| MobileNetV2 (fine-tuned) | Skin disease classification — 46 classes |
| Llama-3.3-70B via Groq | Medical Q&A and disease explanation |
| Google Speech Recognition | Voice-to-text in 50+ languages |
| deep-translator | Auto-translation to/from English |
| pyttsx3 | Offline text-to-speech output |

---

## 🗂️ Dataset

Trained on a merged dataset of:
- **HAM10000** — 10,000+ dermatoscopy images (7 classes)
- **SD-198** — 6,584 clinical skin images (198 categories)
- Combined into **46 unified disease classes**

---

## 📁 Project Structure
```
chatbot/
├── main.py                     # Entry point
├── models/
│   ├── skin_model.pth          # Trained MobileNetV2 weights
│   └── class_names.json        # 46 disease class labels
├── ui/
│   └── healthbot_frame.py      # Full application UI + logic
├── training/
│   ├── prepare_dataset.py      # Dataset merging and preprocessing
│   └── train_skin_model.py     # MobileNetV2 training script
├── prediction/
│   └── skin_predictor_frame.py # Original standalone predictor
├── data/                       # Raw dataset files
└── chat_history.json           # Auto-created conversation history
```

---

## ⚙️ Installation
```bash
# 1. Clone the repository
git clone https://github.com/yourusername/medbot.git
cd medbot

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install torch torchvision pillow groq deep-translator \
            SpeechRecognition pyaudio pyttsx3

# 4. Add your Groq API key (free at console.groq.com)
# Open ui/healthbot_frame.py and set:
# GROQ_API_KEY = "gsk_your_key_here"

# 5. Run
python main.py
```

---

## 🔬 How Skin Detection Works

1. User clicks 📎 and uploads a skin photo
2. Image is resized to 224×224 and passed through MobileNetV2
3. Softmax gives confidence score across 46 disease classes
4. If confidence ≥ 60% → HIGH CONFIDENCE result
5. Groq LLM explains the detected condition in detail
6. Response translated to user's selected language

---
##Contributors:
Nakshatra Gupta
Gurpreet Nagar

## 🌐 Supported Languages

Hindi, Urdu, Tamil, Telugu, Punjabi, Bengali, Gujarati, Marathi,
Kannada, Malayalam, Arabic, Persian, Turkish, English, Spanish,
French, German, Chinese, Japanese, Korean, Russian, Portuguese,
and 30+ more.

---

## ⚕️ Disclaimer

MedBot is an AI-powered educational tool. It is **not a substitute 
for professional medical diagnosis or treatment**. Always consult a 
licensed healthcare professional for medical decisions.

---

## 📄 License

MIT License — free to use, modify, and distribute with attribution.
```

---

**GitHub Topics** (add these as tags on your repo page):
```
python  tkinter  healthcare  machine-learning  skin-disease  
groq  llm  mobilenet  nlp  multilingual  voice-assistant  
medical-ai  deep-learning  chatbot  dermatology
