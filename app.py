import os
import openai
import requests
from flask import Flask, render_template, request, redirect, url_for
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

@app.route('/process', methods=['POST'])
def process():
    description = request.form['description']
    emotions = request.form['emotions']
    support_reason = request.form['support_reason']
    
    response = openai.Completion.create(
        engine="gpt-3.5-turbo",  # Use o modelo atualizado aqui
        prompt=f"Descrição: {description}\nEmoções: {emotions}\nRazão do apoio: {support_reason}\n",
        max_tokens=150
    )
    
    return render_template('response.html', response=response.choices[0].text)

@app.route('/continue', methods=['POST'])
def continue_conversation():
    previous_answer = request.form['previous_answer']
    
    response = openai.Completion.create(
        engine="gpt-3.5-turbo",  # Use o modelo atualizado aqui
        prompt=f"Continuar a conversa: {previous_answer}\n",
        max_tokens=150
    )
    
    return render_template('response.html', response=response.choices[0].text)

@app.route('/search_professionals', methods=['POST'])
def search_professionals():
    professional_type = request.form['professional_type']
    # Simulando a obtenção de localização do usuário
    location = "-23.3106665, -51.1899247"  # Substitua pela lógica de geolocalização real
    
    return render_template('search_results.html', professional_type=professional_type, location=location)

if __name__ == '__main__':
    app.run(debug=True)
