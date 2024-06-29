import os
import openai
import requests
from flask import Flask, render_template, request
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
    situation_description = request.form.get('situation_description')
    feelings = request.form.get('feelings')
    support_reason = request.form.get('support_reason')
    ia_action = request.form.get('ia_action')
    
    if not situation_description or not feelings or not support_reason or not ia_action:
        return "All form fields are required", 400
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente útil."},
            {"role": "user", "content": f"Descrição: {situation_description}\nEmoções: {feelings}\nRazão do apoio: {support_reason}\nAção da IA: {ia_action}"}
        ],
        max_tokens=150
    )
    
    answer = response['choices'][0]['message']['content']
    tokens_used = response['usage']['total_tokens']

    return render_template('results.html', description=situation_description, answer=answer, tokens_used=tokens_used)

@app.route('/continue-conversation', methods=['POST'])
def continue_conversation():
    user_feedback = request.form.get('user_feedback')
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente útil."},
            {"role": "user", "content": f"Continuar a conversa: {user_feedback}"}
        ],
        max_tokens=150
    )
    
    answer = response['choices'][0]['message']['content']
    tokens_used = response['usage']['total_tokens']
    
    return render_template('results.html', description=user_feedback, answer=answer, tokens_used=tokens_used)

@app.route('/search-location', methods=['POST'])
def search_location():
    location = request.form.get('user_location', '-23.3106665, -51.1899247')  # Simulando a localização do usuário
    professional_type = "psychologist"  # Alterar conforme a lógica da aplicação
    
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

    return render_template('results.html', professionals=professionals)

if __name__ == '__main__':
    app.run(debug=True)
