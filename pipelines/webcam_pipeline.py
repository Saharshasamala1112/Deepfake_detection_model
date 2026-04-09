import cv2
import torch
import numpy as np
from pathlib import Path
from core.model import DeepfakeModel
from torchvision import transforms

def process_webcam(device_id=0, num_frames=10):
    """Process webcam feed for deepfake detection.

    Args:
        device_id: Camera device ID (default 0)
        num_frames: Number of frames to analyze

    Returns:
        dict: Analysis results
    """
    try:
        # Load model
        model_path = None
        for candidate in [Path("models/best_model.pth"), Path("best_model.pth"), Path("training/model.pth")]:
            if candidate.exists():
                model_path = candidate
                break

        if model_path is None:
            return {"type": "webcam", "error": "No trained model found"}

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = DeepfakeModel()
        state = torch.load(model_path, map_location=device)
        if isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]
        model.load_state_dict(state)
        model.to(device)
        model.eval()

        # Setup transform
        transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((128, 128)),
            transforms.ToTensor(),
        ])

        # Open webcam
        cap = cv2.VideoCapture(device_id)
        if not cap.isOpened():
            return {"type": "webcam", "error": "Cannot access webcam"}

        scores = []
        frames_processed = 0

        while frames_processed < num_frames:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert to RGB and preprocess
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            input_tensor = transform(rgb_frame).unsqueeze(0).to(device)

            # Get prediction
            with torch.no_grad():
                raw_output = model(input_tensor)
                score = float(torch.sigmoid(raw_output).item())

            scores.append(score)
            frames_processed += 1

            # Small delay to not overwhelm
            cv2.waitKey(100)

        cap.release()
        cv2.destroyAllWindows()

        if not scores:
            return {"type": "webcam", "error": "No frames captured"}

        # Aggregate results
        avg_score = sum(scores) / len(scores)
        prediction = "FAKE" if avg_score > 0.5 else "REAL"
        confidence = max(avg_score, 1 - avg_score)  # Use the stronger prediction

        return {
            "type": "webcam",
            "prediction": prediction,
            "confidence": float(confidence),
            "avg_score": float(avg_score),
            "frames_analyzed": len(scores),
            "threshold": 0.5
        }

    except Exception as e:
        return {"type": "webcam", "error": f"Webcam processing failed: {str(e)}"}

# Legacy function for standalone webcam demo
def run_webcam_demo():
    """Standalone webcam demo (legacy function)"""
    import cv2
    import torch
    from core.model import DeepfakeModel
    from torchvision import transforms

    # Load model
    model_path = None
    for candidate in [Path("models/best_model.pth"), Path("best_model.pth"), Path("training/model.pth")]:
        if candidate.exists():
            model_path = candidate
            break

    if model_path is None:
        print("No trained model found!")
        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = DeepfakeModel()
    state = torch.load(model_path, map_location=device)
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    model.load_state_dict(state)
    model.to(device)
    model.eval()

    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
    ])

    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        input_tensor = transform(rgb_frame).unsqueeze(0).to(device)

        with torch.no_grad():
            raw_output = model(input_tensor)
            score = float(torch.sigmoid(raw_output).item())

        label = "FAKE" if score > 0.5 else "REAL"
        confidence = max(score, 1 - score)

        # Display results
        cv2.putText(frame, f"{label} ({confidence:.2f})", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("DeepShield-X Webcam Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()