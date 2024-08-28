import requests
import json
import re

# Define the API URL and API key
api_url = "https://wei587.top/v1/chat/completions"
api_key = "sk-cAmOxwk6yZH5Y156B16027958dCb473dB4EeA46bE5703740"

# 定义全局变量
raw_nl_2 = ""
ltl_1 = ""

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

def gpt_transform(prompt, max_tokens=10000):
    data = {
        "model": "gpt-4-32k",
        "messages": [{"role": "system", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
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
    
    return response_json['choices'][0]['message']['content'].strip()



def check_syntactic_correctness(ltl_formula):
    # 检查LTL公式的语法正确性
    # 简单地检查括号是否匹配
    stack = []
    for char in ltl_formula:
        if char == '(':
            stack.append(char)
        elif char == ')':
            if not stack:
                return False
            stack.pop()
    return not stack

def correct_syntactic_errors(ltl_formula):
    # Correct the syntactic errors in the LTL formula using GPT
    prompt_fix = f"""
    The following LTL formula has syntax errors, please correct it:
    {ltl_formula}
    You need to pay attention to the matching relationships between the parentheses. Please output without adding any text display symbols, such as (*#), only pure LTL expression text is needed.
    """
    corrected_ltl = gpt_transform(prompt_fix)
    return corrected_ltl

def correct_ltl_formula(ltl_formula):
    while True:
        if check_syntactic_correctness(ltl_formula):
            break
        else:
            ltl_formula = correct_syntactic_errors(ltl_formula)
            if ltl_formula is None:
                print("Error correcting LTL formula")
                break
            print(f"Syntactic correction: {ltl_formula}")
        print("-" * 50)
    
    return ltl_formula

def generate_final_ltl_from_nl2(nl2_description):
    # GPT-3 act as a professional LTL expertise to generate the final LTL formula from NL2
    prompt = f"As a professional LTL expertise, generate an LTL formula from the following natural language description:\n{nl2_description}\nLTL formula:"
    return gpt_transform(prompt)

def extract_ltl_expression(response_text):
    # 定义正则表达式来匹配 "LTL Expression" 的内容
    ltl_expression_pattern = re.compile(r"LTL Expression:\s*(\{[\s\S]*?\}|\s*G[\s\S]*?(?=Explanation|$))", re.DOTALL)
    
    # 搜索匹配内容
    match = ltl_expression_pattern.search(response_text)
    if match:
        ltl_expression = match.group(1)
        return ltl_expression.strip()
    else:
        return None

def extract_location_info(response_text):
    # 定义正则表达式来匹配 "Location Information" 的内容，包括可能的格式
    location_info_pattern = re.compile(
        r"Location Information:\s*{[\s\S]*?}\s*(?=LTL Expression:)",
        re.DOTALL
    )
    
    # 搜索匹配内容
    match = location_info_pattern.search(response_text)
    if match:
        location_info = match.group()
        print("Location Information:")
        print(location_info)
    else:
        # 如果没有找到 "Location Information"，提取 "LTL Expression" 之前的所有信息
        general_info_pattern = re.compile(
            r"([\s\S]*?)(?=LTL Expression:)",
            re.DOTALL
        )
        match = general_info_pattern.search(response_text)
        if match:
            general_info = match.group(1)
            print("Additional Information:")
            print(general_info)
        else:
            print("No relevant information found in the response.")
        
        
def generate_and_print_ltl():
    global raw_nl_2
    global ltl_1
    
    ltl_prompt = (
        """
        Generate a set of random navigation instructions and a corresponding linear temporal logic (LTL) expression. Also, provide detailed location information and an explanation of the LTL expression. 

        1.Navigation Instructions Requirements: Instructions should include multiple steps, such as turning left, turning right, going straight, etc. Each step should include specific distances or location descriptions. The final instruction should include arriving at the destination. Please generate a short command, as subsequent operations have limitations on command length. 

        2.Location Information Requirements: 
            {
            Current Location:
                {
                Place: Specific street name and city. 
                Current Lane: For example, straight lane, left-turn lane, etc. 
                Speed Limit: Speed in kilometers per hour. 
                Environmental Conditions: For example, there is a car overtaking in the right lane, road conditions ahead, current distance to the turn, etc. 
                Traffic conditions (e.g., heavy traffic, smooth traffic, etc.). 
                Weather conditions (e.g., sunny, rainy, etc.). 
                }
            Target Location: 
                {
                Place: Specific street name and city. 
                Distance: Distance from the current location to the target location. 
                Estimated Arrival Time: Estimated time to reach the destination. 
                }
            Additional Details: 
                {
                Surrounding buildings: For example, commercial buildings, office buildings, etc. 
                Nearby landmarks: For example, universities, museums, etc. 
                Pedestrian activity: For example, high pedestrian activity, low pedestrian activity, etc. 
                Traffic signals: For example, are traffic lights functioning properly. 
                }
            }

        3.LTL Expression Requirements: Include multiple nested "eventually" (F), "globally" (G), "next" (X), "implies"(->), "equivalent"(<->), "and"(&), "or"(|),"not"(!) operators. Logically represent the navigation sequence, ensuring the expression accurately reflects the instructions and conditions. Please note that vehicle actions are the key to instructions. Ensure that the movements of the vehicle are reflected in the LTL.Pay attention to the matching relationships between the parentheses. Please try to avoid line breaks in the output. Don't generate an overly long LTL, since LatencyInfo vector size 113 is too big.

        4.Explanation Requirements: Provide a clear and concise explanation of the LTL expression. Describe how the expression models the navigation instructions. Connect the expression to the detailed location information provided.
        
        Please output in the given format without adding any text display symbols, such as (*#), only pure text content is needed. Please enclose the location information in {} and mention the key words "Location information".
        """
    )
    
    # Step 1: 生成与交通导航相关的随机LTL公式
    print("-" * 35 , 'Step 1: Generate LTL and context' ,"-" * 35 )
    ltl_1 = gpt_transform(ltl_prompt)
    if ltl_1 is None:
        print("Failed to generate LTL")
        return
    
    print(ltl_1)
    print("-" * 50)
    ltl_expression = extract_ltl_expression(ltl_1)
    
    if ltl_expression is None:
        print("Failed to extract LTL expression")
        return
    
    print("LTL Expression:")
    print(ltl_expression)


    # Step 2: GPT-3将LTL-1转换为原始自然语言描述NL-1
    print("-" * 35 , 'Step 2: LTL-1 to NL-1' ,"-" * 35 )
    prompt_1 = f"""
    Transform the following LTL formula into a natural language driving instruction as a professional LTL expert:
    {ltl_expression}
    Requirement: Please ensure that the original traffic instruction information is preserved as much as possible. Please output only the natural language parts; no additional content is needed.
    """
    raw_nl_1 = gpt_transform(prompt_1)
    if raw_nl_1 is None:
        print("Failed to transform LTL-1 to NL-1")
        return
    print(raw_nl_1)

    # Step 3: 将原始自然语言描述NL-1放回GPT-3以获取LTL-2
    print("-" * 35 , 'Step 3: NL-1 to LTL-2' ,"-" * 35 )
    prompt_2 = f"""
        Transform the following natural language driving instruction back into an LTL formula as a professional LTL expert:
        {raw_nl_1}
        LTL Expression Requirements: Include multiple nested "eventually" (F), "globally" (G), "next" (X), "implies"(->), "equivalent"(<->), "and"(&), "or"(|),"not"(!) operators. Logically represent the navigation sequence, ensuring the expression accurately reflects the instructions and conditions. Ensure that the movements of the vehicle are reflected in the LTL.pay attention to the matching relationships between the parentheses.
        Please output without adding any text display symbols, such as (*#), only pure LTL expression text is needed. Don't generate an overly long LTL, since LatencyInfo vector size 113 is too big.
        """
    ltl_2 = gpt_transform(prompt_2)
    if ltl_2 is None:
        print("Failed to transform NL-1 to LTL-2")
        return
    print(f"LTL-2: {ltl_2}")

    # Step 4: 检查LTL-2的语法正确性，如果错误则调用GPT进行修改
    print("-" * 35, 'Step 4: check LTL-2 correctness', "-" * 35)
    ltl_3 = correct_ltl_formula(ltl_2)
    if ltl_3 is None:
        print("Failed to correct LTL-2 syntax")
        return
    print(f"LTL-2 is syntactically correct: {ltl_3}")


    # Step 5: GPT-3将LTL-2转换为原始自然语言描述NL-2
    print("-" * 35, 'Step 5: LTL-2 to NL-2', "-" * 35)
    prompt_3 = f"""Transform the following LTL formula into a natural language driving instruction as a professional LTL expert:
    {ltl_expression}
    Requirement: Please ensure that the original traffic instruction information is preserved as much as possible. Please output only the natural language parts; no additional content is needed.
    """
    raw_nl_2 = gpt_transform(prompt_3)
    if raw_nl_2 is None:
        print("Failed to transform LTL-2 to NL-2")
        return
    print(f"Raw NL-2: {raw_nl_2}")
    print("-" * 50)
    extract_location_info(ltl_1)
    
    print("-" * 35 , 'New LTL' ,"-" * 35 )
    prompt_2 = f"""
        Transform the following natural language driving instruction back into an LTL formula as a professional LTL expert:
        {raw_nl_2}
        LTL Expression Requirements: Include multiple nested "eventually" (F), "globally" (G), "next" (X), "implies"(->), "equivalent"(<->), "and"(&), "or"(|),"not"(!) operators. Logically represent the navigation sequence, ensuring the expression accurately reflects the instructions and conditions. Ensure that the movements of the vehicle are reflected in the LTL.pay attention to the matching relationships between the parentheses.
        Please output without adding any text display symbols, such as (*#), only pure LTL expression text is needed. Don't generate an overly long LTL, since LatencyInfo vector size 113 is too big.
        """
    ltl_3 = gpt_transform(prompt_2)
    if ltl_3 is None:
        print("Failed to transform NL-2 to LTL")
        return
    print(f"LTL: {ltl_3}")
    
    return ltl_3, raw_nl_2

# 生成一个LTL公式并打印输出
generate_and_print_ltl()
