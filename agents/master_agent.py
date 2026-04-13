"""
主控智能体 - 负责路由分发，决定调用哪个子智能体
"""
import re
import sys
sys.path.append('d:\\0travel_agent')

from .navigation_agent import nav_agent_chat
from .weather_agent import weather_agent_chat
from .planning_agent import planning_agent_chat

# 导入底层函数（相对导入可能失败，使用 sys.path）
try:
    from tools import _get_attractions, _get_spot_detail, _get_weather
except ImportError:
    import importlib.util
    spec = importlib.util.spec_from_file_location("tools", r"d:\0travel_agent\tools.py")
    tools_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tools_module)
    _get_attractions = tools_module._get_attractions
    _get_spot_detail = tools_module._get_spot_detail
    _get_weather = tools_module._get_weather


def master_agent_chat(user_input: str, chat_history: list = None) -> str:
    """
    主控智能体入口函数
    根据用户输入特征，分发到对应的子智能体或直接调用工具
    """
    if chat_history is None:
        chat_history = []
    
    user_input_clean = user_input.strip().lower()
    
    # 意图识别：导航类
    if re.search(r'从(.+?)到(.+?)', user_input_clean) or \
       any(kw in user_input_clean for kw in ['导航', '怎么去', '怎么走', '路线', '距离', '公里']):
        print(f"[主控] 识别为导航意图，调用导航智能体")
        return nav_agent_chat(user_input, chat_history)
    
    # 意图识别：天气类
    if any(kw in user_input_clean for kw in ['天气', '温度', '气温', '下雨', '晴', '阴', '雾霾']):
        # 提取城市名：匹配"XX天气"格式
        city_match = re.search(r'([\u4e00-\u9fa5]{2,6})(?:天气|温度|气温)', user_input)
        if city_match:
            city = city_match.group(1)
            print(f"[主控] 识别为天气意图，查询: {city}")
            return _get_weather(city)
        # 如果提取失败，尝试简单提取前几个字
        city_match = re.search(r'^([\u4e00-\u9fa5]{2,6})', user_input.strip())
        if city_match:
            city = city_match.group(1)
            print(f"[主控] 识别为天气意图，查询: {city}")
            return _get_weather(city)
        # 如果都失败，走Agent
        print(f"[主控] 识别为天气意图，调用天气智能体")
        return weather_agent_chat(user_input, chat_history)
    
    # 意图识别：纯景点查询（不是行程规划）
    # 匹配 "XX有什么景点"、"XX好玩的地方"、"XX景点"、"XX古城" 等
    attraction_keywords = ['景点', '好玩', '哪里', '有什么', '有啥', '古城', '古镇', '景区', '名胜', '旅游', '值得去', '推荐', '植物园', '公园', '博物馆', '纪念馆', '详细信息', '介绍']
    is_attraction_query = any(kw in user_input_clean for kw in attraction_keywords)
    is_planning_query = any(kw in user_input_clean for kw in ['规划', '行程', '攻略', '几天', '预算', '日游', '安排', '计划'])
    
    if is_attraction_query and not is_planning_query:
        # 判断是查询具体景点详情，还是查询城市景点列表
        # 如果输入包含"植物园"、"博物馆"等具体景点类型词，且前面有城市名，视为具体景点查询
        spot_types = ['植物园', '动物园', '博物馆', '纪念馆', '公园', '广场', '大厦', '中心', '塔', '寺', '庙', '陵', '园']
        has_spot_type = any(st in user_input for st in spot_types)
        
        # 提取城市名
        city_input = user_input.strip()
        
        # 去掉常见后缀
        suffixes = ['景点', '景区', '名胜', '旅游', '好玩', '哪里', '推荐', '值得去', '的地方', '的景点', '详细信息', '介绍', '攻略']
        for suffix in suffixes:
            if city_input.endswith(suffix):
                city_input = city_input[:-len(suffix)]
                break
        
        # 去掉前缀词
        prefixes = ['去', '到', '在']
        for prefix in prefixes:
            if city_input.startswith(prefix):
                city_input = city_input[len(prefix):]
        
        # 去掉"有什么"、"有啥"等
        city_input = re.sub(r'有(什么|啥)$', '', city_input)
        city_input = re.sub(r'有(什么|啥)景点$', '', city_input)
        
        # 如果包含具体景点类型词，查询该景点详情
        if has_spot_type:
            for st in spot_types:
                if st in city_input:
                    # 提取景点名（城市名+景点类型）
                    spot_match = re.search(r'([\u4e00-\u9fa5]{2,4})' + st, city_input)
                    if spot_match:
                        spot_name = spot_match.group(0)
                        print(f"[主控] 识别为具体景点查询，查询: {spot_name}")
                        return _get_spot_detail(spot_name)
        
        # 否则查询城市景点列表
        # 去掉具体景点名后缀，保留城市名
        for suffix in spot_types:
            if city_input.endswith(suffix):
                city_input = city_input[:-len(suffix)]
                break
        
        # 提取前2-4个字作为城市名
        city_match = re.search(r'^([\u4e00-\u9fa5]{2,4})', city_input)
        if city_match:
            city = city_match.group(1)
            # 去掉"古城"、"古镇"等后缀（如果是城市名的一部分）
            if city.endswith('古城') or city.endswith('古镇'):
                city = city[:-2]
            if city:
                print(f"[主控] 识别为城市景点查询，查询: {city}")
                return _get_attractions(city)
    
    # 意图识别：规划类（默认）
    print(f"[主控] 识别为规划意图，调用规划智能体")
    return planning_agent_chat(user_input, chat_history)


if __name__ == "__main__":
    # 测试不同意图
    test_cases = [
        "从北京南站到天安门怎么走",
        "北京今天天气怎么样",
        "帮我规划北京3日游",
        "上海有什么好玩的",
    ]
    
    for test in test_cases:
        print(f"\n用户: {test}")
        result = master_agent_chat(test)
        print(f"结果: {result[:100]}...")
