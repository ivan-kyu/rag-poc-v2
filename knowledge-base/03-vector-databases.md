# Vector Databases: Storing and Searching at Scale

## What Is a Vector Database?

A vector database is a specialized database designed to efficiently store, index, and query high-dimensional vectors (embeddings).

Traditional databases store and search structured data using exact-match queries:
```sql
SELECT * FROM users WHERE name = 'Alice'
```

Vector databases store and search embeddings using approximate similarity:
```
Find the 10 vectors most similar to [0.23, -0.81, 0.44, ...]
```

## The Naive Approach (What We Do in This POC)

The simplest possible vector "database" is an **in-memory list**:

1. Store all chunks and their embeddings in an array
2. On each query, compute cosine similarity between the query vector and *every* stored vector
3. Sort by similarity and return the top-k results

This is called **exact nearest neighbor search** — it's 100% accurate but scales as O(n) for every query. Fine for hundreds or thousands of documents, but too slow for millions.

## The Real Problem: Approximate Nearest Neighbor (ANN)

With millions of vectors, comparing the query against every single one takes too long. The solution is **Approximate Nearest Neighbor (ANN)** search — algorithms that trade a tiny amount of accuracy for massive speed improvements.

### HNSW (Hierarchical Navigable Small World)
The most popular ANN algorithm. Builds a multi-layer graph where:
- Higher layers have fewer, well-connected "highway" nodes
- Lower layers have all nodes with short-range connections
- Search starts at the top (fast long-distance jumps) and descends to fine-grained results

Think of it like navigating a city: take the highway to get close, then use local streets to find the exact house.

### IVF (Inverted File Index)
Groups vectors into clusters (using k-means). At query time:
1. Find the nearest cluster centroids
2. Search only within those clusters
- Much faster than full scan, with minor accuracy loss

## Popular Vector Databases

### Fully Managed (Cloud)
- **Pinecone**: Most popular managed vector DB. Simple API, scales automatically. Great for production.
- **Weaviate Cloud**: Open-source with managed option. Supports hybrid search (keywords + vectors).
- **Qdrant Cloud**: Rust-based, very fast. Excellent for high-throughput applications.

### Self-Hosted / Local
- **Chroma**: The easiest to get started with locally. Built for AI applications. Can run embedded in Python or as a server.
- **Qdrant**: Can run locally via Docker. Same API as the cloud version.
- **Milvus**: Enterprise-grade, runs on Kubernetes. Handles billions of vectors.

### Embedded in SQL
- **pgvector**: A PostgreSQL extension that adds vector types and ANN search to your existing Postgres database. If you're already using Postgres (e.g., Supabase), this is the easiest upgrade path.

## Metadata Filtering: Beyond Pure Similarity

Most vector databases support **filtered search**: find the top-k similar vectors WHERE some condition is true.

Example: "Find the most relevant chunks from documents in the 'legal' category created after 2024-01-01"

This combines:
- Semantic similarity (embedding search)
- Structured filtering (metadata conditions)

Very powerful for multi-tenant applications or domain-specific search.

## Hybrid Search: The Best of Both Worlds

Combining dense vector search (semantic) with sparse keyword search (BM25/TF-IDF):
- Dense search: "What documents *mean* the same as my query?"
- Sparse search: "What documents *contain* the keywords in my query?"
- Combined score: weighted sum of both scores

This catches both semantically related content AND exact-match keywords, reducing the risk of missing critical results.

## What Lives in a Vector Database Record?

Each record typically contains:
```json
{
  "id": "chunk_42",
  "vector": [0.23, -0.81, 0.44, ...],
  "metadata": {
    "source": "return-policy.md",
    "chunk_index": 3,
    "created_at": "2024-01-15"
  },
  "content": "Our return policy allows returns within 30 days..."
}
```

The vector enables similarity search; the metadata enables filtering; the content is what you return to the LLM.

## This POC vs. Production

| Feature | This POC | Production |
|---|---|---|
| Storage | In-memory array | Persistent DB |
| Search | Exact (O(n)) | ANN (O(log n)) |
| Scale | Hundreds of chunks | Millions of chunks |
| Persistence | Lost on restart | Durable |
| Filtering | Manual | Built-in |

For this POC, the in-memory approach is perfect: it's transparent, easy to understand, and requires zero infrastructure setup. The upgrade path to a real vector DB (like pgvector or Chroma) is straightforward.
