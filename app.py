
import streamlit as st
from google import genai
from google.genai import types
from pypdf import PdfReader
from PIL import Image
from io import BytesIO
import fitz  # PyMuPDF
import re

st.set_page_config(
    page_title="AI Document & Image Assistant",
    page_icon="📚",
    layout="wide"
)

st.title("📚 AI Document & Image Assistant")
st.write("Upload PDFs and images, extract their content, and ask questions.")

# ---------------- SESSION STATE ----------------
defaults = {
    "client": None,
    "model": "gemini-2.5-flash",
    "chunks": [],
    "history": [],
    "connected": False
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------- HELPERS ----------------
def split_text(text, size=2200, overlap=250):
    """Split extracted content into searchable chunks."""
    chunks = []
    step = size - overlap

    for start in range(0, len(text), step):
        piece = text[start:start + size].strip()
        if piece:
            chunks.append(piece)

    return chunks


def analyze_image(client, model, image_bytes, mime_type, instructions):
    """Ask Gemini to read and describe an image."""
    response = client.models.generate_content(
        model=model,
        contents=[
            instructions,
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            )
        ]
    )
    return response.text or ""


def add_chunks(records, text, source, page=None, kind="text"):
    """Store content along with its source information."""
    for part in split_text(text):
        records.append({
            "text": part,
            "source": source,
            "page": page,
            "kind": kind
        })


def retrieve(question, records, limit=6):
    """Simple keyword-based retrieval over extracted text."""
    words = set(
        re.findall(r"\w+", question.lower())
    )
    words = {word for word in words if len(word) > 2}

    if not words:
        return records[:limit]

    def calculate_score(record):
        content = record["text"].lower()
        score = sum(
            len(re.findall(r"\b" + re.escape(word) + r"\b", content))
            for word in words
        )
        return score

    ranked = sorted(
        records,
        key=calculate_score,
        reverse=True
    )

    relevant = [r for r in ranked if calculate_score(r) > 0]

    # Fall back to the first chunks if no exact keyword matches.
    return (relevant or ranked)[:limit]


# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("🔐 Gemini connection")

    api_key = st.text_input(
        "Gemini API key",
        type="password",
        placeholder="Enter your own API key"
    )

    model = st.text_input(
        "Model name",
        value=st.session_state.model
    )

    if st.button("Connect to Gemini", type="primary"):
        if not api_key.strip() or not model.strip():
            st.error("Enter both an API key and model name.")
        else:
            try:
                new_client = genai.Client(api_key=api_key.strip())

                with st.spinner("Testing connection..."):
                    new_client.models.generate_content(
                        model=model.strip(),
                        contents="Reply with the word Connected."
                    )

                st.session_state.client = new_client
                st.session_state.model = model.strip()
                st.session_state.connected = True
                st.session_state.chunks = []
                st.session_state.history = []

                st.success("Gemini connected!")
                st.rerun()

            except Exception as e:
                st.session_state.client = None
                st.session_state.connected = False
                st.error("Connection failed. Check the key, model and quota.")
                st.code(str(e))

    if st.session_state.connected:
        st.success("Ready to process files")
        st.caption(f"Model: {st.session_state.model}")

    st.divider()
    st.caption(
        "Your key is not saved to a configuration file by this app. "
        "It is used to send requests to Google."
    )


# ---------------- FILE UPLOAD ----------------
st.header("1. Upload documents and images")

uploads = st.file_uploader(
    "Select PDFs or images",
    type=["pdf", "png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True
)

st.caption(
    "PDF pages are processed for text and visual content. "
    "Images are analyzed for text, tables, charts and diagrams."
)

if st.button("Extract and index content", type="primary"):
    if not st.session_state.connected or not st.session_state.client:
        st.warning("Enter your API key and connect first.")
    elif not uploads:
        st.warning("Please upload at least one file.")
    else:
        records = []
        client = st.session_state.client
        model_name = st.session_state.model
        progress = st.progress(0)

        for file_index, uploaded in enumerate(uploads):
            filename = uploaded.name
            data = uploaded.getvalue()

            st.write(f"Processing: **{filename}**")

            try:
                if filename.lower().endswith(".pdf"):
                    # Extract selectable text first.
                    reader = PdfReader(BytesIO(data))

                    for page_num, page in enumerate(reader.pages, start=1):
                        page_text = page.extract_text() or ""

                        if page_text.strip():
                            add_chunks(
                                records,
                                page_text,
                                filename,
                                page=page_num,
                                kind="PDF text"
                            )

                    # Render every PDF page and use vision to read
                    # scanned text, charts, diagrams and other visuals.
                    pdf_doc = fitz.open(stream=data, filetype="pdf")

                    for page_index in range(len(pdf_doc)):
                        page = pdf_doc.load_page(page_index)

                        # Render at moderate resolution to limit request size.
                        pix = page.get_pixmap(
                            matrix=fitz.Matrix(1.5, 1.5),
                            alpha=False
                        )

                        image_bytes = pix.tobytes("jpeg")

                        visual_text = analyze_image(
                            client,
                            model_name,
                            image_bytes,
                            "image/jpeg",
                            """
                            Inspect this document page carefully.
                            Extract visible text that may be missing from
                            ordinary PDF text extraction. Describe tables,
                            charts, diagrams, labels, figures and their
                            relationships. Preserve numbers and units where
                            legible. Clearly mark unreadable content.
                            Do not guess missing values.
                            """
                        )

                        if visual_text.strip():
                            add_chunks(
                                records,
                                visual_text,
                                filename,
                                page=page_index + 1,
                                kind="Visual extraction"
                            )

                    pdf_doc.close()

                else:
                    # Process standalone images.
                    image = Image.open(BytesIO(data))
                    image = image.convert("RGB")

                    # Re-encode as JPEG for a predictable MIME type.
                    buffer = BytesIO()
                    image.save(buffer, format="JPEG", quality=90)

                    visual_text = analyze_image(
                        client,
                        model_name,
                        buffer.getvalue(),
                        "image/jpeg",
                        """
                        Analyze this image for document retrieval.
                        Read visible text, headings, labels, tables,
                        chart titles, axes, legends, values and diagrams.
                        Describe important visual information.
                        Preserve numbers and units where legible.
                        Clearly state when text or values are unreadable.
                        Do not invent information.
                        """
                    )

                    if visual_text.strip():
                        add_chunks(
                            records,
                            visual_text,
                            filename,
                            kind="Image extraction"
                        )

            except Exception as e:
                st.warning(f"Could not fully process {filename}: {e}")

            progress.progress((file_index + 1) / len(uploads))

        st.session_state.chunks = records
        st.session_state.history = []

        if records:
            st.success(
                f"Extraction complete. Indexed {len(records)} text chunks."
            )
        else:
            st.error("No content was extracted from the uploaded files.")


# ---------------- RETRIEVAL AND Q&A ----------------
st.divider()
st.header("2. Retrieve information and ask questions")

if st.session_state.chunks:
    st.info(
        f"{len(st.session_state.chunks)} searchable chunks are available."
    )

question = st.text_area(
    "Ask a question about your files",
    placeholder=(
        "Example: What does the chart show? "
        "What is the highest value in the table? "
        "Summarize page 3."
    )
)

if st.button("Search and answer"):
    if not st.session_state.connected or not st.session_state.client:
        st.warning("Connect to Gemini first.")
    elif not st.session_state.chunks:
        st.warning("Upload and index files first.")
    elif not question.strip():
        st.warning("Enter a question.")
    else:
        try:
            with st.spinner("Retrieving relevant content..."):
                matches = retrieve(
                    question,
                    st.session_state.chunks,
                    limit=6
                )

                context_parts = []

                for item in matches:
                    location = item["source"]

                    if item.get("page") is not None:
                        location += f", page {item['page']}"

                    context_parts.append(
                        f"Source: {location}\n"
                        f"Content type: {item['kind']}\n"
                        f"{item['text']}"
                    )

                context = "\n\n---\n\n".join(context_parts)

            with st.spinner("Generating answer..."):
                prompt = f"""
You are a document and image question-answering assistant.

Answer using only the retrieved excerpts below.
If the excerpts do not answer the question, say that the
available retrieved content is insufficient.
Do not invent facts, numbers or chart values.
Distinguish directly extracted information from interpretation.
Cite source filenames and PDF page numbers in your answer.

RETRIEVED EXCERPTS:
{context}

QUESTION:
{question}
"""

                response = st.session_state.client.models.generate_content(
                    model=st.session_state.model,
                    contents=prompt
                )

                answer = response.text or "No answer was returned."

            st.subheader("💡 Answer")
            st.markdown(answer)

            st.subheader("📌 Retrieved sources")

            for item in matches:
                location = item["source"]

                if item.get("page") is not None:
                    location += f" — page {item['page']}"

                with st.expander(f"{location} · {item['kind']}"):
                    st.write(item["text"])

            st.session_state.history.append({
                "question": question,
                "answer": answer
            })

        except Exception as e:
            st.error("Could not retrieve or answer the question.")
            st.code(str(e))


# ---------------- HISTORY ----------------
if st.session_state.history:
    st.divider()
    st.header("Previous questions")

    for item in reversed(st.session_state.history):
        with st.expander(item["question"]):
            st.markdown(item["answer"])

    if st.button("Clear history"):
        st.session_state.history = []
        st.rerun()