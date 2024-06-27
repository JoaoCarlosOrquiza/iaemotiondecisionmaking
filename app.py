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

@app.route('/process', methods=['POST'])
def process():
    if request.method == 'POST':
        language = request.form.get('language')
        description = request.form.get('description')
        emotions = request.form.get('emotions')
        support_reason = request.form.get('support_reason')
        ia_role = request.form.get('ia_role')

        # Preparar a entrada para a API do OpenAI
        prompt = f"""
        Language: {language}
        Description: {description}
        Emotions: {emotions}
        Support Reason: {support_reason}
        IA Role: {ia_role}

        Responda de acordo com o papel da IA e forneça suporte apropriado.
        """

        # Atualização para usar o modelo gpt-3.5-turbo
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um assistente útil."},
                {"role": "user", "content": prompt}
            ]
        )

        answer = response.choices[0].text.strip()

        return jsonify({'answer': answer})

if __name__ == '__main__':
    app.run(debug=True) 
