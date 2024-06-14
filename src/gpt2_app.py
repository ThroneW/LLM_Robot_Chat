from flask import Flask, render_template, request, jsonify
from flask_predict import *

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('gpt2_chat.html')


@app.route('/chat_message', methods=['POST'])
def ask():
    user_input = request.json['message']
    print(f'user_input-->{user_input}')

    # 使用 GPT-2 模型进行问答处理
    response = model_predict(user_input)

    response = "小G: " + response
    return jsonify({"message": response})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
