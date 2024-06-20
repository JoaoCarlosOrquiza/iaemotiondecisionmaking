from flask import Flask, request, jsonify
from decision_making_gpt import decision_making_prompt, count_tokens, search_support_locations, geocode_location

app = Flask(__name__)

@app.route('/')
def home():
    return 'Home - Flask Server is Running'

@app.route('/decide', methods=['POST'])
def decide():
    data = request.json
    context = data.get('context')
    feelings = data.get('feelings')
    options = data.get('options')
    result = decision_making_prompt(context, feelings, options)
    return jsonify({'decision': result})

if __name__ == '__main__':
    app.run(debug=True)
