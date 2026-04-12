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
 - Added Offline Medicine Database with detailed medicine information
 - Added Offline First Aid Guide with emergency procedures
 - Added Health Risk Calculator for personalized health risk assessment
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import os
import datetime
import uuid
import webbrowser
import urllib.request
import xml.etree.ElementTree as ET

# ─── PASTE YOUR GROQ API KEY HERE ────────────────────────────────────────────
GROQ_API_KEY = "paste_here"
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
    from gtts import gTTS
    import pygame
    pygame.mixer.init()
    TTS_AVAILABLE = True
    TTS_ENGINE = "gtts"
except Exception:
    try:
        import pyttsx3
        TTS_AVAILABLE = True
        TTS_ENGINE = "pyttsx3"
    except ImportError:
        TTS_AVAILABLE = False
        TTS_ENGINE = None

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

try:
    import feedparser
    FEED_AVAILABLE = True
except ImportError:
    FEED_AVAILABLE = False

# ─── Paths ────────────────────────────────────────────────────────────────────
_BASE      = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(_BASE, "..", "chat_history.json")
MODELS_DIR   = os.path.join(_BASE, "..", "models")
MEDICINE_FILE = os.path.join(_BASE, "..", "medicines.json")

# ─── Premium Color Palette — Deep Medical Teal Theme ─────────────────────────
C = {
    "bg_dark":       "#060f1b",
    "bg_sidebar":    "#091522",
    "bg_chat":       "#060f1b",
    "bg_input":      "#0e1f32",
    "bg_bot":        "#0c2040",
    "bg_hover":      "#132540",
    "bg_active":     "#0e2e50",
    "bg_card":       "#0a1c30",
    "accent":        "#00c4e8",
    "accent2":       "#50d8f4",
    "accent3":       "#0082c8",
    "bg_user":       "#0082c8",
    "success":       "#06d6a0",
    "warning":       "#ffd60a",
    "danger":        "#ef476f",
    "txt":           "#eaf6ff",
    "txt2":          "#88c4dc",
    "txt3":          "#366a86",
    "border":        "#1c4060",
    "border2":       "#102a40",
    "sep":           "#122e4a",
    "grad_start":    "#00c4e8",
    "grad_end":      "#0082c8",
}

# ─── Custom Drawing Helpers ──────────────────────────────────────────────────
def draw_rounded_rect(canvas, x1, y1, x2, y2, r=12, **kwargs):
    canvas.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, style="pieslice", **kwargs)
    canvas.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, style="pieslice", **kwargs)
    canvas.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, style="pieslice", **kwargs)
    canvas.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, style="pieslice", **kwargs)
    canvas.create_rectangle(x1+r, y1, x2-r, y2, **kwargs)
    canvas.create_rectangle(x1, y1+r, x2, y2-r, **kwargs)

class RoundedButton(tk.Frame):
    def __init__(self, parent, text="", command=None,
                 bg_color="#00b4d8", fg_color="#ffffff",
                 hover_color="#48cae4", width=140, height=36,
                 radius=10, font=("Segoe UI", 10, "bold"),
                 icon="", **kwargs):
        kwargs.pop("highlightthickness", None)
        kwargs.pop("bd", None)
        super().__init__(parent, bg=bg_color, width=width, height=height, **kwargs)
        self.pack_propagate(False)
        self.grid_propagate(False)

        self._bg = bg_color
        self._hover = hover_color
        self._fg = fg_color
        self._text = text
        self._icon = icon
        self._cmd = command
        self._font = font
        self._state = "normal"
        self._width = width
        self._height = height

        label_text = (f"{icon}  {text}").strip() if icon else text
        self._lbl = tk.Label(self, text=label_text, font=font, bg=bg_color, fg=fg_color, cursor="hand2", anchor="center")
        self._lbl.place(relx=0.5, rely=0.5, anchor="center")

        for w in (self, self._lbl):
            w.bind("<Enter>", lambda e: self._on_enter())
            w.bind("<Leave>", lambda e: self._on_leave())
            w.bind("<Button-1>", lambda e: self._on_click())

    def _set_bg(self, color):
        self.config(bg=color)
        self._lbl.config(bg=color)

    def _on_enter(self):
        if self._state == "normal":
            self._set_bg(self._hover)

    def _on_leave(self):
        if self._state == "normal":
            self._set_bg(self._bg)

    def _on_click(self):
        if self._state == "normal" and self._cmd:
            self._set_bg(self._hover)
            self.after(120, lambda: self._set_bg(self._bg))
            self._cmd()

    def config_state(self, state):
        self._state = state
        disabled_bg = "#1a3a4a"
        self._set_bg(disabled_bg if state == "disabled" else self._bg)
        self._lbl.config(fg="#3d6b8a" if state=="disabled" else self._fg)

    def update_text(self, text):
        self._text = text
        icon = self._icon
        label_text = (f"{icon}  {text}").strip() if icon else text
        self._lbl.config(text=label_text)


class GlowFrame(tk.Frame):
    def __init__(self, parent, accent=None, **kwargs):
        super().__init__(parent, **kwargs)
        if accent:
            tk.Frame(self, bg=accent, height=2).pack(side="top", fill="x")


# ─── Languages ────────────────────────────────────────────────────────────────
LANGUAGES = {
    "English": ("en", "en-US"),
    "Hindi": ("hi", "hi-IN"),
    "Urdu": ("ur", "ur-PK"),
    "Tamil": ("ta", "ta-IN"),
    "Telugu": ("te", "te-IN"),
    "Punjabi": ("pa", "pa-IN"),
    "Bengali": ("bn", "bn-IN"),
    "Gujarati": ("gu", "gu-IN"),
    "Marathi": ("mr", "mr-IN"),
    "Kannada": ("kn", "kn-IN"),
    "Malayalam": ("ml", "ml-IN"),
    "Spanish": ("es", "es-ES"),
    "French": ("fr", "fr-FR"),
    "German": ("de", "de-DE"),
    "Arabic": ("ar", "ar-SA"),
    "Chinese (Simplified)": ("zh-CN", "zh-CN"),
    "Japanese": ("ja", "ja-JP"),
    "Korean": ("ko", "ko-KR"),
    "Russian": ("ru", "ru-RU"),
}

def lang_trans_code(name):
    v = LANGUAGES.get(name, ("en", "en-US"))
    return v[0] if isinstance(v, tuple) else v

def lang_sr_code(name):
    v = LANGUAGES.get(name, ("en", "en-US"))
    return v[1] if isinstance(v, tuple) else "en-US"

def lang_display_list():
    return list(LANGUAGES.keys())

# ─── System Prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are MedBot, a highly knowledgeable and empathetic AI medical assistant specializing in dermatology and general health.

RESPONSE STYLE:
- Always give detailed, thorough, well-structured answers
- Use proper markdown: ## for headings, **bold** for key terms, * for bullets
- NEVER output raw ### symbols as text — always use them as proper headings
- NEVER write lines like '###Title###' or '**##word##**'
- Minimum 150 words per response unless the question is very simple
- Be warm, professional, and reassuring

YOUR CAPABILITIES:
1. Answer medical and health questions in depth
2. Analyze skin disease predictions from an AI model and explain them thoroughly
3. Provide detailed information about diseases, symptoms, causes, treatments, and prevention
4. Provide detailed medicine information including uses, dosage, side effects, and precautions
5. Provide first aid instructions for medical emergencies
6. Provide health risk assessment based on user health parameters
7. Guide users on when and why to seek professional medical help

IMPORTANT:
- Always add a brief reminder that you are an AI and a doctor should confirm any diagnosis
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
        msg = {"role": role, "content": content, "timestamp": datetime.datetime.now().isoformat()}
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
        return sorted(self.conversations.values(), key=lambda x: x.get("updated", ""), reverse=True)


# ─── Health Risk Calculator Service ────────────────────────────────────────────
class HealthRiskCalculator:
    """
    Calculates health risk based on user inputs:
    - Age, Weight, Height, Blood Pressure, Sugar level, Smoking habit
    """
    
    def __init__(self):
        pass
    
    def calculate_bmi(self, weight_kg, height_cm):
        """Calculate BMI from weight (kg) and height (cm)."""
        if height_cm <= 0 or weight_kg <= 0:
            return 0
        height_m = height_cm / 100
        bmi = weight_kg / (height_m * height_m)
        return round(bmi, 1)
    
    def get_bmi_category(self, bmi):
        """Get BMI category and risk level."""
        if bmi < 18.5:
            return "Underweight", "Low", "May need nutritional guidance"
        elif 18.5 <= bmi < 25:
            return "Normal weight", "Low", "Healthy weight range"
        elif 25 <= bmi < 30:
            return "Overweight", "Moderate", "Increased risk for heart disease, diabetes"
        elif 30 <= bmi < 35:
            return "Obese (Class I)", "High", "Significantly increased health risks"
        elif 35 <= bmi < 40:
            return "Obese (Class II)", "Very High", "High risk for cardiovascular diseases"
        else:
            return "Severely Obese (Class III)", "Critical", "Extremely high health risks"
    
    def assess_blood_pressure(self, systolic, diastolic):
        """Assess blood pressure reading."""
        if systolic < 90 or diastolic < 60:
            return "Low Blood Pressure", "Low", "May cause dizziness, fatigue"
        elif systolic < 120 and diastolic < 80:
            return "Normal", "Low", "Optimal blood pressure"
        elif systolic < 130 and diastolic < 80:
            return "Elevated", "Low-Moderate", "Monitor regularly"
        elif systolic < 140 or diastolic < 90:
            return "High Blood Pressure (Stage 1)", "Moderate", "Consult doctor for lifestyle changes"
        elif systolic < 180 or diastolic < 120:
            return "High Blood Pressure (Stage 2)", "High", "Medical attention recommended"
        else:
            return "Hypertensive Crisis", "Critical", "Seek immediate medical attention"
    
    def assess_blood_sugar(self, sugar_level, is_fasting=True):
        """Assess blood sugar level (mg/dL)."""
        if is_fasting:
            if sugar_level < 70:
                return "Low Blood Sugar (Hypoglycemia)", "High", "Eat/drink sugar immediately"
            elif 70 <= sugar_level < 100:
                return "Normal", "Low", "Healthy blood sugar level"
            elif 100 <= sugar_level < 126:
                return "Prediabetes", "Moderate", "Lifestyle changes recommended"
            elif 126 <= sugar_level < 200:
                return "Diabetes", "High", "Consult doctor for management"
            else:
                return "Very High Blood Sugar", "Critical", "Seek medical attention"
        else:
            if sugar_level < 70:
                return "Low Blood Sugar", "High", "Eat/drink sugar immediately"
            elif 70 <= sugar_level < 140:
                return "Normal", "Low", "Healthy blood sugar level"
            elif 140 <= sugar_level < 200:
                return "Prediabetes", "Moderate", "Monitor and consult doctor"
            else:
                return "Diabetes", "High", "Consult doctor for management"
    
    def calculate_risk_score(self, age, bmi, bp_risk, sugar_risk, smoking):
        """Calculate overall risk score (0-100)."""
        score = 0
        
        # Age risk (0-25 points)
        if age < 30:
            score += 5
        elif age < 40:
            score += 10
        elif age < 50:
            score += 15
        elif age < 60:
            score += 20
        else:
            score += 25
        
        # BMI risk (0-25 points)
        if bmi < 18.5:
            score += 10
        elif bmi < 25:
            score += 5
        elif bmi < 30:
            score += 15
        elif bmi < 35:
            score += 20
        else:
            score += 25
        
        # Blood pressure risk (0-25 points)
        bp_risk_map = {"Low": 5, "Low-Moderate": 10, "Moderate": 15, "High": 20, "Critical": 25}
        score += bp_risk_map.get(bp_risk, 10)
        
        # Blood sugar risk (0-15 points)
        sugar_risk_map = {"Low": 5, "Moderate": 10, "High": 13, "Critical": 15}
        score += sugar_risk_map.get(sugar_risk, 8)
        
        # Smoking habit (0-10 points)
        if smoking == "Non-smoker":
            score += 0
        elif smoking == "Former smoker":
            score += 5
        elif smoking == "Occasional smoker":
            score += 8
        else:  # Regular smoker
            score += 10
        
        return min(score, 100)
    
    def get_risk_level(self, score):
        """Get risk level based on score."""
        if score < 20:
            return "Very Low", "Excellent health profile. Keep up the good work!"
        elif score < 35:
            return "Low", "Good health. Minor improvements recommended."
        elif score < 50:
            return "Moderate", "Some health concerns. Consider lifestyle changes."
        elif score < 70:
            return "High", "Significant health risks. Consult a doctor."
        else:
            return "Very High", "Critical health risks. Seek medical attention promptly."
    
    def generate_recommendations(self, age, bmi, bmi_category, bp_result, sugar_result, smoking):
        """Generate personalized health recommendations."""
        recommendations = []
        
        # BMI recommendations
        if "Underweight" in bmi_category:
            recommendations.append("🍎 **Nutrition:** Increase calorie intake with nutrient-rich foods. Consult a nutritionist.")
        elif "Overweight" in bmi_category or "Obese" in bmi_category:
            recommendations.append("🏃 **Exercise:** Aim for 30 minutes of moderate exercise, 5 days a week.")
            recommendations.append("🥗 **Diet:** Reduce processed foods, increase fruits, vegetables, and whole grains.")
        
        # Blood pressure recommendations
        if "High" in bp_result or "Hypertensive" in bp_result:
            recommendations.append("💙 **Blood Pressure:** Reduce sodium intake, limit alcohol, manage stress.")
            recommendations.append("🩺 **Medical:** Monitor BP regularly and consult doctor for medication if needed.")
        elif "Low" in bp_result:
            recommendations.append("💧 **Blood Pressure:** Stay hydrated, increase salt moderately if advised by doctor.")
        
        # Blood sugar recommendations
        if "Prediabetes" in sugar_result or "Diabetes" in sugar_result:
            recommendations.append("🩸 **Blood Sugar:** Limit sugary foods and refined carbohydrates.")
            recommendations.append("🏃 **Lifestyle:** Regular exercise helps control blood sugar levels.")
            recommendations.append("🩺 **Medical:** Regular monitoring and doctor consultation essential.")
        elif "Low Blood Sugar" in sugar_result:
            recommendations.append("🍬 **Blood Sugar:** Eat small, frequent meals. Keep quick sugar sources handy.")
        
        # Smoking recommendations
        if smoking == "Regular smoker":
            recommendations.append("🚭 **Smoking:** Quit smoking to dramatically reduce heart disease and cancer risk.")
            recommendations.append("📞 **Support:** Consider nicotine replacement therapy or smoking cessation programs.")
        elif smoking == "Occasional smoker":
            recommendations.append("🚭 **Smoking:** Even occasional smoking increases health risks. Consider quitting completely.")
        elif smoking == "Former smoker":
            recommendations.append("👍 **Great job quitting smoking!** Continue maintaining a smoke-free lifestyle.")
        
        # Age-based recommendations
        if age >= 50:
            recommendations.append("📅 **Screening:** Regular health checkups including cancer screening recommended.")
        elif age >= 40:
            recommendations.append("📅 **Prevention:** Annual health checkups advised.")
        
        if not recommendations:
            recommendations.append("✅ **Great job!** Your health parameters look good. Maintain healthy lifestyle.")
        
        return recommendations
    
    def format_risk_response(self, data):
        """Format the complete risk assessment response."""
        age = data.get("age", 0)
        weight = data.get("weight", 0)
        height = data.get("height", 0)
        systolic = data.get("systolic", 0)
        diastolic = data.get("diastolic", 0)
        sugar = data.get("sugar", 0)
        sugar_fasting = data.get("sugar_fasting", True)
        smoking = data.get("smoking", "Non-smoker")
        
        # Calculate metrics
        bmi = self.calculate_bmi(weight, height)
        bmi_category, bmi_risk, bmi_advice = self.get_bmi_category(bmi)
        bp_result, bp_risk, bp_advice = self.assess_blood_pressure(systolic, diastolic)
        sugar_result, sugar_risk, sugar_advice = self.assess_blood_sugar(sugar, sugar_fasting)
        
        # Calculate overall risk
        risk_score = self.calculate_risk_score(age, bmi, bp_risk, sugar_risk, smoking)
        risk_level, risk_message = self.get_risk_level(risk_score)
        recommendations = self.generate_recommendations(age, bmi, bmi_category, bp_result, sugar_result, smoking)
        
        # Build response
        lines = [
            "## 📊 Health Risk Assessment Report",
            "",
            "### 📋 Your Health Parameters",
            f"• **Age:** {age} years",
            f"• **Weight:** {weight} kg",
            f"• **Height:** {height} cm",
            f"• **BMI:** {bmi} - {bmi_category}",
            f"• **Blood Pressure:** {systolic}/{diastolic} mmHg - {bp_result}",
            f"• **Blood Sugar:** {sugar} mg/dL ({'Fasting' if sugar_fasting else 'Random'}) - {sugar_result}",
            f"• **Smoking Status:** {smoking}",
            "",
            "### 🎯 Overall Risk Assessment",
            f"**Risk Score:** {risk_score}/100",
            f"**Risk Level:** **{risk_level}**",
            f"**Summary:** {risk_message}",
            "",
            "### 📈 Detailed Analysis",
            "",
            "**Body Mass Index (BMI):**",
            f"• Your BMI is {bmi} ({bmi_category})",
            f"• {bmi_advice}",
            "",
            "**Blood Pressure:**",
            f"• Your BP is {systolic}/{diastolic} mmHg ({bp_result})",
            f"• {bp_advice}",
            "",
            "**Blood Sugar:**",
            f"• Your sugar level is {sugar} mg/dL ({sugar_result})",
            f"• {sugar_advice}",
            "",
            "### 💡 Personalized Recommendations",
            ""
        ]
        
        for rec in recommendations:
            lines.append(rec)
        
        lines.extend([
            "",
            "---",
            "⚠️ **Medical Disclaimer:** This is an AI-generated risk assessment based on provided data. It is not a substitute for professional medical advice. Please consult a qualified healthcare provider for accurate diagnosis and treatment recommendations.",
            "",
            "🩺 **Next Steps:**",
            "• Share this report with your doctor",
            "• Schedule regular health checkups",
            "• Follow up on any abnormal readings"
        ])
        
        return "\n".join(lines)


# ─── Medicine Database Service ──────────────────────────────────────────────────
class MedicineDatabase:
    def __init__(self):
        self.medicines = {}
        self._load_database()
    
    def _load_database(self):
        try:
            if os.path.exists(MEDICINE_FILE):
                with open(MEDICINE_FILE, "r", encoding="utf-8") as f:
                    self.medicines = json.load(f)
                print(f"✓ Medicine database loaded: {len(self.medicines)} medicines")
            else:
                print(f"⚠️ medicines.json not found, creating sample database")
                self._create_sample_database()
        except Exception as e:
            print(f"Medicine DB load error: {e}")
            self.medicines = {}
    
    def _create_sample_database(self):
        sample = {
            "paracetamol": {
                "name": "Paracetamol (Acetaminophen)",
                "generic_name": "Acetaminophen",
                "brand_names": ["Crocin", "Dolo", "Tylenol", "P 500"],
                "category": ["Analgesic", "Antipyretic"],
                "indications": ["Fever", "Mild to moderate pain", "Headache", "Body aches"],
                "dosage": {"adults": "500-1000 mg every 4-6 hours (max 4000 mg/day)"},
                "how_to_take": "Take with or without food. Swallow tablets whole with water.",
                "side_effects": {"common": ["Nausea", "Headache"], "serious": ["Liver damage (overdose)"]},
                "contraindications": ["Severe liver disease", "Hypersensitivity to paracetamol"],
                "precautions": ["Do not exceed recommended dose", "Avoid alcohol while taking"],
                "prescription_required": False,
                "description": "Paracetamol is a widely used over-the-counter analgesic and antipyretic medication."
            },
            "ibuprofen": {
                "name": "Ibuprofen",
                "generic_name": "Ibuprofen",
                "brand_names": ["Brufen", "Motrin", "Advil", "Ibugesic"],
                "category": ["NSAID", "Analgesic", "Anti-inflammatory"],
                "indications": ["Fever", "Pain", "Inflammation", "Arthritis", "Menstrual cramps"],
                "dosage": {"adults": "200-400 mg every 4-6 hours (max 1200 mg/day)"},
                "how_to_take": "Take with food or milk to reduce stomach upset",
                "side_effects": {"common": ["Stomach upset", "Heartburn", "Nausea"], "serious": ["Stomach bleeding", "Kidney problems"]},
                "contraindications": ["Active stomach ulcer", "Bleeding disorders", "Severe kidney disease"],
                "precautions": ["Take with food to protect stomach", "Avoid alcohol"],
                "prescription_required": False,
                "description": "Ibuprofen is an NSAID that reduces hormones that cause inflammation and pain."
            }
        }
        os.makedirs(os.path.dirname(MEDICINE_FILE), exist_ok=True)
        with open(MEDICINE_FILE, "w", encoding="utf-8") as f:
            json.dump(sample, f, indent=2)
        self.medicines = sample
    
    def search_medicine(self, query):
        query_lower = query.lower().strip()
        results = []
        for key, data in self.medicines.items():
            if query_lower in key.lower():
                results.append((key, data))
                continue
            brand_names = data.get("brand_names", [])
            if isinstance(brand_names, list):
                for brand in brand_names:
                    if query_lower in brand.lower():
                        results.append((key, data))
                        break
            med_name = data.get("name", "").lower()
            if query_lower in med_name and (key, data) not in results:
                results.append((key, data))
        return results
    
    def format_medicine_response(self, query, results):
        if not results:
            return f"## 💊 Medicine Not Found\n\nI couldn't find information about **{query}** in the database.\n\n**Suggestions:**\n* Check the spelling\n* Try using the generic name\n* Ask your doctor or pharmacist for information\n\n⚕️ Always consult a healthcare professional before taking any medication."
        
        lines = [f"## 💊 Medicine Information: {query}", ""]
        for key, data in results[:3]:
            name = data.get("name", key.title())
            lines.append(f"### {name}")
            lines.append("")
            category = data.get("category", [])
            if category:
                cat_str = ', '.join(category) if isinstance(category, list) else str(category)
                lines.append(f"**Category:** {cat_str}")
                lines.append("")
            indications = data.get("indications", [])
            if indications:
                lines.append("**What it's used for:**")
                ind_list = indications if isinstance(indications, list) else [indications]
                for ind in ind_list[:5]:
                    lines.append(f"* {ind}")
                lines.append("")
            dosage = data.get("dosage", {})
            if dosage:
                lines.append("**Dosage:**")
                if isinstance(dosage, dict):
                    for age_group, dose in dosage.items():
                        lines.append(f"* {age_group.title()}: {dose}")
                else:
                    lines.append(f"* {dosage}")
                lines.append("")
            how_to = data.get("how_to_take", "")
            if how_to:
                lines.append(f"**How to take:** {how_to}")
                lines.append("")
            side_effects = data.get("side_effects", {})
            if side_effects:
                lines.append("**Possible Side Effects:**")
                if isinstance(side_effects, dict):
                    common = side_effects.get("common", [])
                    if common:
                        lines.append("*Common:*")
                        for se in common[:4]:
                            lines.append(f"  • {se}")
                    serious = side_effects.get("serious", [])
                    if serious:
                        lines.append("*Serious (seek medical attention):*")
                        for se in serious[:3]:
                            lines.append(f"  • {se}")
                lines.append("")
            rx = data.get("prescription_required", False)
            lines.append(f"**Prescription Required:** {'Yes ✓' if rx else 'No - OTC'}")
            lines.append("")
            lines.append("---")
            lines.append("")
        lines.append("⚠️ **Important Medical Disclaimer**\nThis information is for educational purposes only. Always consult a doctor or pharmacist before taking any medication.")
        return "\n".join(lines)


# ─── First Aid Guide Service ──────────────────────────────────────────────────
class FirstAidGuide:
    def __init__(self):
        self.first_aid_data = self._initialize_first_aid_data()
        print("✓ First Aid Guide initialized")
    
    def _initialize_first_aid_data(self):
        return {
            "burn": {
                "title": "🔥 Burns and Scalds",
                "categories": ["burn", "burns", "scald", "burnt"],
                "steps": [
                    "1️⃣ Cool the burn under cool running water for 10-15 minutes",
                    "2️⃣ Remove jewelry or tight clothing from burned area before swelling",
                    "3️⃣ Cover with sterile gauze or clean cloth",
                    "4️⃣ Take over-the-counter pain relievers if needed",
                    "5️⃣ Do NOT apply ice, butter, oil, or toothpaste",
                    "6️⃣ Do NOT break blisters"
                ],
                "when_to_seek_medical": [
                    "🚨 Burn covers a large area (larger than palm of hand)",
                    "🚨 Burn on face, hands, feet, genitals, or over joints",
                    "🚨 Signs of infection: increased pain, redness, swelling, fever",
                    "🚨 Chemical or electrical burns"
                ]
            },
            "cut": {
                "title": "🩸 Cuts and Bleeding",
                "categories": ["cut", "cuts", "wound", "bleeding", "laceration"],
                "steps": [
                    "1️⃣ Wash hands thoroughly with soap and water",
                    "2️⃣ Apply direct pressure with clean cloth for 5-10 minutes",
                    "3️⃣ Once bleeding stops, clean wound gently with running water",
                    "4️⃣ Remove visible debris with tweezers cleaned with alcohol",
                    "5️⃣ Apply antibiotic ointment",
                    "6️⃣ Cover with sterile bandage"
                ],
                "when_to_seek_medical": [
                    "🚨 Severe bleeding that won't stop after 15 minutes",
                    "🚨 Deep wound or longer than 1/2 inch",
                    "🚨 Caused by animal or human bite",
                    "🚨 Signs of infection develop"
                ]
            },
            "choking": {
                "title": "🫁 Choking",
                "categories": ["choking", "choke", "blocked airway", "can't breathe"],
                "adult_child": {
                    "name": "For Adults and Children > 1 year",
                    "steps": [
                        "1️⃣ Ask: 'Are you choking?' If they can speak/cough, encourage coughing",
                        "2️⃣ If cannot breathe, perform Heimlich maneuver:",
                        "   - Stand behind person, wrap arms around waist",
                        "   - Make fist, place above navel",
                        "   - Grasp fist with other hand, thrust inward and upward",
                        "   - Repeat until object is expelled"
                    ]
                },
                "infant": {
                    "name": "For Infants (< 1 year)",
                    "steps": [
                        "1️⃣ Hold infant face-down on your forearm",
                        "2️⃣ Give 5 back blows between shoulder blades",
                        "3️⃣ Turn face-up, give 5 chest thrusts (2 fingers on breastbone)",
                        "4️⃣ Repeat until object comes out"
                    ]
                },
                "when_to_call_emergency": [
                    "🚨 Person becomes unconscious",
                    "🚨 Cannot breathe after Heimlich",
                    "🚨 Infant is choking"
                ]
            },
            "heart_attack": {
                "title": "❤️ Heart Attack",
                "categories": ["heart attack", "chest pain", "cardiac"],
                "signs": [
                    "⚠️ Chest discomfort (pressure, squeezing, fullness)",
                    "⚠️ Pain in arms, back, neck, jaw, or stomach",
                    "⚠️ Shortness of breath",
                    "⚠️ Cold sweat, nausea, lightheadedness"
                ],
                "steps": [
                    "🚨 CALL EMERGENCY SERVICES IMMEDIATELY (108 in India)",
                    "🫀 Have person sit down, rest, and stay calm",
                    "🫀 Loosen tight clothing",
                    "🫀 If person has aspirin and is not allergic, have them chew one (300mg)",
                    "🫀 If unconscious and not breathing, begin CPR"
                ]
            },
            "stroke": {
                "title": "🧠 Stroke",
                "categories": ["stroke", "brain attack", "paralysis"],
                "fast_test": {
                    "title": "F.A.S.T. Test",
                    "items": [
                        "F - Face drooping: Ask person to smile",
                        "A - Arm weakness: Ask person to raise both arms",
                        "S - Speech difficulty: Ask person to repeat a sentence",
                        "T - Time to call emergency services (108)"
                    ]
                },
                "steps": [
                    "🚨 CALL EMERGENCY SERVICES IMMEDIATELY (108)",
                    "📝 Note the time symptoms started",
                    "🧠 Keep person calm and comfortable",
                    "🧠 Do not give food, drink, or medication"
                ]
            },
            "fracture": {
                "title": "🦴 Fractures and Broken Bones",
                "categories": ["fracture", "broken bone", "break", "sprain"],
                "steps": [
                    "1️⃣ Keep the person still and calm",
                    "2️⃣ Do NOT try to straighten or move the broken bone",
                    "3️⃣ Apply ice wrapped in cloth to reduce swelling",
                    "4️⃣ Immobilize using a splint or sling",
                    "5️⃣ Elevate the injured area if possible",
                    "6️⃣ Seek medical attention immediately"
                ],
                "signs": [
                    "✓ Intense pain at the injury site",
                    "✓ Swelling, bruising, or deformity",
                    "✓ Inability to move or use the affected area"
                ]
            },
            "seizure": {
                "title": "⚡ Seizures",
                "categories": ["seizure", "convulsion", "epilepsy", "fit"],
                "steps": [
                    "1️⃣ Stay calm and time the seizure",
                    "2️⃣ Clear area of sharp or hard objects",
                    "3️⃣ Cushion person's head with something soft",
                    "4️⃣ Loosen tight clothing around neck",
                    "5️⃣ Turn person on side to help breathing",
                    "6️⃣ Do NOT put anything in person's mouth",
                    "7️⃣ Do NOT restrain or hold person down"
                ],
                "when_to_call_ambulance": [
                    "🚨 Seizure lasts more than 5 minutes",
                    "🚨 Person has difficulty breathing",
                    "🚨 Repeated seizures without recovery",
                    "🚨 First-time seizure"
                ]
            },
            "cpr": {
                "title": "🫀 CPR (Cardiopulmonary Resuscitation)",
                "categories": ["cpr", "resuscitation", "heart stopped", "not breathing"],
                "adult_cpr": {
                    "name": "Adult CPR (Age 12+)",
                    "steps": [
                        "1️⃣ Check responsiveness: Tap shoulder and shout",
                        "2️⃣ Call emergency services (108)",
                        "3️⃣ Check breathing (no more than 10 seconds)",
                        "4️⃣ If not breathing, begin chest compressions:",
                        "   - Place heel of one hand on center of chest",
                        "   - Push hard and fast: 100-120 compressions per minute",
                        "   - Compress at least 2 inches (5 cm) deep",
                        "5️⃣ After 30 compressions, give 2 rescue breaths",
                        "6️⃣ Continue cycles of 30 compressions : 2 breaths"
                    ]
                }
            },
            "poisoning": {
                "title": "☠️ Poisoning",
                "categories": ["poison", "poisoning", "toxic", "overdose"],
                "steps": [
                    "☠️ CALL EMERGENCY SERVICES (108) or Poison Control",
                    "☠️ Try to identify what was swallowed, how much, and when",
                    "☠️ Do NOT induce vomiting unless told by medical professional",
                    "☠️ If chemical on skin, rinse with water for 15-20 minutes",
                    "☠️ If fumes inhaled, move person to fresh air immediately"
                ],
                "never_do": [
                    "❌ Do NOT induce vomiting",
                    "❌ Do NOT give anything by mouth unless directed",
                    "❌ Do NOT leave person alone"
                ]
            },
            "nosebleed": {
                "title": "👃 Nosebleed",
                "categories": ["nosebleed", "nose bleed", "bleeding nose"],
                "steps": [
                    "1️⃣ Sit upright and lean slightly forward (not backward)",
                    "2️⃣ Pinch soft part of nose just below bridge",
                    "3️⃣ Continue pinching for 10-15 minutes continuously",
                    "4️⃣ Apply cold compress to bridge of nose",
                    "5️⃣ Breathe through mouth"
                ],
                "when_to_seek_help": [
                    "🚨 Bleeding lasts more than 20 minutes",
                    "🚨 Bleeding is heavy",
                    "🚨 Caused by serious injury"
                ]
            },
            "snake_bite": {
                "title": "🐍 Snake Bite",
                "categories": ["snake bite", "snakebite", "venomous snake"],
                "steps": [
                    "🐍 CALL EMERGENCY SERVICES (108)",
                    "🐍 Keep person calm and still - movement spreads venom",
                    "🐍 Remove jewelry and tight clothing from affected limb",
                    "🐍 Position bite area below heart level",
                    "🐍 Clean wound with soap and water",
                    "🐍 Cover bite with clean, dry bandage"
                ],
                "what_not_to_do": [
                    "❌ Do NOT apply tourniquet",
                    "❌ Do NOT cut the wound",
                    "❌ Do NOT try to suck out venom"
                ]
            }
        }
    
    def search_first_aid(self, query):
        query_lower = query.lower().strip()
        results = []
        for key, data in self.first_aid_data.items():
            categories = data.get("categories", [])
            if any(cat in query_lower for cat in categories):
                results.append((key, data))
            elif query_lower in data.get("title", "").lower():
                results.append((key, data))
        return results
    
    def format_first_aid_response(self, query, results):
        if not results:
            return f"## 🚑 First Aid Not Found\n\nI couldn't find specific first aid instructions for **{query}**.\n\n**Try searching for:** burn, cut, choking, heart attack, stroke, fracture, seizure, poisoning, CPR\n\n🚨 For emergencies, call 108 immediately!"
        
        lines = [f"## 🚑 First Aid Guide: {results[0][1]['title']}", ""]
        
        for key, data in results[:2]:
            if "steps" in data:
                lines.append("### 📋 Immediate Steps")
                lines.append("")
                for step in data["steps"]:
                    lines.append(step)
                lines.append("")
            
            if "adult_child" in data:
                lines.append(f"### {data['adult_child']['name']}")
                for step in data['adult_child']['steps']:
                    lines.append(step)
                lines.append("")
            
            if "infant" in data:
                lines.append(f"### {data['infant']['name']}")
                for step in data['infant']['steps']:
                    lines.append(step)
                lines.append("")
            
            if "signs" in data:
                lines.append("### ⚠️ Signs to Watch For")
                for sign in data["signs"]:
                    lines.append(sign)
                lines.append("")
            
            if "when_to_seek_medical" in data:
                lines.append("### 🏥 When to See a Doctor")
                for item in data["when_to_seek_medical"]:
                    lines.append(item)
                lines.append("")
            
            if "when_to_call_emergency" in data:
                lines.append("### 🚨 When to Call Emergency")
                for item in data["when_to_call_emergency"]:
                    lines.append(item)
                lines.append("")
            
            if "fast_test" in data:
                lines.append("### 🔍 F.A.S.T. Test")
                for item in data["fast_test"]["items"]:
                    lines.append(f"* {item}")
                lines.append("")
            
            if "adult_cpr" in data:
                lines.append(f"### {data['adult_cpr']['name']}")
                for step in data['adult_cpr']['steps']:
                    lines.append(step)
                lines.append("")
            
            if "what_not_to_do" in data:
                lines.append("### ❌ What NOT to Do")
                for item in data["what_not_to_do"]:
                    lines.append(item)
                lines.append("")
        
        lines.append("")
        lines.append("---")
        lines.append("⚠️ **IMPORTANT: Call emergency services (108 in India) for any life-threatening emergency.**")
        
        return "\n".join(lines)


# ─── Skin Predictor ───────────────────────────────────────────────────────────
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
                self.model.classifier[1] = nn.Linear(self.model.last_channel, len(self.class_names))
                self.model.load_state_dict(torch.load(mf, map_location=self.device))
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
        return disease, pct, conf.item() >= 0.60


# ─── LLM Client (Groq) ────────────────────────────────────────────────────────
class LLMClient:
    MODEL = "llama-3.3-70b-versatile"

    def __init__(self):
        self.client = None
        key = GROQ_API_KEY.strip()
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
                return f"⚠️ Error communicating with AI: {e}"
        else:
            return "👋 Hello! I'm MedBot, your AI health assistant.\n\nI'm here to help you with medical questions, health guidance, first aid, and skin disease analysis."


# ─── Translation ──────────────────────────────────────────────────────────────
class TranslationService:
    def to_english(self, text, src_code):
        if src_code in ("en", "en-US") or not text or not TRANSLATE_AVAILABLE:
            return text
        short = src_code.split("-")[0] if "-" in src_code else src_code
        try:
            return GoogleTranslator(source=short, target="en").translate(text)
        except Exception:
            return text

    def from_english(self, text, dest_code):
        if dest_code in ("en", "en-US") or not text or not TRANSLATE_AVAILABLE:
            return text
        short = dest_code.split("-")[0] if "-" in dest_code else dest_code
        try:
            return GoogleTranslator(source="en", target=short).translate(text)
        except Exception:
            return text


# ─── Voice Service ──────────────────────────────────────────────────────────
class VoiceService:
    def __init__(self):
        self.recognizer = sr.Recognizer() if SR_AVAILABLE else None
        self.speaking = False
        self._stop_flag = False

    def listen(self, lang_code="en-US"):
        if not self.recognizer:
            return None
        try:
            with sr.Microphone() as src:
                self.recognizer.adjust_for_ambient_noise(src, duration=0.5)
                audio = self.recognizer.listen(src, timeout=10, phrase_time_limit=15)
            return self.recognizer.recognize_google(audio, language=lang_code)
        except Exception:
            return None

    def speak(self, text, lang_code="en", on_done=None):
        if self.speaking:
            if on_done:
                on_done()
            return
        if not TTS_AVAILABLE:
            if on_done:
                on_done()
            return

        import re, tempfile, os as _os, time
        clean = re.sub(r'[^\x00-\x7F\u0080-\u024F\u0600-\u06FF\u0900-\u097F\u4E00-\u9FFF]', '', text)
        clean = re.sub(r'#+\s*', '', clean)
        clean = re.sub(r'\*{1,3}', '', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        if not clean:
            if on_done:
                on_done()
            return

        short = lang_code.split("-")[0].lower() if "-" in lang_code else lang_code.lower()
        self.speaking = True
        self._stop_flag = False

        def _run():
            try:
                if TTS_ENGINE == "gtts":
                    from gtts import gTTS
                    import pygame
                    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                    tmp.close()
                    tts = gTTS(text=clean[:500], lang=short, slow=False)
                    tts.save(tmp.name)
                    if not self._stop_flag:
                        pygame.mixer.music.load(tmp.name)
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy() and not self._stop_flag:
                            time.sleep(0.1)
                        pygame.mixer.music.stop()
                    _os.remove(tmp.name)
            except Exception as e:
                print(f"TTS error: {e}")
            finally:
                self.speaking = False
                if on_done:
                    on_done()

        threading.Thread(target=_run, daemon=True).start()

    def stop(self):
        self._stop_flag = True
        self.speaking = False
        if TTS_ENGINE == "gtts":
            try:
                import pygame
                pygame.mixer.music.stop()
            except Exception:
                pass


# ─── Outbreak Alert Service ──────────────────────────────────────────────────
class OutbreakService:
    WHO_RSS = "https://www.who.int/feeds/entity/csr/don/en/rss.xml"

    RISK_KEYWORDS = {
        "high": ["outbreak", "epidemic", "emergency", "alert", "surge"],
        "medium": ["increase", "cases", "monitoring", "watch"],
        "low": ["seasonal", "mild", "contained"],
    }

    def fetch_alerts(self, country="India", state=""):
        alerts = []
        try:
            alerts += self._fetch_who(country, state)
        except Exception as e:
            print(f"WHO fetch error: {e}")
        if not alerts:
            alerts = self._fallback_alerts(country)
        return alerts[:8]

    def _fetch_who(self, country, state):
        results = []
        try:
            req = urllib.request.Request(self.WHO_RSS, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                raw = r.read().decode("utf-8")
            root = ET.fromstring(raw)
            country_lower = country.lower()
            for item in root.findall(".//item")[:15]:
                title = ""
                desc = ""
                for child in item:
                    tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if tag == "title":
                        title = child.text or ""
                    if tag == "description":
                        desc = child.text or ""
                combined = (title + " " + desc).lower()
                if country_lower in combined or "global" in combined:
                    risk = self._assess_risk(combined)
                    results.append({
                        "title": title[:100],
                        "summary": desc[:300] if desc else "See WHO website",
                        "risk": risk,
                        "source": "WHO",
                    })
        except Exception:
            pass
        return results

    def _assess_risk(self, text):
        text = text.lower()
        for level, keywords in self.RISK_KEYWORDS.items():
            if any(k in text for k in keywords):
                return level
        return "info"

    def _fallback_alerts(self, country):
        return [{
            "title": f"No active alerts found for {country}",
            "summary": "No major disease outbreaks reported at this time.",
            "risk": "info",
            "source": "Info",
        }]

    def format_for_llm(self, alerts, country, state):
        if not alerts:
            return ""
        lines = [f"LIVE DISEASE OUTBREAK ALERTS for {country}:"]
        for a in alerts:
            risk_icon = {"high": "🔴", "medium": "🟡", "low": "🟢", "info": "🔵"}.get(a["risk"], "⚪")
            lines.append(f"{risk_icon} [{a['source']}] {a['title']}")
        return "\n".join(lines)


# ─── Vaccination Service ──────────────────────────────────────────────────────
class VaccinationService:
    INDIA_SCHEDULE = {
        "At Birth": [("BCG", "TB prevention"), ("OPV-0", "Polio"), ("Hepatitis B", "Birth dose")],
        "6 Weeks": [("DPT-1", "Diphtheria/Pertussis/Tetanus"), ("OPV-1", "Polio"), ("Hib-1", "Meningitis")],
        "10 Weeks": [("DPT-2", "Second dose"), ("OPV-2", "Polio"), ("Hib-2", "Second dose")],
        "14 Weeks": [("DPT-3", "Third dose"), ("OPV-3", "Polio"), ("Hib-3", "Third dose")],
        "9 Months": [("MR/MMR-1", "Measles/Rubella"), ("Vitamin A", "First dose")],
        "16-24 Months": [("DPT Booster", "First booster"), ("MR/MMR-2", "Second dose")],
        "5 Years": [("DPT Booster-2", "School booster")],
        "10-12 Years": [("Td Booster", "Tetanus booster"), ("HPV (Girls)", "Cervical cancer")],
        "Adults": [("Td/Tdap", "Every 10 years"), ("Influenza", "Yearly"), ("COVID-19", "As advised")],
    }

    def format_schedule(self, age=None, for_pregnant=False, for_travel=False):
        lines = ["## Vaccination Schedule"]
        if for_travel:
            lines.append("**Travel Vaccines:** Yellow Fever, Meningococcal, Typhoid, Hepatitis A")
        elif for_pregnant:
            lines.append("**Pregnancy:** Td vaccine (2 doses), Influenza vaccine")
        elif age is not None:
            lines.append(f"**For Age {age} years:**")
            if age < 1:
                lines.append("* Birth to 14 weeks: BCG, OPV, DPT, Hib, Hepatitis B, Rotavirus")
            elif age <= 5:
                lines.append("* 9 months to 5 years: MMR, Vitamin A, DPT booster")
            else:
                lines.append("* 10+ years: Td booster, HPV (girls), COVID-19")
        else:
            for period, vaccines in self.INDIA_SCHEDULE.items():
                lines.append(f"### {period}")
                for v in vaccines:
                    lines.append(f"* {v[0]} - {v[1]}")
        lines.append("\n**Booking:** cowin.gov.in | Practo | 1mg | Govt hospitals free")
        return "\n".join(lines)


# ─── Main App ─────────────────────────────────────────────────────────────────
class HealthBotApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MedBot — AI Health Assistant")
        self.geometry("1400x920")
        self.minsize(1000, 740)
        self.configure(bg=C["bg_dark"])

        self.hist_mgr = ChatHistoryManager()
        self.predictor = SkinPredictor()
        self.llm = LLMClient()
        self.translator = TranslationService()
        self.voice = VoiceService()
        self.outbreak_svc = OutbreakService()
        self.vaccine_svc = VaccinationService()
        self.medicine_db = MedicineDatabase()
        self.first_aid = FirstAidGuide()
        self.risk_calculator = HealthRiskCalculator()  # Added health risk calculator

        self.current_cid = None
        self.llm_messages = []
        self.pending_img = None
        self.pending_tk = None
        self.last_response = ""
        self.language = tk.StringVar(value="English")
        self.auto_speak = tk.BooleanVar(value=False)
        self.username = tk.StringVar(value="You")
        self.user_country = tk.StringVar(value="India")
        self.user_state = tk.StringVar(value="")

        self._build_ui()

        existing = self.hist_mgr.sorted_list()
        if existing:
            self._load_conv(existing[0]["id"])
        else:
            self._new_chat()

    # ─── UI Building ────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._apply_ttk_styles()
        self._build_sidebar()
        self._build_main()

    def _apply_ttk_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox",
                        fieldbackground=C["bg_input"],
                        background=C["bg_input"],
                        foreground=C["txt"],
                        selectbackground=C["accent"],
                        selectforeground=C["txt"],
                        bordercolor=C["border"],
                        arrowcolor=C["accent"],
                        padding=6)
        style.configure("Vertical.TScrollbar",
                        background=C["bg_dark"],
                        troughcolor=C["bg_dark"],
                        arrowcolor=C["accent"],
                        width=8)

    def _build_sidebar(self):
        sb = tk.Frame(self, bg=C["bg_sidebar"], width=285)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(2, weight=1)
        sb.grid_columnconfigure(0, weight=1)

        tk.Frame(sb, bg=C["accent"], height=3).grid(row=0, column=0, sticky="ew")

        logo_frame = tk.Frame(sb, bg=C["bg_sidebar"], pady=14)
        logo_frame.grid(row=1, column=0, sticky="ew", padx=14)

        icon_frame = tk.Frame(logo_frame, bg=C["accent"], width=48, height=48)
        icon_frame.pack(side="left")
        icon_frame.pack_propagate(False)
        tk.Label(icon_frame, text="🩺", font=("Segoe UI Emoji", 22), bg=C["accent"], fg="white").place(relx=0.5, rely=0.5, anchor="center")

        name_frame = tk.Frame(logo_frame, bg=C["bg_sidebar"])
        name_frame.pack(side="left", padx=10)
        tk.Label(name_frame, text="MedBot", font=("Segoe UI", 17, "bold"), bg=C["bg_sidebar"], fg=C["txt"]).pack(anchor="w")
        tk.Label(name_frame, text="AI Health Assistant", font=("Segoe UI", 9), bg=C["bg_sidebar"], fg=C["txt2"]).pack(anchor="w")

        self._tab_frames = {}
        self._tab_labels = {}
        self._active_tab = tk.StringVar(value="chats")

        tab_container = tk.Frame(sb, bg=C["sep"], height=1)
        tab_container.grid(row=2, column=0, sticky="nsew")
        tab_container.grid_rowconfigure(1, weight=1)
        tab_container.grid_columnconfigure(0, weight=1)

        tabs_row = tk.Frame(tab_container, bg=C["bg_card"])
        tabs_row.grid(row=0, column=0, sticky="ew")

        def make_tab(text, name, icon):
            f = tk.Frame(tabs_row, bg=C["bg_card"], cursor="hand2")
            f.pack(side="left", fill="x", expand=True)
            lbl = tk.Label(f, text=f"{icon}  {text}", font=("Segoe UI", 9, "bold"), bg=C["bg_card"], fg=C["txt3"], pady=11, cursor="hand2")
            lbl.pack(fill="x")
            bar = tk.Frame(f, bg=C["bg_card"], height=3)
            bar.pack(fill="x")
            self._tab_labels[name] = (lbl, bar, f)

            def activate(n=name):
                for nm, (lb, br, fr) in self._tab_labels.items():
                    is_active = nm == n
                    lb.config(fg=C["accent"] if is_active else C["txt3"], bg=C["bg_card"])
                    br.config(bg=C["accent"] if is_active else C["bg_card"])
                    fr.config(bg=C["bg_card"])
                for nm, tf in self._tab_frames.items():
                    tf.grid() if nm == n else tf.grid_remove()
                self._active_tab.set(n)

            lbl.bind("<Button-1>", lambda e, a=activate: a())
            f.bind("<Button-1>", lambda e, a=activate: a())
            return activate

        activate_chats = make_tab("Chats", "chats", "💬")
        activate_settings = make_tab("Settings", "settings", "⚙")

        content_area = tk.Frame(tab_container, bg=C["bg_sidebar"])
        content_area.grid(row=1, column=0, sticky="nsew")
        content_area.grid_rowconfigure(0, weight=1)
        content_area.grid_columnconfigure(0, weight=1)

        # CHAT TAB
        chat_tab = tk.Frame(content_area, bg=C["bg_sidebar"])
        chat_tab.grid(row=0, column=0, sticky="nsew")
        chat_tab.grid_rowconfigure(1, weight=1)
        chat_tab.grid_columnconfigure(0, weight=1)
        self._tab_frames["chats"] = chat_tab

        nc_frame = tk.Frame(chat_tab, bg=C["bg_sidebar"], pady=10)
        nc_frame.grid(row=0, column=0, sticky="ew", padx=12)
        nc_frame.grid_columnconfigure(0, weight=1)
        nc_btn = RoundedButton(nc_frame, text="New Chat", icon="＋", bg_color=C["accent"], hover_color=C["accent2"], fg_color="#ffffff", width=255, height=40, radius=10, font=("Segoe UI", 10, "bold"), command=self._new_chat)
        nc_btn.grid(row=0, column=0, sticky="ew")

        tk.Label(chat_tab, text="RECENT CHATS", font=("Segoe UI", 8, "bold"), bg=C["bg_sidebar"], fg=C["txt2"], anchor="w").grid(row=1, column=0, sticky="new", padx=16, pady=(6, 2))

        hf = tk.Frame(chat_tab, bg=C["bg_sidebar"])
        hf.grid(row=1, column=0, sticky="nsew", pady=(22, 0))
        hf.grid_columnconfigure(0, weight=1)
        hf.grid_rowconfigure(0, weight=1)

        self.hist_canvas = tk.Canvas(hf, bg=C["bg_sidebar"], highlightthickness=0, bd=0)
        hs = ttk.Scrollbar(hf, orient="vertical", command=self.hist_canvas.yview, style="Vertical.TScrollbar")
        self.hist_canvas.configure(yscrollcommand=hs.set)
        self.hist_canvas.grid(row=0, column=0, sticky="nsew")
        hs.grid(row=0, column=1, sticky="ns")
        self.hist_inner = tk.Frame(self.hist_canvas, bg=C["bg_sidebar"])
        self._hist_win_id = self.hist_canvas.create_window((0, 0), window=self.hist_inner, anchor="nw")
        self.hist_inner.bind("<Configure>", lambda e: self.hist_canvas.configure(scrollregion=self.hist_canvas.bbox("all")))
        self.hist_canvas.bind("<Configure>", lambda e: self.hist_canvas.itemconfig(self._hist_win_id, width=e.width))

        # SETTINGS TAB
        settings_tab = tk.Frame(content_area, bg=C["bg_sidebar"])
        settings_tab.grid(row=0, column=0, sticky="nsew")
        settings_tab.grid_remove()
        settings_tab.grid_rowconfigure(0, weight=1)
        settings_tab.grid_columnconfigure(0, weight=1)
        self._tab_frames["settings"] = settings_tab

        sc = tk.Canvas(settings_tab, bg=C["bg_sidebar"], highlightthickness=0, bd=0)
        ss = ttk.Scrollbar(settings_tab, orient="vertical", command=sc.yview, style="Vertical.TScrollbar")
        sc.configure(yscrollcommand=ss.set)
        sc.grid(row=0, column=0, sticky="nsew")
        ss.grid(row=0, column=1, sticky="ns")
        sf = tk.Frame(sc, bg=C["bg_sidebar"])
        sc.create_window((0, 0), window=sf, anchor="nw")
        sf.bind("<Configure>", lambda e: sc.configure(scrollregion=sc.bbox("all")))
        sf.grid_columnconfigure(0, weight=1)

        row = [0]
        def R(): r = row[0]; row[0] += 1; return r

        def section_header(text):
            tk.Label(sf, text=text, font=("Segoe UI", 8, "bold"), bg=C["bg_sidebar"], fg=C["accent"], anchor="w").grid(row=R(), column=0, sticky="ew", padx=14, pady=(12, 0))
            tk.Frame(sf, bg=C["sep"], height=1).grid(row=R(), column=0, sticky="ew", padx=14, pady=(2, 6))

        def field_label(text):
            tk.Label(sf, text=text, font=("Segoe UI", 9), bg=C["bg_sidebar"], fg=C["txt2"], anchor="w").grid(row=R(), column=0, sticky="w", padx=14, pady=(4, 0))

        def styled_entry(var):
            f = tk.Frame(sf, bg=C["border"], bd=0)
            f.grid(row=R(), column=0, sticky="ew", padx=14, pady=(2, 0))
            tk.Entry(f, textvariable=var, font=("Segoe UI", 10), bg=C["bg_input"], fg=C["txt"], insertbackground=C["accent"], relief="flat", bd=8, highlightthickness=0).pack(fill="x")

        section_header("⚙ PREFERENCES")
        field_label("🌐 Language")
        ttk.Combobox(sf, textvariable=self.language, values=lang_display_list(), state="readonly", width=22).grid(row=R(), column=0, sticky="ew", padx=14, pady=(2, 0))
        field_label("👤 Username")
        styled_entry(self.username)

        section_header("📍 YOUR LOCATION")
        field_label("🌍 Country")
        styled_entry(self.user_country)
        field_label("📍 State / City")
        styled_entry(self.user_state)

        section_header("🏥 HEALTH TOOLS")
        
        # Disease Alerts Button
        self.alert_btn = RoundedButton(sf, text="Check Disease Alerts", icon="🚨", bg_color=C["danger"], hover_color="#ff6b6b", fg_color="#ffffff", width=249, height=40, radius=10, font=("Segoe UI", 9, "bold"), command=self._fetch_and_show_alerts)
        self.alert_btn.grid(row=R(), column=0, sticky="ew", padx=12, pady=(0, 8))
        
        # Vaccination Schedule Button
        vacc_btn = RoundedButton(sf, text="Vaccination Schedule", icon="💉", bg_color="#059669", hover_color="#10b981", fg_color="#ffffff", width=249, height=40, radius=10, font=("Segoe UI", 9, "bold"), command=self._show_vaccination_dialog)
        vacc_btn.grid(row=R(), column=0, sticky="ew", padx=12, pady=(0, 8))
        
        # Medicine Database Button
        med_btn = RoundedButton(sf, text="Medicine Database", icon="💊", bg_color="#7c3aed", hover_color="#8b5cf6", fg_color="#ffffff", width=249, height=40, radius=10, font=("Segoe UI", 9, "bold"), command=self._show_medicine_dialog)
        med_btn.grid(row=R(), column=0, sticky="ew", padx=12, pady=(0, 8))
        
        # First Aid Guide Button
        firstaid_btn = RoundedButton(sf, text="First Aid Guide", icon="🚑", bg_color="#e67e22", hover_color="#f39c12", fg_color="#ffffff", width=249, height=40, radius=10, font=("Segoe UI", 9, "bold"), command=self._show_first_aid_dialog)
        firstaid_btn.grid(row=R(), column=0, sticky="ew", padx=12, pady=(0, 8))
        
        # Health Risk Calculator Button
        risk_btn = RoundedButton(sf, text="Health Risk Calculator", icon="📊", bg_color="#d97706", hover_color="#f59e0b", fg_color="#ffffff", width=249, height=40, radius=10, font=("Segoe UI", 9, "bold"), command=self._show_risk_calculator_dialog)
        risk_btn.grid(row=R(), column=0, sticky="ew", padx=12, pady=(0, 8))

        # ── FREE TELEMEDICINE section ────────────────────────────────────────
        section_header("🏥 FREE TELEMEDICINE")

        # Subtle description label
        tk.Label(sf, text="Connect to a real government doctor — FREE",
                 font=("Segoe UI", 8), bg=C["bg_sidebar"],
                 fg=C["txt3"], anchor="w", wraplength=230
                 ).grid(row=R(), column=0, sticky="ew", padx=14, pady=(0, 4))

        # eSanjeevani button — teal green to stand out as important
        esanj_btn = RoundedButton(
            sf, text="eSanjeevani Free Doctor", icon="🏥",
            bg_color="#0d9488", hover_color="#14b8a6",
            fg_color="#ffffff", width=249, height=40,
            radius=10, font=("Segoe UI", 9, "bold"),
            command=self._show_esanjeevani)
        esanj_btn.grid(row=R(), column=0, sticky="ew", padx=12, pady=(0, 4))

        # Government badge label under the button
        tk.Label(sf, text="🇮🇳  Ministry of Health & Family Welfare, India",
                 font=("Segoe UI", 7), bg=C["bg_sidebar"],
                 fg=C["txt3"], anchor="w").grid(
            row=R(), column=0, sticky="ew", padx=14, pady=(0, 8))

        self.alert_status = tk.Label(sf, text="", font=("Segoe UI", 8), bg=C["bg_sidebar"], fg=C["txt3"], anchor="w", wraplength=220, justify="left")
        self.alert_status.grid(row=R(), column=0, sticky="ew", padx=14, pady=(0, 12))

        activate_chats()

    def _build_main(self):
        main = tk.Frame(self, bg=C["bg_dark"])
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(0, weight=0)
        main.grid_rowconfigure(1, weight=1)
        main.grid_rowconfigure(2, weight=0)
        main.grid_columnconfigure(0, weight=1)

        hdr = tk.Frame(main, bg=C["bg_card"], height=68)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(1, weight=1)

        tk.Frame(hdr, bg=C["accent"], width=5).grid(row=0, column=0, sticky="ns")

        title_area = tk.Frame(hdr, bg=C["bg_card"])
        title_area.grid(row=0, column=1, sticky="ew", padx=18)
        self.title_var = tk.StringVar(value="New Conversation")
        tk.Label(title_area, textvariable=self.title_var, font=("Segoe UI", 14, "bold"), bg=C["bg_card"], fg=C["txt"]).pack(anchor="w", pady=(12, 0))
        model_label = "Llama-3.3 · Groq AI" if self.llm.is_ready else "Offline mode"
        tk.Label(title_area, text=model_label, font=("Segoe UI", 8), bg=C["bg_card"], fg=C["txt3"]).pack(anchor="w")

        right_hdr = tk.Frame(hdr, bg=C["bg_card"])
        right_hdr.grid(row=0, column=2, sticky="e", padx=18)

        status_pill = tk.Frame(right_hdr, bg=C["bg_dark"], highlightbackground=C["border"], highlightthickness=1)
        status_pill.pack(side="right")
        self._status_dot = tk.Label(status_pill, text="●", font=("Segoe UI", 10), bg=C["bg_dark"], fg=C["success"])
        self._status_dot.pack(side="left", padx=(10, 3), pady=6)
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(status_pill, textvariable=self.status_var, font=("Segoe UI", 10), bg=C["bg_dark"], fg=C["txt2"]).pack(side="left", padx=(0, 10), pady=6)

        tk.Frame(main, bg=C["accent"], height=2).grid(row=0, column=0, sticky="ew", pady=(68, 0))

        cc = tk.Frame(main, bg=C["bg_chat"])
        cc.grid(row=1, column=0, sticky="nsew")
        cc.grid_rowconfigure(0, weight=1)
        cc.grid_columnconfigure(0, weight=1)
        self.chat_canvas = tk.Canvas(cc, bg=C["bg_chat"], highlightthickness=0, bd=0)
        cs = ttk.Scrollbar(cc, orient="vertical", command=self.chat_canvas.yview, style="Vertical.TScrollbar")
        self.chat_canvas.configure(yscrollcommand=cs.set)
        self.chat_canvas.grid(row=0, column=0, sticky="nsew")
        cs.grid(row=0, column=1, sticky="ns")
        self.chat_frame = tk.Frame(self.chat_canvas, bg=C["bg_chat"])
        self._chat_win_id = self.chat_canvas.create_window((0, 0), window=self.chat_frame, anchor="nw")
        self.chat_frame.bind("<Configure>", lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))
        self.chat_canvas.bind("<Configure>", lambda e: self.chat_canvas.itemconfig(self._chat_win_id, width=e.width))

        input_zone = tk.Frame(main, bg=C["bg_dark"])
        input_zone.grid(row=2, column=0, sticky="ew")
        input_zone.grid_columnconfigure(0, weight=1)
        tk.Frame(input_zone, bg=C["sep"], height=1).grid(row=0, column=0, sticky="ew")

        self.preview_frame = tk.Frame(input_zone, bg=C["bg_dark"])
        self.preview_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(8, 0))

        ib_card = tk.Frame(input_zone, bg=C["bg_input"], highlightbackground=C["accent"], highlightthickness=1)
        ib_card.grid(row=2, column=0, sticky="ew", padx=18, pady=10)
        ib_card.grid_columnconfigure(1, weight=1)

        attach = tk.Label(ib_card, text="📎", font=("Segoe UI Emoji", 17), bg=C["bg_input"], fg=C["txt3"], cursor="hand2", padx=12, pady=8)
        attach.grid(row=0, column=0, sticky="ns")
        attach.bind("<Button-1>", lambda e: self._attach_image())
        attach.bind("<Enter>", lambda e: attach.config(fg=C["accent"]))
        attach.bind("<Leave>", lambda e: attach.config(fg=C["txt3"]))

        self.input_box = tk.Text(ib_card, height=3, font=("Segoe UI", 11), bg=C["bg_input"], fg=C["txt"], insertbackground=C["accent"], relief="flat", bd=8, wrap="word", selectbackground=C["accent3"])
        self.input_box.grid(row=0, column=1, sticky="ew")
        self.input_box.bind("<Return>", self._on_enter)
        self.input_box.bind("<Shift-Return>", lambda e: None)
        self._set_placeholder()

        send_frame = tk.Frame(ib_card, bg=C["accent"], width=46, height=46, cursor="hand2")
        send_frame.grid(row=0, column=2, sticky="ns", padx=(0, 6), pady=4)
        send_frame.pack_propagate(False)
        send_lbl = tk.Label(send_frame, text="➤", font=("Segoe UI", 14, "bold"), bg=C["accent"], fg="white", cursor="hand2")
        send_lbl.place(relx=0.5, rely=0.5, anchor="center")
        for w in (send_frame, send_lbl):
            w.bind("<Enter>", lambda e: [send_frame.config(bg=C["accent2"]), send_lbl.config(bg=C["accent2"])])
            w.bind("<Leave>", lambda e: [send_frame.config(bg=C["accent"]), send_lbl.config(bg=C["accent"])])
            w.bind("<Button-1>", lambda e: self._send())

        tb_frame = tk.Frame(input_zone, bg=C["bg_card"], highlightbackground=C["border"], highlightthickness=1)
        tb_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 10))
        tb_inner = tk.Frame(tb_frame, bg=C["bg_card"], pady=7, padx=10)
        tb_inner.pack(fill="x")

        self.mic_btn = RoundedButton(tb_inner, text="Speak to Type", icon="🎤", bg_color="#059669", hover_color="#10b981", fg_color="white", width=158, height=34, radius=8, font=("Segoe UI", 9, "bold"), command=self._voice_input)
        self.mic_btn.pack(side="left", padx=(0, 6))

        self.speak_btn = RoundedButton(tb_inner, text="Speak Response", icon="🔊", bg_color=C["accent3"], hover_color=C["accent"], fg_color="white", width=160, height=34, radius=8, font=("Segoe UI", 9, "bold"), command=self._speak_response)
        self.speak_btn.pack(side="left", padx=(0, 6))

        self.stop_btn = RoundedButton(tb_inner, text="Stop", icon="⏹", bg_color="#6b1f2a", hover_color=C["danger"], fg_color="white", width=96, height=34, radius=8, font=("Segoe UI", 9, "bold"), command=self._stop_speaking)
        self.stop_btn.pack(side="left", padx=(0, 10))
        self.stop_btn.config_state("disabled")

        tk.Frame(tb_inner, bg=C["sep"], width=1).pack(side="left", fill="y", padx=6)

        self._as_frame = tk.Frame(tb_inner, bg=C["bg_card"], cursor="hand2")
        self._as_frame.pack(side="left", padx=(0, 6))
        self._as_box = tk.Canvas(self._as_frame, width=16, height=16, bg=C["bg_card"], highlightthickness=0)
        self._as_box.pack(side="left", padx=(0, 4))
        tk.Label(self._as_frame, text="Auto Speak", font=("Segoe UI", 9), bg=C["bg_card"], fg=C["txt2"]).pack(side="left")

        def draw_checkbox():
            self._as_box.delete("all")
            checked = self.auto_speak.get()
            bg = C["accent"] if checked else C["bg_input"]
            self._as_box.create_rectangle(0, 0, 16, 16, fill=bg, outline=C["border"], width=1)
            if checked:
                self._as_box.create_text(8, 8, text="✓", font=("Segoe UI", 9, "bold"), fill="white")

        def toggle_as():
            self.auto_speak.set(not self.auto_speak.get())
            draw_checkbox()

        draw_checkbox()
        self._as_frame.bind("<Button-1>", lambda e: toggle_as())
        self._as_box.bind("<Button-1>", lambda e: toggle_as())

        tk.Label(tb_inner, text="Shift+Enter = new line  |  Enter = send", font=("Segoe UI", 8), bg=C["bg_card"], fg=C["txt3"]).pack(side="right")

    _PH = "Ask a health question or describe your symptoms..."

    def _set_placeholder(self):
        self.input_box.insert("1.0", self._PH)
        self.input_box.config(fg=C["txt3"])
        self.input_box.bind("<FocusIn>", self._ph_clear)
        self.input_box.bind("<FocusOut>", self._ph_restore)

    def _ph_clear(self, e=None):
        if self.input_box.get("1.0", "end-1c") == self._PH:
            self.input_box.delete("1.0", "end")
            self.input_box.config(fg=C["txt"])

    def _ph_restore(self, e=None):
        if not self.input_box.get("1.0", "end-1c").strip():
            self.input_box.insert("1.0", self._PH)
            self.input_box.config(fg=C["txt3"])

    # ─── History Methods ────────────────────────────────────────────────────────
    def _refresh_hist(self):
        for w in self.hist_inner.winfo_children():
            w.destroy()
        for conv in self.hist_mgr.sorted_list():
            cid = conv["id"]
            active = cid == self.current_cid
            bg = C["bg_active"] if active else C["bg_sidebar"]

            outer = tk.Frame(self.hist_inner, bg=bg)
            outer.pack(fill="x", padx=8, pady=3)
            outer.grid_columnconfigure(1, weight=1)

            if active:
                tk.Frame(outer, bg=C["accent"], width=3).grid(row=0, column=0, rowspan=2, sticky="ns")
            else:
                tk.Frame(outer, bg=bg, width=3).grid(row=0, column=0, rowspan=2, sticky="ns")

            title_lbl = tk.Label(outer, text=conv.get("title", "Untitled")[:30], font=("Segoe UI", 9, "bold" if active else "normal"), bg=bg, fg=C["accent2"] if active else C["txt"], anchor="w", wraplength=185)
            title_lbl.grid(row=0, column=1, sticky="ew", padx=(6, 4), pady=(7, 0))

            date_lbl = tk.Label(outer, text=conv.get("updated", "")[:10], font=("Segoe UI", 8), bg=bg, fg=C["txt3"], anchor="w")
            date_lbl.grid(row=1, column=1, sticky="ew", padx=(6, 4), pady=(0, 6))

            del_btn = tk.Label(outer, text="✕", font=("Segoe UI", 9), bg=bg, fg=C["txt3"], cursor="hand2", padx=6)
            del_btn.grid(row=0, column=2, rowspan=2, padx=(0, 4))
            del_btn.bind("<Button-1>", lambda e, c=cid: self._delete_conv(c))
            del_btn.bind("<Enter>", lambda e, d=del_btn: d.config(fg=C["danger"]))
            del_btn.bind("<Leave>", lambda e, d=del_btn: d.config(fg=C["txt3"]))

            for w in [outer, title_lbl, date_lbl]:
                w.bind("<Button-1>", lambda e, c=cid: self._load_conv(c))
                w.config(cursor="hand2")

            def _enter(e, o=outer, bg_norm=bg, act=active, tl=title_lbl, dl=date_lbl, db=del_btn):
                if not act:
                    col = C["bg_hover"]
                    o.config(bg=col)
                    tl.config(bg=col)
                    dl.config(bg=col)
                    db.config(bg=col)
            def _leave(e, o=outer, bg_norm=bg, act=active, tl=title_lbl, dl=date_lbl, db=del_btn):
                o.config(bg=bg_norm)
                tl.config(bg=bg_norm)
                dl.config(bg=bg_norm)
                db.config(bg=bg_norm)
            outer.bind("<Enter>", _enter)
            outer.bind("<Leave>", _leave)

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
            if msg["role"] == "user":
                self._bubble_user(msg["content"], msg.get("image_path"))
                if msg["content"]:
                    self.llm_messages.append({"role": "user", "content": msg["content"]})
            else:
                self._bubble_bot(msg["content"])
                self.last_response = msg["content"]
                self.llm_messages.append({"role": "assistant", "content": msg["content"]})
        title = self.hist_mgr.conversations[cid].get("title", "Conversation")
        self.title_var.set(title)
        self._refresh_hist()
        self._scroll_bottom()

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
        outer = tk.Frame(self.chat_frame, bg=C["bg_chat"], pady=36)
        outer.pack(fill="x", padx=44)

        card = tk.Frame(outer, bg=C["bg_card"], highlightbackground=C["accent"], highlightthickness=1)
        card.pack(fill="x")

        tk.Frame(card, bg=C["accent"], height=4).pack(fill="x")

        inner = tk.Frame(card, bg=C["bg_card"], padx=32, pady=26)
        inner.pack(fill="x")
        inner.grid_columnconfigure(1, weight=1)

        icon_frame = tk.Frame(inner, bg=C["bg_card"])
        icon_frame.grid(row=0, column=0, rowspan=3, sticky="n", padx=(0, 24))
        ic_badge = tk.Frame(icon_frame, bg=C["accent"], width=72, height=72)
        ic_badge.pack()
        ic_badge.pack_propagate(False)
        tk.Label(ic_badge, text="🩺", font=("Segoe UI Emoji", 32), bg=C["accent"], fg="white").place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(inner, text="Hello! I'm MedBot", font=("Segoe UI", 17, "bold"), bg=C["bg_card"], fg=C["txt"]).grid(row=0, column=1, sticky="w", pady=(0, 5))
        subtitle = f"AI health assistant  ·  Skin disease detection  ·  { 'Groq AI ready ✓' if self.llm.is_ready else 'Offline mode'}"
        tk.Label(inner, text=subtitle, font=("Segoe UI", 9), bg=C["bg_card"], fg=C["txt2"]).grid(row=1, column=1, sticky="w", pady=(0, 16))

        features = [
            ("🔬", "Skin Disease Detection", "Upload a photo — AI predicts 46 conditions"),
            ("💊", "Medicine Database", "Search medicines with detailed info"),
            ("🚑", "First Aid Guide", "Emergency procedures for common situations"),
            ("📊", "Health Risk Calculator", "Assess your health risks instantly"),
            ("💬", "Medical Q&A", "Ask about symptoms, treatments, medicines"),
            ("🚨", "Outbreak Alerts", "Live WHO disease alerts for your region"),
            ("💉", "Vaccination Schedule", "India UIP schedule + booking links"),
            ("🎤", "Voice in Any Language", "50+ languages: Hindi, Tamil, Gujarati..."),
            ("🌍", "Multilingual Responses", "Replies in your native language"),
        ]
        feat_frame = tk.Frame(inner, bg=C["bg_card"])
        feat_frame.grid(row=2, column=1, sticky="ew")
        for i, (icon, title, desc) in enumerate(features):
            col = i % 2
            row_n = i // 2
            f = tk.Frame(feat_frame, bg=C["bg_input"], highlightbackground=C["border"], highlightthickness=1)
            f.grid(row=row_n, column=col, sticky="ew", padx=(0, 6) if col == 0 else (0, 0), pady=4)
            feat_frame.grid_columnconfigure(col, weight=1)
            inner2 = tk.Frame(f, bg=C["bg_input"], padx=12, pady=10)
            inner2.pack(fill="x")
            tk.Label(inner2, text=icon, font=("Segoe UI Emoji", 15), bg=C["bg_input"]).pack(side="left", padx=(0, 10))
            text_f = tk.Frame(inner2, bg=C["bg_input"])
            text_f.pack(side="left", fill="x")
            tk.Label(text_f, text=title, font=("Segoe UI", 9, "bold"), bg=C["bg_input"], fg=C["txt"], anchor="w").pack(anchor="w")
            tk.Label(text_f, text=desc, font=("Segoe UI", 8), bg=C["bg_input"], fg=C["txt2"], anchor="w").pack(anchor="w")

        tk.Frame(card, bg=C["sep"], height=1).pack(fill="x")
        tk.Label(card, text="⚕️  AI assistant — always consult a licensed healthcare professional for medical decisions", font=("Segoe UI", 8), bg=C["bg_card"], fg=C["txt3"], pady=10).pack()
        self._scroll_bottom()

    # ─── Chat Display Methods ───────────────────────────────────────────────────
    def _bubble_user(self, text, image_path=None):
        outer = tk.Frame(self.chat_frame, bg=C["bg_chat"], pady=10)
        outer.pack(fill="x", padx=28)

        wrap = tk.Frame(outer, bg=C["bg_chat"])
        wrap.pack(side="right")

        meta = tk.Frame(wrap, bg=C["bg_chat"])
        meta.pack(anchor="e", pady=(0, 4))
        tk.Label(meta, text=self.username.get() or "You", font=("Segoe UI", 9, "bold"), bg=C["bg_chat"], fg=C["accent2"]).pack(side="left")
        tk.Label(meta, text=f"  {datetime.datetime.now().strftime('%H:%M')}", font=("Segoe UI", 8), bg=C["bg_chat"], fg=C["txt3"]).pack(side="left")

        bubble_wrap = tk.Frame(wrap, bg=C["accent"], bd=0)
        bubble_wrap.pack(anchor="e")
        tk.Frame(bubble_wrap, bg=C["accent"], width=4).pack(side="right", fill="y")
        bubble = tk.Frame(bubble_wrap, bg=C["bg_user"], padx=16, pady=12)
        bubble.pack(side="left")

        if image_path and os.path.exists(image_path) and PIL_AVAILABLE:
            try:
                img = Image.open(image_path)
                img.thumbnail((200, 200))
                photo = ImageTk.PhotoImage(img)
                lbl = tk.Label(bubble, image=photo, bg=C["bg_user"], relief="flat", bd=0)
                lbl.image = photo
                lbl.pack(anchor="e", pady=(0, 6))
                tk.Label(bubble, text=f"📎 {os.path.basename(image_path)}", font=("Segoe UI", 8), bg=C["bg_user"], fg="#ffffffaa").pack(anchor="e")
            except Exception:
                pass
        if text:
            tk.Label(bubble, text=text, font=("Segoe UI", 10), bg=C["bg_user"], fg=C["txt"], wraplength=520, justify="left", anchor="w").pack(anchor="w")
        self._scroll_bottom()

    def _bubble_bot(self, text):
        import re
        outer = tk.Frame(self.chat_frame, bg=C["bg_chat"], pady=10)
        outer.pack(fill="x", padx=28)
        wrap = tk.Frame(outer, bg=C["bg_chat"])
        wrap.pack(side="left", fill="x", expand=True)

        meta = tk.Frame(wrap, bg=C["bg_chat"])
        meta.pack(anchor="w", pady=(0, 4))
        tk.Label(meta, text="●", font=("Segoe UI", 9), bg=C["bg_chat"], fg=C["accent"]).pack(side="left")
        tk.Label(meta, text=" MedBot", font=("Segoe UI", 9, "bold"), bg=C["bg_chat"], fg=C["accent"]).pack(side="left")
        tk.Label(meta, text=f"  {datetime.datetime.now().strftime('%H:%M')}", font=("Segoe UI", 8), bg=C["bg_chat"], fg=C["txt3"]).pack(side="left")

        bubble_wrap = tk.Frame(wrap, bg=C["bg_bot"], highlightbackground=C["border"], highlightthickness=1)
        bubble_wrap.pack(anchor="w", fill="x")
        tk.Frame(bubble_wrap, bg=C["accent"], width=4).pack(side="left", fill="y")
        bubble = tk.Frame(bubble_wrap, bg=C["bg_bot"], padx=16, pady=12)
        bubble.pack(side="left", fill="x", expand=True)

        url_pat = re.compile(r'https?://[^\s]+')

        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                tk.Label(bubble, text="", font=("Segoe UI", 3), bg=C["bg_bot"]).pack(anchor="w")
                continue

            lf = tk.Frame(bubble, bg=C["bg_bot"])
            lf.pack(anchor="w", fill="x", pady=1)

            # If line has URLs, handle separately
            if url_pat.search(stripped):
                parts = url_pat.split(stripped)
                urls = url_pat.findall(stripped)
                url_iter = iter(urls)
                for i, part in enumerate(parts):
                    clean_part = part.strip("* ").strip()
                    if clean_part:
                        tk.Label(lf, text=clean_part, font=("Segoe UI", 10), bg=C["bg_bot"], fg=C["txt"], justify="left").pack(side="left")
                    try:
                        url = next(url_iter)
                        lnk = tk.Label(lf, text=url, font=("Segoe UI", 10, "underline"), bg=C["bg_bot"], fg=C["accent2"], cursor="hand2")
                        lnk.pack(side="left")
                        lnk.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
                    except StopIteration:
                        pass
            else:
                self._render_markdown_line(lf, stripped)

        self._scroll_bottom()

    def _bubble_bot_with_links(self, text):
        import re
        outer = tk.Frame(self.chat_frame, bg=C["bg_chat"], pady=10)
        outer.pack(fill="x", padx=28)
        wrap = tk.Frame(outer, bg=C["bg_chat"])
        wrap.pack(side="left", fill="x", expand=True)
        tk.Label(wrap, text="● MedBot", font=("Segoe UI", 9, "bold"), bg=C["bg_chat"], fg=C["accent"]).pack(anchor="w", pady=(0, 4))
        bubble_wrap = tk.Frame(wrap, bg=C["bg_bot"], highlightbackground=C["border"], highlightthickness=1)
        bubble_wrap.pack(anchor="w", fill="x")
        tk.Frame(bubble_wrap, bg=C["accent"], width=4).pack(side="left", fill="y")
        bubble = tk.Frame(bubble_wrap, bg=C["bg_bot"], padx=16, pady=12)
        bubble.pack(side="left", fill="x", expand=True)

        url_pat = re.compile(r'https?://[^\s]+')

        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                tk.Label(bubble, text="", font=("Segoe UI", 3), bg=C["bg_bot"]).pack(anchor="w")
                continue

            lf = tk.Frame(bubble, bg=C["bg_bot"])
            lf.pack(anchor="w", fill="x", pady=1)

            urls = url_pat.findall(stripped)
            if urls:
                parts = url_pat.split(stripped)
                url_iter = iter(urls)
                for i, part in enumerate(parts):
                    clean_part = part.strip("* ").strip()
                    if clean_part:
                        tk.Label(lf, text=clean_part, font=("Segoe UI", 9), bg=C["bg_bot"], fg=C["txt"], justify="left").pack(side="left")
                    try:
                        url = next(url_iter)
                        lnk = tk.Label(lf, text=url, font=("Segoe UI", 9, "underline"), bg=C["bg_bot"], fg=C["accent2"], cursor="hand2")
                        lnk.pack(side="left")
                        lnk.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
                    except StopIteration:
                        pass
            else:
                self._render_markdown_line(lf, stripped)
        self._scroll_bottom()

    def _render_markdown_line(self, lf, stripped):
        import re
        hm = re.match(r'^(#{1,3})\s+(.*)', stripped)
        if hm:
            level = len(hm.group(1))
            htxt = re.sub(r'\*+', '', hm.group(2)).strip()
            sizes = {1: 14, 2: 12, 3: 11}
            tk.Frame(lf, bg=C["accent"], width=4).pack(side="left", fill="y", padx=(0, 10))
            tk.Label(lf, text=htxt, font=("Segoe UI", sizes.get(level, 12), "bold"),
                     bg=C["bg_bot"], fg=C["accent2"], anchor="w", justify="left",
                     wraplength=700).pack(side="left", fill="x", expand=True)
            return
        bm = re.match(r'^[*\-•]\s+(.*)', stripped)
        if bm:
            tk.Label(lf, text="   •", font=("Segoe UI", 10), bg=C["bg_bot"], fg=C["accent2"]).pack(side="left", padx=(4, 6))
            self._render_inline(lf, bm.group(1))
            return
        self._render_inline(lf, stripped)

    def _render_inline(self, parent, text):
        import re
        parts = re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*)', text)
        for part in parts:
            if part.startswith("**") and part.endswith("**") and len(part) > 4:
                tk.Label(parent, text=part[2:-2], font=("Segoe UI", 10, "bold"), bg=C["bg_bot"], fg=C["txt"], justify="left").pack(side="left")
            elif part.startswith("*") and part.endswith("*") and len(part) > 2:
                tk.Label(parent, text=part[1:-1], font=("Segoe UI", 10, "italic"), bg=C["bg_bot"], fg=C["txt2"], justify="left").pack(side="left")
            elif part:
                tk.Label(parent, text=part, font=("Segoe UI", 10), bg=C["bg_bot"], fg=C["txt"], wraplength=740, justify="left").pack(side="left")

    def _typing_indicator(self):
        outer = tk.Frame(self.chat_frame, bg=C["bg_chat"], pady=10)
        outer.pack(fill="x", padx=28)
        wrap = tk.Frame(outer, bg=C["bg_chat"])
        wrap.pack(side="left")
        tk.Label(wrap, text="● MedBot", font=("Segoe UI", 9, "bold"), bg=C["bg_chat"], fg=C["accent"]).pack(anchor="w", pady=(0, 4))
        bubble_wrap = tk.Frame(wrap, bg=C["bg_bot"], highlightbackground=C["border"], highlightthickness=1)
        bubble_wrap.pack(anchor="w")
        tk.Frame(bubble_wrap, bg=C["accent"], width=4).pack(side="left", fill="y")
        bubble = tk.Frame(bubble_wrap, bg=C["bg_bot"], padx=16, pady=12)
        bubble.pack(side="left")
        inner = tk.Frame(bubble, bg=C["bg_bot"])
        inner.pack(side="left")
        tk.Label(inner, text="🩺  MedBot is thinking", font=("Segoe UI", 9, "bold"), bg=C["bg_bot"], fg=C["accent"]).pack(side="left")
        tk.Label(inner, text="  ...", font=("Segoe UI", 10, "italic"), bg=C["bg_bot"], fg=C["txt3"]).pack(side="left")
        return outer

    def _scroll_bottom(self):
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    # ─── Image Attachment ───────────────────────────────────────────────────────
    def _attach_image(self):
        path = filedialog.askopenfilename(title="Select Skin Image", filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("All", "*.*")])
        if not path:
            return
        self.pending_img = path
        for w in self.preview_frame.winfo_children():
            w.destroy()
        if PIL_AVAILABLE:
            try:
                img = Image.open(path)
                img.thumbnail((72, 72))
                ph = ImageTk.PhotoImage(img)
                lbl = tk.Label(self.preview_frame, image=ph, bg=C["bg_dark"])
                lbl.image = ph
                lbl.pack(side="left", padx=4)
                self.pending_tk = ph
            except Exception:
                pass
        tk.Label(self.preview_frame, text=f"📎 {os.path.basename(path)[:28]}", font=("Segoe UI", 9), bg=C["bg_dark"], fg=C["accent2"]).pack(side="left")
        tk.Button(self.preview_frame, text="✕", font=("Segoe UI", 9), bg=C["bg_dark"], fg=C["danger"], relief="flat", cursor="hand2", command=self._clear_img).pack(side="left", padx=4)

    def _clear_img(self):
        self.pending_img = None
        self.pending_tk = None
        for w in self.preview_frame.winfo_children():
            w.destroy()

    # ─── Send Message ───────────────────────────────────────────────────────────
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
        if hasattr(self, "_voice_en_cache") and self._voice_en_cache and raw:
            en_text = self._voice_en_cache
            self._voice_en_cache = None
        else:
            en_text = self.translator.to_english(raw, trans_code) if raw else ""

        self._bubble_user(raw or "", img)
        self.hist_mgr.add_message(self.current_cid, "user", raw or "", img)

        title = self.hist_mgr.conversations.get(self.current_cid, {}).get("title", "New Chat")
        self.title_var.set(title)
        self._refresh_hist()

        typing = self._typing_indicator()
        self.status_var.set("Thinking...")
        self._status_dot.config(fg=C["warning"])
        threading.Thread(target=self._process, args=(en_text, img, trans_code, typing), daemon=True).start()

    def _process(self, en_text, image_path, lang_code, typing_w):
        try:
            # Check for health risk assessment query
            if en_text and not image_path:
                risk_keywords = ["health risk", "risk assessment", "calculate my risk", "health assessment", 
                                "risk calculator", "check my health risk", "am i at risk", "health score"]
                if any(kw in en_text.lower() for kw in risk_keywords):
                    self.after(0, lambda: self._show_risk_calculator_dialog())
                    return

            # Check for first aid query
            if en_text and not image_path:
                first_aid_keywords = ["first aid", "emergency", "burn", "cut", "bleeding", "choking", "heart attack", 
                                      "stroke", "fracture", "broken bone", "seizure", "poisoning", "cpr", "nosebleed", 
                                      "heat stroke", "allergic reaction", "snake bite", "how to treat", "what to do if"]
                query_lower = en_text.lower()
                if any(kw in query_lower for kw in first_aid_keywords):
                    results = self.first_aid.search_first_aid(en_text)
                    if results:
                        response = self.first_aid.format_first_aid_response(en_text, results)
                        resp_final = self.translator.from_english(response, lang_code)
                        self.after(0, lambda: self._show_response(resp_final, typing_w, lang_code))
                        return

            # Check for medicine query
            if en_text and not image_path:
                medicine_keywords = ["paracetamol", "ibuprofen", "medicine", "medication", "drug", "pill", "tablet", 
                                    "what is", "tell me about", "side effects", "dosage"]
                query_lower = en_text.lower()
                if any(kw in query_lower for kw in medicine_keywords):
                    results = self.medicine_db.search_medicine(en_text)
                    if results:
                        response = self.medicine_db.format_medicine_response(en_text, results)
                        resp_final = self.translator.from_english(response, lang_code)
                        self.after(0, lambda: self._show_response(resp_final, typing_w, lang_code))
                        return

            prediction = ""
            if image_path:
                prediction = self._skin_predict(image_path)

            if prediction.startswith("__DIRECT__:"):
                direct = prediction[len("__DIRECT__:"):].strip()
                resp_final = self.translator.from_english(direct, lang_code)
                self.after(0, lambda: self._show_response(resp_final, typing_w, lang_code))
                return

            country = self.user_country.get().strip() or "India"
            state = self.user_state.get().strip()
            loc_ctx = f"[User location: {country}" + (f", {state}" if state else "") + "] "

            if image_path and not en_text:
                content = f"{loc_ctx}The user uploaded a skin image. {prediction}"
            elif image_path and en_text:
                content = f"{loc_ctx}{en_text}\n\n{prediction}"
            else:
                content = f"{loc_ctx}{en_text}" if en_text else ""

            # Check for outbreak alerts in query
            lower_q = content.lower()
            if any(w in lower_q for w in ["outbreak", "dengue", "malaria", "cholera", "covid", "flu"]):
                try:
                    alerts = self.outbreak_svc.fetch_alerts(country, state)
                    alert_ctx = self.outbreak_svc.format_for_llm(alerts, country, state)
                    if alert_ctx:
                        content += f"\n\nLIVE OUTBREAK DATA:\n{alert_ctx}"
                except Exception:
                    pass

            # Check for vaccination query
            if any(w in lower_q for w in ["vaccin", "immuniz", "shot", "dose", "bcg", "polio", "mmr"]):
                try:
                    sched = self.vaccine_svc.format_schedule(age=25)
                    content += f"\n\nVACCINATION INFO:\n{sched[:500]}"
                except Exception:
                    pass

            if content:
                self.llm_messages.append({"role": "user", "content": content})

            response_en = self.llm.chat(self.llm_messages)
            self.llm_messages.append({"role": "assistant", "content": response_en})

            response_final = self.translator.from_english(response_en, lang_code)
            self.after(0, lambda: self._show_response(response_final, typing_w, lang_code))
        except Exception as e:
            self.after(0, lambda: self._show_response(f"Error: {e}", typing_w, lang_code))

    def _skin_predict(self, path):
        THRESHOLD = 70.0
        if not self.predictor.loaded:
            return "[SKIN_ANALYSIS: Model not loaded. Ensure models/skin_model.pth exists.]"
        try:
            disease, conf, _ = self.predictor.predict(path)
            if conf >= THRESHOLD:
                return (f"[SKIN_ANALYSIS: disease={disease}, confidence={conf}%, status=HIGH_CONFIDENCE]\n"
                        f"The AI skin model detected **{disease}** with **{conf}% confidence**.\n"
                        f"Please provide a detailed explanation of {disease} including: "
                        f"what it is, how it looks, symptoms, causes, treatment options, "
                        f"precautions, and whether urgent care is needed.")
            else:
                return (f"__DIRECT__:\n## Skin Analysis Result\n\n**Detected Condition:** {disease}\n"
                        f"**Confidence Score:** {conf}%\n\n## ⚠️ Low Confidence — Please Consult a Doctor\n\n"
                        f"The model confidence ({conf}%) is below the 70% required threshold.\n\n"
                        f"**Please visit a certified dermatologist** for a proper clinical examination.\n\n"
                        f"⚕️ This AI tool does not replace professional medical advice.")
        except Exception as e:
            return f"[SKIN_ANALYSIS: Error — {e}]"

    def _show_response(self, text, typing_w, lang_code):
        typing_w.destroy()
        self._bubble_bot(text)
        self.last_response = text
        self.hist_mgr.add_message(self.current_cid, "assistant", text)
        self._refresh_hist()
        self.status_var.set("Ready")
        self._status_dot.config(fg=C["success"])
        if self.auto_speak.get():
            self._do_speak(text)

    # ─── Outbreak Alerts ────────────────────────────────────────────────────────
    def _fetch_and_show_alerts(self):
        country = self.user_country.get().strip() or "India"
        state = self.user_state.get().strip()
        self.alert_btn.update_text("⏳ Fetching...")
        self.alert_status.config(text="Checking WHO feeds...")
        self.update()

        def _fetch():
            alerts = self.outbreak_svc.fetch_alerts(country, state)
            self.after(0, lambda: self._display_alerts(alerts, country, state))

        threading.Thread(target=_fetch, daemon=True).start()

    def _display_alerts(self, alerts, country, state):
        self.alert_btn.update_text("🚨 Check Disease Alerts")
        location = country + (f", {state}" if state else "")
        lines = [f"## Live Disease Outbreak Alerts — {location}", ""]
        for a in alerts:
            risk_icon = {"high": "🔴", "medium": "🟡", "low": "🟢", "info": "🔵"}.get(a.get("risk", "info"), "⚪")
            lines.append(f"{risk_icon} [{a['source']}] {a['title']}")
            if a.get("summary"):
                lines.append(f"   {a['summary'][:200]}")
            lines.append("")
        lines.append("⚕️ Always verify with official health portals.")
        msg = "\n".join(lines)
        lcode = lang_trans_code(self.language.get())
        final = self.translator.from_english(msg, lcode)
        self._bubble_bot_with_links(final)
        self.hist_mgr.add_message(self.current_cid, "assistant", final)
        self._refresh_hist()
        active = len([a for a in alerts if a.get("risk") == "high"])
        self.alert_status.config(text=f"✓ {len(alerts)} alert(s) — {active} active", fg=C["danger"] if active > 0 else C["success"])
        self._scroll_bottom()

    # ─── Vaccination Dialog ─────────────────────────────────────────────────────
    def _show_vaccination_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Vaccination Schedule")
        dlg.geometry("400x320")
        dlg.configure(bg=C["bg_sidebar"])
        dlg.grab_set()

        tk.Frame(dlg, bg=C["accent"], height=3).pack(fill="x")
        tk.Label(dlg, text="💉 Vaccination Schedule", font=("Segoe UI", 13, "bold"), bg=C["bg_sidebar"], fg=C["txt"], pady=14).pack()
        tk.Frame(dlg, bg=C["sep"], height=1).pack(fill="x", padx=20)
        tk.Label(dlg, text="Select schedule type:", font=("Segoe UI", 9), bg=C["bg_sidebar"], fg=C["txt2"], pady=8).pack()

        vtype = tk.StringVar(value="adult")
        for label, val in [("Adult / General (18+)", "adult"), ("Child — enter age", "child"), ("Pregnant Women", "pregnant"), ("Travel Vaccines", "travel")]:
            tk.Radiobutton(dlg, text=label, variable=vtype, value=val, font=("Segoe UI", 10), bg=C["bg_sidebar"], fg=C["txt"], selectcolor=C["bg_input"], activebackground=C["bg_sidebar"]).pack(anchor="w", padx=30, pady=2)

        age_frame = tk.Frame(dlg, bg=C["bg_sidebar"])
        age_frame.pack(pady=4)
        tk.Label(age_frame, text="Age (years):", font=("Segoe UI", 9), bg=C["bg_sidebar"], fg=C["txt2"]).pack(side="left", padx=8)
        age_var = tk.StringVar(value="5")
        tk.Entry(age_frame, textvariable=age_var, width=6, font=("Segoe UI", 10), bg=C["bg_input"], fg=C["txt"], insertbackground=C["accent2"], relief="flat", bd=4).pack(side="left")

        def _show():
            t = vtype.get()
            dlg.destroy()
            if t == "child":
                try:
                    age = int(age_var.get())
                except:
                    age = 5
                self._show_vaccine_in_chat(age=age)
            elif t == "pregnant":
                self._show_vaccine_in_chat(for_pregnant=True)
            elif t == "travel":
                self._show_vaccine_in_chat(for_travel=True)
            else:
                self._show_vaccine_in_chat(age=25)

        tk.Button(dlg, text="Show Schedule", font=("Segoe UI", 10, "bold"), bg=C["accent"], fg="white", activebackground=C["accent2"], relief="flat", cursor="hand2", pady=8, command=_show).pack(fill="x", padx=30, pady=12)

    def _show_vaccine_in_chat(self, age=None, for_pregnant=False, for_travel=False):
        text = self.vaccine_svc.format_schedule(age=age, for_pregnant=for_pregnant, for_travel=for_travel)
        lcode = lang_trans_code(self.language.get())
        final = self.translator.from_english(text, lcode)
        self._bubble_bot_with_links(final)
        self.hist_mgr.add_message(self.current_cid, "assistant", final)
        self._refresh_hist()
        self._scroll_bottom()

    # ─── Medicine Database Dialog ───────────────────────────────────────────────
    def _show_medicine_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Medicine Database")
        dlg.geometry("500x400")
        dlg.configure(bg=C["bg_sidebar"])
        dlg.grab_set()

        tk.Frame(dlg, bg=C["accent"], height=3).pack(fill="x")
        tk.Label(dlg, text="💊 Medicine Information Database", font=("Segoe UI", 13, "bold"), bg=C["bg_sidebar"], fg=C["txt"], pady=14).pack()
        tk.Frame(dlg, bg=C["sep"], height=1).pack(fill="x", padx=20)
        tk.Label(dlg, text="Search for medicines by name or brand:", font=("Segoe UI", 9), bg=C["bg_sidebar"], fg=C["txt2"], pady=8).pack()

        search_frame = tk.Frame(dlg, bg=C["bg_sidebar"])
        search_frame.pack(fill="x", padx=20, pady=5)
        search_entry = tk.Entry(search_frame, font=("Segoe UI", 11), bg=C["bg_input"], fg=C["txt"], insertbackground=C["accent"], relief="flat", bd=8)
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        def do_search():
            query = search_entry.get().strip()
            if not query:
                return
            dlg.destroy()
            self._search_and_show_medicine(query)

        RoundedButton(search_frame, text="Search", icon="🔍", bg_color=C["accent"], hover_color=C["accent2"], fg_color="white", width=100, height=36, radius=8, font=("Segoe UI", 9, "bold"), command=do_search).pack(side="right")
        search_entry.bind("<Return>", lambda e: do_search())
        search_entry.focus()

        examples_frame = tk.Frame(dlg, bg=C["bg_sidebar"])
        examples_frame.pack(fill="x", padx=20, pady=15)
        tk.Label(examples_frame, text="Popular searches:", font=("Segoe UI", 8, "bold"), bg=C["bg_sidebar"], fg=C["txt2"]).pack(anchor="w")
        example_btn_frame = tk.Frame(examples_frame, bg=C["bg_sidebar"])
        example_btn_frame.pack(fill="x", pady=5)
        for ex in ["Paracetamol", "Ibuprofen"]:
            btn = tk.Label(example_btn_frame, text=ex, font=("Segoe UI", 9), bg=C["bg_hover"], fg=C["accent2"], cursor="hand2", padx=10, pady=4)
            btn.pack(side="left", padx=3)
            btn.bind("<Button-1>", lambda e, q=ex: [dlg.destroy(), self._search_and_show_medicine(q)])

        tk.Label(dlg, text="💡 Tip: You can also ask me about medicines directly in chat!\nExample: 'Tell me about Paracetamol'", font=("Segoe UI", 8), bg=C["bg_sidebar"], fg=C["txt3"], wraplength=460, justify="left").pack(pady=15)

    def _search_and_show_medicine(self, query):
        self.status_var.set(f"Searching for {query}...")
        self.update()
        results = self.medicine_db.search_medicine(query)
        response = self.medicine_db.format_medicine_response(query, results)
        lang_code = lang_trans_code(self.language.get())
        final_response = self.translator.from_english(response, lang_code)
        self._bubble_bot_with_links(final_response)
        self.hist_mgr.add_message(self.current_cid, "assistant", final_response)
        self._refresh_hist()
        self._scroll_bottom()
        self.status_var.set("Ready")

    # ─── First Aid Guide Dialog ─────────────────────────────────────────────────
    def _show_first_aid_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("First Aid Guide")
        dlg.geometry("500x450")
        dlg.configure(bg=C["bg_sidebar"])
        dlg.grab_set()

        tk.Frame(dlg, bg=C["accent"], height=3).pack(fill="x")
        tk.Label(dlg, text="🚑 First Aid Guide", font=("Segoe UI", 13, "bold"), bg=C["bg_sidebar"], fg=C["txt"], pady=14).pack()
        tk.Frame(dlg, bg=C["sep"], height=1).pack(fill="x", padx=20)
        tk.Label(dlg, text="Search for emergency first aid instructions:", font=("Segoe UI", 9), bg=C["bg_sidebar"], fg=C["txt2"], pady=8).pack()

        search_frame = tk.Frame(dlg, bg=C["bg_sidebar"])
        search_frame.pack(fill="x", padx=20, pady=5)
        search_entry = tk.Entry(search_frame, font=("Segoe UI", 11), bg=C["bg_input"], fg=C["txt"], insertbackground=C["accent"], relief="flat", bd=8)
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        def do_search():
            query = search_entry.get().strip()
            if not query:
                return
            dlg.destroy()
            self._search_and_show_first_aid(query)

        RoundedButton(search_frame, text="Search", icon="🔍", bg_color=C["accent"], hover_color=C["accent2"], fg_color="white", width=100, height=36, radius=8, font=("Segoe UI", 9, "bold"), command=do_search).pack(side="right")
        search_entry.bind("<Return>", lambda e: do_search())
        search_entry.focus()

        common_frame = tk.Frame(dlg, bg=C["bg_sidebar"])
        common_frame.pack(fill="x", padx=20, pady=15)
        tk.Label(common_frame, text="Common Emergencies:", font=("Segoe UI", 8, "bold"), bg=C["bg_sidebar"], fg=C["txt2"]).pack(anchor="w")
        btn_frame = tk.Frame(common_frame, bg=C["bg_sidebar"])
        btn_frame.pack(fill="x", pady=5)
        emergencies = ["Burn", "Cut", "Choking", "Heart Attack", "Stroke", "Fracture", "CPR", "Poisoning"]
        for em in emergencies:
            btn = tk.Label(btn_frame, text=em, font=("Segoe UI", 9), bg=C["bg_hover"], fg=C["accent2"], cursor="hand2", padx=8, pady=4)
            btn.pack(side="left", padx=2, pady=2)
            btn.bind("<Button-1>", lambda e, q=em: [dlg.destroy(), self._search_and_show_first_aid(q)])

        tk.Label(dlg, text="💡 Tip: You can also ask me about first aid in chat!\nExample: 'How to treat a burn?' or 'First aid for choking'", font=("Segoe UI", 8), bg=C["bg_sidebar"], fg=C["txt3"], wraplength=460, justify="left").pack(pady=15)

    def _search_and_show_first_aid(self, query):
        self.status_var.set(f"Searching first aid for {query}...")
        self.update()
        results = self.first_aid.search_first_aid(query)
        response = self.first_aid.format_first_aid_response(query, results)
        lang_code = lang_trans_code(self.language.get())
        final_response = self.translator.from_english(response, lang_code)
        self._bubble_bot_with_links(final_response)
        self.hist_mgr.add_message(self.current_cid, "assistant", final_response)
        self._refresh_hist()
        self._scroll_bottom()
        self.status_var.set("Ready")

    # ─── Health Risk Calculator Dialog ──────────────────────────────────────────
    def _show_risk_calculator_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Health Risk Calculator")
        dlg.geometry("550x700")
        dlg.configure(bg=C["bg_sidebar"])
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Frame(dlg, bg=C["accent"], height=3).pack(fill="x")
        tk.Label(dlg, text="📊 Health Risk Calculator", font=("Segoe UI", 14, "bold"), bg=C["bg_sidebar"], fg=C["txt"], pady=14).pack()
        tk.Frame(dlg, bg=C["sep"], height=1).pack(fill="x", padx=20)

        # Main frame
        main_frame = tk.Frame(dlg, bg=C["bg_sidebar"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)

        # Age
        tk.Label(main_frame, text="Age (years):", font=("Segoe UI", 10, "bold"), bg=C["bg_sidebar"], fg=C["accent"], anchor="w").pack(fill="x", pady=(0, 5))
        age_entry = tk.Entry(main_frame, font=("Segoe UI", 11), bg=C["bg_input"], fg=C["txt"], insertbackground=C["accent"], relief="flat", bd=8, width=20)
        age_entry.pack(fill="x", pady=(0, 10))
        age_entry.insert(0, "30")

        # Weight
        tk.Label(main_frame, text="Weight (kg):", font=("Segoe UI", 10, "bold"), bg=C["bg_sidebar"], fg=C["accent"], anchor="w").pack(fill="x", pady=(0, 5))
        weight_entry = tk.Entry(main_frame, font=("Segoe UI", 11), bg=C["bg_input"], fg=C["txt"], insertbackground=C["accent"], relief="flat", bd=8, width=20)
        weight_entry.pack(fill="x", pady=(0, 10))
        weight_entry.insert(0, "70")

        # Height
        tk.Label(main_frame, text="Height (cm):", font=("Segoe UI", 10, "bold"), bg=C["bg_sidebar"], fg=C["accent"], anchor="w").pack(fill="x", pady=(0, 5))
        height_entry = tk.Entry(main_frame, font=("Segoe UI", 11), bg=C["bg_input"], fg=C["txt"], insertbackground=C["accent"], relief="flat", bd=8, width=20)
        height_entry.pack(fill="x", pady=(0, 10))
        height_entry.insert(0, "170")

        # Blood Pressure
        tk.Label(main_frame, text="Blood Pressure (mmHg):", font=("Segoe UI", 10, "bold"), bg=C["bg_sidebar"], fg=C["accent"], anchor="w").pack(fill="x", pady=(0, 5))
        bp_frame = tk.Frame(main_frame, bg=C["bg_sidebar"])
        bp_frame.pack(fill="x", pady=(0, 10))
        systolic_entry = tk.Entry(bp_frame, font=("Segoe UI", 11), bg=C["bg_input"], fg=C["txt"], insertbackground=C["accent"], relief="flat", bd=8, width=10)
        systolic_entry.pack(side="left", padx=(0, 5))
        systolic_entry.insert(0, "120")
        tk.Label(bp_frame, text="/", font=("Segoe UI", 14), bg=C["bg_sidebar"], fg=C["txt"]).pack(side="left", padx=2)
        diastolic_entry = tk.Entry(bp_frame, font=("Segoe UI", 11), bg=C["bg_input"], fg=C["txt"], insertbackground=C["accent"], relief="flat", bd=8, width=10)
        diastolic_entry.pack(side="left", padx=(5, 0))
        diastolic_entry.insert(0, "80")

        # Blood Sugar
        tk.Label(main_frame, text="Blood Sugar (mg/dL):", font=("Segoe UI", 10, "bold"), bg=C["bg_sidebar"], fg=C["accent"], anchor="w").pack(fill="x", pady=(0, 5))
        sugar_frame = tk.Frame(main_frame, bg=C["bg_sidebar"])
        sugar_frame.pack(fill="x", pady=(0, 10))
        sugar_entry = tk.Entry(sugar_frame, font=("Segoe UI", 11), bg=C["bg_input"], fg=C["txt"], insertbackground=C["accent"], relief="flat", bd=8, width=15)
        sugar_entry.pack(side="left", padx=(0, 10))
        sugar_entry.insert(0, "95")
        sugar_fasting = tk.BooleanVar(value=True)
        tk.Radiobutton(sugar_frame, text="Fasting", variable=sugar_fasting, value=True, font=("Segoe UI", 9), bg=C["bg_sidebar"], fg=C["txt"], selectcolor=C["bg_input"]).pack(side="left", padx=(0, 10))
        tk.Radiobutton(sugar_frame, text="Random", variable=sugar_fasting, value=False, font=("Segoe UI", 9), bg=C["bg_sidebar"], fg=C["txt"], selectcolor=C["bg_input"]).pack(side="left")

        # Smoking Habit
        tk.Label(main_frame, text="Smoking Habit:", font=("Segoe UI", 10, "bold"), bg=C["bg_sidebar"], fg=C["accent"], anchor="w").pack(fill="x", pady=(0, 5))
        smoking_var = tk.StringVar(value="Non-smoker")
        smoking_frame = tk.Frame(main_frame, bg=C["bg_sidebar"])
        smoking_frame.pack(fill="x", pady=(0, 15))
        for habit in ["Non-smoker", "Former smoker", "Occasional smoker", "Regular smoker"]:
            tk.Radiobutton(smoking_frame, text=habit, variable=smoking_var, value=habit, font=("Segoe UI", 9), bg=C["bg_sidebar"], fg=C["txt"], selectcolor=C["bg_input"], anchor="w").pack(fill="x", pady=2)

        # Calculate Button
        def calculate_risk():
            try:
                age = int(age_entry.get())
                weight = float(weight_entry.get())
                height = float(height_entry.get())
                systolic = int(systolic_entry.get())
                diastolic = int(diastolic_entry.get())
                sugar = float(sugar_entry.get())
                is_fasting = sugar_fasting.get()
                smoking = smoking_var.get()
                
                data = {
                    "age": age,
                    "weight": weight,
                    "height": height,
                    "systolic": systolic,
                    "diastolic": diastolic,
                    "sugar": sugar,
                    "sugar_fasting": is_fasting,
                    "smoking": smoking
                }
                
                response = self.risk_calculator.format_risk_response(data)
                dlg.destroy()
                
                # Translate and display
                lang_code = lang_trans_code(self.language.get())
                final_response = self.translator.from_english(response, lang_code)
                self._bubble_bot_with_links(final_response)
                self.hist_mgr.add_message(self.current_cid, "assistant", final_response)
                self._refresh_hist()
                self._scroll_bottom()
                self.status_var.set("Ready")
                
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numbers for all fields.")
        
        calc_btn = RoundedButton(main_frame, text="Calculate My Health Risk", icon="📊", bg_color=C["accent"], hover_color=C["accent2"], fg_color="white", width=400, height=42, radius=10, font=("Segoe UI", 11, "bold"), command=calculate_risk)
        calc_btn.pack(pady=(10, 5))
        
        tk.Label(main_frame, text="💡 This calculator assesses your health risks based on WHO guidelines.\nAlways consult a doctor for medical advice.", font=("Segoe UI", 8), bg=C["bg_sidebar"], fg=C["txt3"], justify="center").pack(pady=(10, 0))

    # ─── Voice Methods ──────────────────────────────────────────────────────────
    def _voice_input(self):
        if not SR_AVAILABLE:
            messagebox.showinfo("Voice Input", "Install packages:\npip install SpeechRecognition pyaudio")
            return
        lang_name = self.language.get()
        sr_code = lang_sr_code(lang_name)
        trans_code = lang_trans_code(lang_name)
        self.status_var.set(f"Listening — {lang_name}...")
        self._status_dot.config(fg=C["success"])
        self.mic_btn.update_text("Listening...")
        self.update()

        def _listen():
            raw_text = self.voice.listen(sr_code)
            if raw_text:
                en_text = self.translator.to_english(raw_text, trans_code)
                self.after(0, lambda rt=raw_text, et=en_text: self._voice_done(rt, et))
            else:
                self.after(0, lambda: self._voice_done(None, None))

        threading.Thread(target=_listen, daemon=True).start()

    def _voice_done(self, raw_text, en_text):
        self.mic_btn.update_text("Speak to Type")
        if raw_text:
            self.status_var.set("● Ready  |  ✓ Voice captured — press Enter to send")
            self._ph_clear()
            self.input_box.delete("1.0", "end")
            self.input_box.config(fg=C["txt"])
            self.input_box.insert("1.0", raw_text)
            self._voice_en_cache = en_text
        else:
            self.status_var.set("Mic error — try again")
            self._status_dot.config(fg=C["danger"])
            self._voice_en_cache = None

    def _speak_response(self):
        if not self.last_response:
            messagebox.showinfo("Nothing to speak", "No response to speak yet.")
            return
        if not TTS_AVAILABLE:
            messagebox.showinfo("Voice Output", "Install pyttsx3:\npip install pyttsx3")
            return
        self._do_speak(self.last_response)

    def _do_speak(self, text):
        self.speak_btn.config_state("disabled")
        self.stop_btn.config_state("normal")
        self.status_var.set("Speaking...")
        self._status_dot.config(fg=C["accent"])

        def on_done():
            self.after(0, self._speak_finished)

        lang_name = self.language.get()
        trans_code = lang_trans_code(lang_name)
        self.voice.speak(text, lang_code=trans_code, on_done=on_done)

    def _speak_finished(self):
        self.speak_btn.config_state("normal")
        self.stop_btn.config_state("disabled")
        self.status_var.set("Ready")
        self._status_dot.config(fg=C["success"])

    def _stop_speaking(self):
        self.voice.stop()
        self._speak_finished()


    # ══════════════════════════════════════════════════════════════════════
    # eSANJEEVANI — FREE GOVERNMENT TELEMEDICINE INTEGRATION
    # Ministry of Health & Family Welfare, Government of India
    # ══════════════════════════════════════════════════════════════════════
    def _show_esanjeevani(self):
        """
        eSanjeevani is the Government of India's official free telemedicine
        platform. It connects rural users to real qualified doctors via video
        call at zero cost. Available Mon-Sat 9AM-5PM.
        """
        win = tk.Toplevel(self)
        win.title("🏥 eSanjeevani — Free Government Doctor")
        win.geometry("580x620")
        win.configure(bg=C["bg_dark"])
        win.resizable(False, False)
        win.grab_set()

        # ── Top accent bar — green = health/safety ───────────────────────
        tk.Frame(win, bg="#0d9488", height=4).pack(fill="x")

        # ── Header ────────────────────────────────────────────────────────
        hdr = tk.Frame(win, bg=C["bg_card"], pady=14)
        hdr.pack(fill="x")
        hdr.grid_columnconfigure(1, weight=1)

        # Icon badge
        icon_badge = tk.Frame(hdr, bg="#0d9488", width=52, height=52)
        icon_badge.grid(row=0, column=0, rowspan=2, padx=(18,12), pady=4)
        icon_badge.pack_propagate(False)
        tk.Label(icon_badge, text="🏥",
                 font=("Segoe UI Emoji", 22),
                 bg="#0d9488").place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(hdr, text="eSanjeevani",
                 font=("Segoe UI", 17, "bold"),
                 bg=C["bg_card"], fg="#0d9488").grid(
            row=0, column=1, sticky="w")
        tk.Label(hdr, text="FREE Online Doctor  |  Government of India",
                 font=("Segoe UI", 9),
                 bg=C["bg_card"], fg=C["txt2"]).grid(
            row=1, column=1, sticky="w")

        # ── Divider ───────────────────────────────────────────────────────
        tk.Frame(win, bg=C["sep"], height=1).pack(fill="x")

        # ── Feature cards grid ────────────────────────────────────────────
        grid_frame = tk.Frame(win, bg=C["bg_dark"], padx=16, pady=12)
        grid_frame.pack(fill="x")
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)

        features = [
            ("✅", "Completely FREE",
             "No charges. No registration fee. For every Indian citizen.",
             "#0d9488"),
            ("👨‍⚕️", "Real Qualified Doctors",
             "Government verified doctors. Not a bot — real human doctors.",
             C["accent"]),
            ("📱", "Works From Village",
             "Any mobile or laptop with internet. No travel needed.",
             "#7c3aed"),
            ("🗣️", "Multiple Languages",
             "Hindi, Tamil, Telugu, Gujarati, Marathi, Bengali and more.",
             "#0077b6"),
            ("⏰", "Working Hours",
             "Monday to Saturday  |  9:00 AM — 5:00 PM IST",
             C["warning"]),
            ("📋", "Get Prescription",
             "Doctor writes prescription online. Valid at all pharmacies.",
             "#b5451b"),
        ]

        for i, (icon, title, desc, color) in enumerate(features):
            row_n = i // 2
            col_n = i % 2
            card = tk.Frame(grid_frame, bg=C["bg_card"],
                            highlightbackground=C["border"],
                            highlightthickness=1)
            card.grid(row=row_n, column=col_n,
                      sticky="nsew", padx=4, pady=4)
            grid_frame.grid_rowconfigure(row_n, weight=1)

            # Color top strip
            tk.Frame(card, bg=color, height=2).pack(fill="x")
            inner = tk.Frame(card, bg=C["bg_card"], padx=10, pady=8)
            inner.pack(fill="x")
            tk.Label(inner, text=icon,
                     font=("Segoe UI Emoji", 18),
                     bg=C["bg_card"]).pack(side="left",
                                            padx=(0,10), anchor="n")
            txt_f = tk.Frame(inner, bg=C["bg_card"])
            txt_f.pack(side="left", fill="x", expand=True)
            tk.Label(txt_f, text=title,
                     font=("Segoe UI", 9, "bold"),
                     bg=C["bg_card"], fg=color,
                     anchor="w").pack(anchor="w")
            tk.Label(txt_f, text=desc,
                     font=("Segoe UI", 8),
                     bg=C["bg_card"], fg=C["txt2"],
                     anchor="w", justify="left").pack(anchor="w")

        tk.Frame(win, bg=C["sep"], height=1).pack(fill="x", padx=16, pady=(8,0))

        # ── How to access steps ───────────────────────────────────────────
        steps_frame = tk.Frame(win, bg=C["bg_dark"], padx=20, pady=8)
        steps_frame.pack(fill="x")
        tk.Label(steps_frame, text="📱  How to Use eSanjeevani",
                 font=("Segoe UI", 10, "bold"),
                 bg=C["bg_dark"], fg=C["txt"]).pack(anchor="w", pady=(0,6))

        steps = [
            ("1", "Click 'Open eSanjeevani Website' button below"),
            ("2", "Select your State from the dropdown"),
            ("3", "Enter your mobile number — OTP will be sent"),
            ("4", "Book a consultation slot (usually available same day)"),
            ("5", "Join the video call at your slot time — doctor connects"),
            ("6", "Get prescription and advice — all for FREE"),
        ]
        for num, step_text in steps:
            row = tk.Frame(steps_frame, bg=C["bg_dark"])
            row.pack(fill="x", pady=2)
            # Step number badge
            badge = tk.Frame(row, bg="#0d9488", width=22, height=22)
            badge.pack(side="left", padx=(0,10))
            badge.pack_propagate(False)
            tk.Label(badge, text=num,
                     font=("Segoe UI", 8, "bold"),
                     bg="#0d9488", fg="white").place(
                relx=0.5, rely=0.5, anchor="center")
            tk.Label(row, text=step_text,
                     font=("Segoe UI", 9),
                     bg=C["bg_dark"], fg=C["txt"]).pack(
                side="left", anchor="w")

        tk.Frame(win, bg=C["sep"], height=1).pack(fill="x", padx=16, pady=(8,0))

        # ── Action buttons ────────────────────────────────────────────────
        btn_frame = tk.Frame(win, bg=C["bg_dark"], pady=12)
        btn_frame.pack(fill="x", padx=16)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        # Open website button
        open_btn = tk.Button(
            btn_frame,
            text="🌐  Open eSanjeevani Website",
            font=("Segoe UI", 10, "bold"),
            bg="#0d9488", fg="white",
            activebackground="#14b8a6",
            activeforeground="white",
            relief="flat", cursor="hand2",
            pady=10,
            command=lambda: webbrowser.open(
                "https://esanjeevani.mohfw.gov.in")
        )
        open_btn.grid(row=0, column=0, sticky="ew", padx=(0,6))

        # Helpline button
        call_btn = tk.Button(
            btn_frame,
            text="📞  Helpline: 1800-180-1104",
            font=("Segoe UI", 10, "bold"),
            bg=C["accent3"], fg="white",
            activebackground=C["accent"],
            activeforeground="white",
            relief="flat", cursor="hand2",
            pady=10,
            command=lambda: messagebox.showinfo(
                "eSanjeevani Helpline",
                "Toll-Free Helpline\n\n"
                "Number: 1800-180-1104\n\n"
                "This call is completely FREE.\n"
                "Available: 9 AM to 5 PM, Mon-Sat\n\n"
                "Tell the operator:\n"
                "- Your name\n"
                "- Your state\n"
                "- Your health problem\n\n"
                "They will connect you to a doctor.")
        )
        call_btn.grid(row=0, column=1, sticky="ew", padx=(6,0))

        # Also inject into chat button
        def send_to_chat():
            win.destroy()
            chat_msg = (
                "## 🏥 eSanjeevani — Free Government Telemedicine\n\n"
                "**What is eSanjeevani?**\n"
                "eSanjeevani is the Government of India's official free "
                "telemedicine platform under the National Health Mission. "
                "It connects patients directly to real qualified doctors "
                "via video call at absolutely zero cost.\n\n"
                "**How to access:**\n"
                "* Visit: https://esanjeevani.mohfw.gov.in\n"
                "* Select your state\n"
                "* Enter your mobile number\n"
                "* Book a same-day slot\n"
                "* Join video call at slot time\n\n"
                "**Working Hours:** Monday to Saturday, 9:00 AM – 5:00 PM\n\n"
                "**Toll-Free Helpline:** 1800-180-1104\n\n"
                "**Available in:** Hindi, Tamil, Telugu, Gujarati, Marathi, "
                "Bengali and other regional languages.\n\n"
                "⚕️ This is a completely free government service — "
                "no hidden charges, no registration fees."
            )
            lang_code = lang_trans_code(self.language.get())
            final = self.translator.from_english(
                chat_msg.replace("\n", "\n"), lang_code)
            self._bubble_bot_with_links(final)
            if not self.current_cid:
                self._new_chat()
            self.hist_mgr.add_message(
                self.current_cid, "assistant", final)
            self._refresh_hist()
            self._scroll_bottom()

        tk.Button(
            win,
            text="💬  Add to Chat",
            font=("Segoe UI", 9),
            bg=C["bg_input"], fg=C["txt2"],
            activebackground=C["bg_hover"],
            relief="flat", cursor="hand2",
            pady=6,
            command=send_to_chat
        ).pack(pady=(0,4))

        # ── Disclaimer ────────────────────────────────────────────────────
        tk.Label(
            win,
            text="🇮🇳  eSanjeevani is a Government of India initiative under the "
                 "National Health Mission (NHM). Completely free for all citizens.",
            font=("Segoe UI", 7),
            bg=C["bg_dark"], fg=C["txt3"],
            wraplength=540, justify="center",
            pady=6
        ).pack()


# ─── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = HealthBotApp()
    app.mainloop()
