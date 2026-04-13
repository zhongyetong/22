"""
规划智能体 - 专门处理旅行规划
"""
import sys
sys.path.append('d:\\0travel_agent')

from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
import config
from tools import get_attractions, search_hotels, get_weather

# 规划智能体专用工具
planning_tools = [get_attractions, search_hotels, get_weather]

# 规划智能体专用提示词
planning_system_prompt = """你是专业的旅行规划师，专门帮助用户制定旅行计划。

## 可用工具
1. get_attractions(city, interests) - 查询城市景点
   - interests: 可选，用户兴趣偏好，如"历史文化"、"自然风光"
   
2. search_hotels(city) - 查询城市酒店

3. get_weather(city) - 查询城市天气

## 工作规则
1. 分析用户需求：目的地、天数、预算、人数、偏好
2. 主动调用工具获取信息，不要反复询问用户
3. 信息足够时直接生成完整行程方案
4. 仅缺少关键信息（如目的地）时，最多询问一次
5. 行程要包含：每日安排、景点推荐、酒店建议、交通提示

## 输出格式
【XX城市X日游行程】

Day1: ...
Day2: ...

【住宿推荐】
...

【实用提示】
天气/交通/注意事项
"""

# 创建规划智能体
llm = ChatDeepSeek(
    model=config.MODEL_NAME,
    temperature=0.7,
    max_tokens=4096
)

planning_agent = create_agent(
    model=llm,
    tools=planning_tools,
    system_prompt=planning_system_prompt
)


def planning_agent_chat(user_input: str, chat_history: list = None) -> str:
    """
    规划智能体入口函数
    """
    if chat_history is None:
        chat_history = []
    
    try:
        response = planning_agent.invoke({
            "input": user_input,
            "chat_history": chat_history
        })
        
        # 处理不同类型的返回值
        if isinstance(response, dict):
            # 优先取 output 字段
            if "output" in response:
                return response["output"]
            # 取 messages 列表最后一条
            if "messages" in response and response["messages"]:
                last_msg = response["messages"][-1]
                if hasattr(last_msg, 'content'):
                    return last_msg.content
                return str(last_msg)
            # 其他情况转字符串
            return str(response)
        elif hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
            
    except Exception as e:
        return f"行程规划出错: {str(e)}"


if __name__ == "__main__":
    # 测试
    print(planning_agent_chat("帮我规划北京3日游，喜欢历史文化"))
