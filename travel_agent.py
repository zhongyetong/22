# travel_agent.py
"""
多智能体版本 - 使用主控智能体进行路由分发
"""
from agents import master_agent_chat

def travel_agent_chat(user_input: str) -> str:
    """
    旅行助手入口函数
    调用主控智能体进行意图识别和路由分发
    """
    return master_agent_chat(user_input)


# 启动
if __name__ == "__main__":
    print("=" * 50)
    print("欢迎使用AI旅行规划助手！（多智能体版本）")
    print("=" * 50)
    print("您可以这样提问：")
    print("  - '帮我规划北京5日游，预算5000元'")
    print("  - '保定有哪些景点'")
    print("  - '从天安门到颐和园怎么走'")
    print("  - '北京今天天气怎么样'")
    print("=" * 50)
    
    while True:
        user_input = input("\n请输入您的旅行需求（输入'退出'结束）: ")
        if user_input.lower() in ['退出', 'exit', 'quit']:
            print("感谢使用，祝您旅途愉快！")
            break
        
        print("\n正在处理...\n")
        response = travel_agent_chat(user_input)
        print(response)