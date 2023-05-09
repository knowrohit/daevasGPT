from flask import Flask, render_template, request, jsonify
from infant_daevas import DaevasAGI

app = Flask(__name__)
daevas = DaevasAGI()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    prompt = request.json['prompt']
    response = daevas.chatbot(prompt)
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)
