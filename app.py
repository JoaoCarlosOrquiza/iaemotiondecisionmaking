from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

openai.api_key = os.getenv('OPENAI_API_KEY')

@app.route('/')
def home():
    return "Home - Flask Server is Running"

@app.route('/decide', methods=['POST'])
def decide():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid input"}), 400
        
        context = data.get('context', '')
        feelings = data.get('feelings', '')
        options = data.get('options', [])
        
        if not context or not feelings or not options:
            return jsonify({"error": "Missing fields"}), 400

        response = decision_making_prompt(context, feelings, options)
        return jsonify({"decision": response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def decision_making_prompt(context, feelings, options):
    messages = [
        {"role": "system", "content": "Você é um assistente útil."},
        {"role": "user", "content": f"Contexto: {context}\nSentimentos: {feelings}\nOpções: {options}\nDecida:"}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150
    )
    return response.choices[0].message['content'].strip()

if __name__ == '__main__':
    app.run(debug=True)
