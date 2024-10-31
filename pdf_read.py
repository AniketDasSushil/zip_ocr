import streamlit as st
from PIL import Image
import io
import zipfile
import tempfile
import os
import pytesseract

def process_zip_to_searchable_pdf(zip_file):
    """Convert images from zip file to a searchable PDF using Tesseract OCR."""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract zip contents
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Collect valid image files
            images = []
            valid_extensions = {'.jpg', '.jpeg', '.png'}
            
            for root, _, files in os.walk(temp_dir):
                for file in sorted(files):
                    if any(file.lower().endswith(ext) for ext in valid_extensions):
                        image_path = os.path.join(root, file)
                        try:
                            img = Image.open(image_path)
                            if img.mode != 'RGB':
                                img = img.convert('RGB')
                            images.append(img)
                        except Exception as e:
                            st.warning(f"Skipped {file}: {str(e)}")
            
            if not images:
                st.error("No valid images found in the ZIP file")
                return None
            
            # Create a PDF from images using Tesseract OCR
            pdf_bytes = io.BytesIO()
            for img in images:
                text = pytesseract.image_to_string(img)
                pdf_bytes.write(f"{text}\n".encode('utf-8'))
            return pdf_bytes.getvalue()

    except Exception as e:
        st.error(f"Error processing ZIP file: {str(e)}")
        return None

def main():
    st.title("ZIP to Searchable PDF Converter with Tesseract OCR")
    st.write("Upload a ZIP file containing images to convert them into a searchable PDF file with OCR.")

    uploaded_file = st.file_uploader("Choose a ZIP file", type=['zip'])

    if uploaded_file:
        st.write(f"Uploaded: {uploaded_file.name}")
        
        if st.button("Convert to Searchable PDF"):
            with st.spinner("Converting images from ZIP to searchable PDF..."):
                searchable_pdf_bytes = process_zip_to_searchable_pdf(uploaded_file)
                
                if searchable_pdf_bytes:
                    st.success("Conversion completed!")
                    st.download_button(
                        label="Download Searchable PDF",
                        data=searchable_pdf_bytes,
                        file_name="searchable_converted_images.pdf",
                        mime="application/pdf"
                    )
        
        st.info("""
        📝 Notes:
        - Supported image formats: JPG, JPEG, PNG
        - Images will be ordered alphabetically by filename
        - The ZIP file should contain only images you want to convert
        - The resulting PDF will be searchable thanks to Tesseract OCR
        """)

if __name__ == "__main__":
    main()
