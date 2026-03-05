# ApproveRules/__init__.py
import azure.functions as func, json, os, redis

r = redis.StrictRedis.from_url(
    os.environ['REDIS_CONN'], decode_responses=True, ssl_cert_reqs=None)

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = json.loads(req.get_body().decode('utf-8-sig'))
    except Exception as e:
        return func.HttpResponse(
            json.dumps({'error': f'Invalid JSON body: {str(e)}'}),
            status_code=400,
            mimetype='application/json'
        )
    applied = []
    for rule in body.get('rules', []):
        if rule['key'] == 'restricted_list_add':
            r.sadd('restricted_list', rule['value'])
        else:
            r.set(rule['key'], rule['value'])
        applied.append(rule['key'])
    return func.HttpResponse(
        json.dumps({'status': 'applied', 'rules_applied': applied}),
        mimetype='application/json',
        headers={'Access-Control-Allow-Origin': '*'}
    )