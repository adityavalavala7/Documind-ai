# DocuMind AI — Multimodal Document Intelligence

DocuMind AI is a Python-based application that uses Google Gemini to analyze PDF documents and images, extract useful information, and answer questions using retrieved document content.

## Features

- **PDF Processing:** Extract text from uploaded PDF documents.
- **Image Understanding:** Analyze images, charts, tables, diagrams, and visible text using Gemini vision.
- **Scanned PDF Support:** Analyze rendered PDF pages to extract information that may not be available through ordinary text extraction.
- **Question Answering:** Ask natural-language questions about uploaded documents.
- **Retrieval-Augmented Generation (RAG):** Retrieve relevant text chunks and use them as context for AI-generated answers.
- **Dynamic API Key:** Enter your own Google Gemini API key through the application interface.
- **Interactive UI:** Built with Streamlit for a simple, browser-based experience.
- **Source References:** Display retrieved content with filenames and PDF page numbers where available.

## Tech Stack

- Python
- Streamlit
- Google Gemini API
- Google Gen AI SDK
- PyMuPDF
- PyPDF
- Pillow
- Retrieval-Augmented Generation (RAG)
- Multimodal AI

## Project Structure

```text
Documind-ai/
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/adityavalavala7/Documind-ai.git
cd Documind-ai
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```cmd
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run the Application

Start the Streamlit application:

```bash
python -m streamlit run app.py
```

Open the local URL displayed in your terminal, usually:

```text
http://localhost:8501
```

## How to Use

1. Open the application.
2. Enter your Google Gemini API key in the sidebar.
3. Connect to Gemini.
4. Upload PDF documents or supported image files.
5. Process the uploaded files.
6. Ask questions about their contents.
7. Review the generated answers and retrieved source excerpts.

## API Key

Obtain a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).

Enter the key directly into the application's password field. Never commit API keys, passwords, or other secrets to GitHub.

API access, model availability, usage limits, and charges depend on Google's current policies and your account.

## Current Retrieval Approach

The application uses keyword-based retrieval over extracted text chunks. This is a basic RAG implementation and does not currently provide semantic vector search.

The quality of answers depends on the extracted content, retrieval relevance, model capabilities, and document readability.

## Limitations

- Scanned PDFs and complex visuals may not be extracted perfectly.
- Unreadable text and ambiguous chart values can affect accuracy.
- Processing many PDF pages may consume substantial API quota.
- Keyword-based retrieval may miss relevant passages when different terminology is used.
- Uploaded documents are processed during the active application session.

## Future Improvements

- Semantic embeddings and vector database integration.
- Improved retrieval accuracy and reranking.
- OCR enhancements for scanned documents.
- More efficient processing of large PDF collections.
- Better source citations and evaluation metrics.
- Support for additional document formats.

## Author

**Aditya Valavala**

GitHub: [adityavalavala7](https://github.com/adityavalavala7)

---

*DocuMind AI — Turn your documents into answers.*
