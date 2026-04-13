"""
天气智能体 - 专门处理天气查询
"""
import sys
sys.path.append('d:\\0travel_agent')

from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
import config
from tools import get_weather

# 天气智能体专用工具
weather_tools = [get_weather]

# 天气智能体专用提示词
weather_system_prompt = """你是专业的天气助手，专门帮助用户查询天气信息。

## 可用工具
- get_weather(city) - 查询城市实时天气
  - 返回：天气状况、温度、湿度、风向、风力、发布时间

## 工作规则
1. 提取用户输入中的城市名称
2. 直接调用工具返回天气信息
3. 用友好的方式呈现天气数据
4. 如果城市不明确，询问用户

## 示例
用户：北京今天天气怎么样
→ 调用 get_weather("北京")
→ 返回格式化天气信息
"""

# 创建天气智能体
llm = ChatDeepSeek(
    model=config.MODEL_NAME,
    temperature=0.3,
    max_tokens=2048
)

weather_agent = create_agent(
    model=llm,
    tools=weather_tools,
    system_prompt=weather_system_prompt
)


def weather_agent_chat(user_input: str, chat_history: list = None) -> str:
    """
    天气智能体入口函数
    """
    if chat_history is None:
        chat_history = []
    
    try:
        response = weather_agent.invoke({
            "input": user_input,
            "chat_history": chat_history
        })
        
        # 处理不同类型的返回值
        if isinstance(response, dict):
            if "output" in response:
                return response["output"]
            if "messages" in response and response["messages"]:
                last_msg = response["messages"][-1]
                if hasattr(last_msg, 'content'):
                    return last_msg.content
                return str(last_msg)
            return str(response)
        elif hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
            
    except Exception as e:
        return f"天气查询出错: {str(e)}"


if __name__ == "__main__":
    # 测试
    print(weather_agent_chat("北京今天天气怎么样"))
