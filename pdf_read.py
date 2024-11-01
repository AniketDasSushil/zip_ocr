import streamlit as st
from PIL import Image
import io
import zipfile
import tempfile
import os
import pytesseract
from pdf2image import convert_from_bytes
from fpdf import FPDF
import cv2
import numpy as np
from PIL import ImageEnhance

def enhance_image(image):
    """Enhance image for better OCR results."""
    # Convert PIL Image to OpenCV format
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # Convert back to PIL Image
    return Image.fromarray(thresh)

def process_image_with_ocr(image):
    """Process single image with OCR and return extracted text."""
    # Enhance image for better OCR results
    enhanced_img = enhance_image(image)
    
    # Extract text using Tesseract
    try:
        text = pytesseract.image_to_string(enhanced_img)
        return text
    except Exception as e:
        st.warning(f"OCR failed: {str(e)}")
        return ""

def create_searchable_pdf(images, texts):
    """Create a searchable PDF with images and OCR text."""
    pdf = FPDF()
    for image, text in zip(images, texts):
        # Add image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            image.save(tmp, 'JPEG')
            tmp_path = tmp.name
        
        # Add new page and image
        pdf.add_page()
        pdf.image(tmp_path, x=10, y=10, w=190)
        
        # Add invisible text layer
        pdf.set_font("Arial", size=1)  # Tiny font size for invisible text
        pdf.set_text_color(255, 255, 255)  # White color (invisible)
        pdf.multi_cell(0, 1, text)
        
        # Clean up temporary file
        os.unlink(tmp_path)
    
    # Save PDF to memory
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    return pdf_buffer.getvalue()

def process_zip_to_searchable_pdf(zip_file):
    """Convert images from zip file to searchable PDF with OCR."""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract zip contents
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Get all image files
            images = []
            texts = []
            valid_extensions = {'.jpg', '.jpeg', '.png'}
            
            # Process each image
            for root, _, files in os.walk(temp_dir):
                for file in sorted(files):
                    if any(file.lower().endswith(ext) for ext in valid_extensions):
                        image_path = os.path.join(root, file)
                        try:
                            # Open and process image
                            img = Image.open(image_path)
                            if img.mode != 'RGB':
                                img = img.convert('RGB')
                            
                            # Extract text using OCR
                            text = process_image_with_ocr(img)
                            
                            images.append(img)
                            texts.append(text)
                            
                            st.success(f"Processed {file}")
                        except Exception as e:
                            st.warning(f"Skipped {file}: {str(e)}")
            
            if not images:
                st.error("No valid images found in the ZIP file")
                return None
            
            # Create searchable PDF
            return create_searchable_pdf(images, texts)
            
    except Exception as e:
        st.error(f"Error processing ZIP file: {str(e)}")
        return None

def main():
    st.title("Searchable PDF Converter")
    st.write("Upload a ZIP file containing images to convert them into a searchable PDF file.")
    
    # File uploader for ZIP
    uploaded_file = st.file_uploader(
        "Choose a ZIP file",
        type=['zip']
    )
    
    if uploaded_file:
        st.write(f"Uploaded: {uploaded_file.name}")
        
        # Add quality settings
        ocr_quality = st.select_slider(
            "OCR Quality",
            options=["Fast", "Balanced", "High Quality"],
            value="Balanced"
        )
        
        if st.button("Convert to Searchable PDF"):
            with st.spinner("Converting images and performing OCR..."):
                pdf_bytes = process_zip_to_searchable_pdf(uploaded_file)
                
                if pdf_bytes:
                    st.success("Conversion completed!")
                    st.download_button(
                        label="Download Searchable PDF",
                        data=pdf_bytes,
                        file_name="searchable_images.pdf",
                        mime="application/pdf"
                    )
        
        st.info("""
        📝 Notes:
        - Supported image formats: JPG, JPEG, PNG
        - Images will be ordered alphabetically by filename
        - The output PDF will be searchable with embedded OCR text
        - Higher quality OCR may take longer to process
        - For best results, ensure images are clear and well-lit
        """)

if __name__ == "__main__":
    main()
