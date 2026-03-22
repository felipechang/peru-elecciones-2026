"""Tesseract OCR service with FastAPI."""
from __future__ import annotations

import base64
import io
from typing import List, Dict, Any

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from pydantic import BaseModel

app = FastAPI(
    title="Tesseract OCR Service",
    description="OCR service for extracting text from images and PDFs",
    version="1.0.0"
)


class OCRResponse(BaseModel):
    """Response model for OCR results."""
    pages: List[Dict[str, Any]]
    total_pages: int


class Base64Request(BaseModel):
    """Request model for base64 encoded images."""
    image_data: str
    language: str = "spa"


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ocr"}


@app.post("/ocr/image", response_model=OCRResponse)
async def ocr_image(
        file: UploadFile = File(...),
        language: str = Form(default="spa")
):
    """
    Extract text from an uploaded image file.
    
    Args:
        file: Image file (PNG, JPG, etc.)
        language: Tesseract language code (default: spa for Spanish)
        
    Returns:
        OCRResponse with extracted text
    """
    try:
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # Run OCR
        text = pytesseract.image_to_string(image, lang=language)

        pages = []
        if text.strip():
            pages.append({
                "text": text,
                "page": 1
            })

        return OCRResponse(pages=pages, total_pages=1)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")


@app.post("/ocr/image/base64", response_model=OCRResponse)
async def ocr_image_base64(request: Base64Request):
    """
    Extract text from a base64 encoded image.
    
    Args:
        request: Base64Request with image_data and language
        
    Returns:
        OCRResponse with extracted text
    """
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(request.image_data)
        image = Image.open(io.BytesIO(image_bytes))

        # Run OCR
        text = pytesseract.image_to_string(image, lang=request.language)

        pages = []
        if text.strip():
            pages.append({
                "text": text,
                "page": 1
            })

        return OCRResponse(pages=pages, total_pages=1)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")


@app.post("/ocr/pdf", response_model=OCRResponse)
async def ocr_pdf(
        file: UploadFile = File(...),
        language: str = Form(default="spa"),
        zoom: float = Form(default=2.0)
):
    """
    Extract text from a PDF file using OCR.
    
    Each page is rendered to an image and processed with Tesseract.
    
    Args:
        file: PDF file
        language: Tesseract language code (default: spa for Spanish)
        zoom: Zoom factor for rendering (higher = better quality but slower)
        
    Returns:
        OCRResponse with extracted text per page
    """
    try:
        # Read PDF
        contents = await file.read()
        doc = fitz.open(stream=contents, filetype="pdf")
        total_pages = len(doc)

        pages = []

        for page_num in range(total_pages):
            page = doc[page_num]

            # Render page to image at specified resolution
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Run OCR
            text = pytesseract.image_to_string(img, lang=language)

            if text.strip():
                pages.append({
                    "text": text,
                    "page": page_num + 1  # 1-indexed
                })

        doc.close()

        return OCRResponse(pages=pages, total_pages=total_pages)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")


@app.post("/ocr/pdf/base64", response_model=OCRResponse)
async def ocr_pdf_base64(
        pdf_data: str = Form(...),
        language: str = Form(default="spa"),
        zoom: float = Form(default=2.0)
):
    """
    Extract text from a base64 encoded PDF using OCR.
    
    Args:
        pdf_data: Base64 encoded PDF content
        language: Tesseract language code (default: spa for Spanish)
        zoom: Zoom factor for rendering
        
    Returns:
        OCRResponse with extracted text per page
    """
    try:
        # Decode base64 PDF
        pdf_bytes = base64.b64decode(pdf_data)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)

        pages = []

        for page_num in range(total_pages):
            page = doc[page_num]

            # Render page to image
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Run OCR
            text = pytesseract.image_to_string(img, lang=language)

            if text.strip():
                pages.append({
                    "text": text,
                    "page": page_num + 1
                })

        doc.close()

        return OCRResponse(pages=pages, total_pages=total_pages)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
