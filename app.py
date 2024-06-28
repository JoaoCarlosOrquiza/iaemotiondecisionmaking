import os
import openai
from flask import Flask, render_template, request, jsonify, redirect, url_for
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

@app.route('/process-form', methods=['POST'])
def process_form():
    if request.method == 'POST':
        language = request.form['language']
        description = request.form['situation_description']
        emotions = request.form['feelings']
        support_reason = request.form['support_reason']
        ia_action = request.form['ia_action']

        prompt = f"""
        Language: {language}
        Description: {description}
        Emotions: {emotions}
        Support Reason: {support_reason}
        IA Role: {ia_action}

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
            answer = response.choices[0].message.content.strip()
            # Aqui você pode calcular o percentual de tokens usados
            tokens_used = response['usage']['total_tokens']
            token_percentage = (tokens_used / 4096) * 100  # Supondo um limite de 4096 tokens

            return render_template('results.html', 
                                   situation_description=description, 
                                   suggestions=[answer], 
                                   token_percentage=token_percentage)
        except Exception as e:
            logging.error(f"Erro ao chamar a API do OpenAI: {e}")
            return render_template('results.html', 
                                   situation_description=description, 
                                   suggestions=["Erro no servidor: tente novamente mais tarde."], 
                                   token_percentage=0)

@app.route('/final')
def final():
    return render_template('final.html')

if __name__ == '__main__':
    app.run(debug=True)
