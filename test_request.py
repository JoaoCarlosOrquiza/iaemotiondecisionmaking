import requests
import json

url = 'http://127.0.0.1:5001/decide'
headers = {'Content-Type': 'application/json'}
data = {
    "context": "Contexto de teste",
    "feelings": "Sentimentos de teste",
    "options": ["Opção 1", "Opção 2"]
}

response = requests.post(url, headers=headers, data=json.dumps(data))

print(response.status_code)
print(response.json())
