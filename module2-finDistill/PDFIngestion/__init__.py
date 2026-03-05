# PDFIngestion/__init__.py
import azure.functions as func
import json
import os
import io
import logging
from azure.storage.blob import BlobServiceClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchFieldDataType)
from azure.core.credentials import AzureKeyCredential
import PyPDF2

SEARCH_ENDPOINT = os.environ['SEARCH_ENDPOINT']
SEARCH_KEY      = os.environ['SEARCH_API_KEY']
BLOB_CONN       = os.environ['BLOB_CONN_STRING']
INDEX_NAME      = 'regulatory-docs'
CONTAINER_NAME  = 'regulatory-pdfs'
MAX_CHUNK_CHARS = 10000


def ensure_index():
    """Create or update the AI Search index."""
    logging.info("Ensuring search index '%s' exists.", INDEX_NAME)
    client = SearchIndexClient(SEARCH_ENDPOINT, AzureKeyCredential(SEARCH_KEY))
    index  = SearchIndex(name=INDEX_NAME, fields=[
        SimpleField(name='id', type=SearchFieldDataType.String, key=True),
        SearchableField(name='content', type=SearchFieldDataType.String),
        SimpleField(name='source', type=SearchFieldDataType.String, filterable=True),
    ])
    client.create_or_update_index(index)
    logging.info("Search index '%s' is ready.", INDEX_NAME)


def clean_text(text: str) -> str:
    """Remove non-printable characters and cap at MAX_CHUNK_CHARS."""
    cleaned = ''.join(c for c in text if c.isprintable() or c in ('\n', '\t'))
    return cleaned[:MAX_CHUNK_CHARS].strip()


def sanitize_doc_id(index: int) -> str:
    """Return an AI-Search-safe document id (letters, numbers, hyphens, underscores only)."""
    doc_id = f'doc-{index}'.replace('.', '-').replace('/', '-')
    return doc_id


def _json_response(body: dict, status_code: int = 200) -> func.HttpResponse:
    """Helper to build a JSON HttpResponse with CORS header."""
    return func.HttpResponse(
        json.dumps(body),
        status_code=status_code,
        mimetype='application/json',
        headers={'Access-Control-Allow-Origin': '*'},
    )


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # ── 1. Read incoming PDF bytes ──────────────────────────────
        logging.info("PDFIngestion triggered.")
        pdf_bytes = req.get_body()
        filename  = req.params.get('filename', 'regulation.pdf')
        logging.info("Received PDF '%s' (%d bytes).", filename, len(pdf_bytes))

        # ── 2. Upload to Blob Storage ───────────────────────────────
        logging.info("Uploading to Blob container '%s'.", CONTAINER_NAME)
        blob = BlobServiceClient.from_connection_string(BLOB_CONN) \
                   .get_blob_client(CONTAINER_NAME, filename)
        blob.upload_blob(pdf_bytes, overwrite=True)
        logging.info("Blob upload complete for '%s'.", filename)

        # ── 3. Extract text from PDF ────────────────────────────────
        logging.info("Extracting text with PyPDF2.")
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        chunks = []
        for pg in reader.pages:
            text = pg.extract_text()
            if text:
                clean = clean_text(text)
                if clean:
                    chunks.append(clean)

        logging.info("Extracted %d non-empty text chunks from %d pages.",
                     len(chunks), len(reader.pages))

        if not chunks:
            logging.warning("No text could be extracted from PDF '%s'.", filename)
            return _json_response(
                {'status': 'error', 'message': 'No text extracted from PDF'},
                status_code=400,
            )

        # ── 4. Create / update AI Search index ─────────────────────
        ensure_index()

        # ── 5. Upload documents one at a time ──────────────────────
        sc = SearchClient(SEARCH_ENDPOINT, INDEX_NAME, AzureKeyCredential(SEARCH_KEY))
        indexed_count = 0
        errors = []

        for i, chunk in enumerate(chunks):
            doc_id = sanitize_doc_id(i)
            doc = {
                'id':      doc_id,
                'content': chunk,
                'source':  filename,
            }
            try:
                logging.info("Uploading document %d/%d (id=%s, %d chars).",
                             i + 1, len(chunks), doc_id, len(chunk))
                sc.upload_documents(documents=[doc])
                indexed_count += 1
                logging.info("Document '%s' uploaded successfully.", doc_id)
            except Exception as doc_err:
                error_msg = f"Failed to upload doc '{doc_id}': {doc_err}"
                logging.error(error_msg)
                errors.append(error_msg)

        logging.info("Indexing complete: %d/%d documents indexed.", indexed_count, len(chunks))

        if errors:
            logging.warning("%d document(s) failed to upload.", len(errors))

        return _json_response({
            'status': 'ok',
            'pages_indexed': indexed_count,
        })

    except Exception as exc:
        error_text = str(exc)
        logging.exception("PDFIngestion failed: %s", error_text)
        return _json_response(
            {'status': 'error', 'message': error_text},
            status_code=500,
        )