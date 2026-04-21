import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms
from core.dataset import DeepfakeDataset
from core.autoencoder import Autoencoder

transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((128,128)),
    transforms.ToTensor()
])

dataset = DeepfakeDataset("data/train", transform=transform)
loader = DataLoader(dataset, batch_size=16, shuffle=True)

model = Autoencoder()
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

for epoch in range(5):
    total_loss = 0

    for images, _ in loader:
        outputs = model(images)
        loss = criterion(outputs, images)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    print(f"Epoch {epoch+1}, Loss: {total_loss/len(loader):.4f}")

torch.save(model.state_dict(), "models/autoencoder.pth")
