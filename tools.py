# tools.py
import requests
import json
import os
from langchain_core.tools import tool
import config

def _geocode(address: str, api_key: str) -> str:
    """地名转经纬度（返回 '经度,纬度' 格式）"""
    try:
        resp = requests.get(
            "https://restapi.amap.com/v3/geocode/geo",
            params={"key": api_key, "address": address},
            timeout=10
        )
        data = resp.json()
        if data.get("status") == "1" and data.get("geocodes"):
            return data["geocodes"][0]["location"]  # 格式: "116.397428,39.90923"
    except:
        pass
    return None


def _do_navigation(origin: str, destination: str, mode: str = "driving") -> str:
    """导航底层实现函数（可直接调用）——使用高德地图路径规划 API"""
    
    api_key = os.getenv("GAODE_MAP_API_KEY")
    if not api_key:
        return "错误：未找到高德地图 API 密钥，请检查环境变量 GAODE_MAP_API_KEY。"
    
    # 将地名转换为经纬度
    origin_coord = _geocode(origin, api_key)
    dest_coord = _geocode(destination, api_key)
    
    if not origin_coord:
        return f"无法解析地名「{origin}」，请输入更具体的地址"
    if not dest_coord:
        return f"无法解析地名「{destination}」，请输入更具体的地址"
    
    # 高德路径规划 API 地址
    mode_map = {
        "driving": "https://restapi.amap.com/v3/direction/driving",
        "walking": "https://restapi.amap.com/v3/direction/walking",
        "transit": "https://restapi.amap.com/v3/direction/transit/integrated",
        "riding": "https://restapi.amap.com/v4/direction/bicycling",
    }
    base_url = mode_map.get(mode, mode_map["driving"])
    
    mode_names = {"driving": "驾车", "riding": "骑行", "walking": "步行", "transit": "公交"}
    
    params = {
        "key": api_key,
        "origin": origin_coord,
        "destination": dest_coord,
    }
    # 公交路线需要城市参数
    if mode == "transit":
        params["city"] = origin
    
    try:
        response = requests.get(base_url, params=params, timeout=15)
        data = response.json()
        
        # 高德驾车/步行返回格式
        if mode in ("driving", "walking"):
            if data.get("status") != "1":
                return f"导航查询失败: {data.get('info', '未知错误')}"
            route = data.get("route", {})
            paths = route.get("paths", [])
            if not paths:
                return f"未找到从 {origin} 到 {destination} 的路线。"
            path = paths[0]
            distance = int(path.get("distance", 0))
            duration = int(path.get("duration", 0))
            steps_raw = path.get("steps", [])
        
        # 高德公交返回格式
        elif mode == "transit":
            if data.get("status") != "1":
                return f"导航查询失败: {data.get('info', '未知错误')}"
            route = data.get("route", {})
            transits = route.get("transits", [])
            if not transits:
                return f"未找到从 {origin} 到 {destination} 的公交方案。"
            transit = transits[0]
            distance = int(route.get("distance", 0))
            duration = int(transit.get("duration", 0))
            steps_raw = transit.get("segments", [])
        
        # 高德骑行返回格式
        elif mode == "riding":
            if data.get("errcode") is not None and data.get("errcode") != 0:
                return f"导航查询失败: {data.get('errmsg', '未知错误')}"
            data_inner = data.get("data", {})
            paths = data_inner.get("paths", [])
            if not paths:
                return f"未找到从 {origin} 到 {destination} 的骑行路线。"
            path = paths[0]
            distance = int(path.get("distance", 0))
            duration = int(path.get("duration", 0))
            steps_raw = path.get("steps", [])
        
        # 格式化输出
        distance_str = f"{distance / 1000:.1f}公里" if distance >= 1000 else f"{distance}米"
        duration_str = f"{duration / 3600:.1f}小时" if duration >= 3600 else f"{duration / 60:.0f}分钟"
        
        output = f"【{mode_names.get(mode, '驾车')}路线】{origin} → {destination}\n"
        output += f"总距离: {distance_str} | 预计时间: {duration_str}\n\n"
        
        # 添加路线步骤
        if steps_raw:
            output += "路线指引:\n"
            for i, step in enumerate(steps_raw[:10], 1):
                if mode == "transit":
                    # 公交段落格式不同
                    bus_lines = step.get("bus", {}).get("buslines", [])
                    walking = step.get("walking", {})
                    if bus_lines:
                        line = bus_lines[0]
                        output += f"  {i}. 乘 {line.get('name', '')}，{line.get('departure_stop', {}).get('name', '')}上车，{line.get('arrival_stop', {}).get('name', '')}下车\n"
                    elif walking:
                        walk_dist = int(walking.get("distance", 0))
                        output += f"  {i}. 步行 {walk_dist}米\n"
                else:
                    instruction = step.get("instruction", step.get("step_info", ""))
                    step_dist = int(step.get("distance", 0))
                    step_dist_str = f"{step_dist}米" if step_dist < 1000 else f"{step_dist/1000:.1f}公里"
                    output += f"  {i}. {instruction} ({step_dist_str})\n"
            if len(steps_raw) > 10:
                output += f"  ... 还有 {len(steps_raw) - 10} 个步骤\n"
        
        return output
        
    except requests.exceptions.RequestException as e:
        return f"请求导航信息失败: {str(e)}"


@tool
def get_navigation(origin: str, destination: str, mode: str = "driving") -> str:
    """
    使用高德地图 API 获取从起点到终点的导航路线。
    Args:
        origin: 出发地，如"北京市天安门"
        destination: 目的地，如"北京市颐和园"
        mode: 出行方式，可选 driving、walking、transit、riding
    Returns:
        路线规划结果的格式化字符串
    """
    return _do_navigation(origin, destination, mode)


@tool
def search_hotels(city: str, check_in: str = None, check_out: str = None, budget: int = None) -> str:
    """
    使用高德地图 API 搜索城市内的酒店信息。
    Args:
        city: 城市名称，如"北京"、"上海"、"保定"
        check_in: 入住日期 YYYY-MM-DD，可选
        check_out: 离店日期 YYYY-MM-DD，可选
        budget: 预算上限（元/晚），可选
    Returns:
        酒店信息的格式化字符串
    """
    api_key = os.getenv("GAODE_MAP_API_KEY")
    if not api_key:
        return "错误：未找到高德地图 API 密钥，请检查环境变量 GAODE_MAP_API_KEY。"
    
    # 高德地图地点搜索 API
    base_url = "https://restapi.amap.com/v3/place/text"
    
    # 构建关键词：城市名 + 酒店
    keywords = f"{city}酒店"
    
    params = {
        "key": api_key,
        "keywords": keywords,
        "city": city,
        "citylimit": "true",
        "offset": 10,
        "page": 1,
        "extensions": "all"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") != "1":
            return f"查询失败: {data.get('info', '未知错误')}"
        
        pois = data.get("pois", [])
        if not pois:
            return f"未找到{city}的酒店信息。"
        
        result = f"【{city}酒店推荐】\n"
        
        for i, hotel in enumerate(pois[:5], 1):
            name = hotel.get("name", "未知")
            address = hotel.get("address", "地址未知")
            tel = hotel.get("tel", "")
            rating = hotel.get("biz_ext", {}).get("rating", "暂无")
            
            result += f"\n{i}. {name}\n"
            result += f"   地址: {address}\n"
            if tel:
                result += f"   电话: {tel}\n"
            if rating and rating != "[]":
                result += f"   评分: {rating}\n"
        
        return result
        
    except requests.exceptions.RequestException as e:
        return f"请求酒店信息失败: {str(e)}"

def _get_attractions(city: str, interests: str = None) -> str:
    """
    底层函数：使用高德地图 API 搜索城市内的旅游景点（可直接调用）
    """
    api_key = os.getenv("GAODE_MAP_API_KEY")
    if not api_key:
        return "错误：未找到高德地图 API 密钥，请检查环境变量 GAODE_MAP_API_KEY。"
    
    # 高德地图地点搜索 API
    base_url = "https://restapi.amap.com/v3/place/text"
    
    # 根据兴趣偏好选择关键词
    type_keywords = {
        "历史": "古迹",
        "文化": "博物馆",
        "自然": "公园",
        "美食": "美食街",
        "购物": "商圈",
        "娱乐": "游乐场"
    }
    
    if interests and interests in type_keywords:
        keywords = f"{city}{type_keywords[interests]}"
    else:
        keywords = f"{city}景点"
    
    params = {
        "key": api_key,
        "keywords": keywords,
        "city": city,
        "citylimit": "true",
        "offset": 10,
        "page": 1,
        "extensions": "all"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") != "1":
            return f"查询失败: {data.get('info', '未知错误')}"
        
        pois = data.get("pois", [])
        if not pois:
            return f"未找到{city}的景点信息。"
        
        result = f"【{city}景点推荐】"
        if interests:
            result += f"（{interests}相关）"
        result += "\n"
        
        for i, spot in enumerate(pois[:6], 1):
            name = spot.get("name", "未知")
            address = spot.get("address", "地址未知")
            tel = spot.get("tel", "")
            rating = spot.get("biz_ext", {}).get("rating", "")
            
            result += f"\n{i}. {name}\n"
            result += f"   地址: {address}\n"
            if tel:
                result += f"   电话: {tel}\n"
            if rating and rating != "[]":
                result += f"   评分: {rating}\n"
        
        return result
        
    except requests.exceptions.RequestException as e:
        return f"请求景点信息失败: {str(e)}"


@tool
def get_attractions(city: str, interests: str = None) -> str:
    """
    使用高德地图 API 搜索城市内的旅游景点。
    Args:
        city: 城市名称，如"北京"、"上海"、"保定"
        interests: 兴趣偏好，如"历史"、"自然"、"美食"等，可选
    Returns:
        景点推荐的格式化字符串
    """
    return _get_attractions(city, interests)


def _get_spot_detail(spot_name: str) -> str:
    """
    底层函数：查询特定景点的详细信息
    """
    api_key = os.getenv("GAODE_MAP_API_KEY")
    if not api_key:
        return "错误：未找到高德地图 API 密钥。"
    
    base_url = "https://restapi.amap.com/v3/place/text"
    
    params = {
        "key": api_key,
        "keywords": spot_name,
        "offset": 3,
        "page": 1,
        "extensions": "all"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") != "1":
            return f"查询失败: {data.get('info', '未知错误')}"
        
        pois = data.get("pois", [])
        if not pois:
            return f"未找到'{spot_name}'的详细信息。"
        
        # 取最匹配的第一个结果
        spot = pois[0]
        name = spot.get("name", "未知")
        address = spot.get("address", "地址未知")
        tel = spot.get("tel", "")
        rating = spot.get("biz_ext", {}).get("rating", "")
        typecode = spot.get("type", "")
        
        result = f"【{name}】\n\n"
        result += f"地址: {address}\n"
        if tel:
            result += f"电话: {tel}\n"
        if rating and rating != "[]":
            result += f"评分: {rating}\n"
        if typecode:
            result += f"类型: {typecode}\n"
        
        # 如果有更多结果，显示相似景点
        if len(pois) > 1:
            result += "\n【相似景点】\n"
            for i, similar in enumerate(pois[1:3], 1):
                sim_name = similar.get("name", "未知")
                sim_address = similar.get("address", "地址未知")
                result += f"{i}. {sim_name} - {sim_address}\n"
        
        return result
        
    except requests.exceptions.RequestException as e:
        return f"请求景点信息失败: {str(e)}"


@tool
def get_spot_detail(spot_name: str) -> str:
    """
    查询特定景点的详细信息。
    Args:
        spot_name: 景点名称，如"故宫博物院"、"颐和园"、"保定植物园"
    Returns:
        景点的详细信息，包含地址、电话、评分等
    """
    return _get_spot_detail(spot_name)


def _get_weather(city: str) -> str:
    """
    底层函数：使用高德地图 API 查询城市实时天气（可直接调用）
    """
    api_key = os.getenv("GAODE_MAP_API_KEY")
    if not api_key:
        return "错误：未找到高德地图 API 密钥。"
    
    # 高德天气查询 API
    base_url = "https://restapi.amap.com/v3/weather/weatherInfo"
    
    params = {
        "key": api_key,
        "city": city,
        "extensions": "base"  # 实时天气
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") != "1":
            return f"查询失败: {data.get('info', '未知错误')}"
        
        lives = data.get("lives", [])
        if not lives:
            return f"未找到{city}的天气信息。"
        
        weather = lives[0]
        
        result = f"【{city}实时天气】\n\n"
        result += f"天气状况: {weather.get('weather', '未知')}\n"
        result += f"温度: {weather.get('temperature', '未知')}°C\n"
        result += f"湿度: {weather.get('humidity', '未知')}%\n"
        result += f"风向: {weather.get('winddirection', '未知')}\n"
        result += f"风力: {weather.get('windpower', '未知')}级\n"
        result += f"发布时间: {weather.get('reporttime', '未知')}\n"
        
        return result
        
    except requests.exceptions.RequestException as e:
        return f"请求天气信息失败: {str(e)}"


@tool
def get_weather(city: str) -> str:
    """
    使用高德地图 API 查询城市实时天气。
    Args:
        city: 城市名称，如"北京"、"上海"、"保定"
    Returns:
        天气信息的格式化字符串，包含温度、湿度、风向、天气状况
    """
    return _get_weather(city)