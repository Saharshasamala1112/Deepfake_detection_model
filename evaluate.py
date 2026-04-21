import torch
from torch.utils.data import DataLoader
from torchvision import transforms
from core.dataset import DeepfakeDataset
from core.model import DeepfakeModel
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((128, 128)),
    transforms.ToTensor()
])

dataset = DeepfakeDataset("data/test", transform=transform)
loader = DataLoader(dataset, batch_size=16)

model = DeepfakeModel()
model.load_state_dict(torch.load("models/best_model.pth"))
model.eval()

all_preds = []
all_labels = []
all_outputs = []

with torch.no_grad():
    for images, labels in loader:
        outputs = model(images).squeeze()
        probs = torch.sigmoid(outputs)

        preds = (probs > 0.5).int()

        all_preds.extend(preds.numpy())
        all_labels.extend(labels.numpy())
        all_outputs.extend(probs.numpy())

print("Accuracy:", accuracy_score(all_labels, all_preds))
print("F1 Score:", f1_score(all_labels, all_preds))
print("ROC AUC:", roc_auc_score(all_labels, all_outputs))
