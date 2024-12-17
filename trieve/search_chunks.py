import requests

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
    return [{**item['chunk'], 'score': item['score']} for item in r['chunks']]

data = semantic_search('Jobs that relate to AI strategy or machine learning deployment', 0.75)
for item in data: print(item['score'], item['tracking_id'])
print(len(data))
