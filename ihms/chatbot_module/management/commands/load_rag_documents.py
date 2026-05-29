import os
import pdfplumber
import chromadb
from sentence_transformers import SentenceTransformer
from django.core.management.base import BaseCommand
from django.conf import settings


COLLECTION_MAP = {
    'phm_en': 'guidelines_phm_en',
    'parent_en': 'guidelines_parent_en',
    'parent_si': 'guidelines_parent_si',
    'parent_ta': 'guidelines_parent_ta',
}

CHUNK_SIZE = 300  # words per chunk
CHUNK_OVERLAP = 50  # words overlap between chunks


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract plain text from a text-based PDF."""
    text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + '\n'
    return text.strip()


def extract_text_from_txt(txt_path: str) -> str:
    """Read plain text file."""
    with open(txt_path, 'r', encoding='utf-8') as f:
        return f.read().strip()


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping word-based chunks.
    Overlap ensures context isn't lost at chunk boundaries.
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = ' '.join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


class Command(BaseCommand):
    help = 'Load RAG documents from rag_docs/ into ChromaDB collections'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete and recreate collections before loading'
        )
        parser.add_argument(
            '--collection',
            type=str,
            help='Load only a specific collection (phm_en, parent_en, parent_si, parent_ta)'
        )

    def handle(self, *args, **options):
        rag_docs_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'rag_docs'
        )

        if not os.path.exists(rag_docs_path):
            self.stderr.write(self.style.ERROR(f'rag_docs/ not found at {rag_docs_path}'))
            return

        client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
        model = SentenceTransformer('all-MiniLM-L6-v2')

        collections_to_process = options.get('collection')
        if collections_to_process:
            if collections_to_process not in COLLECTION_MAP:
                self.stderr.write(self.style.ERROR(f'Unknown collection: {collections_to_process}'))
                return
            folders = {collections_to_process: COLLECTION_MAP[collections_to_process]}
        else:
            folders = COLLECTION_MAP

        for folder_name, collection_name in folders.items():
            folder_path = os.path.join(rag_docs_path, folder_name)

            if not os.path.exists(folder_path):
                self.stdout.write(self.style.WARNING(f'Folder not found, skipping: {folder_path}'))
                continue

            # Reset collection if requested
            if options['reset']:
                try:
                    client.delete_collection(name=collection_name)
                    self.stdout.write(f'Deleted existing collection: {collection_name}')
                except Exception:
                    pass

            collection = client.get_or_create_collection(name=collection_name)

            files = [
                f for f in os.listdir(folder_path)
                if f.endswith('.pdf') or f.endswith('.txt')
            ]

            if not files:
                self.stdout.write(self.style.WARNING(f'No files found in {folder_path}'))
                continue

            self.stdout.write(f'\nProcessing collection: {collection_name} ({len(files)} files)')

            total_chunks = 0

            for filename in files:
                file_path = os.path.join(folder_path, filename)
                base_name = os.path.splitext(filename)[0]

                try:
                    if filename.endswith('.pdf'):
                        text = extract_text_from_pdf(file_path)
                    else:
                        text = extract_text_from_txt(file_path)

                    if not text:
                        self.stdout.write(self.style.WARNING(f'  No text extracted: {filename}'))
                        continue

                    chunks = chunk_text(text)
                    embeddings = model.encode(chunks).tolist()

                    ids = [f'{folder_name}_{base_name}_{i:03d}' for i in range(len(chunks))]

                    # Add in batches to avoid memory issues
                    batch_size = 50
                    for i in range(0, len(chunks), batch_size):
                        collection.add(
                            documents=chunks[i:i+batch_size],
                            embeddings=embeddings[i:i+batch_size],
                            ids=ids[i:i+batch_size]
                        )

                    total_chunks += len(chunks)
                    self.stdout.write(f'  ✓ {filename} → {len(chunks)} chunks')

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ {filename}: {e}'))

            self.stdout.write(self.style.SUCCESS(
                f'Done: {collection_name} — {total_chunks} chunks loaded'
            ))

        self.stdout.write(self.style.SUCCESS('\nAll collections processed.'))