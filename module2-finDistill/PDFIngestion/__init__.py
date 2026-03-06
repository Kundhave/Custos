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
from groq import Groq

SEARCH_ENDPOINT = os.environ['SEARCH_ENDPOINT']
SEARCH_KEY      = os.environ['SEARCH_API_KEY']
BLOB_CONN       = os.environ['BLOB_CONN_STRING']
INDEX_NAME      = 'regulatory-docs'
CONTAINER_NAME  = 'regulatory-pdfs'
MAX_CHUNK_CHARS = 10000

def build_extraction_prompt(pdf_text: str) -> str:
    """Build a structured extraction prompt with the PDF content injected."""
    return f"""You are a financial compliance rule extractor for a pre-trade risk system.

Analyze this regulatory document and extract numeric trading thresholds.
Map them ONLY to these exact rule keys if you find clear numeric evidence:

Rule keys and what to look for:
- rule:daily_limit_usd → any mention of maximum daily trading value or order value limit in USD (e.g. "$25,000", "$10 million")
- rule:fat_finger_multiplier → any multiplier for detecting abnormally large orders (e.g. "4 times", "2.5x")
- rule:max_order_size → maximum number of shares or units per order
- rule:min_account_equity → minimum account equity or net equity requirement in USD
- rule:max_day_trades → maximum number of day trades allowed within 5 business days
- restricted_list_add → any specific ticker symbols or company names explicitly flagged as restricted or prohibited

STRICT RULES:
1. Only extract a rule if a specific numeric value is clearly stated in the document
2. Do not invent or estimate values
3. If the same rule appears multiple times with different values, use the most restrictive (lowest limit or highest multiplier)
4. If no clear numeric rules are found, return an empty list
5. Return ONLY valid JSON, no explanation text

Document content:
{pdf_text}

Return this exact JSON format:
{{"rules": [{{"key": "rule:daily_limit_usd", "value": 25000, "source_quote": "exact quote from document"}}]}}"""


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
    # ── Handle CORS preflight ──────────────────────────────────
    if req.method.upper() == 'OPTIONS':
        return func.HttpResponse(
            '',
            status_code=204,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Max-Age': '86400',
            },
        )

    _debug = {
        'pdf_bytes_received': 0,
        'pdf_text_length': 0,
        'chunks_extracted': 0,
        'pages_in_pdf': 0,
        'indexed_count': 0,
        'groq_called': False,
        'groq_raw_response': None,
        'parse_success': False,
        'rules_before_dedup': 0,
        'rules_after_dedup': 0,
        'groq_error': None,
        'prompt_length': 0,
    }

    try:
        # ── 1. Read incoming PDF bytes ──────────────────────────────
        logging.info("PDFIngestion triggered.")
        pdf_bytes = req.get_body()
        filename  = req.params.get('filename', 'regulation.pdf')
        _debug['pdf_bytes_received'] = len(pdf_bytes)
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
        _debug['pages_in_pdf'] = len(reader.pages)
        for pg in reader.pages:
            text = pg.extract_text()
            if text:
                clean = clean_text(text)
                if clean:
                    chunks.append(clean)

        _debug['chunks_extracted'] = len(chunks)
        pdf_text = '\n---\n'.join(chunks)
        _debug['pdf_text_length'] = len(pdf_text)
        logging.info("Extracted %d non-empty text chunks from %d pages (%d chars total).",
                     len(chunks), len(reader.pages), len(pdf_text))

        if not chunks:
            logging.warning("No text could be extracted from PDF '%s'.", filename)
            return _json_response({
                'status': 'error',
                'message': 'No text extracted from PDF',
                '_debug': _debug,
            }, status_code=400)

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

        _debug['indexed_count'] = indexed_count
        logging.info("Indexing complete: %d/%d documents indexed.", indexed_count, len(chunks))

        if errors:
            logging.warning("%d document(s) failed to upload.", len(errors))

        # ── 6. Extract Rules using Groq ────────────────────────────
        logging.info("Extracting rules using Groq LLM.")
        prompt = build_extraction_prompt(pdf_text)
        _debug['prompt_length'] = len(prompt)
        logging.info("Prompt built: %d chars.", len(prompt))

        proposed_rules = []

        try:
            _debug['groq_called'] = True
            groq_api_key = os.environ.get('GROQ_API_KEY', '')
            if not groq_api_key:
                raise ValueError("GROQ_API_KEY environment variable is not set!")
            logging.info("Calling Groq API (key present: %d chars)...", len(groq_api_key))

            groq_client = Groq(api_key=groq_api_key)
            response = groq_client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=[{'role': 'user', 'content': prompt}],
                response_format={'type': 'json_object'},
                temperature=0.1
            )

            raw_content = response.choices[0].message.content
            _debug['groq_raw_response'] = raw_content[:2000]  # cap for safety
            logging.info("Groq raw response (%d chars): %s", len(raw_content), raw_content[:500])

            extracted = json.loads(raw_content)
            _debug['parse_success'] = True
            raw_rules = extracted.get('rules', [])
            _debug['rules_before_dedup'] = len(raw_rules)
            logging.info("Parsed %d rules from Groq response.", len(raw_rules))

            # ── 7. Deduplicate: keep most restrictive value per key ──
            HIGH_WINS = {'rule:fat_finger_multiplier'}
            deduped = {}
            for r in raw_rules:
                key = r.get('key')
                if not key:
                    continue
                # Coerce value to number when possible
                try:
                    r['value'] = float(r['value']) if '.' in str(r['value']) else int(r['value'])
                except (ValueError, TypeError):
                    pass
                if key not in deduped:
                    deduped[key] = r
                else:
                    try:
                        old_val = float(deduped[key]['value'])
                        new_val = float(r['value'])
                        if key in HIGH_WINS:
                            if new_val > old_val:
                                deduped[key] = r
                        else:
                            if new_val < old_val:
                                deduped[key] = r
                    except (ValueError, TypeError):
                        deduped[key] = r

            proposed_rules = list(deduped.values())
            _debug['rules_after_dedup'] = len(proposed_rules)
            logging.info("Deduplicated to %d rules.", len(proposed_rules))

        except Exception as groq_err:
            error_str = f"{type(groq_err).__name__}: {str(groq_err)}"
            _debug['groq_error'] = error_str
            logging.error("Failed to extract rules: %s", error_str)
            proposed_rules = []

        return _json_response({
            'status': 'ok',
            'filename': filename,
            'pages_indexed': indexed_count,
            'proposed_rules': proposed_rules,
            '_debug': _debug,
        })

    except Exception as exc:
        error_text = str(exc)
        logging.exception("PDFIngestion failed: %s", error_text)
        _debug['fatal_error'] = error_text
        return _json_response(
            {'status': 'error', 'message': error_text, '_debug': _debug},
            status_code=500,
        )