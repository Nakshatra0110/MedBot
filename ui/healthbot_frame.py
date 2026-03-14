"""
AI Health Chatbot - Unified Modern Interface
Fixes applied:
 - Groq API key hardcoded at top (no dialog needed)
 - No "add API key" hints in responses
 - Longer, more detailed LLM responses
 - Chat continues properly without repeating welcome
 - Only 1 chat created on startup (not 3)
 - Voice input fills the text box in the selected language
 - Voice output speaks response in selected language with Stop button
 - Auto-speak toggle works correctly
 - Settings button removed (key is hardcoded)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import os
import datetime
import uuid

# ─── PASTE YOUR GROQ API KEY HERE ────────────────────────────────────────────
GROQ_API_KEY = ""   # <-- replace with your gsk_... key
# ─────────────────────────────────────────────────────────────────────────────

# ─── Optional imports ────────────────────────────────────────────────────────
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

try:
    from deep_translator import GoogleTranslator
    TRANSLATE_AVAILABLE = True
except ImportError:
    TRANSLATE_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    import torch
    import torchvision.transforms as transforms
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# ─── Paths ────────────────────────────────────────────────────────────────────
_BASE      = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(_BASE, "..", "chat_history.json")
MODELS_DIR   = os.path.join(_BASE, "..", "models")

# ─── Colors ───────────────────────────────────────────────────────────────────
C = {
    "bg_dark":       "#0d1117",
    "bg_sidebar":    "#161b22",
    "bg_chat":       "#0d1117",
    "bg_input":      "#1c2128",
    "bg_user":       "#1f6feb",
    "bg_bot":        "#21262d",
    "bg_hover":      "#30363d",
    "bg_active":     "#1a2a3a",
    "accent":        "#1f6feb",
    "accent2":       "#58a6ff",
    "success":       "#3fb950",
    "warning":       "#d29922",
    "danger":        "#f85149",
    "txt":           "#e6edf3",
    "txt2":          "#8b949e",
    "txt3":          "#484f58",
    "border":        "#30363d",
}

# ─── Languages ────────────────────────────────────────────────────────────────
# Maps display name → (deep-translator code, speech-recognition BCP-47 code)
LANGUAGES = {
    # South Asian
    "English":              ("en",    "en-US"),
    "Hindi":                ("hi",    "hi-IN"),
    "Urdu":                 ("ur",    "ur-PK"),
    "Tamil":                ("ta",    "ta-IN"),
    "Telugu":               ("te",    "te-IN"),
    "Punjabi":              ("pa",    "pa-IN"),
    "Bengali":              ("bn",    "bn-IN"),
    "Gujarati":             ("gu",    "gu-IN"),
    "Marathi":              ("mr",    "mr-IN"),
    "Kannada":              ("kn",    "kn-IN"),
    "Malayalam":            ("ml",    "ml-IN"),
    "Odia":                 ("or",    "or-IN"),
    "Sindhi":               ("sd",    "sd-PK"),
    "Nepali":               ("ne",    "ne-NP"),
    "Sinhala":              ("si",    "si-LK"),
    # Middle East & Central Asia
    "Arabic":               ("ar",    "ar-SA"),
    "Persian (Farsi)":      ("fa",    "fa-IR"),
    "Pashto":               ("ps",    "ps-AF"),
    "Turkish":              ("tr",    "tr-TR"),
    "Azerbaijani":          ("az",    "az-AZ"),
    "Kazakh":               ("kk",    "kk-KZ"),
    # East & Southeast Asia
    "Chinese (Simplified)": ("zh-CN", "zh-CN"),
    "Chinese (Traditional)":("zh-TW", "zh-TW"),
    "Japanese":             ("ja",    "ja-JP"),
    "Korean":               ("ko",    "ko-KR"),
    "Vietnamese":           ("vi",    "vi-VN"),
    "Thai":                 ("th",    "th-TH"),
    "Indonesian":           ("id",    "id-ID"),
    "Malay":                ("ms",    "ms-MY"),
    "Filipino (Tagalog)":   ("tl",    "tl-PH"),
    "Burmese":              ("my",    "my-MM"),
    # Europe
    "Spanish":              ("es",    "es-ES"),
    "French":               ("fr",    "fr-FR"),
    "German":               ("de",    "de-DE"),
    "Portuguese":           ("pt",    "pt-PT"),
    "Russian":              ("ru",    "ru-RU"),
    "Italian":              ("it",    "it-IT"),
    "Dutch":                ("nl",    "nl-NL"),
    "Polish":               ("pl",    "pl-PL"),
    "Ukrainian":            ("uk",    "uk-UA"),
    "Greek":                ("el",    "el-GR"),
    "Romanian":             ("ro",    "ro-RO"),
    # Africa
    "Swahili":              ("sw",    "sw-KE"),
    "Amharic":              ("am",    "am-ET"),
    "Hausa":                ("ha",    "ha-NG"),
    "Yoruba":               ("yo",    "yo-NG"),
    "Zulu":                 ("zu",    "zu-ZA"),
    "Afrikaans":            ("af",    "af-ZA"),
    # Americas
    "Spanish (Mexico)":     ("es",    "es-MX"),
    "Portuguese (Brazil)":  ("pt",    "pt-BR"),
}

def lang_trans_code(name):
    """Return deep-translator code for the language name."""
    v = LANGUAGES.get(name, ("en", "en-US"))
    return v[0] if isinstance(v, tuple) else v

def lang_sr_code(name):
    """Return BCP-47 speech-recognition code for the language name."""
    v = LANGUAGES.get(name, ("en", "en-US"))
    return v[1] if isinstance(v, tuple) else "en-US"

def lang_display_list():
    return list(LANGUAGES.keys())

# ─── System Prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are MedBot, a highly knowledgeable and empathetic AI medical assistant specializing in dermatology and general health.

RESPONSE STYLE:
- Always give detailed, thorough, well-structured answers
- Use clear headings and bullet points where appropriate
- Minimum 150 words per response unless the question is very simple
- Be warm, professional, and reassuring

YOUR CAPABILITIES:
1. Answer medical and health questions in depth
2. Analyze skin disease predictions from an AI model and explain them thoroughly
3. Provide detailed information about diseases, symptoms, causes, treatments, and prevention
4. Guide users on when and why to seek professional medical help

SKIN DISEASES YOU CAN EXPLAIN (detected by the AI model):
Acne Keloidalis Nuchae, Acne Vulgaris, Acute Eczema, Allergic Contact Dermatitis,
Cafe Au Lait Macule, Callus, Cellulitis, Dry Skin Eczema, Dyshidrosiform Eczema,
Guttate Psoriasis, Herpes Simplex Virus, Herpes Zoster, Impetigo, Keloid, Lipoma,
Melasma, Molluscum Contagiosum, Nummular Eczema, Onychomycosis, Perioral Dermatitis,
Pomade Acne, Pseudofolliculitis Barbae, Psoriasis, Pustular Psoriasis, Scalp Psoriasis,
Scar, Seborrheic Dermatitis, Skin Tag, Solar Lentigo, Steroid Acne, Tinea Corporis,
Tinea Cruris, Tinea Faciale, Tinea Manus, Tinea Pedis, Tinea Versicolor, Varicella,
Vitiligo, Wound Infection, akiec (actinic keratoses), bcc (basal cell carcinoma),
bkl (benign keratosis), df (dermatofibroma), mel (melanoma), nv (melanocytic nevi), vasc (vascular lesions).

WHEN SKIN ANALYSIS IS PROVIDED [SKIN_ANALYSIS: ...]:
Give a comprehensive response covering:
1. What the detected condition is (clear definition)
2. How it typically looks and where it appears
3. Common causes and risk factors
4. Symptoms the patient may experience
5. Available treatment options (home care + medical)
6. Precautions and lifestyle advice
7. Urgency: whether immediate medical attention is needed

IMPORTANT:
- Always add a brief reminder that you are an AI and a dermatologist should confirm the diagnosis
- Never refuse to answer health questions
- Do not mention API keys, system limitations, or technical details in your responses
- Keep the conversation flowing naturally — never restart with a greeting mid-conversation"""


# ─── Chat History ─────────────────────────────────────────────────────────────
class ChatHistoryManager:
    def __init__(self):
        self.conversations = {}
        self._load()

    def _load(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.conversations = json.load(f)
        except Exception:
            self.conversations = {}

    def _save(self):
        try:
            os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.conversations, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def new_conversation(self, title="New Chat"):
        cid = str(uuid.uuid4())
        self.conversations[cid] = {
            "id": cid, "title": title,
            "created": datetime.datetime.now().isoformat(),
            "updated": datetime.datetime.now().isoformat(),
            "messages": [],
        }
        self._save()
        return cid

    def add_message(self, cid, role, content, image_path=None):
        if cid not in self.conversations:
            return
        msg = {"role": role, "content": content,
               "timestamp": datetime.datetime.now().isoformat()}
        if image_path:
            msg["image_path"] = image_path
        self.conversations[cid]["messages"].append(msg)
        self.conversations[cid]["updated"] = datetime.datetime.now().isoformat()
        msgs = self.conversations[cid]["messages"]
        if len(msgs) == 1 and role == "user" and content:
            self.conversations[cid]["title"] = content[:40] + ("..." if len(content) > 40 else "")
        self._save()

    def get_messages(self, cid):
        return self.conversations.get(cid, {}).get("messages", [])

    def delete(self, cid):
        if cid in self.conversations:
            del self.conversations[cid]
            self._save()

    def sorted_list(self):
        return sorted(self.conversations.values(),
                      key=lambda x: x.get("updated", ""), reverse=True)


# ─── Skin Predictor ───────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.60

class SkinPredictor:
    def __init__(self):
        self.model = None
        self.class_names = []
        self.loaded = False
        self.device = torch.device("cpu") if TORCH_AVAILABLE else None
        self._load()

    def _load(self):
        try:
            cf = os.path.join(MODELS_DIR, "class_names.json")
            if os.path.exists(cf):
                with open(cf) as f:
                    self.class_names = json.load(f)
            mf = os.path.join(MODELS_DIR, "skin_model.pth")
            if TORCH_AVAILABLE and os.path.exists(mf):
                import torch.nn as nn
                from torchvision import models as tvm
                self.model = tvm.mobilenet_v2(weights=None)
                self.model.classifier[1] = nn.Linear(
                    self.model.last_channel, len(self.class_names))
                self.model.load_state_dict(
                    torch.load(mf, map_location=self.device))
                self.model.to(self.device)
                self.model.eval()
                self.loaded = True
                print(f"✓ Skin model loaded — {len(self.class_names)} classes")
        except Exception as e:
            print(f"Model load warning: {e}")

    def predict(self, image_path):
        if not self.loaded:
            raise RuntimeError("Model not loaded.")
        tf = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor()])
        img = Image.open(image_path).convert("RGB")
        tensor = tf(img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            probs = torch.softmax(self.model(tensor), dim=1)
            conf, idx = torch.max(probs, 1)
        disease = self.class_names[idx.item()].replace("_", " ") if self.class_names else f"Class {idx.item()}"
        pct = round(conf.item() * 100, 2)
        return disease, pct, conf.item() >= CONFIDENCE_THRESHOLD


# ─── LLM Client (Groq) ────────────────────────────────────────────────────────
class LLMClient:
    MODEL = "llama-3.3-70b-versatile"

    def __init__(self):
        self.client = None
        key = GROQ_API_KEY.strip()
        if not key or key == "your_groq_api_key_here":
            key = os.environ.get("GROQ_API_KEY", "").strip()
        if key and GROQ_AVAILABLE:
            try:
                self.client = Groq(api_key=key)
                print("✓ Groq LLM ready")
            except Exception as e:
                print(f"Groq init error: {e}")

    @property
    def is_ready(self):
        return self.client is not None

    def chat(self, messages):
        if self.client:
            try:
                resp = self.client.chat.completions.create(
                    model=self.MODEL,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                    max_tokens=2000,
                    temperature=0.7,
                )
                return resp.choices[0].message.content
            except Exception as e:
                return f"⚠️ Error communicating with AI: {e}\n\nPlease check your Groq API key."
        else:
            # Offline fallback — detailed built-in responses
            last = messages[-1]["content"] if messages else ""
            lw = last.lower()

            if "SKIN_ANALYSIS:" in last:
                import re
                d = re.search(r"disease=([^,\]]+)", last)
                c = re.search(r"confidence=([0-9.]+)%", last)
                s = re.search(r"status=(\w+)", last)
                disease = d.group(1).strip() if d else "Unknown condition"
                conf    = c.group(1) if c else "?"
                low     = (s.group(1) if s else "") == "LOW_CONFIDENCE"
                if low:
                    return (f"🔍 Skin Analysis — Low Confidence Result\n\n"
                            f"Tentative Detection: {disease}\n"
                            f"Confidence Score: {conf}% (below the 60% threshold)\n\n"
                            f"What this means:\n"
                            f"The AI model was unable to make a confident determination from this image. "
                            f"This can happen when the image is blurry, poorly lit, taken at an unusual angle, "
                            f"or if the skin condition does not closely match the training data.\n\n"
                            f"Recommended Steps:\n"
                            f"• Retake the photo in good natural lighting, close-up and in focus\n"
                            f"• Ensure no filters or heavy shadows in the image\n"
                            f"• Consult a certified dermatologist for a proper clinical examination\n"
                            f"• If the condition is worsening, seek medical attention promptly\n\n"
                            f"⚕️ Note: This is an AI-based tool and should not replace professional diagnosis.")
                else:
                    return (f"🔬 Skin Analysis Result\n\n"
                            f"Detected Condition: {disease}\n"
                            f"Confidence: {conf}%\n\n"
                            f"The AI model has identified this skin condition with {conf}% confidence. "
                            f"Below is general information about this condition:\n\n"
                            f"General Advice:\n"
                            f"• Visit a certified dermatologist to confirm this diagnosis\n"
                            f"• Avoid scratching or irritating the affected area\n"
                            f"• Keep the area clean and moisturized unless advised otherwise\n"
                            f"• Note when the condition started and if it is spreading\n"
                            f"• Avoid self-medicating with prescription-strength treatments\n\n"
                            f"When to Seek Urgent Care:\n"
                            f"If the condition is rapidly spreading, extremely painful, accompanied by fever, "
                            f"or shows signs of infection (pus, warmth, swelling), visit a doctor immediately.\n\n"
                            f"⚕️ This is an AI prediction — always confirm with a licensed dermatologist.")

            if any(w in lw for w in ["fever","temperature","pyrexia","high temp"]):
                return ("🌡️ Understanding Fever\n\n"
                        "Fever is defined as a body temperature above 38°C (100.4°F). It is one of the body's "
                        "natural defense mechanisms — raising temperature makes the environment less hospitable "
                        "for bacteria and viruses.\n\n"
                        "Common Causes:\n"
                        "• Viral infections (flu, cold, COVID-19)\n"
                        "• Bacterial infections (urinary tract, throat, ear)\n"
                        "• Inflammatory conditions\n"
                        "• Heat exhaustion\n"
                        "• Certain medications\n\n"
                        "Temperature Guide:\n"
                        "• Normal: 36.1–37.2°C (97–99°F)\n"
                        "• Low-grade fever: 37.3–38°C\n"
                        "• Moderate fever: 38–39°C\n"
                        "• High fever: 39–40°C — seek medical attention\n"
                        "• Very high: >40°C — emergency\n\n"
                        "Home Management:\n"
                        "• Rest and stay hydrated\n"
                        "• Paracetamol or ibuprofen (as directed)\n"
                        "• Light clothing, cool room temperature\n"
                        "• Lukewarm sponge bath if very uncomfortable\n\n"
                        "See a Doctor Immediately If:\n"
                        "• Fever exceeds 39.4°C\n"
                        "• Lasts more than 3 days\n"
                        "• Accompanied by stiff neck, severe headache, rash, or confusion\n"
                        "• Child under 3 months has any fever\n\n"
                        "⚕️ Always consult a doctor for persistent or high fever.")

            return ("👋 Hello! I'm MedBot, your AI health assistant.\n\n"
                    "I'm here to help you with medical questions, health guidance, and skin disease analysis.\n\n"
                    "How I can help:\n"
                    "• Answer questions about symptoms, diseases, and treatments\n"
                    "• Analyze skin conditions from uploaded photos (use 📎)\n"
                    "• Provide health education and preventive advice\n\n"
                    "Please feel free to ask your question!")


# ─── Translation ──────────────────────────────────────────────────────────────
class TranslationService:
    def to_english(self, text, src_code):
        """Translate text from src_code to English."""
        if src_code in ("en", "en-US") or not text or not TRANSLATE_AVAILABLE:
            return text
        # deep-translator uses short codes like "hi", "ur", "ta"
        short = src_code.split("-")[0] if "-" in src_code else src_code
        # Special case for Chinese
        if src_code in ("zh-CN", "zh-TW", "zh-cn", "zh-tw"):
            short = src_code.lower()
        try:
            return GoogleTranslator(source=short, target="en").translate(text)
        except Exception as e:
            print(f"Translation error (to_english): {e}")
            return text

    def from_english(self, text, dest_code):
        """Translate English text to dest_code language."""
        if dest_code in ("en", "en-US") or not text or not TRANSLATE_AVAILABLE:
            return text
        short = dest_code.split("-")[0] if "-" in dest_code else dest_code
        if dest_code in ("zh-CN", "zh-TW", "zh-cn", "zh-tw"):
            short = dest_code.lower()
        try:
            return GoogleTranslator(source="en", target=short).translate(text)
        except Exception as e:
            print(f"Translation error (from_english): {e}")
            return text


# ─── Voice Service ────────────────────────────────────────────────────────────
class VoiceService:
    def __init__(self):
        self.recognizer = sr.Recognizer() if SR_AVAILABLE else None
        self.engine = None
        self.speaking = False
        if TTS_AVAILABLE:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", 155)
                self.engine.setProperty("volume", 1.0)
            except Exception:
                self.engine = None

    def listen(self, lang_code="en"):
        if not self.recognizer:
            return None
        try:
            with sr.Microphone() as src:
                self.recognizer.adjust_for_ambient_noise(src, duration=0.5)
                audio = self.recognizer.listen(src, timeout=10, phrase_time_limit=15)
            return self.recognizer.recognize_google(audio, language=lang_code)
        except Exception as e:
            print(f"Voice error: {e}")
            return None

    def speak(self, text, on_done=None):
        if not self.engine or self.speaking:
            return
        # Strip emoji for TTS
        import re
        clean = re.sub(r'[^\x00-\x7F\u0080-\u024F\u0600-\u06FF\u0900-\u097F\u4E00-\u9FFF\u3040-\u30FF]', '', text)
        clean = re.sub(r'\s+', ' ', clean).strip()
        self.speaking = True
        def _run():
            try:
                self.engine.say(clean)
                self.engine.runAndWait()
            except Exception:
                pass
            self.speaking = False
            if on_done:
                on_done()
        threading.Thread(target=_run, daemon=True).start()

    def stop(self):
        if self.engine:
            try:
                self.engine.stop()
            except Exception:
                pass
        self.speaking = False


# ─── Main App ─────────────────────────────────────────────────────────────────
class HealthBotApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Health Chatbot")
        self.geometry("1280x860")
        self.minsize(960, 700)
        self.configure(bg=C["bg_dark"])

        self.hist_mgr    = ChatHistoryManager()
        self.predictor   = SkinPredictor()
        self.llm         = LLMClient()
        self.translator  = TranslationService()
        self.voice       = VoiceService()

        self.current_cid  = None
        self.llm_messages = []
        self.pending_img  = None
        self.pending_tk   = None
        self.last_response = ""
        self.language     = tk.StringVar(value="English")
        self.auto_speak   = tk.BooleanVar(value=False)
        self.username     = tk.StringVar(value="You")

        self._build_ui()

        # ── Start: load most recent existing conv OR create exactly one new one ──
        existing = self.hist_mgr.sorted_list()
        if existing:
            self._load_conv(existing[0]["id"])
        else:
            self._new_chat()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main()

    def _build_sidebar(self):
        sb = tk.Frame(self, bg=C["bg_sidebar"], width=260)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(3, weight=1)
        sb.grid_columnconfigure(0, weight=1)

        # Logo
        lf = tk.Frame(sb, bg=C["bg_sidebar"], pady=16)
        lf.grid(row=0, column=0, sticky="ew", padx=12)
        tk.Label(lf, text="🩺", font=("Segoe UI Emoji", 22),
                 bg=C["bg_sidebar"], fg=C["accent2"]).pack(side="left")
        tk.Label(lf, text=" MedBot", font=("Segoe UI", 15, "bold"),
                 bg=C["bg_sidebar"], fg=C["txt"]).pack(side="left")

        # New Chat
        tk.Button(sb, text="＋  New Chat", font=("Segoe UI", 10),
                  bg=C["accent"], fg="white", activebackground=C["accent2"],
                  activeforeground="white", relief="flat", cursor="hand2",
                  padx=12, pady=8, command=self._new_chat
                  ).grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))

        tk.Label(sb, text="Chat History", font=("Segoe UI", 9, "bold"),
                 bg=C["bg_sidebar"], fg=C["txt3"], anchor="w"
                 ).grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 2))

        # History scroll
        hf = tk.Frame(sb, bg=C["bg_sidebar"])
        hf.grid(row=3, column=0, sticky="nsew")
        hf.grid_columnconfigure(0, weight=1)
        hf.grid_rowconfigure(0, weight=1)
        self.hist_canvas = tk.Canvas(hf, bg=C["bg_sidebar"], highlightthickness=0, bd=0)
        hs = tk.Scrollbar(hf, orient="vertical", command=self.hist_canvas.yview)
        self.hist_canvas.configure(yscrollcommand=hs.set)
        self.hist_canvas.grid(row=0, column=0, sticky="nsew")
        hs.grid(row=0, column=1, sticky="ns")
        self.hist_inner = tk.Frame(self.hist_canvas, bg=C["bg_sidebar"])
        self._hcw = self.hist_canvas.create_window((0, 0), window=self.hist_inner, anchor="nw")
        self.hist_inner.bind("<Configure>", lambda e: self.hist_canvas.configure(
            scrollregion=self.hist_canvas.bbox("all")))
        self.hist_canvas.bind("<Configure>", lambda e: self.hist_canvas.itemconfig(
            self._hcw, width=e.width))

        # Bottom controls
        bot = tk.Frame(sb, bg=C["bg_sidebar"], pady=10)
        bot.grid(row=4, column=0, sticky="ew", padx=12)
        bot.grid_columnconfigure(0, weight=1)

        tk.Label(bot, text="🌐 Language", font=("Segoe UI", 9),
                 bg=C["bg_sidebar"], fg=C["txt2"], anchor="w"
                 ).grid(row=0, column=0, sticky="w")
        lc = ttk.Combobox(bot, textvariable=self.language,
                           values=lang_display_list(), state="readonly", width=20)
        lc.grid(row=1, column=0, sticky="ew", pady=(2, 8))
        s = ttk.Style(); s.theme_use("clam")
        s.configure("TCombobox", fieldbackground=C["bg_input"], background=C["bg_input"],
                    foreground=C["txt"], selectbackground=C["accent"], bordercolor=C["border"])

        tk.Label(bot, text="👤 Username", font=("Segoe UI", 9),
                 bg=C["bg_sidebar"], fg=C["txt2"], anchor="w"
                 ).grid(row=2, column=0, sticky="w")
        tk.Entry(bot, textvariable=self.username, font=("Segoe UI", 10),
                 bg=C["bg_input"], fg=C["txt"], insertbackground=C["accent2"],
                 relief="flat", bd=4).grid(row=3, column=0, sticky="ew", pady=(2, 0))

    def _build_main(self):
        main = tk.Frame(self, bg=C["bg_dark"])
        main.grid(row=0, column=1, sticky="nsew")
        # row 0 = header (fixed), row 1 = chat (expands), row 2 = input+toolbar (fixed)
        main.grid_rowconfigure(0, weight=0)
        main.grid_rowconfigure(1, weight=1)
        main.grid_rowconfigure(2, weight=0)
        main.grid_columnconfigure(0, weight=1)

        # Header
        hdr = tk.Frame(main, bg=C["bg_sidebar"], height=56)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(0, weight=1)
        self.title_var = tk.StringVar(value="New Conversation")
        tk.Label(hdr, textvariable=self.title_var, font=("Segoe UI", 13, "bold"),
                 bg=C["bg_sidebar"], fg=C["txt"]).grid(row=0, column=0, sticky="w", padx=20, pady=16)
        self.status_var = tk.StringVar(value="● Ready")
        tk.Label(hdr, textvariable=self.status_var, font=("Segoe UI", 9),
                 bg=C["bg_sidebar"], fg=C["success"]).grid(row=0, column=1, sticky="e", padx=20)

        # Chat area
        cc = tk.Frame(main, bg=C["bg_chat"])
        cc.grid(row=1, column=0, sticky="nsew")
        cc.grid_rowconfigure(0, weight=1)
        cc.grid_columnconfigure(0, weight=1)
        self.chat_canvas = tk.Canvas(cc, bg=C["bg_chat"], highlightthickness=0, bd=0)
        cs = tk.Scrollbar(cc, orient="vertical", command=self.chat_canvas.yview)
        self.chat_canvas.configure(yscrollcommand=cs.set)
        self.chat_canvas.grid(row=0, column=0, sticky="nsew")
        cs.grid(row=0, column=1, sticky="ns")
        self.chat_frame = tk.Frame(self.chat_canvas, bg=C["bg_chat"])
        self._ccw = self.chat_canvas.create_window((0, 0), window=self.chat_frame, anchor="nw")
        self.chat_frame.bind("<Configure>", lambda e: self.chat_canvas.configure(
            scrollregion=self.chat_canvas.bbox("all")))
        self.chat_canvas.bind("<Configure>", lambda e: self.chat_canvas.itemconfig(
            self._ccw, width=e.width))
        self.chat_canvas.bind_all("<MouseWheel>", lambda e: self.chat_canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"))

        # Input area
        ia = tk.Frame(main, bg=C["bg_dark"], pady=6, padx=14)
        ia.grid(row=2, column=0, sticky="ew")
        ia.grid_columnconfigure(0, weight=1)

        self.preview_frame = tk.Frame(ia, bg=C["bg_dark"])
        self.preview_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        # Input box
        ib = tk.Frame(ia, bg=C["bg_input"], highlightbackground=C["border"], highlightthickness=1)
        ib.grid(row=1, column=0, sticky="ew")
        ib.grid_columnconfigure(1, weight=1)

        tk.Button(ib, text="📎", font=("Segoe UI Emoji", 14), bg=C["bg_input"],
                  fg=C["txt2"], activebackground=C["bg_hover"], relief="flat",
                  cursor="hand2", padx=8, pady=6, command=self._attach_image
                  ).grid(row=0, column=0, sticky="ns", padx=(6, 0))

        self.input_box = tk.Text(ib, height=3, font=("Segoe UI", 11),
                                 bg=C["bg_input"], fg=C["txt"],
                                 insertbackground=C["accent2"],
                                 relief="flat", bd=6, wrap="word",
                                 selectbackground=C["accent"])
        self.input_box.grid(row=0, column=1, sticky="ew")
        self.input_box.bind("<Return>", self._on_enter)
        self.input_box.bind("<Shift-Return>", lambda e: None)
        self._set_placeholder()

        tk.Button(ib, text="➤", font=("Segoe UI", 14), bg=C["bg_input"],
                  fg=C["accent"], activebackground=C["bg_hover"],
                  relief="flat", cursor="hand2", padx=10, pady=6,
                  command=self._send).grid(row=0, column=2, sticky="ns", padx=(0, 6))

        # ── Toolbar — voice & speak controls ─────────────────────────────────
        tb_outer = tk.Frame(ia, bg=C["bg_sidebar"],
                            highlightbackground=C["border"], highlightthickness=1)
        tb_outer.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        tb = tk.Frame(tb_outer, bg=C["bg_sidebar"], pady=6, padx=8)
        tb.pack(fill="x")

        # 🎤 Voice Input button — prominent, green accent
        self.mic_btn = tk.Button(
            tb, text="🎤  Speak to Type",
            font=("Segoe UI", 10, "bold"),
            bg="#1a7f37", fg="white",
            activebackground="#2ea043", activeforeground="white",
            relief="flat", cursor="hand2", padx=12, pady=6,
            command=self._voice_input)
        self.mic_btn.pack(side="left", padx=(0, 6))

        # 🔊 Speak Response button
        self.speak_btn = tk.Button(
            tb, text="🔊  Speak Response",
            font=("Segoe UI", 10, "bold"),
            bg=C["accent"], fg="white",
            activebackground=C["accent2"], activeforeground="white",
            relief="flat", cursor="hand2", padx=12, pady=6,
            command=self._speak_response)
        self.speak_btn.pack(side="left", padx=(0, 6))

        # ⏹ Stop Speaking button
        self.stop_btn = tk.Button(
            tb, text="⏹  Stop Speaking",
            font=("Segoe UI", 10, "bold"),
            bg="#6e1b1b", fg="white",
            activebackground=C["danger"], activeforeground="white",
            relief="flat", cursor="hand2", padx=12, pady=6,
            command=self._stop_speaking)
        self.stop_btn.pack(side="left", padx=(0, 6))
        self.stop_btn.config(state="disabled")

        # Separator
        tk.Frame(tb, bg=C["border"], width=1).pack(side="left", fill="y", padx=6)

        # Auto Speak checkbox
        tk.Checkbutton(
            tb, text="Auto Speak",
            variable=self.auto_speak,
            font=("Segoe UI", 9), bg=C["bg_sidebar"], fg=C["txt"],
            selectcolor=C["bg_input"], activebackground=C["bg_sidebar"],
            activeforeground=C["txt"], relief="flat"
        ).pack(side="left", padx=(0, 8))

        # Hint on right
        tk.Label(tb, text="Shift+Enter = newline  |  Enter = send",
                 font=("Segoe UI", 8), bg=C["bg_sidebar"], fg=C["txt3"]
                 ).pack(side="right")

    # ── Placeholder ───────────────────────────────────────────────────────────
    _PH = "Ask a health question or describe your symptoms..."

    def _set_placeholder(self):
        self.input_box.insert("1.0", self._PH)
        self.input_box.config(fg=C["txt3"])
        self.input_box.bind("<FocusIn>",  self._ph_clear)
        self.input_box.bind("<FocusOut>", self._ph_restore)

    def _ph_clear(self, e=None):
        if self.input_box.get("1.0", "end-1c") == self._PH:
            self.input_box.delete("1.0", "end")
            self.input_box.config(fg=C["txt"])

    def _ph_restore(self, e=None):
        if not self.input_box.get("1.0", "end-1c").strip():
            self.input_box.insert("1.0", self._PH)
            self.input_box.config(fg=C["txt3"])

    # ── History sidebar ───────────────────────────────────────────────────────
    def _refresh_hist(self):
        for w in self.hist_inner.winfo_children():
            w.destroy()
        for conv in self.hist_mgr.sorted_list():
            cid = conv["id"]
            active = cid == self.current_cid
            bg = C["bg_active"] if active else C["bg_sidebar"]
            row = tk.Frame(self.hist_inner, bg=bg, cursor="hand2")
            row.pack(fill="x", padx=6, pady=1)
            row.grid_columnconfigure(0, weight=1)

            tk.Label(row, text=f"💬  {conv.get('title','Untitled')[:30]}",
                     font=("Segoe UI", 9), bg=bg,
                     fg=C["accent2"] if active else C["txt"],
                     anchor="w", wraplength=165
                     ).grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 0))
            tk.Label(row, text=conv.get("updated","")[:10],
                     font=("Segoe UI", 8), bg=bg, fg=C["txt3"], anchor="w"
                     ).grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 4))
            tk.Button(row, text="🗑", font=("Segoe UI Emoji", 10), bg=bg,
                      fg=C["danger"], activebackground=C["bg_hover"],
                      relief="flat", cursor="hand2",
                      command=lambda c=cid: self._delete_conv(c)
                      ).grid(row=0, column=1, rowspan=2, padx=4)

            for child in row.winfo_children():
                child.bind("<Button-1>", lambda e, c=cid: self._load_conv(c))
            row.bind("<Button-1>", lambda e, c=cid: self._load_conv(c))

            def _enter(e, r=row, a=active, b=bg):
                if not a:
                    r.config(bg=C["bg_hover"])
                    for ch in r.winfo_children(): ch.config(bg=C["bg_hover"])
            def _leave(e, r=row, a=active, b=bg):
                r.config(bg=b)
                for ch in r.winfo_children(): ch.config(bg=b)
            row.bind("<Enter>", _enter)
            row.bind("<Leave>", _leave)

    def _delete_conv(self, cid):
        self.hist_mgr.delete(cid)
        if cid == self.current_cid:
            existing = self.hist_mgr.sorted_list()
            if existing:
                self._load_conv(existing[0]["id"])
            else:
                self._new_chat()
        else:
            self._refresh_hist()

    def _load_conv(self, cid):
        self.current_cid = cid
        self.llm_messages = []
        self.last_response = ""
        for w in self.chat_frame.winfo_children():
            w.destroy()
        for msg in self.hist_mgr.get_messages(cid):
            role = msg["role"]
            content = msg["content"]
            img = msg.get("image_path")
            if role == "user":
                self._bubble_user(content, img)
                if content:
                    self.llm_messages.append({"role": "user", "content": content})
            else:
                self._bubble_bot(content)
                self.last_response = content
                self.llm_messages.append({"role": "assistant", "content": content})
        title = self.hist_mgr.conversations[cid].get("title", "Conversation")
        self.title_var.set(title)
        self._refresh_hist()
        self._scroll_bottom()

    # ── New Chat ──────────────────────────────────────────────────────────────
    def _new_chat(self):
        self.current_cid = self.hist_mgr.new_conversation()
        self.llm_messages = []
        self.last_response = ""
        for w in self.chat_frame.winfo_children():
            w.destroy()
        self.title_var.set("New Conversation")
        self._refresh_hist()
        self._welcome()

    def _welcome(self):
        status = "✅ AI ready — Groq LLM connected." if self.llm.is_ready else "⚠️ AI offline — set GROQ_API_KEY."
        msg = (f"Hello! I'm MedBot 🩺\n\n"
               f"I'm your AI medical assistant. I can help you with:\n"
               f"• Medical questions and symptom guidance\n"
               f"• Skin disease analysis from photos (click 📎 to upload)\n"
               f"• Voice input — speak in your language, I'll understand\n"
               f"• Multilingual responses — select your language in the sidebar\n\n"
               f"{status}\n\n"
               f"⚕️ I'm an AI assistant. Always consult a licensed doctor for medical decisions.")
        self._bubble_bot(msg)

    # ── Chat Bubbles ──────────────────────────────────────────────────────────
    def _bubble_user(self, text, image_path=None):
        outer = tk.Frame(self.chat_frame, bg=C["bg_chat"], pady=6)
        outer.pack(fill="x", padx=20)
        wrap = tk.Frame(outer, bg=C["bg_chat"])
        wrap.pack(side="right")
        tk.Label(wrap, text=self.username.get() or "You",
                 font=("Segoe UI", 8, "bold"), bg=C["bg_chat"], fg=C["accent2"]
                 ).pack(anchor="e")
        bubble = tk.Frame(wrap, bg=C["bg_user"], padx=14, pady=10)
        bubble.pack(anchor="e")
        if image_path and os.path.exists(image_path) and PIL_AVAILABLE:
            try:
                img = Image.open(image_path)
                img.thumbnail((180, 180))
                photo = ImageTk.PhotoImage(img)
                lbl = tk.Label(bubble, image=photo, bg=C["bg_user"], relief="flat", bd=0)
                lbl.image = photo
                lbl.pack(anchor="e", pady=(0, 4))
                tk.Label(bubble, text=f"📎 {os.path.basename(image_path)}",
                         font=("Segoe UI", 8), bg=C["bg_user"], fg="#ffffffaa"
                         ).pack(anchor="e")
            except Exception:
                pass
        if text:
            tk.Label(bubble, text=text, font=("Segoe UI", 10),
                     bg=C["bg_user"], fg="white",
                     wraplength=480, justify="left", anchor="w").pack(anchor="w")
        self._scroll_bottom()

    def _bubble_bot(self, text):
        outer = tk.Frame(self.chat_frame, bg=C["bg_chat"], pady=6)
        outer.pack(fill="x", padx=20)
        wrap = tk.Frame(outer, bg=C["bg_chat"])
        wrap.pack(side="left", fill="x", expand=True)
        tk.Label(wrap, text="🩺 MedBot", font=("Segoe UI", 8, "bold"),
                 bg=C["bg_chat"], fg=C["accent"]).pack(anchor="w")
        bubble = tk.Frame(wrap, bg=C["bg_bot"], padx=14, pady=10)
        bubble.pack(anchor="w", fill="x")
        # Render markdown-style text with **bold** support
        self._render_markdown(bubble, text)
        self._scroll_bottom()

    def _render_markdown(self, parent, text):
        """Render text with **bold** and line structure into parent frame."""
        import re
        for line in text.split("\n"):
            line_frame = tk.Frame(parent, bg=C["bg_bot"])
            line_frame.pack(anchor="w", fill="x")
            if not line.strip():
                tk.Label(line_frame, text=" ", font=("Segoe UI", 4),
                         bg=C["bg_bot"]).pack(anchor="w")
                continue
            # Split line on **...**
            parts = re.split(r'(\*\*[^*]+\*\*)', line)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    word = part[2:-2]
                    tk.Label(line_frame, text=word,
                             font=("Segoe UI", 10, "bold"),
                             bg=C["bg_bot"], fg=C["txt"],
                             justify="left").pack(side="left")
                elif part:
                    tk.Label(line_frame, text=part,
                             font=("Segoe UI", 10),
                             bg=C["bg_bot"], fg=C["txt"],
                             wraplength=700, justify="left").pack(side="left")

    def _typing_indicator(self):
        outer = tk.Frame(self.chat_frame, bg=C["bg_chat"], pady=4)
        outer.pack(fill="x", padx=20)
        tk.Label(outer, text="🩺 MedBot is thinking...",
                 font=("Segoe UI", 10, "italic"),
                 bg=C["bg_chat"], fg=C["txt3"]).pack(side="left")
        return outer

    def _scroll_bottom(self):
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    # ── Image Attach ──────────────────────────────────────────────────────────
    def _attach_image(self):
        path = filedialog.askopenfilename(
            title="Select Skin Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("All", "*.*")])
        if not path:
            return
        self.pending_img = path
        for w in self.preview_frame.winfo_children():
            w.destroy()
        if PIL_AVAILABLE:
            try:
                img = Image.open(path); img.thumbnail((72, 72))
                ph = ImageTk.PhotoImage(img)
                lbl = tk.Label(self.preview_frame, image=ph, bg=C["bg_dark"])
                lbl.image = ph
                lbl.pack(side="left", padx=4)
                self.pending_tk = ph
            except Exception:
                pass
        tk.Label(self.preview_frame, text=f"📎 {os.path.basename(path)[:28]}",
                 font=("Segoe UI", 9), bg=C["bg_dark"], fg=C["accent2"]).pack(side="left")
        tk.Button(self.preview_frame, text="✕", font=("Segoe UI", 9),
                  bg=C["bg_dark"], fg=C["danger"], relief="flat", cursor="hand2",
                  command=self._clear_img).pack(side="left", padx=4)

    def _clear_img(self):
        self.pending_img = None
        self.pending_tk = None
        for w in self.preview_frame.winfo_children():
            w.destroy()

    # ── Send ──────────────────────────────────────────────────────────────────
    def _on_enter(self, e):
        if not (e.state & 0x1):
            self._send()
            return "break"

    def _send(self):
        raw = self.input_box.get("1.0", "end-1c").strip()
        if raw == self._PH:
            raw = ""
        img = self.pending_img
        if not raw and not img:
            return

        self.input_box.delete("1.0", "end")
        self.input_box.config(fg=C["txt"])
        self._clear_img()

        lang_name = self.language.get()
        trans_code = lang_trans_code(lang_name)
        sr_code    = lang_sr_code(lang_name)
        # Use cached translation from voice input if available, else translate now
        if hasattr(self, "_voice_en_cache") and self._voice_en_cache and raw:
            en_text = self._voice_en_cache
            self._voice_en_cache = None
        else:
            en_text = self.translator.to_english(raw, trans_code) if raw else ""

        self._bubble_user(raw or "", img)
        self.hist_mgr.add_message(self.current_cid, "user", raw or "", img)

        # Update sidebar title after first message
        title = self.hist_mgr.conversations.get(self.current_cid, {}).get("title", "New Chat")
        self.title_var.set(title)
        self._refresh_hist()

        typing = self._typing_indicator()
        self.status_var.set("⏳ Thinking...")
        threading.Thread(
            target=self._process,
            args=(en_text, img, trans_code, typing),
            daemon=True).start()

    def _process(self, en_text, image_path, lang_code, typing_w):
        try:
            prediction = ""
            if image_path:
                prediction = self._skin_predict(image_path)

            # Build user content for LLM
            if image_path and not en_text:
                content = f"The user uploaded a skin image for analysis. {prediction}"
            elif image_path and en_text:
                content = f"{en_text}\n\n{prediction}"
            else:
                content = en_text

            if content:
                self.llm_messages.append({"role": "user", "content": content})

            response_en = self.llm.chat(self.llm_messages)
            self.llm_messages.append({"role": "assistant", "content": response_en})

            response_final = self.translator.from_english(response_en, lang_code)
            self.after(0, lambda: self._show_response(response_final, typing_w, lang_code))
        except Exception as e:
            self.after(0, lambda: self._show_response(f"Error: {e}", typing_w, lang_code))

    def _skin_predict(self, path):
        if not self.predictor.loaded:
            return "[SKIN_ANALYSIS: Model not loaded. Ensure models/skin_model.pth exists.]"
        try:
            disease, conf, confident = self.predictor.predict(path)
            status = "HIGH_CONFIDENCE" if confident else "LOW_CONFIDENCE"
            return (f"[SKIN_ANALYSIS: disease={disease}, confidence={conf}%, status={status}]\n"
                    f"Please provide a detailed medical explanation of {disease} "
                    f"({'detected with ' + str(conf) + '% confidence' if confident else 'low confidence result — ' + str(conf) + '%'}).")
        except Exception as e:
            return f"[SKIN_ANALYSIS: Error — {e}]"

    def _show_response(self, text, typing_w, lang_code):
        typing_w.destroy()
        self._bubble_bot(text)
        self.last_response = text
        self.hist_mgr.add_message(self.current_cid, "assistant", text)
        self._refresh_hist()
        self.status_var.set("● Ready")
        if self.auto_speak.get():
            self._do_speak(text)

    # ── Voice Input ───────────────────────────────────────────────────────────
    def _voice_input(self):
        if not SR_AVAILABLE:
            messagebox.showinfo("Voice Input",
                "Install packages:\npip install SpeechRecognition pyaudio")
            return
        lang_name = self.language.get()
        sr_code   = lang_sr_code(lang_name)
        trans_code = lang_trans_code(lang_name)
        self.status_var.set(f"🎤 Listening in {lang_name}...")
        self.mic_btn.config(text="🎤 Listening...", state="disabled", bg="#9a6700")
        self.update()

        def _listen():
            # Listen in user's language
            raw_text = self.voice.listen(sr_code)
            if raw_text:
                # Translate to English for the LLM
                en_text = self.translator.to_english(raw_text, trans_code)
                self.after(0, lambda rt=raw_text, et=en_text: self._voice_done(rt, et))
            else:
                self.after(0, lambda: self._voice_done(None, None))

        threading.Thread(target=_listen, daemon=True).start()

    def _voice_done(self, raw_text, en_text):
        self.mic_btn.config(text="🎤  Speak to Type", state="normal", bg="#1a7f37")
        if raw_text:
            self.status_var.set("● Ready  |  ✓ Voice captured — press Enter to send")
            self._ph_clear()
            self.input_box.delete("1.0", "end")
            self.input_box.config(fg=C["txt"])
            # Show user's native language text in input box
            self.input_box.insert("1.0", raw_text)
            # Store the translated English version so _send doesn't re-translate
            self._voice_en_cache = en_text
        else:
            self.status_var.set("⚠ Could not recognize speech. Check your microphone and try again.")
            self._voice_en_cache = None

    # ── Voice Output ──────────────────────────────────────────────────────────
    def _speak_response(self):
        if not self.last_response:
            messagebox.showinfo("Nothing to speak", "No response to speak yet.")
            return
        if not TTS_AVAILABLE:
            messagebox.showinfo("Voice Output",
                "Install pyttsx3:\npip install pyttsx3")
            return
        self._do_speak(self.last_response)
        self.status_var.set(f"🔊 Speaking in {self.language.get()}...")

    def _do_speak(self, text):
        self.speak_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set("🔊 Speaking...")

        def on_done():
            self.after(0, self._speak_finished)

        self.voice.speak(text, on_done=on_done)

    def _speak_finished(self):
        self.speak_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_var.set("● Ready")

    def _stop_speaking(self):
        self.voice.stop()
        self._speak_finished()


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = HealthBotApp()
    app.mainloop()