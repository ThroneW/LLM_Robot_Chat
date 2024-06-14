function login() {
    var username = document.getElementById('username').value;
    var password = document.getElementById('password').value;

    // 这里只是一个基本的示例检查
    if (username === 'user' && password === 'pass') {
        // 启用医疗对话机器人按钮并更新点击事件
        var medicalBtn = document.getElementById('medicalBtn');
        medicalBtn.disabled = false;
        medicalBtn.onclick = function() {
            window.location.href = 'http://127.0.0.1:7860';
        };

        // 启用金融知识小工具按钮并更新点击事件
        var financialBtn = document.getElementById('financeBtn');
        financialBtn.disabled = false;
        financialBtn.onclick = function() {
            window.location.href = 'http://172.26.12.140:5000';
        };

        // 启用基于GPT2的闲聊机器人按钮并设置链接
        var chatBotBtn = document.getElementById('chatBotBtn');
        chatBotBtn.disabled = false;
        chatBotBtn.onclick = function() {
            window.location.href = 'http://172.26.12.140:5001';
        };

        alert('登录成功！');
    } else {
        alert('用户名或密码错误！');
    }
}
