# RuleExtractor/__init__.py
# Uses Groq (LLaMA 3.3 70B) to extract compliance rules from indexed PDF content
import azure.functions as func, json, os
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from groq import Groq

groq_client = Groq(api_key=os.environ['GROQ_API_KEY'])
sc = SearchClient(
    os.environ['SEARCH_ENDPOINT'],
    'regulatory-docs',
    AzureKeyCredential(os.environ['SEARCH_API_KEY'])
)

EXTRACTION_PROMPT = '''You are a financial compliance expert.
Analyze the regulatory text below and extract any risk rules.
Return ONLY valid JSON — no explanation, no markdown, no backticks.
Use exactly this format:
{"rules": [{"key": "rule:daily_limit_usd", "value": "50000000", "rationale": "Section 4.2 sets daily limit"}]}
Valid rule keys: rule:daily_limit_usd, rule:fat_finger_multiplier, restricted_list_add
If no rules are found, return: {"rules": []}'''

def main(req: func.HttpRequest) -> func.HttpResponse:
    query = req.params.get('query', 'daily limit trading restriction position size')
    source = req.params.get('source')
    
    # Retrieve relevant chunks from AI Search
    search_kwargs = {"top": 5}
    if source:
        search_kwargs["filter"] = f"source eq '{source}'"
    
    results = sc.search(query, **search_kwargs)
    context = '\n---\n'.join([r['content'] for r in results])
    if not context.strip():
        return func.HttpResponse(
            json.dumps({'proposed_rules': [], 'message': 'No documents indexed yet'}),
            mimetype='application/json',
            headers={'Access-Control-Allow-Origin': '*'}
        )
    # Call Groq
    response = groq_client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[
            {'role': 'system', 'content': EXTRACTION_PROMPT},
            {'role': 'user', 'content': context}
        ],
        response_format={'type': 'json_object'},
        temperature=0.1
    )
    extracted = json.loads(response.choices[0].message.content)
    return func.HttpResponse(
        json.dumps({'proposed_rules': extracted.get('rules', [])}),
        mimetype='application/json',
        headers={'Access-Control-Allow-Origin': '*'}
    )
