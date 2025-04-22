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
rabit_jar = os.path.join(root_dir, 'rabit250 - new/rabit250 - new/out/artifacts/rabit250____jar/rabit250 - new.jar')
input_ba_path = os.path.join(root_dir, 'output.ba')
comparison_automaton = os.path.join(root_dir, 'Baserule.ba')
Outputfilename=os.path.join(root_dir, 'Output.ba')
benchmarkpath=os.path.join(root_dir, 'Dataset.xlsx')

# ------------------------- GPT API -----------------------------
api_url = "API url"
headers = {
    "Content-Type": "application/json",
    "Authorization": "API Key"  # Replace with your own key.
}

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

# ---------------------- Syntax check and correction -------------------------
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

# ---------------------- LTL generation and transformation ----------------------
def extract_ltl_expression(response_text):
    """
    Match and extract the content starting with "LTL Expression: ..." from the text returned by GPT
    """
    ltl_expression_pattern = re.compile(r"LTL Expression:\s*(\{[\s\S]*?\}|\s*G[\s\S]*?(?=Explanation|$))", re.DOTALL)
    match = ltl_expression_pattern.search(response_text)
    if match:
        ltl_expression = match.group(1).strip()
        return ltl_expression
    return None

def extract_location_info(response_text):
    location_info_pattern = re.compile(r"Location Information:\s*{[\s\S]*?}\s*(?=LTL Expression:)", re.DOTALL)
    match = location_info_pattern.search(response_text)
    if match:
        location_info = match.group()
        print("Location Information:")
        print(location_info)
    else:
        general_info_pattern = re.compile(r"([\s\S]*?)(?=LTL Expression:)", re.DOTALL)
        match = general_info_pattern.search(response_text)
        if match:
            general_info = match.group(1)
            print("Additional Information:")
            print(general_info)
        else:
            print("No relevant information found in the response.")

def generate_and_print_ltl():
    """
    Generate LTL formulas and perform upward and downward transformations.
    """
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
        
        Must obey the format! Please output in the given format without adding any text display symbols, such as (*#), only pure text content is needed. Please enclose the location information in {} and mention the key words "Location information".
        """
    )

    print("-" * 35 , 'Step 1: Generate LTL and context' ,"-" * 35 )
    ltl_1 = gpt_transform(ltl_prompt)
    if ltl_1 is None:
        print("Failed to generate LTL")
        return None, None

    print(ltl_1)
    print("-" * 50)
    ltl_expression = extract_ltl_expression(ltl_1)
    if ltl_expression is None:
        print("Failed to extract LTL expression")
        return None, None

    print("LTL Expression:")
    print(ltl_expression)

    # Step 2: LTL->NL
    print("-" * 35 , 'Step 2: LTL-1 to NL-1' ,"-" * 35 )
    prompt_1 = f"""
    Transform the following LTL formula into a natural language driving instruction as a professional LTL expert:
    {ltl_expression}
    Requirement: Please ensure that the original traffic instruction information is preserved as much as possible. Please output only the natural language parts; no additional content is needed.
    """
    raw_nl_1 = gpt_transform(prompt_1)
    if raw_nl_1 is None:
        print("Failed to transform LTL-1 to NL-1")
        return None, None
    print(raw_nl_1)

    # Step 3: NL->LTL
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
        return None, None
    print(f"LTL-2: {ltl_2}")

    # Step 4: Syntactic check
    print("-" * 35, 'Step 4: check LTL-2 correctness', "-" * 35)
    ltl_3 = correct_ltl_formula(ltl_2)
    if ltl_3 is None:
        print("Failed to correct LTL-2 syntax")
        return None, None
    print(f"LTL-2 is syntactically correct: {ltl_3}")

    # Step 5: LTL->NL
    print("-" * 35, 'Step 5: LTL-2 to NL-2', "-" * 35)
    prompt_3 = f"""Transform the following LTL formula into a natural language driving instruction as a professional LTL expert:
    {ltl_3}
    Requirement: Please ensure that the original traffic instruction information is preserved as much as possible. Please output only the natural language parts; no additional content is needed.
    """
    raw_nl_2 = gpt_transform(prompt_3)
    if raw_nl_2 is None:
        print("Failed to transform LTL-2 to NL-2")
        return None, None
    print(f"Raw NL-2: {raw_nl_2}")
    print("-" * 50)
    extract_location_info(ltl_1)

    # Step 6: NL->LTL
    print("-" * 35 , 'New LTL' ,"-" * 35 )
    prompt_4 = f"""
        Transform the following natural language driving instruction back into an LTL formula as a professional LTL expert:
        {raw_nl_2}
        LTL Expression Requirements: Include multiple nested "eventually" (F), "globally" (G), "next" (X), "implies"(->), "equivalent"(<->), "and"(&), "or"(|),"not"(!) operators. Logically represent the navigation sequence, ensuring the expression accurately reflects the instructions and conditions. Ensure that the movements of the vehicle are reflected in the LTL.pay attention to the matching relationships between the parentheses.
        Please output without adding any text display symbols, such as (*#), only pure LTL expression text is needed. Don't generate an overly long LTL, since LatencyInfo vector size 113 is too big.
        """
    ltl_final = gpt_transform(prompt_4)
    if ltl_final is None:
        print("Failed to transform NL-2 to LTL")
        return None, None
    print(f"LTL: {ltl_final}")

    return ltl_final, raw_nl_2

# --------------------- LTL -> HOA -> BA ----------------------
def automate_web_interaction(ltl_formula):
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

    try:
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
        print(f'Output: {output_text}')

    except NoSuchElementException as e:
        print(f"Element not found: {e}")
    except TimeoutException as e:
        print(f"Operation timed out: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:

        driver.quit()


    
    ba_result = hoa_to_ba(output_text)
    save_to_ba_file(ba_result,input_ba_path)
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

def gpt_replace_AP(atomic_proposition_library,LTL1):
    prompt = (
        f"""
        Please match the following LTL's atomic propositions:{LTL1} to a pre-defined library of atomic propositions library: {atomic_proposition_library}. If any proposition is similar to one in the library, replace it with the library's proposition. Only modify the atomic propositions without making any changes to other parts, ensuring that the LTL and its semantics remain consistent with the original. Return the raw updated LTL.
        """
    )
    return gpt_transform(prompt)

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
            ap_table = [ap.strip('"') for ap in ap_table]  

 
        elif line.startswith("State:"):
            parsing_states = True
            # print('sadasdasdas',line)
            state_info = line.split()
            current_state = f"[{state_info[1]}]"
            # print('sssssssssss', "1 Inf(0)" in" ".join(acceptance_condition))
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

                parts =state_info


                result = []
                temp = ''
                for part in parts:
                    if part.startswith('{'):

                        temp += part
                    elif part.endswith('}'):
      
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

                
                if label == "[t]":
                    transitions.append(f"t,{current_state}->{destination_state}")
                    if "0 t" in " ".join(acceptance_condition):
                        accepting_states.append(f"[{transition_parts[1]}]")
                else:
                    
                    # print(label.strip("[]"))
                    readable_labels = parse_label(label.strip("[]"))  
                    
                    for sub_label in readable_labels:
                        transitions.append(f"{sub_label},{current_state}->{destination_state}")

            except (IndexError, ValueError) as e:
                raise RuntimeError(f"Error processing transition '{line}': {e}")

    
    accepting_states = list(set(accepting_states))

    
    if not initial_state and transitions:
        initial_state = transitions[0].split(",")[1].split("->")[0]

    
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

# --------------------- RABIT  -------------------------
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


def AutoSafeLTL_Method(ltl_3, raw_nl_2):
    comparison_LTL='G((goStraight -> F(turnRight)) & (turnRight -> F(turnLeft)) & (turnLeft -> F(reachDestination)))'
    atomic_proposition_library = extract_atomic_propositions(comparison_LTL)

    if not ltl_3:
        print("No LTL formula generated. Exiting.")
        return False
    
    ltl_3=gpt_replace_AP(atomic_proposition_library,ltl_3)

    # 2) LTL -> BA
    automate_web_interaction(ltl_3)

    included = False
    iteration = 0

    while not included:
        iteration += 1
        print(f"\n***** Starting iteration {iteration} *****")

        # 3) RABIT 
        included, rabit_output = run_rabit_and_check_inclusion()

    if included:
        print("\nThe language of the first automaton is now included in the language of the second automaton after correction.")
    else:
        print(rabit_output)


# --------------------- Main -----------------------------
if __name__ == "__main__":

    ltl_3, raw_nl_2 = generate_and_print_ltl()
    AutoSafeLTL_Method(ltl_3, raw_nl_2)
    
    #for idx, (ltl_3, raw_nl_2) in enumerate(pd.read_excel(benchmarkpath).iloc[:50, [0,1]].values, 1):
        #print(f" Processing Pair {idx}/50 ".center(80, "-"))
        #AutoSafeLTL_Method(ltl_3, raw_nl_2) 
        #print("\n" + "-"*80)
