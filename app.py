import os
import openai
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Configuração das chaves de API
openai.api_key = os.getenv('OPENAI_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process-form', methods=['POST'])
def process_form():
    description = request.form.get('description')
    emotions = request.form.get('emotions')
    support_reason = request.form.get('support_reason')
    
    if not description or not emotions or not support_reason:
        return "All form fields are required", 400
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente útil."},
            {"role": "user", "content": f"Descrição: {description}\nEmoções: {emotions}\nRazão do apoio: {support_reason}"}
        ],
        max_tokens=150
    )
    
    return render_template('response.html', response=response['choices'][0]['message']['content'])

@app.route('/continue', methods=['POST'])
def continue_conversation():
    previous_answer = request.form['previous_answer']
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente útil."},
            {"role": "user", "content": f"Continuar a conversa: {previous_answer}"}
        ],
        max_tokens=150
    )
    
    return render_template('response.html', response=response['choices'][0]['message']['content'])  

@app.route('/search_professionals', methods=['POST'])
def search_professionals():
    professional_type = request.form['professional_type']
    location = request.form.get('user_location', '-23.3106665, -51.1899247')  # Simulando a localização do usuário
    
    # Chamada à API do Google Places para buscar profissionais próximos
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius=1500&type={professional_type}&key={google_api_key}"
    response = requests.get(url)
    places = response.json().get('results', [])

    # Criando uma lista de profissionais a partir dos resultados da API
    professionals = []
    for place in places:
        professional = {
            'name': place.get('name'),
            'specialty': professional_type,
            'distance': '1.5 km'  # Simulando a distância
        }
        professionals.append(professional)

    return render_template('professionals.html', professionals=professionals)


if __name__ == '__main__':
    app.run(debug=True)
