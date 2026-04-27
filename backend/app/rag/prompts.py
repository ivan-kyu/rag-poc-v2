from langchain_core.prompts import ChatPromptTemplate

SYSTEM_PROMPT = """You are a helpful assistant that answers questions based strictly on the provided context.

Rules:
- Answer ONLY from the context below. Do not use prior knowledge.
- If the context does not contain enough information, say so clearly.
- Be concise and precise.
- Always cite your sources by referencing the document name.
"""

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """Context:
{context}

Question: {question}

Provide a structured answer with citations."""),
])

ROUTE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Classify the user's query into one of: factual, definition, procedural.
- factual: asks about specific facts, entities, or data points
- definition: asks what something is or means
- procedural: asks how to do something, step-by-step

Respond with ONLY the single word: factual, definition, or procedural."""),
    ("human", "{query}"),
])

HYDE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Write a short, precise paragraph that would appear in a technical document answering the following question. Be factual and direct."),
    ("human", "{query}"),
])
