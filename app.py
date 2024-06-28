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
    try:
        language = request.form['language']
        description = request.form['situation_description']
        emotions = request.form['feelings']
        support_reason = request.form['support_reason']
        ia_role = request.form['ia_action']
        
        prompt = f"""
        Language: {language}
        Description: {description}
        Emotions: {emotions}
        Support Reason: {support_reason}
        IA Role: {ia_role}

        Responda de acordo com o papel da IA e forneça suporte apropriado.
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um assistente útil."},
                {"role": "user", "content": prompt}
            ]
        )
        suggestions = response.choices[0].message.content.strip().split('\n')
        token_usage = response.usage.total_tokens
        token_percentage = (token_usage / 4096) * 100

        return render_template(
            'results.html',
            description=description,
            suggestions=suggestions,
            token_percentage=token_percentage
        )
    except Exception as e:
        print(f"Erro ao processar o formulário: {e}")
        return render_template('error.html', error_message=str(e))

if __name__ == '__main__':
    app.run(debug=True)