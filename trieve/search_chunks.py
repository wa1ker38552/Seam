import requests
import json

headers = {
    "TR-Dataset": "fb4bbea7-484c-482d-b818-e9e5e41781e6",
    "Authorization": open('authorization.txt', 'r').read(),
    "Content-Type": "application/json"
}

def semantic_search(query, threshold):
    payload = payload = {
        # "page": 1,
        "page_size": 15000,
        "query": query,
        "score_threshold": threshold,
        "search_type": "semantic"
    }

    r = requests.post('https://api.trieve.ai/api/chunk/search', headers=headers, json=payload).json()
    return [{
        'description': item['chunk']['chunk_html'],
        'metadata': item['chunk']['metadata'],
        'score': item['score']
    } for item in r['chunks']]

data = semantic_search('More senior jobs that relate to AI strategy or machine learning deployment', 0.75)
with open('semantic_search_results.json', 'w') as file:
    file.write(json.dumps(data, indent=2))