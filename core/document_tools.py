import os
import fitz  # PyMuPDF
from PIL import Image
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.utils import get_stop_words
from docx import Document as DocxDocument


# ── 1. COMPRESS PDF ─────────────────────────────────────────────
def compress_pdf(input_path, output_path):
    doc = fitz.open(input_path)
    doc.save(output_path, garbage=4, deflate=True, clean=True)
    doc.close()


# ── 2. COMPRESS IMAGE (JPG / PNG) ───────────────────────────────
def compress_image(input_path, output_path, quality=60):
    img = Image.open(input_path)
    ext = os.path.splitext(input_path)[1].lower()
    if ext in ['.jpg', '.jpeg']:
        img = img.convert('RGB')
        img.save(output_path, 'JPEG', quality=quality, optimize=True)
    elif ext == '.png':
        img.save(output_path, 'PNG', optimize=True)
    else:
        img.save(output_path)


# ── 3. MERGE PDFs ───────────────────────────────────────────────
def merge_pdfs(input_paths, output_path):
    merged = fitz.open()
    for path in input_paths:
        doc = fitz.open(path)
        merged.insert_pdf(doc)
        doc.close()
    merged.save(output_path)
    merged.close()


# ── 4. SPLIT PDF ────────────────────────────────────────────────
def split_pdf(input_path, output_dir):
    doc = fitz.open(input_path)
    output_files = []
    for i, page in enumerate(doc):
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=i, to_page=i)
        out_path = os.path.join(output_dir, f'page_{i + 1}.pdf')
        new_doc.save(out_path)
        new_doc.close()
        output_files.append(out_path)
    doc.close()
    return output_files


# ── 5. EXTRACT TEXT PER PAGE ────────────────────────────────────
def extract_text_by_page(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    pages = []

    if ext == '.pdf':
        doc = fitz.open(file_path)
        for i, page in enumerate(doc):
            text = page.get_text().strip()
            if text:
                pages.append({'page': i + 1, 'text': text})
        doc.close()

    elif ext in ['.docx', '.doc']:
        doc = DocxDocument(file_path)
        full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        # Split into chunks of ~500 words to simulate pages
        words = full_text.split()
        chunk_size = 500
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            pages.append({'page': (i // chunk_size) + 1, 'text': chunk})

    elif ext == '.txt':
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            full_text = f.read()
        words = full_text.split()
        chunk_size = 500
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            pages.append({'page': (i // chunk_size) + 1, 'text': chunk})

    return pages


# ── 6. SUMMARIZE ONE BLOCK OF TEXT ──────────────────────────────
def summarize_text(text, num_sentences=10):
    if not text or len(text.split()) < 30:
        return "Not enough text to summarize this section."
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summarizer.stop_words = get_stop_words("english")
        summary = summarizer(parser.document, num_sentences)
        result = " ".join(str(sentence) for sentence in summary)
        return result if result else "Could not generate summary for this section."
    except Exception as e:
        return f"Summary error: {str(e)}"


# ── 7. AI SUMMARIZE (PER PAGE, MAX 10 LINES EACH) ───────────────
def ai_summarize(file_path, num_sentences=10):
    pages = extract_text_by_page(file_path)

    if not pages:
        return [{'page': 1, 'summary': 'No readable text found in this document.'}]

    results = []
    for page in pages:
        summary = summarize_text(page['text'], num_sentences)
        results.append({
            'page': page['page'],
            'summary': summary
        })

    return results