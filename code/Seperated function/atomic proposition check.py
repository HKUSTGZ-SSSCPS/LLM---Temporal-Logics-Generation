import requests
import json

# 原子命题库
atomic_proposition_library = [
    "turn_left",             # 左转
    "turn_right",            # 右转
    "go_straight",           # 直行
    "turn_around",           # 掉头
    "stop",                  # 停止
    "take_exit",             # 出口
    "enter_roundabout",      # 进入环形交叉口
    "exit_roundabout",       # 离开环形交叉口
    "follow_the_road",       # 跟随道路
    "keep_left",             # 保持左侧
    "keep_right",            # 保持右侧
    "continue_on_highway",   # 继续走高速
    "take_the_second_exit",  # 第二个出口
    "take_the_first_exit",   # 第一个出口
    "stay_in_the_left_lane", # 保持左车道
    "stay_in_the_right_lane",# 保持右车道
    "merge_left",            # 向左合并
    "merge_right",           # 向右合并
    "keep_speed",            # 保持车速
    "increase_speed",        # 加速
    "decrease_speed",        # 减速
    "continue_at_traffic_light" # 继续行驶通过交通信号灯
]


api_url = "https://gpt-api.hkust-gz.edu.cn/v1/chat/completions"

headers = { 
    "Content-Type": "application/json", 
    "Authorization": "Bearer 36d2022014eb4e11be67a6dd76e0244cc1ae73a9094d45b9b270e8fc49a860fa"  # 请替换成你自己的API密钥
}

def gpt_transform(input_propositions, atomic_library, max_tokens=4000):
    # 生成与GPT交互的prompt
    prompt = f"Please match the following atomic propositions to a pre-defined library of atomic propositions: {input_propositions}. The library is: {atomic_library}. If any proposition is similar to one in the library, replace it with the library's proposition. Return the updated atomic propositions."
    
    data = { 
        "model": "gpt-3.5-turbo", 
        "messages": [{"role": "user", "content": prompt}],  # 使用传入的prompt
        "temperature": 0.7
    }
    
    # 请求GPT API
    response = requests.post(api_url, headers=headers, data=json.dumps(data))
    
    if response.status_code != 200:
        print(f"API request failed with status code {response.status_code}")
        print(f"Response content: {response.content.decode('utf-8')}")
        return None
    
    response_json = response.json()
    
    if 'choices' not in response_json:
        print("Error: 'choices' not found in the response")
        print(f"Full response: {response_json}")
        return None
    
    # 返回GPT修正后的命题组
    return response_json['choices'][0]['message']['content'].strip()

# 输入原子命题组
input_propositions = ["move_straight_150","turn_left","move_straight_200","arrive_at_destination","turn_right"]

# 调用函数进行转换
updated_propositions = gpt_transform(input_propositions, atomic_proposition_library)

# 输出更新后的命题组
print(updated_propositions)
