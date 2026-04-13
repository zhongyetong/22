"""
导航智能体 - 专门处理路线查询
"""
import re
import sys
sys.path.append('d:\\0travel_agent')

from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
import config
from tools import get_navigation, _do_navigation

# 导航智能体专用工具
nav_tools = [get_navigation]

# 导航智能体专用提示词
nav_system_prompt = """你是专业的导航助手，专门帮助用户查询路线。

## 可用工具
- get_navigation(origin, destination, mode) - 查询两地路线
  - mode可选: driving(驾车)、walking(步行)、transit(公交)、riding(骑行)

## 工作规则
1. 提取用户输入中的起点和终点
2. 默认使用 driving 模式，除非用户指定其他方式
3. 直接调用工具返回路线信息
4. 如果信息不完整，询问用户补充

## 示例
用户：从北京南站到天安门
→ 调用 get_navigation("北京南站", "天安门", "driving")
"""

# 创建导航智能体
llm = ChatDeepSeek(
    model=config.MODEL_NAME,
    temperature=0.3,
    max_tokens=2048
)

navigation_agent = create_agent(
    model=llm,
    tools=nav_tools,
    system_prompt=nav_system_prompt
)


def nav_agent_chat(user_input: str, chat_history: list = None) -> str:
    """
    导航智能体入口函数
    优先使用正则快路径，复杂情况走 Agent
    """
    if chat_history is None:
        chat_history = []
    
    user_input_clean = user_input.strip()
    
    # 快路径：正则匹配 "从A到B"
    match = re.search(r'从(.+?)到(.+?)[怎么|咋|走|去|路线]', user_input_clean)
    if match:
        origin = match.group(1).strip()
        destination = match.group(2).strip()
        return _do_navigation(origin, destination, "driving")
    
    # 快路径：简化匹配
    match = re.search(r'从(.+?)到(.+?)$', user_input_clean)
    if match:
        origin = match.group(1).strip()
        destination = match.group(2).strip()
        return _do_navigation(origin, destination, "driving")
    
    # 慢路径：走 Agent
    try:
        response = navigation_agent.invoke({
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
        return f"导航查询出错: {str(e)}"


if __name__ == "__main__":
    # 测试
    print(nav_agent_chat("从北京南站到天安门怎么走"))
