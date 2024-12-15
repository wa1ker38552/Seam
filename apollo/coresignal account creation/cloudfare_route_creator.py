import requests

headers = {'Authorization': 'Bearer {API TOKEN}'}

payload = {
    "actions": [
        {
            "type": "forward",
            "value": [
                "pokemongouser2537@gmail.com"
            ]
        }
    ],
    "enabled": True,
    "matchers": [
        {
            "field": "to",
            "type": "literal",
            "value": "test@ps99rap.com"
        }
    ],
    "priority": 0
}

def create_route(target):
    payload['matchers'][0]['value'] = target
    r = requests.post('https://api.cloudflare.com/client/v4/zones/3c3fe96ace8fbd1b99b7a4f39e4aaa4e/email/routing/rules', headers=headers, json=payload)
    return r.json()['success']


for i in range(56):
    response = create_route(f'coresignal@mailroute{17+i+1}.ps99rap.com')
    print(i, response)