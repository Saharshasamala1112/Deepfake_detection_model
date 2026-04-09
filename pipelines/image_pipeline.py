from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union
import time

import cv2
import numpy as np
import torch
from torchvision import transforms

from core.model import DeepfakeModel
from pipelines.model_cache import load_model, load_autoencoder, get_device, clear_gpu_cache

LOG = logging.getLogger(__name__)

_DEFAULT_TRANSFORM = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
])


def process_image(
    image_path: Union[str, Path],
    model: Optional[torch.nn.Module] = None,
    model_path: Optional[Union[str, Path]] = None,
    device: Optional[Union[str, torch.device]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    ae_model: Optional[torch.nn.Module] = None,
    ae_model_path: Optional[Union[str, Path]] = None,
    generate_gradcam: bool = True,
) -> Dict[str, Any]:
    """Process an image, run model prediction and produce a Grad-CAM visualization.

    Returns a dictionary containing prediction metadata and paths to saved artifacts.
    """
    start_time = time.time()

    image_path = Path(image_path)
    if not image_path.exists():
        return {"type": "image", "error": f"Image not found: {image_path}"}

    output_dir = Path(output_dir) if output_dir is not None else Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    if device is None:
        device = get_device()
    
    LOG.info("Starting image processing for %s", image_path)

    # Load original image (BGR)
    original_bgr = cv2.imread(str(image_path))
    if original_bgr is None:
        return {"type": "image", "error": f"Failed to read image: {image_path}"}

    # Convert to RGB for model / visualization
    original_rgb = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2RGB)

    # Preprocess
    input_tensor = _DEFAULT_TRANSFORM(original_rgb).unsqueeze(0)  # shape (1, C, H, W)

    # Load model if not provided
    if model is None:
        LOG.info("Loading model for image processing...")
        model = load_model(model_path=model_path, device=device)
        LOG.info("Model loaded successfully")
    
    # Ensure model and tensor are on same device
    device = next(model.parameters()).device
    input_tensor = input_tensor.to(device)

    LOG.info("Starting inference...")
    # Forward
    with torch.no_grad():
        raw = model(input_tensor)
        # raw expected shape (1, 1) or (1,) or (1, 1, ...)
        try:
            raw_score = raw.view(-1).cpu().numpy()[0].item()  # raw logit
        except Exception:
            # Fallback: convert to tensor then float
            raw_score = float(raw.cpu().squeeze().item())

    LOG.info(f"Inference completed, raw_score: {raw_score}")
    # CNN score (probability) from raw logit
    cnn_score = float(torch.sigmoid(torch.tensor(raw_score)).item())

    # Generate Grad-CAM (expect numpy RGB visualization) if the support package is installed.
    cam_path = None
    if generate_gradcam:
        try:
            from core.gradcam_utils import generate_cam

            cam_vis = generate_cam(model, input_tensor, original_rgb)
            if cam_vis is not None:
                cam_path = output_dir / f"{image_path.stem}_gradcam.jpg"
                cv2.imwrite(str(cam_path), cv2.cvtColor(cam_vis, cv2.COLOR_RGB2BGR))
                LOG.info("Grad-CAM generated successfully for %s", image_path)
            else:
                LOG.warning("Grad-CAM returned None for image %s", image_path)
        except ModuleNotFoundError as exc:
            LOG.warning("Grad-CAM support unavailable: %s", exc)
        except Exception as exc:
            LOG.warning("Failed to generate Grad-CAM for image %s: %s", image_path, exc)

    # Optionally use an autoencoder to reconstruct the image. If no autoencoder
    # is provided, fall back to a simple blurred reconstruction. Also compute
    # reconstruction error which will be combined with the CNN score.
    recon_path = output_dir / f"{image_path.stem}_reconstructed.jpg"
    recon_error = 0.0
    recon_error_norm = 0.0
    
    if ae_model is not None or ae_model_path is not None:
        # Load AE if a path was given
        if ae_model is None:
            ae_model = load_autoencoder(model_path=ae_model_path, device=device)
        
        if ae_model is not None:
            # Prepare input tensor for AE (reuse same transform). Ensure it's on device.
            input_tensor_ae = _DEFAULT_TRANSFORM(original_rgb).unsqueeze(0).to(device)

            with torch.no_grad():
                reconstructed = ae_model(input_tensor_ae)

            # Convert tensor to image (CPU, HWC, uint8)
            recon_cpu = reconstructed.squeeze(0).cpu()
            # Expected shape (C, H, W)
            recon_np = recon_cpu.permute(1, 2, 0).numpy()

            # If floats, assume [0,1] range; otherwise clip to [0,255]
            if np.issubdtype(recon_np.dtype, np.floating):
                recon_img = (np.clip(recon_np, 0.0, 1.0) * 255.0).astype("uint8")
            else:
                recon_img = np.clip(recon_np, 0, 255).astype("uint8")

            cv2.imwrite(str(recon_path), cv2.cvtColor(recon_img, cv2.COLOR_RGB2BGR))
            
            # Compute reconstruction error
            recon_error = float(torch.mean((input_tensor_ae - reconstructed) ** 2).cpu().item())
            recon_error_norm = min(recon_error * 10.0, 1.0)
        else:
            # Simple blurred fallback
            recon = cv2.GaussianBlur(original_bgr, (5, 5), 0)
            cv2.imwrite(str(recon_path), recon)
    else:
        # Simple blurred fallback
        recon = cv2.GaussianBlur(original_bgr, (5, 5), 0)
        cv2.imwrite(str(recon_path), recon)

    final_score = 0.7 * cnn_score + 0.3 * recon_error_norm

    # Use static threshold of 0.5 for binary classification
    # FAKE if score > 0.5, REAL if score <= 0.5
    threshold = 0.5
    label = "FAKE" if final_score > threshold else "REAL"

    # Only keep reconstructed image for FAKE predictions
    reconstructed_path = str(recon_path) if label == "FAKE" else ""

    result = {
        "type": "image",
        "prediction": label,
        "confidence": float(final_score),
        "threshold": float(threshold),
        "cnn_score": cnn_score,
        "reconstruction_error": recon_error,
        "reconstruction_error_norm": recon_error_norm,
        "final_score": final_score,
        "raw_score": float(raw_score),
        "gradcam": str(cam_path) if cam_path is not None else "",
        "reconstructed": reconstructed_path,
    }

    total_time = time.time() - start_time
    LOG.info("Image processing completed in %.2f seconds for %s", total_time, image_path)

    LOG.debug("process_image result: %s", result)
    return result


__all__ = ["process_image", "load_model"]
