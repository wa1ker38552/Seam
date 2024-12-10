from groq import Groq
import json

client = Groq(api_key='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')

def condense_broker(broker):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a bot designed to give short quick and concise information. Never add formatting to your responses and return a direct answer."
            },
            {
                "role": "system",
                "content": "Given a broker name return 'I work at <broker>' where <broker> is the broker that the user requests and is said in a way that matches how regular people speak. People often don't say the exact name of the company and I want you to shorten it and omit information that is not relevant to the exact company they work at."
            },
            {
                "role": "user",
                "content": broker,
            }
        ],
        model="llama3-8b-8192"
    )
    parsed = chat_completion.choices[0].message.content.replace('I work at ', '')
    parsed = parsed[:-1] if parsed[-1] == '.' else parsed
    return parsed

agent_data = json.loads(open('zillow_agent_data.json', 'r').read())
offset = 0 # in case you need to re-run
for i, agent in enumerate(agent_data[offset:]):
    print(f'{offset+i}/{len(agent_data)}', agent['full_name'])
    agent_data[i+offset]['broker_simplified'] = condense_broker(agent['broker'])
    # save after every search just in-case it fails and need to re-run
    with open('zillow_agent_data.json', 'w') as file:
        file.write(json.dumps(agent_data, indent=2))
