# web_app.py
# 旅行规划助手 Web 版本

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import re
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
import config
from tools import get_navigation, search_hotels, get_attractions, get_weather, _do_navigation

app = Flask(__name__)
CORS(app)

# 初始化
llm = ChatDeepSeek(
    model=config.MODEL_NAME,
    temperature=0.7,
    max_tokens=4096
)

tools = [get_navigation, search_hotels, get_attractions, get_weather]

system_prompt = """你是一个专业的旅行规划助手，帮助用户制定旅行计划。

## 可用工具
1. get_attractions(city, interests) - 查询城市景点
2. search_hotels(city) - 查询城市酒店
3. get_navigation(origin, destination, mode) - 查询两地路线

## 工作规则
1. 分析用户需求，主动调用工具获取信息
2. 信息足够时直接生成完整方案，禁止反复反问
3. 缺少关键信息时，最多询问一次

## 输出格式
- 使用 Markdown 格式
- 包含：交通建议、住宿推荐、每日行程、预算估算"""

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt
)


def travel_agent_chat(user_input: str) -> str:
    """与旅行规划Agent进行对话"""
    user_input_clean = user_input.strip()
    
    # 处理导航请求
    nav_with_origin = re.search(r'从(.+?)到(.+?)(怎么走|怎么导航|怎么走|$)', user_input_clean)
    if nav_with_origin:
        origin = nav_with_origin.group(1).strip()
        destination = nav_with_origin.group(2).strip()
        if origin and destination:
            return _do_navigation(origin, destination)
    
    nav_simple = re.search(r'(导航到|怎么去|如何到达)(.+)', user_input_clean)
    if nav_simple:
        destination = nav_simple.group(2).strip()
        return f"请告诉我您的出发地，例如：'从北京天安门到{destination}'"
    
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]}
        )
        if "messages" in result:
            return result["messages"][-1].content
        return str(result)
    except Exception as e:
        return f"抱歉，处理您的问题时出现错误：{str(e)}"


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """API接口"""
    data = request.json
    user_input = data.get('message', '')
    
    if not user_input:
        return jsonify({'error': '请输入内容'}), 400
    
    response = travel_agent_chat(user_input)
    return jsonify({'response': response})


@app.route('/api/navigation', methods=['POST'])
def navigation():
    """导航API"""
    data = request.json
    origin = data.get('origin', '')
    destination = data.get('destination', '')
    mode = data.get('mode', 'driving')
    
    if not origin or not destination:
        return jsonify({'error': '请提供起点和终点'}), 400
    
    result = _do_navigation(origin, destination, mode)
    return jsonify({'response': result})


@app.route('/api/attractions', methods=['POST'])
def attractions():
    """景点查询API"""
    data = request.json
    city = data.get('city', '')
    interests = data.get('interests', None)
    
    if not city:
        return jsonify({'error': '请提供城市名称'}), 400
    
    result = get_attractions(city, interests)
    return jsonify({'response': result})


@app.route('/api/hotels', methods=['POST'])
def hotels():
    """酒店查询API"""
    data = request.json
    city = data.get('city', '')
    
    if not city:
        return jsonify({'error': '请提供城市名称'}), 400
    
    result = search_hotels(city)
    return jsonify({'response': result})


@app.route('/api/weather', methods=['POST'])
def weather():
    """天气查询API"""
    data = request.json
    city = data.get('city', '')
    
    if not city:
        return jsonify({'error': '请提供城市名称'}), 400
    
    result = get_weather(city)
    return jsonify({'response': result})


if __name__ == '__main__':
    print("=" * 50)
    print("旅行规划助手 Web 服务")
    print("=" * 50)
    print("访问地址: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
