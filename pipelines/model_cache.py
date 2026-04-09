"""
Global model cache with optimized loading and device management.
This module ensures models are loaded only once and reused across all pipelines.
"""

import torch
from pathlib import Path
from typing import Optional, Union, Dict, Tuple
from core.model import DeepfakeModel
from core.autoencoder import Autoencoder
import logging

LOG = logging.getLogger(__name__)

# Global model caches - shared across all pipelines
_MODEL_CACHE: Dict[str, torch.nn.Module] = {}
_AE_MODEL_CACHE: Dict[str, torch.nn.Module] = {}
_DEVICE_CACHE: Dict[str, torch.device] = {}

# Default device (will be determined on first call)
_DEFAULT_DEVICE: Optional[torch.device] = None


def get_device(force_cpu: bool = False) -> torch.device:
    """Get the default device for model inference.
    
    Args:
        force_cpu: If True, always use CPU even if CUDA is available
        
    Returns:
        torch.device: The device to use for inference
    """
    global _DEFAULT_DEVICE
    
    if _DEFAULT_DEVICE is None:
        if force_cpu:
            _DEFAULT_DEVICE = torch.device("cpu")
        else:
            if torch.cuda.is_available():
                _DEFAULT_DEVICE = torch.device("cuda")
                LOG.info(f"Using CUDA device: {torch.cuda.get_device_name(0)}")
                LOG.info(f"CUDA memory available: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
            else:
                _DEFAULT_DEVICE = torch.device("cpu")
        LOG.info(f"Default device set to: {_DEFAULT_DEVICE}")
    
    return _DEFAULT_DEVICE


def clear_gpu_cache() -> None:
    """Clear GPU cache to free memory."""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        LOG.debug("GPU cache cleared")


def get_cache_key(model_path: Union[str, Path], device: torch.device) -> str:
    """Generate a cache key for model storage."""
    return f"{Path(model_path).resolve()}:{device}"


def load_model(
    model_path: Optional[Union[str, Path]] = None,
    device: Optional[torch.device] = None,
) -> torch.nn.Module:
    """Load and cache a DeepfakeModel.
    
    Uses global caching to avoid reloading the same model multiple times.
    
    Args:
        model_path: Path to model file. If None, uses default location.
        device: Device to load model on. If None, uses default device.
        
    Returns:
        Loaded and cached model ready for inference.
        
    Raises:
        FileNotFoundError: If model file doesn't exist.
    """
    if device is None:
        device = get_device()
    
    if model_path is None:
        # Try default locations in order
        candidates = [
            Path("models/best_model.pth"),
            Path("best_model.pth"),
            Path("training/model.pth"),
        ]
        model_path = None
        for candidate in candidates:
            if candidate.exists():
                model_path = candidate
                break
        if model_path is None:
            raise FileNotFoundError(f"No model found in default locations: {[str(c) for c in candidates]}")
    else:
        model_path = Path(model_path)
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    # Check cache
    cache_key = get_cache_key(model_path, device)
    if cache_key in _MODEL_CACHE:
        LOG.debug(f"Using cached model: {cache_key}")
        return _MODEL_CACHE[cache_key]
    
    # Load model
    LOG.info(f"Loading model from {model_path} on device {device}")
    start_time = __import__('time').time()
    
    model = DeepfakeModel()
    state = torch.load(model_path, map_location=device)
    
    # Handle both full state_dict and checkpoint dict
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    
    model.load_state_dict(state)
    model.to(device)
    model.eval()
    
    # Cache the model
    _MODEL_CACHE[cache_key] = model
    
    load_time = __import__('time').time() - start_time
    LOG.info(f"Model loaded successfully in {load_time:.2f}s and cached")
    
    return model


def load_autoencoder(
    model_path: Optional[Union[str, Path]] = None,
    device: Optional[torch.device] = None,
) -> torch.nn.Module:
    """Load and cache an Autoencoder model.
    
    Uses global caching to avoid reloading the same model multiple times.
    
    Args:
        model_path: Path to model file. If None, uses default location.
        device: Device to load model on. If None, uses default device.
        
    Returns:
        Loaded and cached autoencoder ready for inference.
        
    Raises:
        FileNotFoundError: If model file doesn't exist.
    """
    if device is None:
        device = get_device()
    
    if model_path is None:
        model_path = Path("models/autoencoder.pth")
    else:
        model_path = Path(model_path)
    
    if not model_path.exists():
        LOG.warning(f"Autoencoder not found at {model_path}, returning None")
        return None
    
    # Check cache
    cache_key = get_cache_key(model_path, device)
    if cache_key in _AE_MODEL_CACHE:
        LOG.debug(f"Using cached autoencoder: {cache_key}")
        return _AE_MODEL_CACHE[cache_key]
    
    # Load model
    LOG.info(f"Loading autoencoder from {model_path} on device {device}")
    start_time = __import__('time').time()
    
    model = Autoencoder()
    state = torch.load(model_path, map_location=device)
    
    # Handle both full state_dict and checkpoint dict
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    
    model.load_state_dict(state)
    model.to(device)
    model.eval()
    
    # Cache the model
    _AE_MODEL_CACHE[cache_key] = model
    
    load_time = __import__('time').time() - start_time
    LOG.info(f"Autoencoder loaded successfully in {load_time:.2f}s and cached")
    
    return model


def print_cache_stats() -> None:
    """Print statistics about cached models."""
    LOG.info(f"Model cache size: {len(_MODEL_CACHE)}")
    LOG.info(f"Autoencoder cache size: {len(_AE_MODEL_CACHE)}")
    for key in _MODEL_CACHE:
        LOG.info(f"  Cached model: {key}")
    for key in _AE_MODEL_CACHE:
        LOG.info(f"  Cached autoencoder: {key}")
