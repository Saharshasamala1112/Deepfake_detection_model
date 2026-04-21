import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms
from dataset import DeepfakeDataset
from model import DeepfakeModel

# ✅ CONFIG
BATCH_SIZE = 16  # Increased batch size for better training
EPOCHS = 10  # More epochs for better convergence
LR = 1e-4  # Slightly higher learning rate
PATIENCE = 5  # Early stopping patience

# ✅ TRANSFORMS - Enhanced preprocessing
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((128, 128)),
    transforms.RandomHorizontalFlip(p=0.5),  # Data augmentation
    transforms.RandomRotation(10),  # Data augmentation
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# Validation transform (no augmentation)
val_transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# ✅ DATA
train_dataset = DeepfakeDataset("data/train", transform=transform)
val_dataset = DeepfakeDataset("data/val", transform=val_transform)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, num_workers=0)

print(f"Training samples: {len(train_dataset)}")
print(f"Validation samples: {len(val_dataset)}")

# ✅ DEBUG LABELS (run once)
for _, labels in train_loader:
    print("Sample labels:", labels[:10])
    break

# ✅ MODEL
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = DeepfakeModel().to(device)

# ✅ LOSS & OPTIMIZER - Improved setup
criterion = nn.BCEWithLogitsLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)  # Added weight decay
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=2)

best_loss = float('inf')
patience_counter = 0

# ✅ TRAIN LOOP
for epoch in range(EPOCHS):
    # Training phase
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for images, labels in train_loader:
        images = images.to(device)
        labels = labels.float().to(device)

        outputs = model(images).squeeze()
        loss = criterion(outputs, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # Calculate accuracy
        predictions = (torch.sigmoid(outputs) > 0.5).float()
        correct += (predictions == labels).sum().item()
        total += labels.size(0)
        total_loss += loss.item()

    avg_train_loss = total_loss / len(train_loader)
    train_acc = correct / total

    # Validation phase
    model.eval()
    val_loss = 0
    val_correct = 0
    val_total = 0

    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)
            labels = labels.float().to(device)

            outputs = model(images).squeeze()
            loss = criterion(outputs, labels)

            predictions = (torch.sigmoid(outputs) > 0.5).float()
            val_correct += (predictions == labels).sum().item()
            val_total += labels.size(0)
            val_loss += loss.item()

    avg_val_loss = val_loss / len(val_loader)
    val_acc = val_correct / val_total

    print(".4f")

    # Learning rate scheduling
    scheduler.step(avg_val_loss)

    # Early stopping and model saving
    if avg_val_loss < best_loss:
        best_loss = avg_val_loss
        patience_counter = 0
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'loss': best_loss,
            'val_acc': val_acc
        }, "best_model.pth")
        print("✅ Model saved!")
    else:
        patience_counter += 1
        if patience_counter >= PATIENCE:
            print("Early stopping triggered")
            break

print("Training completed!")
