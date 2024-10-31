import streamlit as st
import ocrmypdf
from PIL import Image
import io
import zipfile
import tempfile
import os
import shutil

def check_dependencies():
    """Check and report on required OCR dependencies."""
    dependencies = {
        'tesseract': shutil.which('tesseract'),
        'gs': shutil.which('gs'),  # Ghostscript
        'unpaper': shutil.which('unpaper'),
        'pngquant': shutil.which('pngquant')
    }
    
    missing_deps = [dep for dep, path in dependencies.items() if path is None]
    return dependencies, missing_deps

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
                ocr_params = {
                    'language': language,
                    'optimize': optimize,
                    'skip_text': False,
                    'progress_bar': True
                }
                
                # Disable image optimization if pngquant is not available
                if shutil.which('pngquant') is None:
                    st.warning("pngquant not found. Disabling image compression.")
                    ocr_params['optimize'] = 0
                
                if len(image_paths) > 1:
                    # Convert first image to PDF
                    ocrmypdf.ocr(
                        image_paths[0],
                        output_pdf_path, 
                        **ocr_params
                    )
                    
                    # Append subsequent images
                    for img_path in image_paths[1:]:
                        ocrmypdf.ocr(
                            img_path,
                            output_pdf_path, 
                            existing_pdf=output_pdf_path,
                            **ocr_params
                        )
                else:
                    # Single image processing
                    ocrmypdf.ocr(
                        image_paths[0],
                        output_pdf_path, 
                        **ocr_params
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
    # Set page configuration
    st.set_page_config(
        page_title="ZIP to Searchable PDF Converter", 
        page_icon="📄", 
        layout="wide"
    )
    
    # Custom CSS for styling
    st.markdown("""
    <style>
    .big-font {
        font-size:20px !important;
    }
    .highlight {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Title and description
    st.title("🖨️ ZIP to Searchable PDF Converter")
    st.markdown("### Convert images from a ZIP file into a single, searchable PDF")

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
    
    # Check and display dependency status
    dependencies, missing_deps = check_dependencies()
    
    if missing_deps:
        st.warning("⚠️ Missing dependencies:")
        for dep in missing_deps:
            st.warning(f"- {dep}")
        
        st.info("""
        📦 Install missing dependencies:
        - Tesseract OCR: `apt-get install tesseract-ocr`
        - Ghostscript: `apt-get install ghostscript`
        - Unpaper: `apt-get install unpaper`
        - pngquant: `apt-get install pngquant`
        """)
    
    # Sidebar for configuration
    st.sidebar.header("🛠️ Conversion Settings")
    
    # Language selection
    language = st.sidebar.selectbox(
        "OCR Language", 
        ["eng", "fra", "deu", "spa", "chi_sim", "rus"],
        help="Choose the language for text recognition"
    )
    
    # Optimization level
    optimize = st.sidebar.selectbox(
        "PDF Optimization Level",
        [0, 1, 2, 3],
        index=2,
        help="Higher levels compress PDF more but may reduce quality"
    )
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload ZIP File", 
        type=['zip'], 
        help="Upload a ZIP file containing images to convert"
    )
    
    # Conversion process
    if uploaded_file:
        # Display uploaded file info
        st.markdown(f"📁 **Uploaded File:** `{uploaded_file.name}`")
        
        # Conversion button
        if st.button("🔄 Convert to Searchable PDF", type="primary"):
            with st.spinner("🕒 Converting images to searchable PDF..."):
                # Process the ZIP file
                pdf_bytes = process_zip_to_searchable_pdf(
                    uploaded_file, 
                    language=language, 
                    optimize=optimize
                )
                
                # Display download button if conversion successful
                if pdf_bytes:
                    st.success("✅ Conversion Completed Successfully!")
                    st.download_button(
                        label="📥 Download Searchable PDF",
                        data=pdf_bytes,
                        file_name="searchable_images.pdf",
                        mime="application/pdf"
                    )
    
    # Information section
    st.markdown("---")
    st.markdown("### 📝 Notes")
    st.markdown("""
    - Supported image formats: JPG, JPEG, PNG, GIF, TIFF, BMP
    - Images will be ordered alphabetically by filename
    - OCR will attempt to recognize text in the images
    - Requires OCRmyPDF and Tesseract OCR to be installed
    """)

if __name__ == "__main__":
    main()
