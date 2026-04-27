"""Curated eval Q/A pairs for the RAG knowledge base."""

EVAL_DATASET = [
    {
        "question": "What is Retrieval-Augmented Generation (RAG)?",
        "ground_truth": "RAG is a technique that combines retrieval of relevant documents with generative AI to answer questions using up-to-date or domain-specific knowledge not baked into the model.",
    },
    {
        "question": "Why is RAG preferred over fine-tuning for adding new knowledge?",
        "ground_truth": "RAG is cheaper and faster to update - you just add documents to the knowledge base instead of retraining. Fine-tuning is expensive and doesn't generalize well to frequent knowledge updates.",
    },
    {
        "question": "What are embeddings in the context of RAG?",
        "ground_truth": "Embeddings are dense vector representations of text that capture semantic meaning, allowing similar concepts to be close together in vector space for retrieval by cosine similarity.",
    },
    {
        "question": "What is cosine similarity and how is it used in RAG?",
        "ground_truth": "Cosine similarity measures the angle between two vectors. In RAG, it compares query embeddings to document chunk embeddings to find the most semantically relevant chunks.",
    },
    {
        "question": "What is a vector database?",
        "ground_truth": "A vector database stores high-dimensional embeddings and supports fast approximate nearest-neighbor search to find semantically similar documents at scale.",
    },
    {
        "question": "What is HNSW and why is it used?",
        "ground_truth": "HNSW (Hierarchical Navigable Small World) is an approximate nearest-neighbor index that provides fast vector search with high recall, used in vector databases like pgvector and Chroma.",
    },
    {
        "question": "What is chunking and why does it matter?",
        "ground_truth": "Chunking splits documents into smaller pieces before embedding. It matters because LLMs have context limits and smaller, focused chunks retrieve more precisely than whole documents.",
    },
    {
        "question": "What is chunk overlap and why is it used?",
        "ground_truth": "Chunk overlap repeats some content between adjacent chunks to avoid losing context at boundaries where a sentence or idea spans the split point.",
    },
    {
        "question": "What is the typical chunk size and overlap for RAG?",
        "ground_truth": "Common values are 512-1000 characters for chunk size and 10-20% of chunk size for overlap, though the optimal values depend on the document type.",
    },
    {
        "question": "What role does the LLM play in a RAG pipeline?",
        "ground_truth": "The LLM synthesizes the retrieved context and user question into a coherent, grounded answer. It does not retrieve - retrieval is done by the vector search step.",
    },
    {
        "question": "What is temperature in LLM generation and what value suits RAG?",
        "ground_truth": "Temperature controls randomness. Lower values (0.0-0.3) produce more deterministic, factual answers - ideal for RAG where you want grounded, consistent responses.",
    },
    {
        "question": "What is a system prompt in RAG?",
        "ground_truth": "The system prompt instructs the LLM to answer only from the provided context, cite sources, and admit uncertainty when context is insufficient.",
    },
    {
        "question": "What is hybrid search in RAG?",
        "ground_truth": "Hybrid search combines dense vector similarity with sparse keyword (BM25) search. It improves retrieval for queries with specific terms or entity names that embeddings alone might miss.",
    },
    {
        "question": "What is pgvector?",
        "ground_truth": "pgvector is a PostgreSQL extension that adds vector storage and similarity search, allowing a standard Postgres database to serve as a vector store for RAG applications.",
    },
    {
        "question": "What is ChromaDB?",
        "ground_truth": "ChromaDB is an open-source, purpose-built vector database designed for embedding storage and semantic search, popular for local development and prototyping.",
    },
    {
        "question": "What models are commonly used for embeddings?",
        "ground_truth": "Popular embedding models include OpenAI text-embedding-3-small/large, Cohere embed, and open-source models like nomic-embed-text and bge-small-en.",
    },
    {
        "question": "What is semantic chunking?",
        "ground_truth": "Semantic chunking splits documents at natural semantic boundaries (e.g., topic changes) rather than fixed character counts, producing more coherent chunks.",
    },
    {
        "question": "What is the difference between approximate and exact nearest-neighbor search?",
        "ground_truth": "Exact search guarantees finding the closest vector but is slow at scale. Approximate search (ANN) trades a small amount of recall for dramatically faster query times.",
    },
    {
        "question": "What is streaming in LLM responses and why is it useful?",
        "ground_truth": "Streaming sends tokens one-by-one as they are generated instead of waiting for the full response, giving users faster perceived response times and real-time feedback.",
    },
    {
        "question": "What popular vector databases exist besides pgvector and ChromaDB?",
        "ground_truth": "Popular alternatives include Pinecone (managed cloud), Qdrant (open-source with cloud tier), Weaviate (hybrid search native), and Milvus (large-scale distributed).",
    },
]
