from flask import Flask, render_template, request, session, jsonify
from decision_making_gpt import decision_making_prompt, count_tokens, search_support_locations, geocode_location

app = Flask(__name__)
app.secret_key = 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6'

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/decide', methods=['POST'])
def decide():
    context = request.form.get('context')
    feelings = request.form.get('feelings')
    options = request.form.get('options')

    # Inicializa a sessão de mensagens se não estiver definida
    if 'messages' not in session:
        session['messages'] = []

    session['messages'].append({"role": "user", "content": f"Contexto: {context}\nSentimentos: {feelings}\nOpções: {options}\nDecida:"})

    tokens_used = count_tokens(session['messages'])
    resultado = decision_making_prompt(context, feelings, options)

    return jsonify({"resultado": resultado, "tokens_usados": tokens_used})

@app.route('/search_support', methods=['POST'])
def search_support():
    location = request.form.get('location')
    radius = request.form.get('radius')

    locations = search_support_locations(location, radius)
    return jsonify(locations)

if __name__ == '__main__':
    app.run(debug=True)