"""Paragraph-based document chunking helpers.

The first version used raw character slicing, which can create chunks that
start in the middle of a word or sentence. This version splits documents into
paragraphs first, then combines paragraphs into readable chunks.
"""

import re


def _clean_paragraph(paragraph):
    """Normalize whitespace and remove Markdown heading markers."""
    paragraph = paragraph.strip()
    paragraph = re.sub(r"^#{1,6}\s*", "", paragraph)
    paragraph = re.sub(r"\s+", " ", paragraph)
    return paragraph.strip()


def _document_paragraphs(text):
    """Return clean paragraphs, skipping the top document title.

    Mock documents begin with an H1 title. The document title is already stored
    as metadata, so chunks start with the body content instead of repeating it.
    """
    raw_paragraphs = re.split(r"\n\s*\n", text.strip())
    paragraphs = []

    for index, paragraph in enumerate(raw_paragraphs):
        paragraph = paragraph.strip()

        if index == 0 and paragraph.startswith("# "):
            continue

        if re.match(r"^#{1,6}\s+.+$", paragraph) and "\n" not in paragraph:
            continue

        clean_paragraph = _clean_paragraph(paragraph)

        if clean_paragraph:
            paragraphs.append(clean_paragraph)

    return paragraphs


def _overlap_paragraphs(paragraphs, overlap):
    """Keep whole paragraphs for overlap instead of cutting by character."""
    if overlap <= 0:
        return []

    selected = []
    total_length = 0

    for paragraph in reversed(paragraphs):
        selected.insert(0, paragraph)
        total_length += len(paragraph)

        if total_length >= overlap:
            break

    return selected


def chunk_document(document, chunk_size=800, overlap=150):
    """Split one document into readable overlapping paragraph chunks.

    Args:
        document: A dictionary with filename, title, and text keys.
        chunk_size: Approximate maximum number of characters per chunk.
        overlap: Approximate amount of previous text to repeat, using whole
            paragraphs when possible.

    Returns:
        A list of chunk dictionaries with text, source, title, and chunk_index.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")

    if overlap < 0:
        raise ValueError("overlap must be 0 or greater.")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    paragraphs = _document_paragraphs(document.get("text", ""))
    if not paragraphs:
        return []

    chunks = []
    current_paragraphs = []
    chunk_index = 1

    for paragraph in paragraphs:
        candidate_paragraphs = current_paragraphs + [paragraph]
        candidate_text = "\n\n".join(candidate_paragraphs)

        if current_paragraphs and len(candidate_text) > chunk_size:
            chunk_text = "\n\n".join(current_paragraphs).strip()
            chunks.append(
                {
                    "text": chunk_text,
                    "source": document.get("filename", ""),
                    "title": document.get("title", ""),
                    "chunk_index": chunk_index,
                }
            )
            chunk_index += 1

            # Start the next chunk with whole previous paragraphs for context.
            current_paragraphs = _overlap_paragraphs(current_paragraphs, overlap)

        current_paragraphs.append(paragraph)

    if current_paragraphs:
        chunk_text = "\n\n".join(current_paragraphs).strip()
        if chunk_text:
            chunks.append(
                {
                    "text": chunk_text,
                    "source": document.get("filename", ""),
                    "title": document.get("title", ""),
                    "chunk_index": chunk_index,
                }
            )

    return chunks


def chunk_documents(documents, chunk_size=800, overlap=150):
    """Split multiple documents into one list of searchable chunks."""
    all_chunks = []

    for document in documents:
        all_chunks.extend(chunk_document(document, chunk_size, overlap))

    return all_chunks
