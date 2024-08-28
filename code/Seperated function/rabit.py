import os
import subprocess

# Define the root directory
root_dir = 'D:/RA/RAwork/Experiment/rabit250/'

# Define file paths
rabit_jar = os.path.join(root_dir, 'RABIT250/RABIT.jar')
input = os.path.join('d:/RA/RAwork/Experiment/rabit250/RABIT250/Examples/test1.ba')
comparison_automaton = os.path.join('d:/RA/RAwork/Experiment/rabit250/RABIT250/Examples/x1.ba')

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
else:
    print("The language of the first automaton is not included in the language of the second automaton.")
    # Extract and display details of non-inclusion
    for line in output.split('\n'):
        if "Counterexample" in line or "Reason" in line or "Not included" in line:
            print(line)
