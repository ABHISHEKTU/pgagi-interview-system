"""
RAG Service
Handles: knowledge base ingestion → FAISS vector store → retrieval
"""
import os
import fitz
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from config import settings

# Role → subfolder mapping in knowledge_base/
ROLE_TO_FOLDER = {
    "AI/ML Engineer": "aiml",
    "Backend Engineer": "backend",
    "Data Scientist": "datascience",
    "Full Stack Engineer": "fullstack",
}

_embeddings = None
_vector_stores: dict[str, FAISS] = {}  # cache per role


def get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings


def _extract_text_from_pdf(path: str) -> str:
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def _get_store_path(role_key: str) -> str:
    return os.path.join(settings.VECTOR_STORE_PATH, role_key)


def ingest_knowledge_base(role: str) -> int:
    """
    Load PDFs from knowledge_base/<role_folder>/,
    chunk, embed, save FAISS index.
    Returns number of chunks indexed.
    """
    role_key = ROLE_TO_FOLDER.get(role, "aiml")
    folder = os.path.join(settings.KNOWLEDGE_BASE_PATH, role_key)

    if not os.path.exists(folder):
        raise FileNotFoundError(f"Knowledge base folder not found: {folder}")

    pdf_files = list(Path(folder).glob("*.pdf"))
    if not pdf_files:
        raise ValueError(f"No PDFs found in {folder}")

    # Extract text from all PDFs
    all_text = ""
    for pdf_path in pdf_files:
        print(f"  Loading: {pdf_path.name}")
        all_text += f"\n\n--- Source: {pdf_path.name} ---\n\n"
        all_text += _extract_text_from_pdf(str(pdf_path))

    # Chunk with overlap for context preservation
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.create_documents([all_text])

    # Embed + store
    embeddings = get_embeddings()
    store = FAISS.from_documents(chunks, embeddings)

    # Save to disk
    store_path = _get_store_path(role_key)
    os.makedirs(store_path, exist_ok=True)
    store.save_local(store_path)

    # Cache in memory
    _vector_stores[role_key] = store

    return len(chunks)


def load_vector_store(role: str) -> FAISS:
    """Load FAISS store from disk (or memory cache)."""
    role_key = ROLE_TO_FOLDER.get(role, "aiml")

    if role_key in _vector_stores:
        return _vector_stores[role_key]

    store_path = _get_store_path(role_key)
    if not os.path.exists(store_path):
        raise FileNotFoundError(
            f"Vector store not found for role '{role}'. Run /api/ingest first."
        )

    embeddings = get_embeddings()
    store = FAISS.load_local(
        store_path, embeddings, allow_dangerous_deserialization=True
    )
    _vector_stores[role_key] = store
    return store


def retrieve_context(role: str, query: str, k: int = None) -> str:
    """
    Retrieve top-k relevant chunks for a query.
    Returns concatenated context string.
    """
    k = k or settings.TOP_K_RETRIEVAL
    store = load_vector_store(role)

    docs = store.similarity_search(query, k=k)
    context = "\n\n---\n\n".join(doc.page_content for doc in docs)
    return context


def build_retrieval_query(role: str, skills: list, topic: str = None) -> str:
    """
    Construct a retrieval query from resume skills + role + topic.
    This drives what RAG fetches — so it must be meaningful.
    """
    skill_str = ", ".join(skills[:8]) if skills else "general concepts"

    if topic:
        query = f"{role} interview questions about {topic}. Candidate knows: {skill_str}"
    else:
        query = f"Core concepts for {role}: {skill_str}"

    return query