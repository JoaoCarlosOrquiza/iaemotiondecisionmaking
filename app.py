import os
import openai
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import logging

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
    if request.method == 'POST':
        data = request.get_json()
        language = data.get('language')
        description = data.get('description')
        emotions = data.get('emotions')
        support_reason = data.get('support_reason')
        ia_role = data.get('ia_role')

        # Preparar a entrada para a API do OpenAI
        prompt = f"""
        Language: {language}
        Description: {description}
        Emotions: {emotions}
        Support Reason: {support_reason}
        IA Role: {ia_role}

        Responda de acordo com o papel da IA e forneça suporte apropriado.
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um assistente útil."},
                    {"role": "user", "content": prompt}
                ]
            )
            answer = response['choices'][0]['message']['content'].strip()
        except Exception as e:
            logging.error(f"Erro ao chamar a API do OpenAI: {e}")
            answer = f"Erro no servidor: {e}"

        return jsonify({'answer': answer})

if __name__ == '__main__':
    app.run(debug=True)
