import os
import shutil
from typing import List

import fitz
import uvicorn
import chromadb

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Settings
)
from llama_index.core.schema import TextNode
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from openai import OpenAI as RawOpenAI


# ============================================================
# CONFIG
# ============================================================

STORAGE_DIR = "./pdf_storage"
CHROMA_DIR = "./chroma_db"

os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

app = FastAPI(title="Enterprise PDF RAG System (Internal Qwen)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# EMBEDDINGS (LOCAL - NO OPENAI)
# ============================================================

Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-large-en-v1.5"
)

# ============================================================
# INTERNAL LLM CLIENT
# ============================================================

INTERNAL_API_KEY = "your internal api key"

llm_client = RawOpenAI(
    base_url="llm endpoint",
    api_key=INTERNAL_API_KEY,
    default_headers={
        "X-API-Key": INTERNAL_API_KEY
    }
)

LLM_MODEL = "qwen2.5-coder:14b"

pdf_index = None


# ============================================================
# SECTION EXTRACTION
# ============================================================

def extract_sections(file_path: str):
    doc = fitz.open(file_path)
    sections = {}

    for page in doc:
        blocks = page.get_text("dict")["blocks"]

        font_sizes = []
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_sizes.append(span["size"])

        if not font_sizes:
            continue

        avg_font = sum(font_sizes) / len(font_sizes)
        threshold = avg_font * 1.2

        current_section = "Main"
        buffer = []

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                text = ""
                max_font = 0

                for span in line["spans"]:
                    text += span["text"]
                    max_font = max(max_font, span["size"])

                stripped = text.strip()
                if not stripped:
                    continue

                if max_font > threshold:
                    if buffer:
                        sections[current_section] = sections.get(current_section, "") + " " + " ".join(buffer)
                        buffer = []
                    current_section = stripped
                    sections.setdefault(current_section, "")
                else:
                    buffer.append(stripped)

        if buffer:
            sections[current_section] = sections.get(current_section, "") + " " + " ".join(buffer)

    doc.close()
    return sections


# ============================================================
# BUILD INDEX
# ============================================================

def build_index(nodes: List[TextNode]):
    global pdf_index

    # Reset collection to avoid dimension mismatch
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

    try:
        chroma_client.delete_collection("pdf_sections")
    except:
        pass

    collection = chroma_client.get_or_create_collection("pdf_sections")

    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    pdf_index = VectorStoreIndex(nodes, storage_context=storage_context)


# ============================================================
# UPLOAD
# ============================================================

@app.post("/upload-pdfs")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    global pdf_index

    nodes = []

    for file in files:

        if not file.filename.lower().endswith(".pdf"):
            return {"error": f"{file.filename} is not a PDF"}

        temp_path = os.path.join(STORAGE_DIR, file.filename)

        try:
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            sections = extract_sections(temp_path)

            for section_name, content in sections.items():
                node = TextNode(
                    text=content,
                    metadata={
                        "filename": file.filename,
                        "section": section_name
                    }
                )
                nodes.append(node)

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    if not nodes:
        return {"error": "No content extracted"}

    build_index(nodes)

    return {"status": "success", "sections_indexed": len(nodes)}


# ============================================================
# HYBRID RETRIEVAL
# ============================================================

def hybrid_retrieve(question: str):

    retriever = VectorIndexRetriever(
        index=pdf_index,
        similarity_top_k=6,
        vector_store_query_mode="mmr"
    )

    nodes = retriever.retrieve(question)

    # Simple keyword re-ranking
    q_words = set(question.lower().split())

    scored = []
    for n in nodes:
        t_words = set(n.text.lower().split())
        score = len(q_words.intersection(t_words))
        scored.append((score, n))

    scored.sort(reverse=True, key=lambda x: x[0])

    return [n for _, n in scored]


# ============================================================
# LLM CALL
# ============================================================

def call_llm(prompt: str):

    response = llm_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are a professional document assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content


# ============================================================
# ASK
# ============================================================

@app.post("/ask")
async def ask_question(question: str = Form(...)):

    global pdf_index

    if pdf_index is None:
        return {"error": "Upload PDFs first."}

    nodes = hybrid_retrieve(question)

    context = "\n\n".join(
        [f"[{n.metadata['filename']} – {n.metadata['section']}]\n{n.text}" for n in nodes]
    )

    if any(w in question.lower() for w in ["difference", "compare", "changes"]):

        prompt = f"""
Compare the documents using ONLY the provided context.

Respond in this format:

## Overview
Short summary.

## Structural Differences
Bullet points

## Content Differences
Bullet points

Embed citations inline like:
(Conveyor belt.pdf – History)

Context:
{context}

Question:
{question}
"""
    else:

        prompt = f"""
Answer clearly using ONLY the provided context.

If answer not found, say:
"I could not find this in the uploaded documents."

Embed citations inline like:
(Conveyor belt.pdf – Main)

Context:
{context}

Question:
{question}
"""

    answer = call_llm(prompt)

    return {"answer": answer}


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
