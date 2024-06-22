from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Home - Flask Server is Running"

@app.route('/decide', methods=['POST'])
def decide():
    try:
        data = request.get_json()
        app.logger.info(f"Received data: {data}")
        if not data:
            app.logger.error("No data received or invalid JSON")
            return jsonify({"error": "Invalid input"}), 400

        context = data.get("context")
        feelings = data.get("feelings")
        options = data.get("options")
        
        if not context or not feelings or not options:
            app.logger.error("Missing data in the request")
            return jsonify({"error": "Missing data"}), 400
        
        # Simulate decision making logic here
        decision = f"Decided based on context: {context}, feelings: {feelings}, options: {options}"
        
        return jsonify({"decision": decision})
    
    except Exception as e:
        app.logger.error(f"Error processing request: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
