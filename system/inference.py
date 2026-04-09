from pipelines.image_pipeline import process_image
from pipelines.video_pipeline import process_video
from pipelines.audio_pipeline import process_audio
from pipelines.document_pipeline import process_document
from pipelines.webcam_pipeline import process_webcam
from pipelines.model_cache import get_device, clear_gpu_cache, print_cache_stats

import time
import logging

LOG = logging.getLogger(__name__)

def run_inference(path, type_, generate_gradcam=True, timeout=300):  # 5 minute timeout
    """Run inference on file with performance monitoring and timeouts."""
    start_time = time.time()
    LOG.info(f"Starting {type_} inference for: {path}")
    
    # Clear GPU cache before processing to ensure availability
    clear_gpu_cache()
    
    # Get device info
    device = get_device()
    LOG.info(f"Using device: {device}")

    result = {}
    try:
        if type_ == "image":
            LOG.info("Processing as image...")
            result = process_image(path, generate_gradcam=generate_gradcam, device=device)
            
        elif type_ == "video":
            LOG.info("Processing as video...")
            result = process_video(path, device=device)
            
        elif type_ == "audio":
            LOG.info("Processing as audio...")
            result = process_audio(path, device=device)
            
        elif type_ == "document":
            LOG.info("Processing as document...")
            result = process_document(path, device=device)
            
        elif type_ == "webcam":
            LOG.info("Processing as webcam...")
            result = process_webcam(path)
            
        else:
            result = {"error": "Unsupported file type", "type": type_}

    except Exception as e:
        LOG.error(f"Error during {type_} processing: {str(e)}", exc_info=True)
        result = {"error": f"Processing error: {str(e)}", "type": type_}

    # Check for timeout
    processing_time = time.time() - start_time
    LOG.info(f"Inference completed in {processing_time:.2f} seconds for type: {type_}")
    
    if processing_time > timeout:
        LOG.warning(f"Processing timeout after {processing_time:.1f} seconds")
        result = {"error": f"Processing timeout after {processing_time:.1f} seconds", "type": type_}
    
    # Log cache statistics
    print_cache_stats()
    
    return result
