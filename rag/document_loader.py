"""Utilities for loading fictional Markdown documents."""

from pathlib import Path


def _title_from_markdown(text, fallback_title):
    """Return the first Markdown heading, or a readable fallback title."""
    for line in text.splitlines():
        clean_line = line.strip()
        if clean_line.startswith("#"):
            return clean_line.lstrip("#").strip()

    return fallback_title


def load_markdown_documents(folder_path):
    """Load mock Markdown documents from a folder.

    The sample questions file is intentionally ignored because it is an app
    helper, not a source document for retrieval.

    Args:
        folder_path: Path to a folder containing `.md` files.

    Returns:
        A list of dictionaries with filename, title, and text keys.

    Raises:
        FileNotFoundError: If the folder does not exist.
    """
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(
            f"Document folder not found: {folder}. "
            "Make sure the mock_documents folder exists in the project root."
        )

    documents = []

    for file_path in sorted(folder.glob("*.md")):
        if file_path.name.lower() == "sample_questions.md":
            continue

        text = file_path.read_text(encoding="utf-8").strip()
        if not text:
            continue

        fallback_title = file_path.stem.replace("_", " ").title()
        title = _title_from_markdown(text, fallback_title)

        documents.append(
            {
                "filename": file_path.name,
                "title": title,
                "text": text,
            }
        )

    return documents
