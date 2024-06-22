from flask import Flask, request, jsonify
import logging
import openai
import os
import requests
import tiktoken  # type: ignore
from decision_making_gpt import decision_making_prompt

app = Flask(__name__)

# Configuração do logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurar chaves de API a partir das variáveis de ambiente
openai.api_key = os.getenv('OPENAI_API_KEY')
app.secret_key = os.getenv('FLASK_SECRET_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')

@app.route('/')
def home():
    return "Home - Flask Server is Running"

@app.route('/decide', methods=['POST'])
def decide():
    try:
        data = request.json
        logging.debug(f'Received data: {data}')
        
        context = data.get('context', '')
        feelings = data.get('feelings', '')
        options = data.get('options', [])
        
        if not context or not feelings or not options:
            raise ValueError("Missing required fields: context, feelings, or options")
        
        decision = decision_making_prompt(context, feelings, options)
        logging.debug(f'Generated decision: {decision}')
        return jsonify({"decision": decision})
    except Exception as e:
        logging.error(f'Error processing request: {e}')
        return jsonify({"error": "Internal server error"}), 500

# Função para gerar decisão com base no contexto, sentimentos e opções fornecidos
def decision_making_prompt(context, feelings, options):
    messages = [
        {"role": "system", "content": "Você é um assistente útil."},
        {"role": "user", "content": f"Contexto: {context}\nSentimentos: {feelings}\nOpções: {options}\nDecida:"}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150
    )
    return response.choices[0].message['content'].strip()

# Função para contar tokens nas mensagens
def count_tokens(messages):
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    combined_messages = "\n".join([msg['content'] for msg in messages])
    return len(encoding.encode(combined_messages))

# Função para geocodificar localização
def geocode_location(location):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={google_api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Função para buscar locais de suporte em um raio ao redor de uma localização
def search_support_locations(location, radius):
    geocoded_location = geocode_location(location)
    if geocoded_location:
        lat_lng = geocoded_location['results'][0]['geometry']['location']
        lat, lng = lat_lng['lat'], lat_lng['lng']
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&key={google_api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    else:
        return None

if __name__ == '__main__':
    app.run(debug=True, port=5001)
