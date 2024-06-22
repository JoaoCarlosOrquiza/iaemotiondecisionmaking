from flask import Flask, request, jsonify
import logging
import os
from decision_making_gpt import decision_making_prompt

app = Flask(__name__)

# Configuração do logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/decide', methods=['POST'])
def decide():
    try:
        data = request.json
        logging.debug(f'Received data: {data}')
        
        context = data.get('context', '')
        feelings = data.get('feelings', '')
        options = data.get('options', [])
        
        if not context or not feelings or not options:
            raise ValueError("Missing required fields: context, feelings, or options")
        
        decision = decision_making_prompt(context, feelings, options)
        logging.debug(f'Generated decision: {decision}')
        return jsonify({"decision": decision})
    except Exception as e:
        logging.error(f'Error processing request: {e}')
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
