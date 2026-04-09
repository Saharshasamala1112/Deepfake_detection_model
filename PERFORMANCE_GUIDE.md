# Performance Optimization & Testing Guide

## Summary of Optimizations Applied

### 1. **Centralized Model Cache** (`pipelines/model_cache.py`)
- **Purpose**: All pipelines now share a single global model cache
- **Benefit**: Model is loaded only once, even if processing multiple files
- **Key Functions**:
  - `get_device()`: Manages device selection (CUDA/CPU)
  - `load_model()`: Loads and caches DeepfakeModel
  - `load_autoencoder()`: Loads and caches Autoencoder
  - `clear_gpu_cache()`: Periodically frees GPU memory
  - `print_cache_stats()`: Logs cache usage for debugging

### 2. **Enhanced Inference System** (`system/inference.py`)
- **GPU Cache Clearing**: Clears GPU memory before each inference
- **Device Logging**: Logs available device and memory info
- **Performance Monitoring**: Tracks processing time for each file type
- **Cache Statistics**: Logs cache hit/miss information

### 3. **Optimized Pipelines**
All pipelines updated to use centralized model cache:
- `pipelines/image_pipeline.py`: Fixed autoencoder loading
- `pipelines/video_pipeline.py`: Using shared cache
- `pipelines/audio_pipeline.py`: Added logging for debugging
- `pipelines/document_pipeline.py`: Added logging for debugging
- **All pipelines have**: Logging, error handling, timeout checks

### 4. **Backend API** (`backend/routes/inference.py`)
- Fixed import statements
- Added request/response logging
- Better error reporting

## Testing the System

### Quick Start
```bash
# 1. Navigate to project directory
cd d:\Deepshield-X

# 2. Start the backend server
python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000

# 3. In another terminal, start the frontend
cd frontend-react
npm run dev

# 4. Test with a sample file
# - Navigate to http://localhost:5173
# - Upload an image, video, audio, or document
# - Check terminal for detailed logging
```

### What to Look For in Logs

#### Model Loading (Should be ONE TIME ONLY)
```
INFO: Loading model from models/best_model.pth on device cuda
INFO: Model loaded successfully in 2.34s and cached
INFO: Device: cuda (GPU name, available memory)
```

#### Subsequent Requests (Should use cache)
```
DEBUG: Using cached model: /path/to/model.pth:device(type='cuda')
```

#### Processing Time
```
INFO: Inference completed in 0.45 seconds for type: image
INFO: Video analysis: 1000 frames, 33.3s duration, will process max 50 frames at 60x sampling
INFO: Inference completed in 2.15 seconds for type: video
```

### Performance Targets

| File Type | Expected Time | Max Frames/Samples |
|-----------|---------------|--------------------|
| Image | < 1 second | N/A |
| Video | 2-5 seconds | 50 frames (60:1 sampling) |
| Audio | 1-2 seconds | Full audio (stored as spectrogram) |
| Document | 3-10 seconds | Limited by timeout |

## Troubleshooting

### Problem: "Model takes 10+ minutes"
**Solution**: 
- Check logs for model loading time
- If model loads multiple times, cache isn't working
- Verify `model_cache.py` is imported in all pipelines
- Clear GPU cache: `torch.cuda.empty_cache()`

### Problem: "CUDA out of memory"
**Solution**:
- Reduce video frame sampling rate HIGHER (e.g., 120 instead of 60)
- Reduce max_frames lower (e.g., 30 instead of 50)
- Enable CPU-only mode in `model_cache.get_device(force_cpu=True)`

### Problem: "Model not found" error
**Solution**:
- Check if `models/best_model.pth` exists
- Alternative locations: `best_model.pth`, `training/model.pth`
- Ensure path is correct relative to working directory

### Problem: "File upload fails"
**Solution**:
- Check `backend/data/inputs/` directory exists
- Verify file format is supported (jpg, png, mp4, wav, pdf, docx, txt)
- Check file size limit (videos: 500MB, documents: 50MB)

## Debugging Commands

### Test Model Loading
```python
from pipelines.model_cache import load_model, get_device
device = get_device()  # Will show device info
model = load_model()   # Load model with timing info
print("Model loaded successfully")
```

### Test Video Processing
```python
from pipelines.video_pipeline import process_video
result = process_video("path/to/video.mp4")
print(f"Processed {result['frames_processed']} frames in {result['processing_time']:.2f}s")
```

### Test Image Processing
```python
from pipelines.image_pipeline import process_image
result = process_image("path/to/image.jpg")
print(f"Confidence: {result['confidence']:.2%}, Prediction: {result['prediction']}")
```

## Memory Profiling

### Enable Memory Tracking
Add to `system/inference.py`:
```python
import tracemalloc
tracemalloc.start()

# ... run inference ...

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory: {current / 1024 / 1024:.2f}MB")
print(f"Peak memory: {peak / 1024 / 1024:.2f}MB")
```

## Next Steps for Further Optimization

1. **Batch Inference**: Process multiple frames together
2. **Async Processing**: Use async/await for non-blocking operations
3. **WebSocket Progress**: Real-time progress updates to frontend
4. **Model Quantization**: Use int8 quantization for faster inference
5. **ONNX Format**: Convert model to ONNX for faster loading
6. **Multi-GPU**: Support multiple GPUs if available
7. **Caching Results**: Cache analysis results by file hash

## Important Notes

- **First Request**: Will be slower as models are being loaded
- **Subsequent Requests**: Should be significantly faster due to caching
- **GPU Usage**: Monitor GPU memory to avoid out-of-memory errors
- **Logging**: Set `LOG.setLevel(logging.DEBUG)` for detailed debugging
