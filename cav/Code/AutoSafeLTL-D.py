import requests
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import os
import subprocess

# Define the API URL and API key
api_url = "https://gpt-api.hkust-gz.edu.cn/v1/chat/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": "API Key"  # 请替换成你自己的API密钥
}

atomic_proposition_library = [
    "turn_left",             # 左转
    "turn_right",            # 右转
]

def gpt_transform(prompt, max_tokens=4000):
    data = {
        "model": "gpt-4-32k",
        "messages": [{"role": "user", "content": prompt}],
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
    """
    用栈来简单判断 LTL 中括号是否匹配
    """
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
    """
    调用 GPT 修正括号等语法错误
    """
    prompt_fix = f"""
    The following LTL formula has syntax errors, please correct it:
    {ltl_formula}
    You need to pay attention to the matching of parentheses. 
    Please output only a pure LTL expression, no extra text.
    """
    corrected_ltl = gpt_transform(prompt_fix)
    return corrected_ltl

def gpt_replace_AP(atomic_proposition_library,LTL1):
    prompt = (
        f"""
        Please match the following LTL's atomic propositions:{LTL1} to a pre-defined library of atomic propositions library: {atomic_proposition_library}. If any proposition is similar to one in the library, replace it with the library's proposition. Only modify the atomic propositions without making any changes to other parts, ensuring that the LTL and its semantics remain consistent with the original. Return the raw updated LTL.
        """
    )
    return gpt_transform(prompt)

def correct_ltl_formula(ltl_formula):
    """
    循环调用 correct_syntactic_errors 直到括号配对正确
    """
    while True:
        if check_syntactic_correctness(ltl_formula):
            break
        else:
            new_ltl = correct_syntactic_errors(ltl_formula)
            if new_ltl is None:
                print("Error correcting LTL formula")
                return None
            ltl_formula = new_ltl
            print(f"Syntactic correction: {ltl_formula}")
        print("-" * 50)
    return ltl_formula


def automate_web_interaction(ltl_formula):
    """
    访问 spot.lre.epita.fr，将 LTL 转为 HOA，然后转成 BA (output.ba)
    """
    url = 'https://spot.lre.epita.fr/app/'
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--incognito")  # 使用无痕模式，避免缓存干扰
    chrome_options.add_argument("--disable-application-cache")  # 禁用缓存

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # 打开页面
        driver.get(url)
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//input[@type="text" and @aria-invalid="false"]'))
        )

        # 定位输入框并清空
        input_element = driver.find_element(By.XPATH, '//input[@type="text" and @aria-invalid="false"]')
        input_element.clear()
        input_element.send_keys(ltl_formula)
        input_element.send_keys(Keys.RETURN)
        time.sleep(3)  # 等待页面响应

        # 查找 HOA 转换选项
        hoa_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//span[text()="HOA"]'))
        )
        hoa_element.click()
        time.sleep(2)

        # 获取转换结果
        output_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//pre[@class="jss15"]'))
        )
        output_text = output_element.text
        print(f'Output: {output_text}')

    except NoSuchElementException as e:
        print(f"元素未找到: {e}")
    except TimeoutException as e:
        print(f"操作超时: {e}")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        # 确保浏览器进程被完全关闭
        driver.quit()

    # 处理结果并保存
    
    ba_result = hoa_to_ba(output_text)
    save_to_ba_file(ba_result)
    print("转换完成，结果已保存为 output.ba")
    print("转换结果：")
    print(ba_result)


def parse_condition(condition_str):
    condition_str = condition_str.strip()
    if condition_str == 't':
        return 'True'
    literals = condition_str.split('&')
    literals = sorted(literal.strip() for literal in literals)
    return '&'.join(literals)

def hoa_to_ba(hoa_content):
    lines = hoa_content.strip().splitlines()

    # 初始化变量
    ap_table = []
    initial_state = None
    accepting_states = []
    transitions = []

    parsing_states = False
    acceptance_condition = None

    def parse_label(label):
        """解析标签，将其中的运算符和原子命题进行处理"""
        
        def process_condition(condition):
            """将原子命题转换为可读格式"""
            result = ""
            i = 0
            while i < len(condition):
                char = condition[i]
                if char.isdigit():  # 数字是 AP 表中的索引
                    result += ap_table[int(char)]  # 使用 AP 表中的原子命题
                elif char in "!&()":  # 运算符
                    result += char
                elif char == " ":
                    i += 1
                    continue
                else:
                    raise ValueError(f"Unexpected character in label: {char}")
                i += 1
            return result

        def split_conditions(expression, operator):
            """根据给定的运算符分割表达式，确保括号匹配"""
            parts = []
            depth = 0
            current = []
            for char in expression:
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                if char == operator and depth == 0:
                    parts.append("".join(current).strip())
                    current = []
                else:
                    current.append(char)
            parts.append("".join(current).strip())
            return parts

        # 检查是否是 | 运算符，并进行分割
        if "|" in label:  # 确保 | 两边有空格
            or_conditions = split_conditions(label, "|")
            parsed_conditions = [process_condition(cond.strip()) for cond in or_conditions]
            return parsed_conditions
        elif "&" in label:
            and_conditions = split_conditions(label, "&")
            return ["&".join([process_condition(cond.strip()) for cond in and_conditions])]
        else:
            return [process_condition(label)]

    for line in lines:
        line = line.strip()

        # 跳过空行或者无关的头部信息
        if not line or line.startswith("HOA") or line.startswith("--") or line.startswith("name"):
            continue

        # 解析状态数
        if line.startswith("States:"):
            total_states = int(line.split()[1])

        # 解析初始状态
        elif line.startswith("Start:"):
            initial_state = f"[{line.split()[1]}]"

        # 解析接受条件
        elif line.startswith("Acceptance:"):
            acceptance_condition = line.split()[1:]

        # 解析原子命题表
        elif line.startswith("AP:"):
            ap_table = line.split(" ")[2:]
            ap_table = [ap.strip('"') for ap in ap_table]  # 去掉引号

        # 开始解析状态定义和转换
        elif line.startswith("State:"):
            parsing_states = True
            # print('sadasdasdas',line)
            state_info = line.split()
            current_state = f"[{state_info[1]}]"
            # print('sssssssssss', "1 Inf(0)" in" ".join(acceptance_condition))
            # 检查状态是否是接受状态
            # print(state_info)
            if len(state_info) > 1 and "{0}" in state_info and "1 Inf(0)" in " ".join(acceptance_condition):
                # print('11111111',current_state)
                accepting_states.append(current_state)
              
            elif len(state_info) > 1 and "{1}" in state_info and "1 Inf(1)" in " ".join(acceptance_condition):
                accepting_states.append(current_state)
           
            elif len(state_info) > 1 and "&" in " ".join(acceptance_condition):
                import re
                numbers = re.findall(r'Inf\((\d+)\)', " ".join(acceptance_condition))
                numbers = [int(num) for num in numbers]
                # 已经拆分好的列表
                parts =state_info

                # 合并花括号中的内容
                result = []
                temp = ''
                for part in parts:
                    if part.startswith('{'):
                        # 如果部分内容以 `{` 开头，开始合并
                        temp += part
                    elif part.endswith('}'):
                        # 如果部分内容以 `}` 结尾，合并并结束
                        temp += ' ' + part if temp else part
                        result.append(temp)
                        temp = ''
                    elif temp:
                        # 如果已经在合并中，将当前部分添加到临时变量
                        temp += ' ' + part
                    else:
                        # 如果没有合并，将该部分直接添加
                        result.append(part)

                state_info_new = result[-1].replace("{", "").replace("}", "")
                arr_new = []
                for i in state_info_new:
                    if i != ' ':
                        arr_new.append(int(i))
                if set(arr_new).issubset(set(numbers)):
                    accepting_states.append(current_state)
         

        elif parsing_states and line.startswith("["):
            try:
                # 解析转移：标签和目标状态
                # print(line)
                if '{' in line:
                    state_info1 = line.split()
                    current_state1 = f"[{state_info1[-2]}]"
                    if len(state_info1) > 1 and "{0}" in state_info1 and "1 Inf(0)" in " ".join(acceptance_condition):
                        # print('niubi')
                        # print('11111111',current_state)
                        accepting_states.append(current_state1)
                        # print(current_state1)
                    elif len(state_info1) > 1 and "{1}" in state_info1 and "1 Inf(1)" in " ".join(acceptance_condition):
                        # print('11111111',current_state)
                        accepting_states.append(current_state)
                        # print(current_state1)
                import re
                if ' | ' in line:
                    line = re.sub(r'\s*\|\s*', '|', line)
                    # line = '[0|1|!2] 0'
                transition_parts = line.split()
                # print(transition_parts)
                label = transition_parts[0]
                destination = transition_parts[1]
                destination_state = f"[{destination}]"

                # 如果标签是 "[t]"，保留不变
                if label == "[t]":
                    transitions.append(f"t,{current_state}->{destination_state}")
                    if "0 t" in " ".join(acceptance_condition):
                        accepting_states.append(f"[{transition_parts[1]}]")
                else:
                    # 使用 AP 表进行标签转换
                    # print(label.strip("[]"))
                    readable_labels = parse_label(label.strip("[]"))  # 获取所有 OR 分隔的条件
                    # 将 OR 转换为单独的转移
                    for sub_label in readable_labels:
                        transitions.append(f"{sub_label},{current_state}->{destination_state}")

            except (IndexError, ValueError) as e:
                raise RuntimeError(f"Error processing transition '{line}': {e}")

    # 确保接受状态是唯一的
    accepting_states = list(set(accepting_states))

    # 如果没有指定初始状态，假设第一个状态为初始状态
    if not initial_state and transitions:
        initial_state = transitions[0].split(",")[1].split("->")[0]

    # 格式化 BA 内容
    ba_content = f"{initial_state}\n"
    ba_content += "\n".join(transitions) + "\n"
    ba_content += "\n".join(accepting_states) + "\n"

    return ba_content


def save_to_ba_file(content, filename="d:/RA/RAwork/Experiment/Round1/output.ba"):
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"文件已保存到 {filename}")
    except Exception as e:
        print(f"保存文件时出错: {e}")

# --------------------- RABIT 相关 -------------------------
root_dir = 'D:/RA/RAwork/Experiment/rabit250 - 副本/'
rabit_jar = os.path.join(root_dir, 'out/artifacts/rabit250____jar/rabit250 - 副本.jar')
input_ba_path = os.path.join('d:/RA/RAwork/Experiment/Round1/output.ba')
comparison_automaton = os.path.join('d:/RA/RAwork/Experiment/Round1/Baserule.ba')

def check_file_exists(file_path):
    if os.path.isfile(file_path):
        print(f"{file_path} exists.")
    else:
        print(f"{file_path} does not exist.")

check_file_exists(rabit_jar)
check_file_exists(input_ba_path)
check_file_exists(comparison_automaton)

print(f"RABIT.jar path: {rabit_jar}")
print(f"Input automaton path: {input_ba_path}")
print(f"Comparison automaton path: {comparison_automaton}")

rabit_command = [
    'java', '-jar', rabit_jar, input_ba_path, comparison_automaton, '-fastc'
]

def run_rabit_and_check_inclusion():
    """
    调用 RABIT 检查 Aut A 与 Aut B 的语言包含性
    """
    print("Checking language inclusion with RABIT...")
    rabit_process = subprocess.run(rabit_command, capture_output=True, text=True)
    output = rabit_process.stdout
    error_output = rabit_process.stderr

    print("RABIT tool output:")
    print(output)
    print("RABIT tool errors:")
    print(error_output)

    if "Included" in output:
        print("The language of the first automaton is included in the language of the second automaton.")
        return True, output
    else:
        print("The language of the first automaton is not included in the language of the second automaton.")
        return False, output

# ---------------- 新版 correct_input_with_gpt 函数 ----------------
def correct_input_with_gpt(input_LTL,input_text, comparison_text, checking_output):
    prompt = (
        f"""
        The language of the first automaton(transformed from the Input LTL) is not included in the language of the second automaton. Please modify the Input LTL to ensure it is included.
        Input LTL:{input_LTL}
        Input Automaton:{input_text}
        Comparison Automaton:{comparison_text}
        RABIT Output:{checking_output}
        To help you better complete the task, I will provide you with some information about the BA format: A BA file consists of three parts in the following order: the initial state, the transitions, and the accepting states (all in separate lines). If the initial state is omitted, the source state of the first transition is assumed to be the initial state. If the accepting states are omitted, it is assumed that all states are accepting. States are described by their names, which can be any string that does not contain any of the special characters “,” “-” “>”. A transition is of the form “label,source state→destination state.” The label can be any string not containing a special character. The following is the content of an example BA file:
            ```
            [1]
            a,[1]->[2]
            b,[2]->[1]
            c,[1]->[3]
            [2]
            [3]
            ```
        Next, I will provide some information about the counterexample. There are two methods to generate a counterexample:
        The first is a BFS depth-first algorithm. It follows the order of breadth-first search, returning the earliest and shortest string that causes the two automata to behave differently.
        At depth 0, the code checks single-symbol strings. If the two automata behave differently when processing a particular symbol, that symbol is considered the first string to cause a behavioral difference.At depth 1, the code checks strings composed of two symbols. If no differences are found at depth 0, it further examines strings of length 2. If a string of length 2 leads to different behavior, that string is the first one found.The process continues in this way, with the code checking longer strings as the depth increases, until it finds the first string that cannot be accepted by both automata. In this case, the counterexample could be a single string like a0 or a sequence such as a0a1a0.
        
        The second method is a Ramsey-based check, which examines whether the returned counterexample is in the form of a prefix(loop), and outputs a complete trace that shows non-inclusion.
        
        The RABIT output can provide some insights for making corrections. The line 'Aut A: # of Trans. X, # of States Y' indicates that the input automaton contains Y states and X state transitions. Similarly, 'Aut B: # of Trans. X, # of States Y' shows that the comparison automaton contains Y states and X state transitions. The line 'Aut A (after light preprocessing): # of Trans. X, # of States Y' represents the number of states Y and state transitions X in the input automaton after light preprocessing. The counterexample can provide some critical information. It represents the first "not included" instance found during depth-first search. The state transition path shows the sequence of state transitions that have occurred up to the point where the transition symbol was encountered. For example, 'S0_d:/RA -> S2_d:/RA' indicates a transition from state 0 to state 2 within the 'd:/RA' file. Since the two automata being compared have undergone light preprocessing, some state transition paths in the counterexample may differ slightly from those in the input automaton. You can understand them by logically reconstructing the transitions.
        
        Your task is to modify and simplify LTL to ensure that it satisfies the inclusion check while keeping the formula as concise and flexible as possible. Adjustments should focus on resolving the specific issues identified in the guidance rather than adding restrictive or overly complex conditions. Aim for an intuitive and streamlined solution that aligns LTL1 with the comparison Buchi automaton.

        Instructions:
        1)Modify LTL based on the provided countereample.
        2)Ensure the revised formula directly addresses the counterexample(s) while improving alignment with the comparison Buchi automaton.
        3)Avoid adding unnecessary constraints or increasing the formula's complexity—prioritize simplicity and precision.
        4)Must ensure that the original task is preserved as much as possible.
        
        Tips:
        1. The 't' in BA is a specially string, it't not a true alphabet string, but a signal of 'unconditional', so don't add anything about 't' to the LTL directly, instead you should think about its logic and change that.
        2. Don't add operators like '<', '>' and '=', which are not allowed by LTL's syntactic rules.
        
        Output Format:
        Provide only the raw corrected LTL formula without any additional information or explanation.
        """
    )
    
    corrected_ltl = gpt_transform(prompt)
    return corrected_ltl


if __name__ == "__main__":
    # 1) 先获取初始 LTL
    ltl_3 = 'G((goStraight & X(turnRight)) & X(F((goStraight & turnRight & X(reachDestination))))) | (goStraight & X(turnLeft) & X(F((goStraight & turnRight & X(reachDestination)))))'
    raw_nl_2 = 'Globally, either going straight is followed by turning right, and eventually going straight and turning right again leads to reaching the destination; or going straight is followed by turning left, and eventually going straight and turning right leads to reaching the destination.'
    atomic_proposition_library= [
    "turnRight",             # 左转
    "goStraight",            # 右转
    "turnLeft","reachDestination"         # 直行
]
    comparison_LTL='G((goStraight -> F(turnRight)) & (turnRight -> F(turnLeft)) & (turnLeft -> F(reachDestination)))'
    if not ltl_3:
        print("No LTL formula generated. Exiting.")
        exit(1)
    
    ltl_3=gpt_replace_AP(atomic_proposition_library,ltl_3)
    # 2) 初次转换 LTL -> BA
    automate_web_interaction(ltl_3)

    # 读入对比 BA (Aut B)
    with open(comparison_automaton, 'r') as f:
        autB_ba_text = f.read()

    current_ltl = ltl_3
    included = False
    iteration = 0

    while not included:
        iteration += 1
        print(f"\n***** Starting iteration {iteration} *****")

        # 3) RABIT 检查包含性
        included, rabit_output = run_rabit_and_check_inclusion()
        if included:
            break

        # 如果不包含，就需要 GPT 修正 LTL
        with open(input_ba_path, 'r') as f:
            autA_ba_text = f.read()  # Aut A 的 BA 文件（output.ba 的最新内容）

        # 调用新版 correct_input_with_gpt，提供(原始 LTL, Aut A BA, Aut B BA, RABIT输出)

        corrected_ltl = correct_input_with_gpt(current_ltl,
            autA_ba_text,
            autB_ba_text,
            rabit_output)
        if corrected_ltl is None:
            print("Failed to get a corrected LTL formula from GPT. Exiting.")
            break

        # 4) 语法校验
        corrected_ltl = correct_ltl_formula(corrected_ltl)
        if corrected_ltl is None:
            print("Failed to correct the LTL syntax. Exiting.")
            break

        print(f"[Iteration {iteration}] Corrected LTL by GPT:\n{corrected_ltl}")

        # 5) 再次转换
        automate_web_interaction(corrected_ltl)
        current_ltl = corrected_ltl

    if included:
        print("\nThe language of the first automaton is now included in the language of the second automaton after correction.")
    else:
        print("\nUnable to reach 'Included' status. Please check your GPT responses or logic.")
