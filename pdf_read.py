import streamlit as st
from PIL import Image, ImageFilter
import io
import zipfile
import tempfile
import os
import pytesseract
from fpdf import FPDF

def preprocess_image(image):
    """Preprocess the image for better OCR results."""
    # Convert to grayscale
    image = image.convert("L")
    
    # Apply thresholding
    image = image.point(lambda x: 0 if x < 128 else 255, '1')
    
    # Resize image to improve OCR accuracy (optional)
    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
    
    return image

def process_zip_to_searchable_pdf(zip_file):
    """Convert images from zip file to a searchable PDF using OCR."""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract zip contents
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Collect valid image files
            images = []
            valid_extensions = {'.jpg', '.jpeg', '.png'}
            
            for root, _, files in os.walk(temp_dir):
                for file in sorted(files):  # Sort files alphabetically
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

            # Create a PDF using fpdf2
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)

            for img in images:
                # Preprocess the image for better OCR
                processed_img = preprocess_image(img)

                # Convert the PIL image to a temporary file
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                    processed_img.save(temp_file.name, "JPEG")
                    
                    # Add image to the PDF
                    pdf.add_page()
                    pdf.image(temp_file.name, x=0, y=0, w=pdf.w, h=pdf.h)

                    # Use pytesseract to extract text for OCR
                    text = pytesseract.image_to_string(processed_img, config='--psm 6')  # Set Page Segmentation Mode

                    # Insert the text into the PDF as a hidden text layer
                    pdf.set_xy(0, 0)  # Position for text
                    pdf.set_font("Arial", size=12)

                    # Handle potential unsupported characters
                    pdf.multi_cell(0, 10, text.encode('latin-1', 'replace').decode('latin-1'))

            # Save the PDF to a BytesIO stream
            pdf_output = io.BytesIO()
            pdf.output(pdf_output)
            pdf_output.seek(0)

            return pdf_output.getvalue()

    except Exception as e:
        st.error(f"Error processing ZIP file: {str(e)}")
        return None

def main():
    st.title("ZIP to Searchable PDF Converter")
    st.write("Upload a ZIP file containing images to convert them into a searchable PDF file with OCR.")

    # File uploader for ZIP
    uploaded_file = st.file_uploader(
        "Choose a ZIP file",
        type=['zip']
    )

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
        - The resulting PDF will be searchable
        """)

if __name__ == "__main__":
    main()
