document.addEventListener('DOMContentLoaded', function() {
    // 显示欢迎消息和服务选项
    displayMessage("欢迎来到金融对话机器人界面，请选择服务：\n1、金融文本分类。\n2、金融实体关系抽取。\n3、金融文本匹配。", 'bot');
    window.inServiceSelection = true;  // 初始化选择服务状态
    window.selectedService = null;  // 初始化选择的服务类型为null
});

document.getElementById('chat-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const userInput = document.getElementById('user-input').value;
    if (userInput.trim()) {
        displayMessage(userInput, 'user');
        document.getElementById('user-input').value = ''; // 清空输入框

        if (window.inServiceSelection) {
            handleServiceSelection(userInput);
        } else {
            sendMessageToServer(userInput, window.selectedService);
        }
    }
});

function handleServiceSelection(input) {
    const services = {
        '1': "您已进入金融文本分类机器人功能，请输入您的金融文本，我将为您进行分类。",
        '2': "您已进入金融实体关系抽取机器人功能，请输入您的金融文本。",
        '3': "您已进入金融文本匹配机器人功能，请输入您的金融文本。请注意：两端文本请用|隔开！"
    };
    if (services[input]) {
        displayMessage(services[input], 'bot');
        window.inServiceSelection = false;
        window.selectedService = input;  // 记录用户选择的服务
    } else {
        displayMessage("您选择的功能有误，请在1~3中选择。", 'bot');
    }
}

function sendMessageToServer(message, serviceType) {
    const thinkingMessage = displayMessage("思考中......", 'bot');
    let url = '/message';  // 默认URL

    if (serviceType === '2') {
        url = '/ie_message';  // 特定于实体关系抽取的路由
    }

    if (serviceType === '3') {
        url = '/text_matching_message';  // 特定于实体关系抽取的路由
    }

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({message: message})
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('chat-box').removeChild(thinkingMessage);
        displayMessage(data.message, 'bot');
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
