import os
import cv2
from torch.utils.data import Dataset

class DeepfakeDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.samples = []
        self.transform = transform

        for label, category in enumerate(['real', 'fake']):
            folder = os.path.join(root_dir, category)

            if not os.path.exists(folder):
                raise ValueError(f"Folder not found: {folder}")

            for file in os.listdir(folder):
                path = os.path.join(folder, file)
                if path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.samples.append((path, label))

        if len(self.samples) == 0:
            raise ValueError(f"No images found in {root_dir}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]

        image = cv2.imread(path)
        if image is None:
            raise ValueError(f"Failed to load image: {path}")

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        if self.transform:
            image = self.transform(image)

        return image, label