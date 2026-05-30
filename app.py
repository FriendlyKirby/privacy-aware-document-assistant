"""Streamlit app for a local privacy-aware document assistant."""

from pathlib import Path

import streamlit as st

from rag.answer_generator import format_sources, generate_grounded_answer
from rag.chunker import chunk_documents
from rag.document_loader import load_markdown_documents
from rag.embeddings import embed_query, embed_texts, load_embedding_model
from rag.privacy_guard import assess_privacy_risk
from rag.vector_store import build_faiss_index, search_index


PROJECT_ROOT = Path(__file__).parent
DOCUMENT_FOLDER = PROJECT_ROOT / "mock_documents"
MIN_RETRIEVAL_SCORE = 0.35

EXAMPLE_QUESTIONS = [
    "What should staff do before using AI tools with client information?",
    "Can I paste client case notes into ChatGPT?",
    "What are the volunteer onboarding steps?",
    "How are donation receipts handled?",
    "What is the process for social media approval?",
    "What should be done after an incident?",
    "What should staff avoid putting into AI tools?",
    "How should leave requests be submitted?",
]

SAMPLE_QUESTION_PLACEHOLDER = "Select a sample question..."


@st.cache_resource(show_spinner="Loading mock documents and building the local search index...")
def build_rag_pipeline():
    """Load documents, create chunks, embed them, and build a FAISS index."""
    documents = load_markdown_documents(DOCUMENT_FOLDER)
    chunks = chunk_documents(documents)
    model = load_embedding_model()
    chunk_texts = [chunk["text"] for chunk in chunks]
    chunk_embeddings = embed_texts(model, chunk_texts)
    index = build_faiss_index(chunk_embeddings)

    return {
        "documents": documents,
        "chunks": chunks,
        "model": model,
        "index": index,
    }


def show_privacy_assessment(assessment):
    """Display the privacy risk result with an appropriate Streamlit style."""
    risk_level = assessment["risk_level"]
    message = f"Privacy risk: {risk_level.upper()} - {assessment['warning_message']}"

    if risk_level == "high":
        st.error(message)
    elif risk_level == "medium":
        st.warning(message)
    else:
        st.success(message)


st.set_page_config(
    page_title="Privacy-Aware Internal Document Assistant",
    layout="wide",
)

st.title("Privacy-Aware Internal Document Assistant")

st.write(
    "This fictional portfolio demo answers questions from mock nonprofit-style "
    "policy, training, and operations documents using a local retrieval pipeline."
)

st.warning(
    "Do not enter real names, addresses, phone numbers, case notes, or "
    "confidential client information."
)

try:
    pipeline = build_rag_pipeline()
except Exception as error:
    st.error("The local RAG pipeline could not be loaded.")
    st.exception(error)
    st.stop()

documents = pipeline["documents"]
chunks = pipeline["chunks"]
model = pipeline["model"]
index = pipeline["index"]

with st.sidebar:
    st.header("Project Summary")
    st.write(
        "A local RAG demo that searches fictional internal documents and returns "
        "simple source-grounded answers without an external LLM API."
    )

    st.header("Demo Status")
    st.write("- Local RAG pipeline")
    st.write("- Mock documents only")
    st.write("- No external LLM API")
    st.write("- Privacy guard enabled")

    st.header("Loaded Documents")
    if documents:
        for document in documents:
            st.write(f"- {document['title']} (`{document['filename']}`)")
    else:
        st.write("No mock documents were loaded.")

    st.header("Pipeline")
    st.write("1. Load mock Markdown documents")
    st.write("2. Split documents into chunks")
    st.write("3. Embed chunks with sentence-transformers")
    st.write("4. Search chunks with FAISS")
    st.write("5. Check privacy risk")
    st.write("6. Generate a local grounded answer")

    st.header("Limitations")
    st.write(
        "The answer generator is simple and extractive. It does not understand "
        "documents like a full LLM and should not be used for real decisions."
    )
    st.write(f"Retrieved chunks below score {MIN_RETRIEVAL_SCORE:.2f} are filtered.")

st.subheader("Ask a Question")

selected_question = st.selectbox(
    "Choose a sample question or write your own below.",
    [SAMPLE_QUESTION_PLACEHOLDER] + EXAMPLE_QUESTIONS,
)

question_default = ""
if selected_question != SAMPLE_QUESTION_PLACEHOLDER:
    question_default = selected_question

question = st.text_area(
    "Question",
    value=question_default,
    height=120,
    placeholder="Ask about the fictional privacy, volunteer, donation, HR, social media, or incident policies.",
)

ask_clicked = st.button("Ask Assistant", type="primary")

if ask_clicked:
    clean_question = question.strip()

    if not clean_question:
        st.warning("Please enter a question first.")
        st.stop()

    assessment = assess_privacy_risk(clean_question)
    show_privacy_assessment(assessment)

    if assessment["should_refuse"]:
        st.subheader("Assistant Response")
        st.write(
            "I cannot process this request because it appears to involve sensitive "
            "or confidential information. Please remove any real personal details "
            "and ask a general policy question instead."
        )
        st.info(
            "Safer next steps: use approved internal systems, consult a supervisor "
            "or privacy lead, and avoid pasting confidential information into public AI tools."
        )
        st.stop()

    query_embedding = embed_query(model, clean_question)
    retrieved_chunks = search_index(
        index,
        query_embedding,
        chunks,
        top_k=3,
        min_score=MIN_RETRIEVAL_SCORE,
    )
    answer = generate_grounded_answer(clean_question, retrieved_chunks)
    sources = format_sources(retrieved_chunks)

    st.subheader("Assistant Response")
    st.write(answer)

    st.subheader("Retrieved Source Snippets")
    if not sources:
        st.write("No relevant source snippets were found.")
    else:
        for source in sources:
            score = source["score"]
            with st.expander(
                f"{source['title']} - {source['source']} "
                f"(chunk {source['chunk_index']}, score {score:.3f})"
            ):
                st.write(source["preview"])
