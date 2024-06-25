from flask import Flask, render_template, request, jsonify
import openai
import os
import requests

from flask import Flask
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Configuração das chaves de API
openai_api_key = os.getenv('OPENAI_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')

@app.route('/')
def home():
    return render_template('index.html')

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

if __name__ == '__main__':
    app.run(debug=True)
