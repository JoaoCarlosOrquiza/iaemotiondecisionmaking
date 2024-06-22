from flask import Flask, request, jsonify
import logging
import os
import openai  # Importando o módulo openai corretamente
from decision_making_utils import decision_making_prompt, geocode_location, search_support_locations

app = Flask(__name__)

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
        data = request.get_json()
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

@app.route('/geocode', methods=['GET'])
def geocode():
    try:
        location = request.args.get('location')
        if not location:
            return jsonify({"error": "Missing 'location' parameter"}), 400
        
        geocode_response = geocode_location(location)
        if not geocode_response:
            return jsonify({"error": "Failed to geocode location"}), 500

        return jsonify(geocode_response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
