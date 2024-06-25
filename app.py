import os
import openai  # Certifique-se de que esta linha está presente
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
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Use o modelo atualizado aqui
        messages=[
            {"role": "system", "content": "Você é um assistente útil."},
            {"role": "user", "content": f"Descrição: {description}\nEmoções: {emotions}\nRazão do apoio: {support_reason}"}
        ]
    )
    
    return render_template('response.html', response=response.choices[0].message['content'])

@app.route('/continue', methods=['POST'])
def continue_conversation():
    previous_answer = request.form['previous_answer']
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Use o modelo atualizado aqui
        messages=[
            {"role": "system", "content": "Você é um assistente útil."},
            {"role": "user", "content": f"Continuar a conversa: {previous_answer}"}
        ]
    )
    
    return render_template('response.html', response=response.choices[0].message['content'])

@app.route('/search_professionals', methods=['POST'])
def search_professionals():
    professional_type = request.form['professional_type']
    # Simulando a obtenção de localização do usuário
    location = "-23.3106665, -51.1899247"  # Substitua pela lógica de geolocalização real
    
    return render_template('search_results.html', professional_type=professional_type, location=location)

if __name__ == '__main__':
    app.run(debug=True)
