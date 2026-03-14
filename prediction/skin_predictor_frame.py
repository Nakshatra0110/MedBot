import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import torch
import torch.nn as nn
from torchvision import transforms, models
import json
import os

MODEL_PATH =  "models/skin_model.pth"
CLASS_FILE = "models/class_names.json"
CONFIDENCE_THRESHOLD = 0.60

device = torch.device("cpu")

# ================= LOAD CLASS NAMES =================
if not os.path.exists(CLASS_FILE):
    raise FileNotFoundError("class_names.json not found!")

with open(CLASS_FILE, "r") as f:
    class_names = json.load(f)

# ================= LOAD MODEL =================
model = models.mobilenet_v2(weights=None)
model.classifier[1] = nn.Linear(model.last_channel, len(class_names))
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.to(device)
model.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

# =====================================================
# CREATE DATASET FRAME
# =====================================================

def create_dataset_frame(parent):

    frame = tk.Frame(parent, bg="#0b1220")

    # ================= TITLE =================
    tk.Label(
        frame,
        text="AI Skin Disease Predictor",
        fg="white",
        bg="#0b1220",
        font=("Arial", 22, "bold")
    ).pack(pady=15)

    # ================= IMAGE PREVIEW =================
    image_label = tk.Label(frame, bg="#0b1220")
    image_label.pack(pady=10)

    # ================= RESULT TEXT =================
    result_text = tk.Text(
        frame,
        height=8,
        width=70,
        bg="#1e293b",
        fg="white",
        insertbackground="white",
        font=("Arial", 11)
    )
    result_text.pack(pady=10)

    # ================= PREDICTION FUNCTION =================
    def predict_image():
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
        )

        if not file_path:
            return

        try:
            # Display Image
            img_display = Image.open(file_path)
            img_display = img_display.resize((250, 250))
            img_tk = ImageTk.PhotoImage(img_display)

            image_label.config(image=img_tk)
            image_label.image = img_tk

            # Prepare for model
            img = Image.open(file_path).convert("RGB")
            img_tensor = transform(img).unsqueeze(0)

            with torch.no_grad():
                outputs = model(img_tensor)
                probabilities = torch.softmax(outputs, dim=1)
                confidence, predicted = torch.max(probabilities, 1)

            confidence_val = confidence.item()
            predicted_class = class_names[predicted.item()]

            result_text.delete("1.0", tk.END)

            if confidence_val >= CONFIDENCE_THRESHOLD:
                result_text.insert(
                    tk.END,
                    f"Prediction: {predicted_class}\n"
                    f"Confidence: {confidence_val*100:.2f}%\n\n"
                    "⚠ This is an AI-based prediction.\n"
                    "Please consult a certified dermatologist."
                )
            else:
                result_text.insert(
                    tk.END,
                    f"Low Confidence: {confidence_val*100:.2f}%\n\n"
                    "The model is uncertain.\n"
                    "Please consult your nearest hospital."
                )

        except Exception as e:
            messagebox.showerror("Prediction Error", str(e))

    # ================= BUTTON =================
    tk.Button(
        frame,
        text="Upload Skin Image",
        command=predict_image,
        bg="#2563eb",
        fg="white",
        font=("Arial", 11, "bold"),
        width=20
    ).pack(pady=20)

    return frame