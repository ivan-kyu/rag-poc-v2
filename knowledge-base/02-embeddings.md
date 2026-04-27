# Embeddings: Turning Meaning into Numbers

## What Is an Embedding?

An embedding is a list of floating-point numbers — a vector — that represents the *semantic meaning* of a piece of text.

For example, the sentence "The cat sat on the mat" might become:
`[0.23, -0.81, 0.44, 0.09, -0.32, ... ]` (typically 768 to 3072 numbers)

The magic: **semantically similar texts produce numerically similar vectors**.

## The Vector Space Mental Model

Imagine a giant multi-dimensional space (like 3D space, but with 1536 dimensions instead of 3). Every piece of text can be placed as a point in this space.

- "dog" and "puppy" → points very close together
- "dog" and "quantum physics" → points far apart
- "What is machine learning?" and "Explain ML to me" → nearly identical points

This property — *proximity = similarity* — is what makes semantic search possible.

## How Embeddings Are Created

Embeddings are produced by neural networks (transformer models) that have been trained to understand language:

1. You pass text to the embedding model API: `embed("What is RAG?")`
2. The model processes the text through many layers of attention and transformations
3. The final layer's output is your embedding vector

Popular embedding models:
- **OpenAI text-embedding-3-small**: 1536 dimensions, fast, excellent quality
- **OpenAI text-embedding-3-large**: 3072 dimensions, higher quality, more expensive
- **nomic-embed-text** (Ollama): 768 dimensions, runs locally, free
- **all-MiniLM-L6-v2**: 384 dimensions, very fast, great for experimentation

## Cosine Similarity: How We Measure Closeness

The most common way to compare two vectors is **cosine similarity**. It measures the angle between two vectors:

- **Score of 1.0**: Identical direction → semantically identical
- **Score of 0.8–1.0**: Very similar meaning
- **Score of 0.5–0.7**: Related but different
- **Score close to 0**: Unrelated

The formula:
```
cosine_similarity(A, B) = (A · B) / (|A| × |B|)
```

Where `A · B` is the dot product (sum of element-wise products) and `|A|` is the magnitude (length) of the vector.

## Why Not Just Use Keyword Search?

Traditional keyword search (like grep or SQL LIKE) only finds **exact word matches**. Semantic search with embeddings finds **meaning matches**.

Example:
- Query: "how do I cancel my order?"
- Keyword search finds: documents containing "cancel" and "order"
- Semantic search finds: documents about "refund policy", "return process", "order cancellation" — even if they don't use those exact words

This is a game-changer for real-world applications where users don't always know the exact terminology.

## The Embedding Process in RAG

RAG uses embeddings in two phases:

### Phase 1: Indexing (happens once, at document load time)
1. Take each text chunk from your documents
2. Call the embedding model API on each chunk
3. Store the chunk + its embedding vector in the vector database

### Phase 2: Querying (happens on every user question)
1. Take the user's question
2. Call the embedding model API on the question → get a query vector
3. Compare the query vector against all stored vectors using cosine similarity
4. Return the top-k most similar chunks

## Embedding Dimensions: What Does "1536 Dimensions" Mean?

Think of dimensions as independent axes of meaning. Each dimension might loosely capture concepts like:
- Dimension 1: Technical vs. casual language
- Dimension 2: Emotional vs. neutral tone
- Dimension 3: Past vs. present vs. future tense
- ...and 1533 more abstract features

No single dimension has a clear human-readable meaning — they emerge from training. Together, they create a rich geometric representation of language.

## Key Takeaway

Embeddings are the secret ingredient that makes semantic search possible. By turning language into geometry, we can find relevant documents not by matching words, but by matching *ideas*.
