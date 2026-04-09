import numpy as np
import torch
import logging
from pathlib import Path
from typing import Optional, Union, Dict
from torchvision import transforms
from PIL import Image, ImageDraw, ImageFont
try:
    import fitz  # PyMuPDF for PDF processing
except ImportError:
    import pymupdf as fitz  # Newer versions use pymupdf
import time

from pipelines.model_cache import load_model, get_device

LOG = logging.getLogger(__name__)

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

def text_to_image(text: str, width: int = 512, height: int = 512) -> np.ndarray:
    """Convert text to an image representation for model input."""
    # Create a white image
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    try:
        # Try to use a default font
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    # Clean and truncate text if too long
    text = text.strip()
    if len(text) > 10000:  # Limit text length to avoid memory issues
        text = text[:10000] + "..."

    # Split text into lines that fit
    lines = []
    words = text.split()
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] < width - 40:  # Leave margin
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
            # Break if we have too many lines
            if len(lines) >= 25:
                break
    if current_line and len(lines) < 25:
        lines.append(current_line)

    # Draw text lines
    y = 20
    for line in lines[:25]:  # Limit to 25 lines to fit in image
        draw.text((20, y), line, fill='black', font=font)
        y += 22  # Slightly tighter line spacing
        if y > height - 40:
            break

    return np.array(img)

def process_document(
    path: Union[str, Path],
    model: Optional[torch.nn.Module] = None,
    model_path: Optional[Union[str, Path]] = None,
    device: Optional[Union[str, torch.device]] = None,
) -> dict:
    """Process a document file by converting it to an image representation."""
    start_time = time.time()
    path = Path(path)
    
    LOG.info(f"Starting document processing: {path}")

    # Check file size limit (50MB)
    if path.stat().st_size > 50 * 1024 * 1024:
        LOG.error("File too large (max 50MB)")
        return {"type": "document", "error": "File too large (max 50MB)"}

    if device is None:
        device = get_device()

    try:
        if path.suffix.lower() == '.pdf':
            # Extract text from PDF with timeout
            LOG.info("Extracting text from PDF...")
            doc = fitz.open(str(path))
            text = ""
            for page_num, page in enumerate(doc):
                if time.time() - start_time > 60:  # 1 minute timeout for PDF processing
                    text += "\n[Processing timeout - document too large]"
                    LOG.warning("PDF processing timeout, stopping at page {page_num}")
                    break
                page_text = page.get_text()
                text += page_text
                # Limit PDF processing to first 50 pages to avoid memory issues
                if page_num >= 49:
                    text += "\n[Content truncated - PDF too long]"
                    LOG.info("PDF page limit reached (50 pages)")
                    break
            doc.close()
        elif path.suffix.lower() == '.docx':
            # Extract text from DOCX with timeout
            if not DOCX_AVAILABLE:
                LOG.error("python-docx not installed")
                return {"type": "document", "error": "python-docx not installed. Cannot process .docx files."}
            LOG.info("Extracting text from DOCX...")
            doc = Document(str(path))
            text = ""
            for para_num, paragraph in enumerate(doc.paragraphs):
                if time.time() - start_time > 60:  # 1 minute timeout for DOCX processing
                    text += "\n[Processing timeout - document too large]"
                    LOG.warning(f"DOCX processing timeout at paragraph {para_num}")
                    break
                text += paragraph.text + "\n"
                # Limit processing to avoid memory issues
                if para_num >= 1000:  # Limit to 1000 paragraphs
                    text += "\n[Content truncated - Document too long]"
                    LOG.info("DOCX paragraph limit reached (1000 paragraphs)")
                    break
        elif path.suffix.lower() == '.doc':
            # .doc files require special handling - not supported yet
            LOG.error(".doc files not supported")
            return {"type": "document", "error": ".doc files are not supported. Please convert to .docx or PDF format."}
        else:
            # Read text file
            LOG.info("Reading text file...")
            with open(path, "r", encoding="utf-8", errors='ignore') as f:
                text = f.read()

    except Exception as e:
        LOG.error(f"Cannot read file: {str(e)}")
        return {"type": "document", "error": f"Cannot read file: {str(e)}"}

    if not text.strip():
        return {"type": "document", "error": "Empty document"}

    word_count = len(text.split())

    # Check processing time
    if time.time() - start_time > 120:  # 2 minute total timeout
        LOG.error("Processing timeout exceeded")
        return {"type": "document", "error": "Processing timeout"}

    try:
        # Convert text to image
        LOG.info("Converting text to image...")
        text_image = text_to_image(text)

        # Prepare for model input
        transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((128, 128)),
            transforms.ToTensor(),
        ])

        input_tensor = transform(text_image).unsqueeze(0)

        # Load model and run inference
        if model is None:
            LOG.info("Loading document model...")
            model = load_model(model_path=model_path, device=device)
            LOG.info("Document model loaded successfully")

        input_tensor = input_tensor.to(device)

        LOG.info("Running document inference...")
        with torch.no_grad():
            raw = model(input_tensor)
            try:
                raw_score = raw.view(-1).cpu().numpy()[0].item()
            except Exception:
                raw_score = float(raw.cpu().squeeze().item())

        cnn_score = float(torch.sigmoid(torch.tensor(raw_score)).item())
        final_score = cnn_score  # For documents, use CNN score directly
        threshold = 0.5
        prediction = "FAKE" if final_score > threshold else "REAL"

        LOG.info(f"Document analysis complete: {prediction} with confidence {final_score:.2%}")

        return {
            "type": "document",
            "prediction": prediction,
            "confidence": float(final_score),
            "threshold": float(threshold),
            "cnn_score": float(cnn_score),
            "word_count": int(word_count),
            "method": "text_to_image_analysis"
        }

    except Exception as e:
        # Fallback to simple heuristic
        if word_count < 50:
            prediction = "UNKNOWN"
            confidence = 0.3
        else:
            prediction = "REAL"
            confidence = 0.6

        return {
            "type": "document",
            "prediction": prediction,
            "confidence": float(confidence),
            "word_count": int(word_count),
            "method": "heuristic_fallback",
            "error": str(e)
        }