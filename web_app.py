# web_app.py
# 旅行规划助手 Web 版本（多智能体架构）

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sys
sys.path.append('d:\\0travel_agent')

from agents import master_agent_chat
from tools import _do_navigation, get_attractions, search_hotels, get_weather

app = Flask(__name__)
CORS(app)


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """API接口 - 使用主控智能体进行路由"""
    data = request.json
    user_input = data.get('message', '')
    
    if not user_input:
        return jsonify({'error': '请输入内容'}), 400
    
    response = master_agent_chat(user_input)
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
    import logging
    # 关闭 LangChain 的详细日志
    logging.getLogger('langchain').setLevel(logging.WARNING)
    
    print("=" * 50)
    print("旅行规划助手 Web 服务（多智能体版本）")
    print("=" * 50)
    print("访问地址: http://127.0.0.1:5000")
    print("=" * 50)
    # debug=False 关闭自动重载和详细日志
    app.run(debug=False, host='0.0.0.0', port=5000)
