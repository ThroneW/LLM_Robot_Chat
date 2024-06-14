from flask import Flask, render_template, request, jsonify

from service_financial import *

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('chat.html')


@app.route('/message', methods=['POST'])
def message():
    print("1")
    user_input = request.json['message']
    # 这里可以接入你的聊天机器人逻辑，现在我们只是简单地回显输入
    service = ServiceFinance()
    response = service.answer_classify(user_input, [])
    # response = "Echo: " + user_input
    response = "Echo: 这个文本的分类是—" + response
    return jsonify({"message": response})


@app.route('/ie_message', methods=['POST'])
def ie_message():
    print("2")
    user_input = request.json['message']
    service = ServiceFinance()
    response = service.answer_ie(user_input, [])
    # response = "Echo: " + user_input
    response = "Echo: 实体抽取的结果如下—" + response
    return jsonify({"message": response})


@app.route('/text_matching_message', methods=['POST'])
def text_matching_message():
    print("3")
    user_input = request.json['message']
    service = ServiceFinance()
    response = service.answer_text_matching(user_input, [])
    # response = "Echo: " + user_input
    response = "Echo: 文本匹配结果为—" + response + "相似语义的句子！"
    return jsonify({"message": response})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5020, debug=False)
