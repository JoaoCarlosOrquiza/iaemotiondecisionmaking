<<<<<<< HEAD
from flask import Flask, render_template, request, jsonify
import openai
import os
import requests

from flask import Flask
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()
=======
from flask import Flask, request, jsonify
import logging
import os
from decision_making_utils import decision_making_prompt, count_tokens, geocode_location, search_support_locations
>>>>>>> 4ad16a62b6515d2cf4123f699147387bd23e6c58

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

<<<<<<< HEAD
# Configuração das chaves de API
openai_api_key = os.getenv('OPENAI_API_KEY')
=======
# Configuração do logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurar chaves de API a partir das variáveis de ambiente
openai.api_key = os.getenv('OPENAI_API_KEY')
app.secret_key = os.getenv('FLASK_SECRET_KEY')
>>>>>>> 4ad16a62b6515d2cf4123f699147387bd23e6c58
google_api_key = os.getenv('GOOGLE_API_KEY')

@app.route('/')
def home():
    return render_template('index.html')

<<<<<<< HEAD
@app.route('/process', methods=['POST'])
def process():
    description = request.form['description']
    emotions = request.form['emotions']
    support_reason = request.form['support_reason']
    
    # Example request to OpenAI API
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"{description}\n{emotions}\n{support_reason}",
        max_tokens=150
    )
    
    return render_template('response.html', response=response.choices[0].text)

@app.route('/continue', methods=['POST'])
def continue_conversation():
    previous_answer = request.form['previous_answer']
    
    # Continue the conversation with OpenAI API
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"{previous_answer}\nContinue:",
        max_tokens=150
    )
    
    return render_template('response.html', response=response.choices[0].text)

@app.route('/search_professionals', methods=['POST'])
def search_professionals():
    professional_type = request.form['professional_type']
    location = request.form['location']  # Assume location is being passed in the form

    # Call Google Places API to search for professionals
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius=5000&type={professional_type}&key={google_api_key}"
    response = requests.get(url)
    results = response.json()

    # Extract relevant information from results
    professionals = []
    if 'results' in results:
        for place in results['results']:
            name = place.get('name')
            address = place.get('vicinity')
            professionals.append(f"{name}, {address}")

    return render_template('results.html', professionals=professionals)
=======
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
>>>>>>> 4ad16a62b6515d2cf4123f699147387bd23e6c58

if __name__ == '__main__':
    app.run(debug=True, port=5001)
