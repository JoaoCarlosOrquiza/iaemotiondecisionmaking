import os
import openai
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
# Configuração do logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.json
        language = data.get('language')
        description = data.get('description')
        emotions = data.get('emotions')
        support_reason = data.get('support_reason')
        ia_role = data.get('ia_role')

        logging.debug(f'Received data: {data}')

        # Preparar a entrada para a API do OpenAI
        prompt = f"""
        Language: {language}
        Description: {description}
        Emotions: {emotions}
        Support Reason: {support_reason}
        IA Role: {ia_role}

        Responda de acordo com o papel da IA e forneça suporte apropriado.
        """

        # Usar a nova API para criar uma conclusão de chat
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um assistente útil."},
                {"role": "user", "content": prompt}
            ]
        )

        logging.debug(f'OpenAI response: {response}')

        answer = response['choices'][0]['message']['content'].strip()

        return jsonify({'answer': answer})
    except Exception as e:
        logging.error(f'Error processing request: {e}')
        return jsonify({'error': 'An error occurred processing your request'}), 500

if __name__ == '__main__':
    app.run(debug=True)