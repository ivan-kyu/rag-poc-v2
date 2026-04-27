from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, UnstructuredMarkdownLoader
from langchain_core.documents import Document


def load_file(path: Path) -> list[Document]:
    suffix = path.suffix.lower()
    if suffix == ".md":
        loader = UnstructuredMarkdownLoader(str(path))
    elif suffix == ".pdf":
        loader = PyPDFLoader(str(path))
    else:
        raise ValueError(f"Unsupported file type: {suffix}")
    docs = loader.load()
    for doc in docs:
        doc.metadata["source"] = path.name
    return docs


def load_directory(directory: Path) -> list[Document]:
    all_docs: list[Document] = []
    for path in sorted(directory.iterdir()):
        if path.suffix.lower() in {".md", ".pdf"} and path.is_file():
            all_docs.extend(load_file(path))
    return all_docs
