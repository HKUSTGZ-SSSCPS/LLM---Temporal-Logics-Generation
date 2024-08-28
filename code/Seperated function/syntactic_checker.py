import NL_Generate
import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time


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
    return NL_Generate.gpt_transform(prompt)

def automate_web_interaction(ltl_3):
    url = 'https://spot.lre.epita.fr/app/'

    # 初始化Chrome浏览器，无头模式
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # 打开网页
        driver.get(url)

        # 等待页面加载
        time.sleep(10)  # 增加等待时间以确保页面完全加载

        # 查找输入框元素并输入内容
        input_element = driver.find_element(By.XPATH, '//input[@type="text" and @aria-invalid="false"]')
        input_element.clear()  # 清空输入框
        input_element.send_keys(ltl_3)

        # 模拟回车
        input_element.send_keys(Keys.RETURN)

        # 等待操作完成
        time.sleep(10)  # 增加等待时间以确保操作完成

        # 查找“HOA”元素并点击
        hoa_element = driver.find_element(By.XPATH, '//span[text()="HOA"]')
        hoa_element.click()

        # 等待操作完成
        time.sleep(5)  # 增加等待时间以确保结果显示

        # 获取操作后的输出内容
        output_element = driver.find_element(By.XPATH, '//pre[@class="jss15"]')
        output_text = output_element.text
        print(f'Output: {output_text}')

    finally:
        # 关闭浏览器
        driver.quit()
    
    BODY=extract_body_lines(output_text)
    print(extract_body_lines(output_text))

def extract_body_lines(output):
    body_lines = []
    in_body = False
    
    for line in output.splitlines():
        if line.strip() == '--BODY--':
            in_body = not in_body
            continue
        if in_body:
            body_lines.append(line)
    
    return body_lines
    

def main():
    ltl_3, raw_nl_2 = NL_Generate.generate_and_print_ltl()

    while True:
        input_str = f"Natural language: {raw_nl_2}\nraw LTL: {ltl_3}"
        natural_language, tokens, props, raw_ltl = parse_string(input_str)

        parentheses_check_result = check_parentheses(ltl_3)
        #operators_check_result = check_operators(tokens, props)

        errors = []
        if parentheses_check_result != 'correct':
            errors.append(parentheses_check_result)
        #if operators_check_result != 'correct':
           # errors.append(operators_check_result)

        if errors:
            print('Errors detected:')
            for error in errors:
                print(error)

            ltl_3 = correct_ltl_with_gpt(ltl_3, "\n".join(errors))
            print(f"Corrected LTL: {ltl_3}")
        else:
            print('The formula is syntactically correct.')
            print(ltl_3)
            break

    automate_web_interaction(ltl_3)


if __name__ == "__main__":
    main()
