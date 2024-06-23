import logging
from flask import Flask, request, jsonify
from decision_making_utils import decision_making_prompt, count_tokens, geocode_location, search_support_locations
import openai
import os

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

if __name__ == '__main__':
    app.run(debug=True, port=5001)
