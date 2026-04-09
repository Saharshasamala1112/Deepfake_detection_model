import torch
import numpy as np
from core.model import DeepfakeModel
from torchvision import transforms
import cv2

def test_model():
    # Load model
    model_path = "best_model.pth"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = DeepfakeModel()
    try:
        state = torch.load(model_path, map_location=device)
        if isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]
        model.load_state_dict(state)
        model.to(device)
        model.eval()
        print("Model loaded successfully")
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    # Create a simple test image (random noise)
    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
    ])

    # Test with random image
    test_image = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)
    input_tensor = transform(test_image).unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(input_tensor)
        raw_score = float(output.item())
        probability = float(torch.sigmoid(output).item())

    print(f"Raw output: {raw_score}")
    print(f"Probability: {probability}")
    print(f"Prediction: {'FAKE' if probability > 0.5 else 'REAL'}")

if __name__ == "__main__":
    test_model()