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
import pandas as pd

# ------------------------- FILE PATH -----------------------------
root_dir = 'local path'
rabit_jar = os.path.join(root_dir, 'rabit250-new/rabit250 - new/out/artifacts/rabit250____jar/rabit250 - new.jar')
input_ba_path = os.path.join(root_dir, 'output.ba')
comparison_automaton = os.path.join(root_dir, 'Code/Baserule.ba')
Outputfilename=os.path.join(root_dir, 'Output.ba')
benchmarkpath=os.path.join(root_dir, 'Dataset/nl2spec_Dataset-1.xlsx')
# ------------------------- GPT API -----------------------------
api_url = "API url"
headers = {
    "Content-Type": "application/json",
    "Authorization": "API Key"  # Replace with your own key.
}


# atomic_proposition_library = [
#     "turn_left",
#     "turn_right",
# ]

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
    Use a stack to check whether brackets match in LTL.
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
    Call GPT to correct bracket and other syntax errors.
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
    Loop to call correct_syntactic_errors until brackets are correctly matched.
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

        driver.get(url)
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//input[@type="text" and @aria-invalid="false"]'))
        )


        input_element = driver.find_element(By.XPATH, '//input[@type="text" and @aria-invalid="false"]')
        input_element.clear()
        input_element.send_keys(ltl_formula)
        input_element.send_keys(Keys.RETURN)
        time.sleep(3)

        # find HOA translate option
        hoa_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//span[text()="HOA"]'))
        )
        hoa_element.click()
        time.sleep(2)

        # get the translate result
        output_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//pre[@class="jss15"]'))
        )
        output_text = output_element.text
        print(f'Output: {output_text}')

    except NoSuchElementException as e:
        print(f"Element not found: {e}")
    except TimeoutException as e:
        print(f"Operation timed out: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

    # save result
    ba_result = hoa_to_ba(output_text)
    save_to_ba_file(ba_result, input_ba_path)
    print("The conversion is complete, and the result has been saved as output.ba")
    print("Conversion result:")
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

    # Initialize variable
    ap_table = []
    initial_state = None
    accepting_states = []
    transitions = []

    parsing_states = False
    acceptance_condition = None

    def parse_label(label):
        """Parse the label and process the operators and atomic propositions within it."""
        
        def process_condition(condition):
            """Convert the atomic propositions into a readable format."""
            result = ""
            i = 0
            while i < len(condition):
                char = condition[i]
                if char.isdigit():
                    result += ap_table[int(char)]
                elif char in "!&()":
                    result += char
                elif char == " ":
                    i += 1
                    continue
                else:
                    raise ValueError(f"Unexpected character in label: {char}")
                i += 1
            return result

        def split_conditions(expression, operator):
            """Split the expression based on the given operators, ensuring the brackets are matched."""
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


        if "|" in label:
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

        # Skip blank lines or irrelevant header information
        if not line or line.startswith("HOA") or line.startswith("--") or line.startswith("name"):
            continue

        if line.startswith("States:"):
            total_states = int(line.split()[1])


        elif line.startswith("Start:"):
            initial_state = f"[{line.split()[1]}]"


        elif line.startswith("Acceptance:"):
            acceptance_condition = line.split()[1:]


        elif line.startswith("AP:"):
            ap_table = line.split(" ")[2:]
            ap_table = [ap.strip('"') for ap in ap_table]   #Remove the quotation marks


        elif line.startswith("State:"):
            parsing_states = True
            # print('sadasdasdas',line)
            state_info = line.split()
            current_state = f"[{state_info[1]}]"
            # print('sssssssssss', "1 Inf(0)" in" ".join(acceptance_condition))
            if len(state_info) > 1 and "{0}" in state_info and "1 Inf(0)" in " ".join(acceptance_condition):
                # print('11111111',current_state)
                accepting_states.append(current_state)
              
            elif len(state_info) > 1 and "{1}" in state_info and "1 Inf(1)" in " ".join(acceptance_condition):
                accepting_states.append(current_state)
           
            elif len(state_info) > 1 and "&" in " ".join(acceptance_condition):
                import re
                numbers = re.findall(r'Inf\((\d+)\)', " ".join(acceptance_condition))
                numbers = [int(num) for num in numbers]

                parts =state_info

                # Merge the contents within the curly braces
                result = []
                temp = ''
                for part in parts:
                    if part.startswith('{'):
                        # If some parts start with '{', begin merging
                        temp += part
                    elif part.endswith('}'):
                        # If some parts end with '}', end merging
                        temp += ' ' + part if temp else part
                        result.append(temp)
                        temp = ''
                    elif temp:
                        temp += ' ' + part
                    else:
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
                # Parsing transition: Labels and target states
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

                #  If the label is "[t]", keep it unchanged
                if label == "[t]":
                    transitions.append(f"t,{current_state}->{destination_state}")
                    if "0 t" in " ".join(acceptance_condition):
                        accepting_states.append(f"[{transition_parts[1]}]")
                else:
                    # Use the AP table for label conversion
                    # print(label.strip("[]"))
                    readable_labels = parse_label(label.strip("[]"))
                    # Convert "OR" to a separate transfer
                    for sub_label in readable_labels:
                        transitions.append(f"{sub_label},{current_state}->{destination_state}")

            except (IndexError, ValueError) as e:
                raise RuntimeError(f"Error processing transition '{line}': {e}")

    # Ensure that the acceptance status is unique
    accepting_states = list(set(accepting_states))

    # If no initial state is specified, assume that the first state is the initial state
    if not initial_state and transitions:
        initial_state = transitions[0].split(",")[1].split("->")[0]

    # Format the BA content
    ba_content = f"{initial_state}\n"
    ba_content += "\n".join(transitions) + "\n"
    ba_content += "\n".join(accepting_states) + "\n"

    return ba_content

def save_to_ba_file(content, input_ba_path):
    try:
        with open(input_ba_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"The file has been saved to {input_ba_path}")
    except Exception as e:
        print(f"Error occurred while saving the file: {e}")

# --------------------- RABIT 相关 -------------------------

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

def gpt_understand_rabit_output(LTL1,input_BA, comparison_BA, checking_output,Comparison_LTL):
    prompt = (
        f"""
Task: Refine LTL Formula Using RABIT Tool Output

Analyze the RABIT tool output to identify counterexamples and propose flexible changes to LTL1, ensuring the language of `input_BA` is a subset of `comparison_BA`. You need to work as a expertise professor in LTL.

Inputs:
- LTL1_Formula: {LTL1}
- Comparison_LTL: {Comparison_LTL}
- Input_BA: {input_BA}
- Comparison_BA: {comparison_BA}
- RABIT_Output: {checking_output}

Steps:
1. Analyze Counterexamples: For each counterexample, explain why it’s accepted by `input_BA`(transformed from LTL1) but rejected by `comparison_BA`(transformed from comparison_LTL), and identify the issue in LTL1 causing the discrepancy.
2. Diagnose LTL1 Issues: Identify problematic parts of LTL1 (e.g., transitions, constraints, temporal logic) and their interaction with states and transitions in both automata.
3. Propose Adjustments: Suggest minimal but flexible changes to LTL1 to resolve issues, keeping the formula simple and avoiding unnecessary complexity. Provide guidance for correction but not a concrete LTL formula.
4. Ensure Alignment: Confirm that proposed changes address all counterexamples and improve LTL1’s compatibility with `comparison_BA`.

Output: 
1. Counterexample_Analysis: "Sequence": "counterexample_sequence", "Reason": "why accepted by input_BA but rejected by comparison_BA", "Issue_in_LTL1": "issue in LTL1"
2. Proposed_Adjustments: "Adjustment": "change to LTL1", "Justification": "how it resolves the discrepancy"
3. General_Guidance: "Summary of the approach and its broader impact"

        """
    )
    return gpt_transform(prompt)

def gpt_correct_ltl(LTL1, understanding_output):
    prompt = (
        f"""
        The current LTL1:
        {LTL1}
        does not satisfy the inclusion check based on the Buchi automaton comparison. Below is the analysis and revision guidance:
        {understanding_output}

        Your task is to modify and simplify LTL1 to ensure that it satisfies the inclusion check while keeping the formula as concise and flexible as possible. Adjustments should focus on resolving the specific issues identified in the guidance rather than adding restrictive or overly complex conditions. Aim for an intuitive and streamlined solution that aligns LTL1 with the comparison Buchi automaton.

        Instructions:
        1)Modify LTL1 based on the provided analysis.
        2)Ensure the revised formula directly addresses the counterexample(s) while improving alignment with the comparison Buchi automaton.
        3)Avoid adding unnecessary constraints or increasing the formula's complexity—prioritize simplicity and precision.
        4)Must ensure that the original task is preserved as much as possible.
        
        Output Format:
        Provide only the corrected LTL1 formula without any additional information or explanation.
        """
    )
    
    corrected_ltl = gpt_transform(prompt)
    return corrected_ltl


def extract_atomic_propositions(ltl_formula):
    url = 'https://spot.lre.epita.fr/app/'
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-application-cache")

    driver = webdriver.Chrome(options=chrome_options)

    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//input[@type="text" and @aria-invalid="false"]'))
    )

    input_element = driver.find_element(By.XPATH, '//input[@type="text" and @aria-invalid="false"]')
    input_element.clear()
    input_element.send_keys(ltl_formula)
    input_element.send_keys(Keys.RETURN)
    time.sleep(3)

    hoa_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//span[text()="HOA"]'))
    )
    hoa_element.click()
    time.sleep(2)

    output_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//pre[@class="jss15"]'))
    )
    output_text = output_element.text

    driver.quit()

    ap_match = re.search(r'AP:\s+\d+\s+((?:"[^"]*"\s*)+)', output_text)

    if not ap_match:
        print("AP section not found.")
        return []

    atomic_propositions = ap_match.group(1).split('" "')

    atomic_propositions = [prop.replace('"', '').strip() for prop in atomic_propositions]

    return atomic_propositions

def nl2spec_method(ltl_3,raw_nl_2):

    comparison_LTL = 'G((goStraight -> F(turnRight)) & (turnRight -> F(turnLeft)) & (turnLeft -> F(reachDestination)))'
    atomic_proposition_library = extract_atomic_propositions(comparison_LTL)

    if not ltl_3:
        print("No LTL formula generated. Exiting.")
        exit(1)

    ltl_3 = gpt_replace_AP(atomic_proposition_library, ltl_3)
    # 2) LTL -> BA
    automate_web_interaction(ltl_3)

    with open(comparison_automaton, 'r') as f:
        autB_ba_text = f.read()

    current_ltl = ltl_3
    included = False
    iteration = 0

    while not included:
        iteration += 1
        print(f"\n***** Starting iteration {iteration} *****")

        # 3) RABIT
        included, rabit_output = run_rabit_and_check_inclusion()
        if included:
            break

        with open(input_ba_path, 'r') as f:
            autA_ba_text = f.read()

        # correct_input_with_gpt
        understanding_output = gpt_understand_rabit_output(current_ltl,
                                                           autA_ba_text,
                                                           autB_ba_text,
                                                           rabit_output,
                                                           comparison_LTL)
        print(f"[Iteration {iteration}] Understanding output by GPT:\n{understanding_output}")
        corrected_ltl = gpt_correct_ltl(current_ltl, understanding_output)
        if corrected_ltl is None:
            print("Failed to get a corrected LTL formula from GPT. Exiting.")
            break

        # 4) syntactic check
        corrected_ltl = correct_ltl_formula(corrected_ltl)
        if corrected_ltl is None:
            print("Failed to correct the LTL syntax. Exiting.")
            break

        print(f"[Iteration {iteration}] Corrected LTL by GPT:\n{corrected_ltl}")

        # 5) ltl2BA
        automate_web_interaction(corrected_ltl)
        current_ltl = corrected_ltl

    if included:
        print(
            "\nThe language of the first automaton is now included in the language of the second automaton after correction.")
    else:
        print("\nUnable to reach 'Included' status. Please check your GPT responses or logic.")

def demo_mode_nl2spec():
    ltl_3 = 'G(((straight -> F(right)) & F(right) & (straight & F(left)) & (right -> F(left)) & (left -> F(destination)) & X((straight & F(destination)))))'
    raw_nl_2 = 'The system must always ensure that if it goes straight, it will eventually turn right; turning right must eventually happen, as well as going straight and turning left; if it turns right, it must eventually turn left, and if it turns left, it must eventually reach the destination; given these conditions, in the next step, it must go straight and eventually reach the destination.'
    nl2spec_method(ltl_3, raw_nl_2)

def full_mode_nl2spec():

    for idx, (raw_nl_2, ltl_3) in enumerate(pd.read_excel(benchmarkpath).iloc[:50, [1, 2]].values, 1):
        print(f" Processing Pair {idx}/50 ".center(80, "-"))
        if pd.isna(ltl_3):
            continue
        nl2spec_method(ltl_3, raw_nl_2)
        print("\n" + "-"*80)

if __name__ == "__main__":

    #Demo mode
    demo_mode_nl2spec()

    #Full mode
    full_mode_nl2spec()



