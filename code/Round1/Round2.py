import os
import subprocess
import requests
import json
import re

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


# Define the root directory
root_dir = 'D:/RA/RAwork/Experiment/rabit250 - 副本/'

# Define file paths
rabit_jar = os.path.join(root_dir, 'out/artifacts/rabit250____jar/rabit250 - 副本.jar')
input = os.path.join('d:/RA/RAwork/Experiment/Round1/output.ba')
comparison_automaton = os.path.join('d:/RA/RAwork/Experiment/Round1/Baserule.ba')

# Check if files exist
def check_file_exists(file_path):
    if os.path.isfile(file_path):
        print(f"{file_path} exists.")
    else:
        print(f"{file_path} does not exist.")

check_file_exists(rabit_jar)
check_file_exists(input)
check_file_exists(comparison_automaton)

# Print file paths for debugging
print(f"RABIT.jar path: {rabit_jar}")
print(f"Input automaton path: {input}")
print(f"Comparison automaton path: {comparison_automaton}")

# Define RABIT command with verbose output
rabit_command = [
    'java', '-jar', rabit_jar, input, comparison_automaton, '-fastc'
]

def run_rabit_and_check_inclusion():
    # Run RABIT tool
    print("Checking language inclusion...")
    rabit_process = subprocess.run(rabit_command, capture_output=True, text=True)
    output = rabit_process.stdout
    error_output = rabit_process.stderr

    print("RABIT tool output:")
    print(output)
    print("RABIT tool errors:")
    print(error_output)

    # Analyze the output to determine incompatibility
    if "Included" in output:
        print("The language of the first automaton is included in the language of the second automaton.")
        return True, output
    else:
        print("The language of the first automaton is not included in the language of the second automaton.")
        return False, output

def correct_input_with_gpt(input_text, comparison_text, checking_output):
    prompt = (
        f"""
        The language of the first automaton is not included in the language of the second automaton. Please modify the input automaton to ensure it is included.
        Input Automaton:\n{input_text}
        Comparison Automaton:\n{comparison_text}
        RABIT Output:\n{checking_output}
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
        
        You can make corrections by pruning or adding state transitions.
        You need to provide the corrected Input Automaton (!Attenton:Only output the pure BA file without adding any extra information or description.).
        !!Must obey: Don't add '```'!!!
        """
    )
    
    corrected_input = gpt_transform(prompt)
    if corrected_input:
        with open(input, 'w') as f:
            f.write(corrected_input)
        print("Input automaton has been corrected by GPT.")
    else:
        print("Failed to get a corrected input from GPT.")

# Read input and comparison automaton files
with open(input, 'r') as f:
    input_content = f.read()
with open(comparison_automaton, 'r') as f:
    comparison_content = f.read()

# Loop until the inclusion check passes
included = False
iteration = 0

while not included:
    print(f"Starting iteration {iteration + 1}...")
    included, output = run_rabit_and_check_inclusion()
    
    if not included:
        correct_input_with_gpt(input_content, comparison_content, output)
        
        # Read the corrected input for the next iteration
        with open(input, 'r') as f:
            input_content = f.read()
    
    iteration += 1

print("The language of the first automaton is now included in the language of the second automaton after correction.")
