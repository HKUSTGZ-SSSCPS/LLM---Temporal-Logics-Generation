import os
import subprocess
import requests
import json
import re

# Define the API URL and API key
api_url = "https://wei587.top/v1/chat/completions"
api_key = "sk-YhNHEPiFlUB8WjmsA8E9D0C3F58e4d80B6CdE9734d88D50b"

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


# Define the root directory
root_dir = 'D:/RA/RAwork/Experiment/rabit250/'

# Define file paths
rabit_jar = os.path.join(root_dir, 'RABIT250/RABIT.jar')
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
        Provide the corrected Input Automaton (Only output the pure BA file without adding any extra information or description).
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
