import io
import fitz  # PyMuPDF
from PIL import Image
from fpdf import FPDF
import openai
import os
import streamlit as st

openai.api_key = os.getenv("OPENAI_API_KEY")  # Make sure your key is set

# Step 1: Extract text and images
def extract_pdf_content(file_path):
    text_blocks = []
    images = []

    doc = fitz.open(file_path)
    for page_num, page in enumerate(doc):
        text = page.get_text("text")
        text_blocks.append((page_num + 1, text))

        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_name = f"page_{page_num+1}_img_{img_index+1}.{image_ext}"
            image = Image.open(io.BytesIO(image_bytes))
            image.save(image_name)
            images.append((image_name, f"Page {page_num+1}"))

    return text_blocks, images

# Step 2: Use GPT to suggest structure
def tag_structure_with_ai(page_text):
    prompt = f"""
    Analyze this page of text and return a structured list using markdown format.
    Use # for H1, ## for H2, and plain text for paragraphs. Return plain markdown.

    Text:
    {page_text}
    """
    
    # Use the updated API call for OpenAI
    response = openai.Completion.create(
        model="gpt-4",  # or gpt-3.5-turbo if you don't have access to gpt-4
        prompt=prompt,
        max_tokens=500  # Adjust tokens based on your needs
    )

    return response.choices[0].text.strip()  # Returns structured markdown

# Step 3: Alt text form for Streamlit UI
def get_alt_texts_ui(images):
    alt_texts = {}
    for img_name, page in images:
        st.image(img_name, caption=img_name)
        alt = st.text_input(f"Alt text for image {img_name} ({page}):", key=img_name)
        alt_texts[img_name] = alt
    return alt_texts

# Step 4: Rebuild PDF
class AccessiblePDF(FPDF):
    def header(self):
        pass

    def add_markdown(self, ma_
