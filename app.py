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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process-form', methods=['POST'])
def process_form():
    description = request.form['situation_description']
    feelings = request.form['feelings']
    support_reason = request.form['support_reason']
    ia_action = request.form['ia_action']
    
    # Lógica para chamar a API do OpenAI
    response = openai.Completion.create(
        engine="davinci",
        prompt=f"Situação: {description}\nSentimentos: {feelings}\nPara quem busca apoio: {support_reason}\nComo a IA deve atuar: {ia_action}\nSugestões:",
        max_tokens=150
    )

    answer = response.choices[0].text.strip()
    tokens_used = response.usage['total_tokens']

    return render_template('results.html', description=description, answer=answer, tokens_used=tokens_used)

@app.route('/continue-conversation', methods=['POST'])
def continue_conversation():
    user_feedback = request.form['user_feedback']
    # Aqui você pode processar o feedback e gerar uma nova resposta da IA
    response = openai.Completion.create(
        engine="davinci",
        prompt=f"Feedback do usuário: {user_feedback}\nNova resposta:",
        max_tokens=150
    )
    
    new_answer = response.choices[0].text.strip()
    tokens_used = response.usage['total_tokens']

    return render_template('results.html', description="Continuação da conversa", answer=new_answer, tokens_used=tokens_used)

if __name__ == '__main__':
    app.run(debug=True)