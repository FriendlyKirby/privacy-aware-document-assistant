"""Simple local answer generation helpers.

This file intentionally avoids external LLM APIs. The answer is extractive:
it selects readable sentences from retrieved mock document chunks.
"""

import re


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "before",
    "can",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "should",
    "staff",
    "the",
    "to",
    "what",
    "when",
    "who",
    "with",
}

FINAL_NOTE = (
    "This answer is limited to the retrieved fictional sources. Human review is "
    "needed for sensitive, privacy-related, HR, safety, or policy decisions."
)


def _clean_markdown(text):
    """Remove simple Markdown markers and normalize whitespace."""
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("*", "")
    return re.sub(r"\s+", " ", text).strip()


def _question_keywords(question):
    """Extract simple keywords from the user's question."""
    words = re.findall(r"[a-zA-Z]{3,}", question.lower())
    return {word for word in words if word not in STOP_WORDS}


def _looks_like_complete_sentence(sentence):
    """Filter out short headings and fragments that look cut off."""
    if len(sentence) < 35:
        return False

    if not re.match(r"^[A-Z0-9]", sentence):
        return False

    if sentence.endswith(":"):
        return False

    return sentence.endswith((".", "?", "!"))


def _split_readable_sentences(text):
    """Split chunk text into readable complete sentences."""
    clean_text = _clean_markdown(text)
    sentences = re.split(r"(?<=[.!?])\s+", clean_text)
    return [
        sentence.strip()
        for sentence in sentences
        if _looks_like_complete_sentence(sentence.strip())
    ]


def _truncate_preview(text, max_length=450):
    """Shorten source previews without cutting through a word."""
    clean_text = _clean_markdown(text)

    if len(clean_text) <= max_length:
        return clean_text

    truncated = clean_text[:max_length].rsplit(" ", 1)[0].rstrip()
    return truncated + "..."


def generate_grounded_answer(question, retrieved_chunks):
    """Generate a concise source-grounded answer from retrieved chunks.

    Args:
        question: User question as a string.
        retrieved_chunks: List of relevant chunk dictionaries.

    Returns:
        A local, extractive answer based only on retrieved mock documents.
    """
    if not retrieved_chunks:
        return "I could not find a clear answer in the available mock documents."

    keywords = _question_keywords(question)
    ranked_sentences = []
    seen_sentences = set()

    for chunk_position, chunk in enumerate(retrieved_chunks):
        chunk_score = chunk.get("score", 0.0)

        for sentence_position, sentence in enumerate(_split_readable_sentences(chunk.get("text", ""))):
            sentence_key = sentence.lower()
            if sentence_key in seen_sentences:
                continue

            keyword_matches = sum(
                1 for keyword in keywords if keyword in sentence.lower()
            )

            # Prefer keyword matches, then higher-ranked chunks, then earlier text.
            rank = (keyword_matches, chunk_score, -chunk_position, -sentence_position)
            ranked_sentences.append((rank, sentence))
            seen_sentences.add(sentence_key)

    if not ranked_sentences:
        return "I could not find a clear answer in the available mock documents."

    ranked_sentences.sort(reverse=True)
    selected_sentences = [sentence for _rank, sentence in ranked_sentences[:5]]

    bullet_points = "\n".join(f"- {sentence}" for sentence in selected_sentences)

    return (
        "Based on the retrieved mock documents, the most relevant guidance is:\n\n"
        f"{bullet_points}\n\n"
        f"{FINAL_NOTE}"
    )


def format_sources(retrieved_chunks):
    """Format retrieved chunks as readable source snippets.

    Args:
        retrieved_chunks: List of relevant chunk dictionaries.

    Returns:
        A list of dictionaries with display-ready source metadata and previews.
    """
    sources = []

    for chunk in retrieved_chunks:
        sources.append(
            {
                "title": chunk.get("title", "Untitled document"),
                "source": chunk.get("source", "Unknown file"),
                "chunk_index": chunk.get("chunk_index", "?"),
                "score": chunk.get("score", 0.0),
                "preview": _truncate_preview(chunk.get("text", "")),
            }
        )

    return sources
