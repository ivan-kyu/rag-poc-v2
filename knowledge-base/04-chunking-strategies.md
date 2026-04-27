# Chunking Strategies: How to Split Documents for RAG

## Why Chunking Matters

You can't embed an entire document as a single vector. Two reasons:

1. **Context window limits**: Embedding models and LLMs have token limits (e.g., 8192 tokens for text-embedding-3-small).
2. **Precision**: A vector representing an entire 50-page document is a vague "average" of its meaning. Smaller chunks create more precise vectors that match specific queries much better.

Chunking is the process of splitting documents into smaller, semantically coherent pieces before embedding them.

Poor chunking = poor retrieval = bad answers. It's often the biggest lever for improving RAG quality.

## The Core Trade-off: Chunk Size

### Small chunks (128–256 tokens)
✅ Very precise matching — retrieve exactly what's needed
✅ Less irrelevant context injected into the prompt
❌ May lose surrounding context that gives the text meaning
❌ More chunks to store and search

### Large chunks (512–1024 tokens)
✅ More context preserved around key information
✅ Fewer chunks total
❌ Embedding is "blurry" — harder to match specific queries
❌ Injects more text into the LLM prompt (higher cost, may dilute relevance)

**Sweet spot**: 256–512 tokens with overlap is the most common production choice.

## Chunking Strategy 1: Fixed-Size with Overlap

Split the document into fixed-size windows with a sliding overlap:

```
[chunk 1: tokens 0–256]
[chunk 2: tokens 128–384]   ← 128 token overlap
[chunk 3: tokens 256–512]   ← 128 token overlap
```

**Why overlap?** Key information often sits at the boundary between chunks. Overlap ensures that information isn't split across chunks and lost.

This is the simplest approach and works well for most documents. It's what this POC uses.

## Chunking Strategy 2: Recursive Character Splitting

Try to split on natural boundaries, in priority order:
1. Split on `\n\n` (paragraph breaks) first
2. If still too large, split on `\n` (line breaks)
3. If still too large, split on `. ` (sentences)
4. Last resort: split on ` ` (words) or characters

This produces more natural chunks that respect document structure. Used by LangChain's `RecursiveCharacterTextSplitter`.

## Chunking Strategy 3: Semantic Chunking

Use embeddings to find natural topic boundaries:
1. Embed each sentence
2. Compute similarity between adjacent sentences
3. When similarity drops sharply (a "semantic break"), start a new chunk

Produces the most coherent chunks — each chunk covers one topic. More expensive (requires embedding every sentence), but can significantly improve retrieval quality.

## Chunking Strategy 4: Document-Aware Splitting

Respect the structure of specific document types:

**Markdown**: Split on headers (`#`, `##`, `###`) to keep sections together
**HTML**: Split on `<section>`, `<article>`, `<p>` tags
**Code**: Split on function/class boundaries, not arbitrary character counts
**PDF**: Split on page breaks or detected sections

This is the most semantically meaningful approach for structured documents.

## Handling Metadata During Chunking

Always preserve source information with each chunk:

```json
{
  "content": "RAG combines retrieval with generation...",
  "source": "01-what-is-rag.md",
  "chunk_index": 2,
  "start_char": 456,
  "header": "The RAG Solution"
}
```

This metadata serves two purposes:
1. **Citations**: Tell the user which document the answer came from
2. **Filtered search**: Only search within certain documents or sections

## The Chunk Size Experiment

A practical way to find the optimal chunk size for your use case:

1. Take 20–30 representative queries from your users
2. For each query, manually identify the "gold standard" document passages that answer it
3. Try different chunk sizes (128, 256, 512, 1024)
4. Measure what percentage of the gold-standard passages appear in the top-3 retrieved chunks
5. Pick the chunk size with the highest recall

This is called **offline evaluation** and is essential for production RAG systems.

## Common Mistakes

**Mistake 1: No overlap**
Splitting "The capital of France is Paris. Paris is famous for its" into two chunks loses the connection between "Paris" in chunk 1 and "its" in chunk 2.

**Mistake 2: Chunks too small**
A chunk of "See above" or "As mentioned earlier" is completely meaningless without surrounding context.

**Mistake 3: Ignoring document structure**
Splitting in the middle of a table, code block, or list creates garbled chunks that confuse the LLM.

**Mistake 4: Not including enough context**
Adding the document title, section heading, or summary to the beginning of each chunk dramatically improves retrieval accuracy (called "contextual chunking").

## Summary

| Strategy | Best For | Complexity |
|---|---|---|
| Fixed-size + overlap | General purpose, quick start | Low |
| Recursive character | Mixed document types | Low |
| Semantic chunking | High-quality retrieval | High |
| Document-aware | Structured docs (Markdown, HTML, PDF) | Medium |

For this POC, we use fixed-size chunking with overlap — simple, effective, and easy to understand.
