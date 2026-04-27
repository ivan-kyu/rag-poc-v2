# LLMs and Prompt Construction in RAG

## What Is a Large Language Model?

A Large Language Model (LLM) is a neural network trained to predict the next token in a sequence of text. Despite this simple objective, models trained at scale develop remarkable emergent capabilities: reasoning, summarization, translation, code generation, and more.

Modern LLMs are based on the **Transformer architecture** (2017, Google). Key components:
- **Attention mechanism**: Allows the model to weigh the importance of different parts of the input when generating each token
- **Feed-forward layers**: Process attention outputs to produce representations
- **Positional encodings**: Give the model a sense of token order

Popular LLMs used in RAG systems:
- **GPT-4o** (OpenAI): State-of-the-art, 128k context window, excellent reasoning
- **GPT-4o-mini** (OpenAI): Faster and cheaper, still very capable for RAG tasks
- **Claude 3.5 Sonnet** (Anthropic): Strong reasoning, 200k context window
- **Llama 3.2** (Meta, via Ollama): Open-source, runs locally, no API costs
- **Mistral / Mixtral** (Mistral AI, via Ollama): Excellent performance/cost ratio

## The Role of the LLM in RAG

In a RAG system, the LLM has one core job: **read the retrieved context and generate a faithful, grounded answer**.

The LLM should:
- Synthesize information from multiple retrieved chunks
- Answer only what the evidence supports
- Cite sources when possible
- Gracefully decline if the context doesn't contain an answer

The LLM should NOT:
- Invent facts not present in the retrieved context
- Override retrieved context with memorized training data
- Hallucinate sources or citations

## The RAG Prompt Template

The quality of the RAG system depends heavily on how you construct the prompt. Here's a battle-tested template:

```
SYSTEM:
You are a helpful assistant that answers questions based strictly on the 
provided context documents. 

Rules:
- Only use information from the provided context to answer.
- If the context doesn't contain enough information, say so clearly.
- Quote or reference the source when relevant.
- Be concise and direct.

USER:
Here are the relevant context documents:

--- Document 1 (source: embeddings.md, relevance: 0.92) ---
An embedding is a list of floating-point numbers that represents 
the semantic meaning of a piece of text...

--- Document 2 (source: what-is-rag.md, relevance: 0.87) ---
RAG combines retrieval with generation to ground LLM answers in 
real documents...

---

Question: What are embeddings and why are they used in RAG?
```

## Context Window: The LLM's Working Memory

The context window is the maximum number of tokens an LLM can process at once. Everything — the system prompt, retrieved chunks, conversation history, and the user's question — must fit within this limit.

| Model | Context Window | Practical RAG Chunks |
|---|---|---|
| GPT-4o | 128,000 tokens | ~100–200 chunks |
| GPT-4o-mini | 128,000 tokens | ~100–200 chunks |
| Llama 3.2 (local) | 8,192 tokens | ~6–12 chunks |

For this POC, we retrieve the top-5 chunks per query — well within any model's context window.

## Token Budgeting

In production RAG, you must carefully budget your tokens:

```
Total budget: 8,000 tokens
System prompt: ~200 tokens
Retrieved context (5 chunks × 300 tokens): ~1,500 tokens  
Conversation history: ~500 tokens
User question: ~50 tokens
Response reserve: ~1,000 tokens
─────────────────────────────
Total used: ~3,250 tokens ✅
```

If you retrieve too many chunks or have too long a conversation history, you'll hit the context limit and the request will fail.

## Streaming Responses

Modern LLMs generate text token by token. Instead of waiting for the complete response, you can **stream** tokens as they're generated:

1. Make the API call with `stream: true`
2. The API returns a stream of chunks, each containing 1–5 new tokens
3. Your UI updates in real-time as tokens arrive
4. Users see the response appear word by word, reducing perceived latency

This is why chatbots feel "alive" — they're streaming the model's output in real-time.

## Preventing Hallucination in RAG

Hallucination (making up plausible-sounding but false information) is the #1 risk with LLMs. RAG reduces it significantly, but you need defensive prompting:

**Explicit grounding instruction**: "Only answer based on the provided context. If the answer is not in the context, say 'I don't have enough information to answer this.'"

**Temperature control**: Lower temperature (0.0–0.3) makes the model more conservative and less likely to invent information. Higher temperature (0.7–1.0) is more creative but more prone to hallucination.

**Citation enforcement**: Ask the model to cite which document each claim comes from. If it can't cite, it shouldn't claim.

## The Answer Quality Flywheel

RAG quality improves iteratively:
1. Users ask questions → some get bad answers
2. You identify which retrieved chunks led to bad answers
3. You improve chunking, add more documents, or refine the prompt
4. Better answers → more user trust → more questions

This is called the **evaluation → improvement loop**. Production RAG systems use automated evaluation frameworks (LangSmith, RAGAS, TruLens) to measure answer quality at scale.

## Summary: The LLM's Place in RAG

```
Query → Embed → Retrieve → [CONTEXT] + Query → LLM → Answer
                              ↑
                    This is where the LLM lives.
                    It reads context, reasons over it,
                    and generates a grounded response.
```

The LLM is powerful but blind — it only sees what you put in its context window. Good RAG is the art of making sure the right information is always in that window.
