import streamlit as st
from PIL import Image
import io
import zipfile
import tempfile
import os
import ocrmypdf

def process_zip_to_searchable_pdf(zip_file, language='eng', optimize=2):
    """Convert images from zip file to a searchable PDF."""
    try:
        # Create temporary directories
        with tempfile.TemporaryDirectory() as temp_dir, \
             tempfile.TemporaryDirectory() as output_dir:
            # Extract zip contents
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Get all image files
            valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.tiff', '.bmp'}
            
            # Collect image paths
            image_paths = []
            for root, _, files in os.walk(temp_dir):
                for file in sorted(files):  # Sort files for consistent order
                    if any(file.lower().endswith(ext) for ext in valid_extensions):
                        image_path = os.path.join(root, file)
                        try:
                            # Open and validate image
                            img = Image.open(image_path)
                            # Convert to RGB if necessary
                            if img.mode != 'RGB':
                                img = img.convert('RGB')
                            
                            # Save validated image
                            output_image_path = os.path.join(temp_dir, f"image_{len(image_paths):03d}.jpg")
                            img.save(output_image_path)
                            image_paths.append(output_image_path)
                        except Exception as e:
                            st.warning(f"Skipped {file}: {str(e)}")
            
            if not image_paths:
                st.error("No valid images found in the ZIP file")
                return None
            
            # Prepare output PDF paths
            output_pdf_path = os.path.join(output_dir, "searchable_output.pdf")
            
            # Use OCRmyPDF to create searchable PDF
            try:
                # If multiple images, create a multi-page PDF
                if len(image_paths) > 1:
                    # Convert first image to PDF
                    ocrmypdf.ocr(
                        image_paths[0],
                        output_pdf_path, 
                        language=language,
                        optimize=optimize,
                        skip_text=False
                    )
                    
                    # Append subsequent images
                    for img_path in image_paths[1:]:
                        ocrmypdf.ocr(
                            img_path,
                            output_pdf_path, 
                            language=language,
                            optimize=optimize,
                            skip_text=False,
                            pdfa_image_compression=True,  # Helps with multi-page PDFs
                            existing_pdf=output_pdf_path
                        )
                else:
                    # Single image processing
                    ocrmypdf.ocr(
                        image_paths[0],
                        output_pdf_path, 
                        language=language,
                        optimize=optimize,
                        skip_text=False
                    )
                
                # Read PDF into memory
                with open(output_pdf_path, 'rb') as pdf_file:
                    pdf_bytes = pdf_file.read()
                
                return pdf_bytes
            
            except Exception as ocr_err:
                st.error(f"OCR Processing failed: {str(ocr_err)}")
                return None
            
    except Exception as e:
        st.error(f"Error processing ZIP file: {str(e)}")
        return None

def main():
    st.title("ZIP to Searchable PDF Converter")
    st.write("Upload a ZIP file containing images to convert them into a single searchable PDF.")
    
    # Check OCR dependencies
    try:
        import ocrmypdf
    except ImportError:
        st.error("""
        OCRmyPDF is not installed. Please install it using:
        ```
        pip install ocrmypdf
        ```
        Also ensure Tesseract OCR is installed on your system.
        """)
        return
    
    # File uploader for ZIP
    uploaded_file = st.file_uploader(
        "Choose a ZIP file",
        type=['zip']
    )
    
    if uploaded_file:
        st.write(f"Uploaded: {uploaded_file.name}")
        
        # Options for OCR
        language = st.selectbox(
            "Select OCR Language", 
            ["eng", "fra", "deu", "spa", "chi_sim", "rus"],
            help="Choose the language for OCR text recognition"
        )
        
        optimize = st.selectbox(
            "PDF Optimization Level",
            [0, 1, 2, 3],
            index=2,
            help="Higher levels compress PDF more but may reduce quality"
        )
        
        if st.button("Convert to Searchable PDF"):
            with st.spinner("Converting images to searchable PDF..."):
                # Call with selected language and optimization
                pdf_bytes = process_zip_to_searchable_pdf(
                    uploaded_file, 
                    language=language, 
                    optimize=optimize
                )
                
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
        - Supported image formats: JPG, JPEG, PNG, GIF, TIFF, BMP
        - Images will be ordered alphabetically by filename
        - OCR will attempt to recognize text in the images
        - Requires OCRmyPDF and Tesseract OCR to be installed
        """)

if __name__ == "__main__":
    main()
