import requests
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Define the API URL and API key
api_url = "https://gpt-api.hkust-gz.edu.cn/v1/chat/completions"

headers = { 
    "Content-Type": "application/json", 
    "Authorization": "Bearer 36d2022014eb4e11be67a6dd76e0244cc1ae73a9094d45b9b270e8fc49a860fa"  # 请替换成你自己的API密钥
}

def gpt_transform(prompt, max_tokens=4000):
    data = { 
        "model": "gpt-3.5-turbo", 
        "messages": [{"role": "user", "content": prompt}],  # 使用传入的prompt
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

# 定义全局变量
raw_nl_2 = ""
ltl_1 = ""

def check_syntactic_correctness(ltl_formula):
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
    prompt = f"As a professional LTL expertise, generate an LTL formula from the following natural language description:\n{nl2_description}\nLTL formula:"
    return gpt_transform(prompt)

def extract_ltl_expression(response_text):
    ltl_expression_pattern = re.compile(r"LTL Expression:\s*(\{[\s\S]*?\}|\s*G[\s\S]*?(?=Explanation|$))", re.DOTALL)
    match = ltl_expression_pattern.search(response_text)
    if match:
        ltl_expression = match.group(1)
        return ltl_expression.strip()
    else:
        return None

def extract_location_info(response_text):
    location_info_pattern = re.compile(
        r"Location Information:\s*{[\s\S]*?}\s*(?=LTL Expression:)",
        re.DOTALL
    )
    match = location_info_pattern.search(response_text)
    if match:
        location_info = match.group()
        print("Location Information:")
        print(location_info)
    else:
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
    {ltl_3}
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

def is_unary_operator(token):
    return token in ('¬', 'G', 'F', 'X')

def is_binary_operator(token):
    return token in ('&', '->', '<->', '|', 'U')

def is_multi_form_operator(token):
    return token in ('G', 'F', 'U')

def is_operator(token):
    return is_unary_operator(token) or is_binary_operator(token) or is_multi_form_operator(token)

def check_syntactic_correct(converted_list):
    count = 0
    for item in converted_list:
        if is_operator(item):
            if is_unary_operator(item):
                pass
            else:
                count -= 1
        elif item[:4] == 'prop' or item[:5] == 'enter' or item[:4] == 'not_':
            count += 1
        else:
            return item
    if count == 1:
        return 'correct'
    else:
        return count

def check_parentheses(ltl):
    stack = []
    for char in ltl:
        if char == '(':
            stack.append(char)
        elif char == ')':
            if not stack:
                return "Syntax error: Mismatched parentheses."
            stack.pop()
    if stack:
        return "Syntax error: Mismatched parentheses."
    return 'correct'

def check_operators(tokens, props):
    i = 0
    n = len(tokens)

    while i < n:
        token = tokens[i]

        if is_unary_operator(token):
            if i + 1 >= n or (tokens[i + 1] not in props and tokens[i + 1] != '('):
                return f"Syntax error: Unary operator '{token}' at position {i} is not followed by a valid operand."

        elif is_binary_operator(token):
            if (i == 0 or (tokens[i - 1] not in props and tokens[i - 1] != ')')) or (
                    i + 1 >= n or (tokens[i + 1] not in props and tokens[i + 1] != '(')):
                return f"Syntax error: Binary operator '{token}' at position {i} does not have valid operands on both sides."

        elif is_multi_form_operator(token):
            if i + 1 >= n or (tokens[i + 1] not in props and tokens[i + 1] != '('):
                return f"Syntax error: Multi-form operator '{token}' at position {i} is not followed by a valid operand."

        i += 1

    return 'correct'

def parse_string(input_str):
    lines = input_str.split('\n')
    natural_language = ""
    raw_ltl = ""

    for line in lines:
        if line.startswith("Natural language:"):
            natural_language = line.split(': ')[1]
        elif line.startswith("raw LTL:"):
            raw_ltl = line.split(': ')[1]

    props = extract_props(natural_language)
    tokens = raw_ltl.replace('(', ' ( ').replace(')', ' ) ').split()

    return natural_language, tokens, props, raw_ltl

def extract_props(natural_language):
    words = natural_language.split()
    props = [' '.join(words[i:i+2]) for i in range(len(words)-1)]
    props.extend(words)
    return set(props)

def correct_ltl_with_gpt(ltl, errors):
    prompt = f"""
    The following LTL formula has errors:
    {ltl}
    Errors detected:
    {errors}
    Please correct the LTL formula according to the detected errors as a professional LTL expert. Ensure the corrections follow the syntax rules of LTL. Please output without adding any text display symbols, such as (*#). Attention: Only pure LTL expression text is needed! Don't add the description like "The corrected LTL formula without syntax errors is:", Only output the LTL formula!!!
    """
    return gpt_transform(prompt)

def automate_web_interaction(ltl_3):
    url = 'https://spot.lre.epita.fr/app/'

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)

        time.sleep(10)

        input_element = driver.find_element(By.XPATH, '//input[@type="text" and @aria-invalid="false"]')
        input_element.clear()
        input_element.send_keys(ltl_3)

        input_element.send_keys(Keys.RETURN)

        time.sleep(5)

        hoa_element = driver.find_element(By.XPATH, '//span[text()="HOA"]')
        hoa_element.click()

        time.sleep(5)

        output_element = driver.find_element(By.XPATH, '//pre[@class="jss15"]')
        output_text = output_element.text
        print(f'Output: {output_text}')

    finally:
        driver.quit()
    
    extracted_hoa = extract_body_lines(output_text)
    print(extracted_hoa)
    
    # 调用第二段代码的功能来将HOA转换为BA格式
    ba_result = convert_hoa_to_ba_format(extracted_hoa)
    save_to_ba_file(ba_result)
    print("转换完成，结果已保存为 output.ba")
    print("转换结果：")
    print(ba_result)

def extract_body_lines(output):
    body_lines = []
    in_body = False
    
    for line in output.splitlines():
        stripped_line = line.strip()
        if stripped_line == '--BODY--':
            in_body = True
            continue
        elif stripped_line == '--END--':
            in_body = False
            continue
        if in_body:
            body_lines.append(stripped_line)
    
    extracted_hoa = "\n".join(body_lines)
    return extracted_hoa


# 第二段代码：HOA转换BA功能
def parse_condition(condition_str):
    condition_str = condition_str.strip()
    if condition_str == 't':
        return 'True'  
    literals = condition_str.split('&')
    literals = sorted(literal.strip() for literal in literals)
    return '&'.join(literals)


def convert_hoa_to_ba_format(hoa_input):
    """
    将HOA格式转换为BA格式。
    """
    lines = hoa_input.strip().split('\n')
    current_state = None
    accepting_states = set()
    transitions = []
    initial_state = None
    condition_to_input = {}
    input_index = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue  # 跳过空行
        if line.startswith("State:"):
            parts = line.split()
            # 提取状态编号，忽略其他部分
            current_state = int(parts[1])
            if len(parts) > 2 and '{' in parts[2]:
                accepting_states.add(current_state)
            if initial_state is None:
                initial_state = current_state
        elif '[' in line and ']' in line:
            condition_part, target_state_part = line.split(']')
            condition_raw = condition_part[1:]  # 去除开头的 '['
            target_state = int(target_state_part.split()[0])  # 只取状态编号，忽略其他内容
            condition = parse_condition(condition_raw)
            if condition not in condition_to_input:
                condition_to_input[condition] = f"a{input_index}"
                input_index += 1
            input_symbol = condition_to_input[condition]
            transitions.append(f"{input_symbol},[{current_state}]->[{target_state}]")

    # 生成BA格式的输出
    output_lines = []
    output_lines.append(f"[{initial_state}]")
    output_lines.extend(transitions)
    for state in accepting_states:
        output_lines.append(f"[{state}]")

    return '\n'.join(output_lines)


def save_to_ba_file(content, filename="d:/RA/RAwork/Experiment/Round1/output.ba"):
    """
    将内容保存为BA文件。
    """
    with open(filename, 'w') as file:
        file.write(content)


if __name__ == "__main__":
    # 运行主要逻辑
    ltl_3, raw_nl_2 = generate_and_print_ltl()
    automate_web_interaction(ltl_3)
