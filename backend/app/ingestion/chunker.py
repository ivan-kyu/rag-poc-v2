from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def chunk_documents(docs: list[Document]) -> list[Document]:
    chunks = _splitter.split_documents(docs)
    for i, chunk in enumerate(chunks):
        chunk.metadata.setdefault("chunk_index", i)
    return chunks
