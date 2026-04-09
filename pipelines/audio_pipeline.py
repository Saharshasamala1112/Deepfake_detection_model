import librosa
import numpy as np
import torch
import logging
from pathlib import Path
from typing import Optional, Union, Dict
from torchvision import transforms

from pipelines.model_cache import load_model, get_device

LOG = logging.getLogger(__name__)

def process_audio(
    path: Union[str, Path],
    model: Optional[torch.nn.Module] = None,
    model_path: Optional[Union[str, Path]] = None,
    device: Optional[Union[str, torch.device]] = None,
) -> dict:
    """Process an audio file using spectrogram analysis."""
    try:
        # Load audio
        LOG.info(f"Loading audio file: {path}")
        y, sr = librosa.load(path, sr=16000)
    except Exception as e:
        LOG.error(f"Cannot load audio: {str(e)}")
        return {"type": "audio", "error": f"Cannot load audio: {str(e)}"}

    if len(y) == 0:
        return {"type": "audio", "error": "Empty audio file"}

    duration = len(y) / sr

    # Generate spectrogram
    try:
        if device is None:
            device = get_device()
        
        # Create mel spectrogram
        LOG.info("Generating mel spectrogram...")
        mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

        # Normalize to 0-1 range
        mel_spec_norm = (mel_spec_db - mel_spec_db.min()) / (mel_spec_db.max() - mel_spec_db.min() + 1e-8)

        # Convert to 3-channel image (repeat the spectrogram)
        if mel_spec_norm.shape[1] < 128:
            # Pad if too short
            pad_width = 128 - mel_spec_norm.shape[1]
            mel_spec_norm = np.pad(mel_spec_norm, ((0, 0), (0, pad_width)), mode='constant')
        elif mel_spec_norm.shape[1] > 128:
            # Truncate if too long
            mel_spec_norm = mel_spec_norm[:, :128]

        # Stack to create 3 channels
        spec_image = np.stack([mel_spec_norm] * 3, axis=0)  # Shape: (3, 128, 128)

        # Convert to tensor
        transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((128, 128)),
            transforms.ToTensor(),
        ])

        # Convert numpy array to PIL Image
        spec_image_uint8 = (spec_image * 255).astype(np.uint8)
        input_tensor = transform(spec_image_uint8).unsqueeze(0)

        # Load model and run inference
        if model is None:
            LOG.info("Loading audio model...")
            model = load_model(model_path=model_path, device=device)
            LOG.info("Audio model loaded successfully")

        input_tensor = input_tensor.to(device)

        LOG.info("Running audio inference...")
        with torch.no_grad():
            raw = model(input_tensor)
            try:
                raw_score = raw.view(-1).cpu().numpy()[0].item()
            except Exception:
                raw_score = float(raw.cpu().squeeze().item())

        cnn_score = float(torch.sigmoid(torch.tensor(raw_score)).item())
        final_score = cnn_score  # For audio, we use CNN score directly
        threshold = 0.5
        prediction = "FAKE" if final_score > threshold else "REAL"

        LOG.info(f"Audio analysis complete: {prediction} with confidence {final_score:.2%}")

        return {
            "type": "audio",
            "prediction": prediction,
            "confidence": float(final_score),
            "threshold": float(threshold),
            "cnn_score": float(cnn_score),
            "duration": float(duration),
            "sample_rate": int(sr),
        }

    except Exception as e:
        # Fallback to simple heuristic if spectrogram processing fails
        LOG.warning(f"Audio processing failed, using fallback: {str(e)}")
        energy = np.mean(y**2)
        if energy > 0.01:
            prediction = "FAKE"
            confidence = min(energy * 10, 1.0)
        else:
            prediction = "REAL"
            confidence = 0.6

        return {
            "type": "audio",
            "prediction": prediction,
            "confidence": float(confidence),
            "duration": float(duration),
            "sample_rate": int(sr),
            "method": "heuristic_fallback",
            "error": str(e)
        }