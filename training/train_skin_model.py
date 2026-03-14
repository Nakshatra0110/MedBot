import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader, random_split
import json
import os

# -----------------------------
# Device (CPU)
# -----------------------------
device = torch.device("cpu")
print("Using device:", device)

# -----------------------------
# Image Transform (CPU Friendly)
# -----------------------------
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

# -----------------------------
# Load Dataset
# -----------------------------
dataset = datasets.ImageFolder(
    root="merged_dataset",
    transform=transform
)

class_names = dataset.classes
num_classes = len(class_names)

print("Total Classes:", num_classes)

# Save class names
with open("class_names.json", "w") as f:
    json.dump(class_names, f)

# -----------------------------
# Train / Validation Split
# -----------------------------
train_size = int(0.8 * len(dataset))
val_size = len(dataset) - train_size

train_dataset, val_dataset = random_split(dataset, [train_size, val_size])

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=32)

# -----------------------------
# Load Pretrained MobileNetV2
# -----------------------------
model = models.mobilenet_v2(weights="IMAGENET1K_V1")

# Freeze feature extractor (FASTER on CPU)
for param in model.features.parameters():
    param.requires_grad = False

# Replace classifier
model.classifier[1] = nn.Linear(model.last_channel, num_classes)

model = model.to(device)

# -----------------------------
# Loss + Optimizer
# -----------------------------
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# -----------------------------
# Training Loop
# -----------------------------
epochs = 10   # Good for CPU

for epoch in range(epochs):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)
        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        running_loss += loss.item()

        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

    train_acc = 100 * correct / total

    # -------------------------
    # Validation
    # -------------------------
    model.eval()
    val_correct = 0
    val_total = 0

    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)

            outputs = model(images)
            _, predicted = torch.max(outputs, 1)

            val_total += labels.size(0)
            val_correct += (predicted == labels).sum().item()

    val_acc = 100 * val_correct / val_total

    print(f"Epoch [{epoch+1}/{epochs}] "
          f"Loss: {running_loss:.4f} "
          f"Train Acc: {train_acc:.2f}% "
          f"Val Acc: {val_acc:.2f}%")

# -----------------------------
# Save Model
# -----------------------------
torch.save(model.state_dict(), "skin_model.pth")
print("Model saved successfully!")