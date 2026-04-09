import os
import time
import logging
from pathlib import Path
from typing import Optional, Union, Dict

import cv2
import numpy as np
import torch
from torchvision import transforms

from core.model import DeepfakeModel
from pipelines.model_cache import load_model, load_autoencoder, get_device, clear_gpu_cache

LOG = logging.getLogger(__name__)

transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
])


def process_video(
    path: Union[str, Path],
    model: Optional[torch.nn.Module] = None,
    model_path: Optional[Union[str, Path]] = None,
    device: Optional[Union[str, torch.device]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    ae_model: Optional[torch.nn.Module] = None,
    ae_model_path: Optional[Union[str, Path]] = None,
    frame_sample_rate: int = 60,  # Process every 60th frame for better efficiency
    max_frames: int = 50,  # Maximum frames to process for very long videos
) -> dict:
    """Process a video file and return a summary dict.

    Samples frames at the specified rate for efficiency.
    """
    start_time = time.time()
    path = Path(path)
    output_dir = Path(output_dir) if output_dir is not None else Path("outputs")
    recon_dir = output_dir / "reconstructed_frames"
    frames_dir = output_dir / "extracted_frames"
    recon_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    if device is None:
        device = get_device()

    LOG.info(f"Loading video model for processing...")
    # Load model with caching
    if model is None:
        model = load_model(model_path=model_path, device=device)
    LOG.info(f"Model loaded successfully")

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {"type": "video", "error": "Cannot open video file"}

    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps if fps > 0 else 0

    LOG.info(f"Video analysis: {total_frames} frames, {duration:.1f}s duration, will process max {max_frames} frames at {frame_sample_rate}x sampling")

    frame_scores = []
    frame_id = 0
    processed_frames = 0
    recon_errors = []  # Store reconstruction errors for averaging
    fake_frames = []  # Track frames detected as fake with timestamps

    # Load autoencoder if needed
    if ae_model is None and ae_model_path is not None:
        ae_model = load_autoencoder(model_path=ae_model_path, device=device)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Sample frames for efficiency
        if frame_id % frame_sample_rate != 0:
            frame_id += 1
            continue

        # Limit maximum frames to process for very long videos
        if processed_frames >= max_frames:
            break

        original_bgr = frame
        rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Save extracted frame
        frame_path = frames_dir / f"frame_{frame_id:06d}.jpg"
        cv2.imwrite(str(frame_path), original_bgr)

        # Prepare input for classifier
        input_tensor = transform(rgb_img).unsqueeze(0).to(device)

        # Classifier forward and CNN score
        with torch.no_grad():
            raw = model(input_tensor)
            try:
                raw_score = raw.view(-1).cpu().numpy()[0].item()
            except Exception:
                raw_score = float(raw.cpu().squeeze().item())

        cnn_score = float(torch.sigmoid(torch.tensor(raw_score)).item())
        frame_scores.append(cnn_score)

        # Check if this frame is detected as fake (using frame-level threshold)
        frame_prediction = "FAKE" if cnn_score > 0.4 else "REAL"  # Lower threshold for frame-level detection
        if frame_prediction == "FAKE":
            # Calculate timestamp for this frame
            timestamp_seconds = frame_id / fps if fps > 0 else 0
            fake_frames.append({
                "frame_id": frame_id,
                "timestamp": timestamp_seconds,
                "score": cnn_score,  # Use 'score' instead of 'cnn_score' for consistency
                "frame_path": str(frame_path)
            })

        # Reconstruction error (if AE available) - calculate for all frames but save only every 10th
        recon_error = 0.0
        if ae_model is not None:
            with torch.no_grad():
                reconstructed = ae_model(input_tensor)

            # Reconstruction error between input and reconstructed tensor
            recon_error = float(torch.mean((input_tensor - reconstructed) ** 2).cpu().item())
            recon_errors.append(recon_error)

            # Save reconstructed frame every 10th frame
            if processed_frames % 10 == 0:
                # Save reconstructed frame
                recon_cpu = reconstructed.squeeze(0).cpu()
                recon_np = recon_cpu.permute(1, 2, 0).numpy()
                if np.issubdtype(recon_np.dtype, np.floating):
                    recon_img = (np.clip(recon_np, 0.0, 1.0) * 255.0).astype("uint8")
                else:
                    recon_img = np.clip(recon_np, 0, 255).astype("uint8")

                recon_path = recon_dir / f"frame_{frame_id:06d}_reconstructed.jpg"
                cv2.imwrite(str(recon_path), cv2.cvtColor(recon_img, cv2.COLOR_RGB2BGR))

        frame_id += 1
        processed_frames += 1

    cap.release()

    if not frame_scores:
        return {"type": "video", "error": "No frames could be processed"}

    # Calculate summary statistics
    avg_cnn_score = np.mean(frame_scores)
    max_cnn_score = np.max(frame_scores)
    min_cnn_score = np.min(frame_scores)

    # Calculate average reconstruction error
    avg_recon_error = np.mean(recon_errors) if recon_errors else 0.0
    avg_recon_error_norm = min(avg_recon_error * 10.0, 1.0)

    # Use weighted combination for final score
    final_score = 0.7 * avg_cnn_score + 0.3 * avg_recon_error_norm
    threshold = 0.4  # Lower threshold for video-level classification
    prediction = "FAKE" if final_score > threshold else "REAL"

    processing_time = time.time() - start_time

    return {
        "type": "video",
        "prediction": prediction,
        "confidence": float(final_score),
        "threshold": float(threshold),
        "avg_cnn_score": float(avg_cnn_score),
        "max_cnn_score": float(max_cnn_score),
        "min_cnn_score": float(min_cnn_score),
        "frames_processed": processed_frames,
        "total_frames": total_frames,
        "duration": float(duration),
        "fps": float(fps),
        "processing_time": float(processing_time),
        "reconstruction_error": float(avg_recon_error),
        "reconstruction_error_norm": float(avg_recon_error_norm),
        "final_score": float(final_score),
        "reconstructed_frames_dir": str(recon_dir),
        "extracted_frames_dir": str(frames_dir),
        "fake_frames": fake_frames,
        "fake_frames_count": len(fake_frames),
    }
