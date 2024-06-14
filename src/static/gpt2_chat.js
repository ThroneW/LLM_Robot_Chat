document.addEventListener('DOMContentLoaded', function() {
    // 显示欢迎消息
    displayMessage("欢迎来到GPT2闲聊机器人，我是小G，请问有什么可以帮您的吗？", 'bot');
});

document.getElementById('chat-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const userInput = document.getElementById('user-input').value;
    if (userInput.trim()) {
        displayMessage(userInput, 'user');
        document.getElementById('user-input').value = ''; // 清空输入框
        sendMessageToServer(userInput);
    }
});

function sendMessageToServer(message) {
    const thinkingMessage = displayMessage("思考中......", 'bot');
    fetch('/chat_message', {  // 假定服务器端点为 /chat_message
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({message: message})
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('chat-box').removeChild(thinkingMessage);
        displayMessage(data.message, 'bot');  // 假设服务器返回的响应包含message字段
    })
    .catch(error => {
        console.error('Error:', error);
        thinkingMessage.textContent = '发生错误，请稍后再试。';
        thinkingMessage.scrollIntoView();
    });
}

function displayMessage(message, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);
    messageDiv.textContent = message;
    document.getElementById('chat-box').appendChild(messageDiv);
    messageDiv.scrollIntoView();
    return messageDiv;  // 返回创建的消息div，以便可以更新或移除
}
