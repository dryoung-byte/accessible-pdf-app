import io
import fitz  # PyMuPDF
from PIL import Image
from fpdf import FPDF
import openai
import os
import streamlit as st

client = openai.OpenAI()  # ✅ new style for OpenAI v1+

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

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

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

    def add_markdown(self, markdown_text):
        lines = markdown_text.split('\n')
        for line in lines:
            if line.startswith('# '):
                self.set_font('Arial', 'B', 16)
                self.cell(0, 10, line[2:], ln=True)
            elif line.startswith('## '):
                self.set_font('Arial', 'B', 14)
                self.cell(0, 10, line[3:], ln=True)
            elif line.strip() == '':
                self.ln(5)
            else:
                self.set_font('Arial', '', 12)
                self.multi_cell(0, 10, line)

    def add_image_with_alt(self, image_path, alt_text):
        self.image(image_path, w=100)
        self.set_font('Arial', 'I', 10)
        self.multi_cell(0, 10, f"Image description: {alt_text}")

# Streamlit UI
def main():
    st.title("Accessible PDF Generator")
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

    if uploaded_file is not None:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.read())

        st.success("PDF uploaded successfully. Extracting content...")
        text_blocks, images = extract_pdf_content("temp.pdf")

        st.subheader("Add Alt Texts")
        alt_texts = get_alt_texts_ui(images)

        if st.button("Generate Accessible PDF"):
            pdf = AccessiblePDF()
            pdf.add_page()

            for page_num, text in text_blocks:
                if text:
                    structured = tag_structure_with_ai(text)
                    pdf.add_markdown(structured)

            for img_path, _ in images:
                pdf.add_image_with_alt(img_path, alt_texts.get(img_path, ""))

            output_path = "accessible_output.pdf"
            pdf.output(output_path)
            with open(output_path, "rb") as f:
                st.download_button("Download Accessible PDF", f, file_name=output_path)

if __name__ == "__main__":
    main()
