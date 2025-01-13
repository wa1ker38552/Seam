import requests

API_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
API_KEY = open('deepinfrakey.txt', 'r').read()

def prompt_deepinfra(prompt_instruction, prompt_text):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "meta-llama/Meta-Llama-3-8B-Instruct",
        "messages": [
            {
                "role": "system",
                "content": prompt_instruction
            },
            {
                "role": "user",
                "content": prompt_text
            }
        ],
    }
    response = requests.post(API_URL, json=payload, headers=headers).json()
    return response['choices'][0]['message']['content']