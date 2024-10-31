import streamlit as st
from PIL import Image
import easyocr
import io
import zipfile
import tempfile
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfMerger

def perform_ocr(image, reader):
    """Perform OCR on an image using EasyOCR."""
    try:
        # Convert PIL Image to numpy array for EasyOCR
        img_array = np.array(image)
        # Perform OCR
        results = reader.readtext(img_array)
        # Extract full text and positions
        return results
    except Exception as e:
        st.warning(f"OCR error: {str(e)}")
        return []

def create_searchable_pdf(image, ocr_results, output_path):
    """Create a PDF with both image and searchable text."""
    # Get image size
    width, height = image.size
    
    # Calculate scale to fit on letter size page
    scale = min(letter[0]/width, letter[1]/height)
    new_width = width * scale
    new_height = height * scale
    
    # Calculate centering position
    x_offset = (letter[0] - new_width) / 2
    y_offset = (letter[1] - new_height) / 2
    
    # Create PDF
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # Add image
    c.drawImage(image, x_offset, y_offset, width=new_width, height=new_height)
    
    # Add invisible text layer for searchability
    c.setFont('Helvetica', 1)  # Very small font size
    c.setFillColorRGB(0, 0, 0, 0)  # Transparent text
    
    # Add text from OCR results
    for bbox, text, conf in ocr_results:
        if conf > 0.5:  # Only add text with confidence > 50%
            # Convert coordinates to PDF space
            x = bbox[0][0] * scale + x_offset
            y = letter[1] - (bbox[0][1] * scale + y_offset)  # Flip Y coordinate
            c.drawString(x, y, text)
    
    c.save()

def process_zip_to_searchable_pdf(zip_file, reader):
    """Convert images from zip file to searchable PDF with OCR."""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract zip contents
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Process each image
            pdf_files = []
            valid_extensions = {'.jpg', '.jpeg', '.png'}
            
            # Get total number of files for progress bar
            total_files = sum(1 for _, _, files in os.walk(temp_dir)
                            for f in files if any(f.lower().endswith(ext) for ext in valid_extensions))
            
            if total_files == 0:
                st.error("No valid images found in the ZIP file")
                return None
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Process each file
            processed_files = 0
            for root, _, files in os.walk(temp_dir):
                for file in sorted(files):
                    if any(file.lower().endswith(ext) for ext in valid_extensions):
                        image_path = os.path.join(root, file)
                        output_pdf = os.path.join(temp_dir, f"{file}_searchable.pdf")
                        
                        try:
                            # Update status
                            status_text.text(f"Processing {file}...")
                            
                            # Open and convert image if necessary
                            image = Image.open(image_path)
                            if image.mode != 'RGB':
                                image = image.convert('RGB')
                            
                            # Perform OCR
                            ocr_results = perform_ocr(image, reader)
                            
                            # Create searchable PDF
                            create_searchable_pdf(image, ocr_results, output_pdf)
                            pdf_files.append(output_pdf)
                            
                            # Update progress
                            processed_files += 1
                            progress_bar.progress(processed_files / total_files)
                            
                        except Exception as e:
                            st.warning(f"Error processing {file}: {str(e)}")
                            continue
            
            if not pdf_files:
                st.error("No PDFs were created successfully")
                return None
            
            # Merge all PDFs
            status_text.text("Merging PDFs...")
            merger = PdfMerger()
            for pdf in pdf_files:
                merger.append(pdf)
            
            # Save final PDF to bytes
            final_pdf = io.BytesIO()
            merger.write(final_pdf)
            merger.close()
            
            status_text.text("Processing complete!")
            return final_pdf.getvalue()
            
    except Exception as e:
        st.error(f"Error processing ZIP file: {str(e)}")
        return None

def main():
    st.title("ZIP to Searchable PDF Converter")
    st.write("""
    Upload a ZIP file containing images to convert them into a single searchable PDF file.
    The text in the images will be recognized using OCR.
    """)

    # Initialize EasyOCR reader
    @st.cache_resource
    def load_ocr_reader():
        return easyocr.Reader(['en'])  # Initialize for English
    
    reader = load_ocr_reader()

    # File uploader for ZIP
    uploaded_file = st.file_uploader(
        "Choose a ZIP file",
        type=['zip']
    )

    if uploaded_file:
        st.write(f"Uploaded: {uploaded_file.name}")
        
        if st.button("Convert to Searchable PDF"):
            with st.spinner("Processing images with OCR..."):
                pdf_bytes = process_zip_to_searchable_pdf(uploaded_file, reader)
                
                if pdf_bytes:
                    st.success("Conversion completed!")
                    st.download_button(
                        label="Download Searchable PDF",
                        data=pdf_bytes,
                        file_name="searchable_document.pdf",
                        mime="application/pdf"
                    )
        
        st.info("""
        📝 Notes:
        - Supported image formats: JPG, JPEG, PNG
        - Images will be processed in alphabetical order
        - The output PDF will be searchable with recognized text
        - OCR quality depends on image quality and text clarity
        """)

if __name__ == "__main__":
    main()