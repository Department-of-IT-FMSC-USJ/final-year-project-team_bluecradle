import chromadb
from sentence_transformers import SentenceTransformer
from django.conf import settings

# Collections mapped to role + language
COLLECTION_MAP = {
    'PHM_EN': 'guidelines_phm_en',
    'PARENT_EN': 'guidelines_parent_en',
    'PARENT_SI': 'guidelines_parent_si',
    'PARENT_TA': 'guidelines_parent_ta',
}

# Initialise ChromaDB client and embedding model once at module load
_chroma_client = None
_embedding_model = None


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
    return _chroma_client


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model


def get_collection_name(role: str, language: str) -> str:
    # Returns the correct ChromaDB collection name.
    # PHM always uses EN. Parent uses SI or TA.
    if role == 'PHM':
        return COLLECTION_MAP['PHM_EN']
    return COLLECTION_MAP.get(f'PARENT_{language}', COLLECTION_MAP['PARENT_EN'])


def retrieve_chunks(query: str, role: str, language: str, n_results: int = 3) -> dict:
    # Embeds the query, queries the correct collection, returns top chunks.
    # Returns:
        # {
        #     'context': str,        # assembled context block for Gemini
        #     'chunk_ids': list[str] # IDs stored on ChatLog.rag_chunks_used
        # }

    client = get_chroma_client()
    model = get_embedding_model()

    collection_name = get_collection_name(role, language)

    try:
        collection = client.get_collection(name=collection_name)
    except Exception:
        # Collection doesn't exist yet — return empty context gracefully
        return {'context': '', 'chunk_ids': []}

    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=['documents', 'metadatas', 'distances']
    )

    documents = results.get('documents', [[]])[0]
    # IDs are always returned by ChromaDB regardless of include list
    ids = results.get('ids', [[]])[0]

    context = '\n\n'.join(documents) if documents else ''

    return {
        'context': context,
        'chunk_ids': ids
    }