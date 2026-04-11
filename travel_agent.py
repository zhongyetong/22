# travel_agent.py
import re
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
import config
from tools import get_navigation, search_hotels, get_attractions, get_weather, _do_navigation

# 初始化DeepSeek模型
llm = ChatDeepSeek(
    model=config.MODEL_NAME,
    temperature=0.7,
    max_tokens=4096
)

# 定义工具列表
tools = [get_navigation, search_hotels, get_attractions, get_weather]

# 定义系统提示词
system_prompt = """你是一个专业的旅行规划助手，帮助用户制定旅行计划。

## 可用工具
1. get_attractions(city, interests) - 查询城市景点
2. search_hotels(city) - 查询城市酒店
3. get_navigation(origin, destination, mode) - 查询两地路线
4. get_weather(city) - 查询城市实时天气

## 工作规则
1. 分析用户需求，明确目的地、天数、预算、人数、偏好
2. 主动调用工具获取信息，不要询问用户"需要查什么"
3. 信息足够时直接生成完整方案，禁止反复反问
4. 缺少关键信息（如目的地）时，最多询问一次

## 输出格式
- 使用 Markdown 格式
- 包含：交通建议、住宿推荐、每日行程、预算估算
- 景点间需要导航时，调用 get_navigation 获取路线

## 示例
用户：北京3日游，预算3000
→ 调用 get_attractions("北京")、search_hotels("北京")
→ 直接输出完整行程方案
"""

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt
)

def travel_agent_chat(user_input: str) -> str:
    """与旅行规划Agent进行对话"""
    user_input_clean = user_input.strip()
    
    # 处理导航请求：匹配“从 A 到 B”、“导航到 B”等
    nav_with_origin = re.search(r'从(.+?)到(.+?)(怎么走|怎么导航|怎么走|$)', user_input_clean)
    if nav_with_origin:
        origin = nav_with_origin.group(1).strip()
        destination = nav_with_origin.group(2).strip()
        if origin and destination:
            return _do_navigation(origin, destination)
    
    nav_simple = re.search(r'(导航到|怎么去|如何到达)(.+)', user_input_clean)
    if nav_simple:
        destination = nav_simple.group(2).strip()
        return "请告诉我您的出发地，例如：'从北京天安门到" + destination + "'"
    
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]}
        )
        if "messages" in result:
            return result["messages"][-1].content
        return str(result)
    except Exception as e:
        return f"抱歉，处理您的问题时出现错误：{str(e)}"

# 启动
if __name__ == "__main__":
    print("=" * 50)
    print("欢迎使用AI旅行规划助手！")
    print("=" * 50)
    print("您可以这样提问：")
    print("  - '帮我规划北京5日游，预算5000元'")
    print("  - '保定有哪些景点'")
    print("  - '从天安门到颐和园怎么走'")
    print("  - '推荐上海适合带孩子的景点'")
    print("=" * 50)
    
    while True:
        user_input = input("\n请输入您的旅行需求（输入'退出'结束）: ")
        if user_input.lower() in ['退出', 'exit', 'quit']:
            print("感谢使用，祝您旅途愉快！")
            break
        
        print("\n正在规划中...\n")
        response = travel_agent_chat(user_input)
        print(response)