from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # LangSmith (new SDK uses LANGSMITH_ prefix)
    langsmith_api_key: str = ""
    langsmith_tracing: bool = False
    langsmith_project: str = "rag-poc-v2"
    langsmith_endpoint: str = "https://api.smith.langchain.com"

    # Vector backend
    vector_backend: str = "chroma"  # "chroma" | "pgvector"
    chroma_persist_dir: str = "./chroma_data"
    database_url: str = ""

    # Supabase (file storage)
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # Reranking
    cohere_api_key: str = ""

    # Knowledge base
    knowledge_base_dir: str = "../knowledge-base"


settings = Settings()
