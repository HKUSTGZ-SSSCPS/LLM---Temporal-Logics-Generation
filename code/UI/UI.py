import tkinter as tk
from tkinter import scrolledtext
import requests
import json
import re
from PIL import Image, ImageTk

# Define the API URL and API key
api_url = "https://wei587.top/v1/chat/completions"
api_key = "sk-wr8T9pMCuJheCyT8F94a6dBbDbD74e26A62908C7545fD4Dd"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

ltl_1_global = ""

def gpt_transform(prompt, max_tokens=10000):
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "system", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    response = requests.post(api_url, headers=headers, data=json.dumps(data))
    response_json = response.json()
    return response_json['choices'][0]['message']['content'].strip()


def extract_ltl_expression(response_text):
    ltl_expression_pattern = re.compile(r"LTL Expression:\s*(\{[\s\S]*?\}|\s*G[\s\S]*?(?=Explanation|$))", re.DOTALL)
    match = ltl_expression_pattern.search(response_text)
    if match:
        ltl_expression = match.group(1)
        return ltl_expression.strip()
    return None


def correct_ltl_formula(ltl_expression):
    # Placeholder for LTL formula correction logic
    return ltl_expression  # For now, returning the input as is


def generate_location_info():
    if ltl_1_global:
        location_info = extract_location_info(ltl_1_global)
        Location_textbox.delete(1.0, tk.END)
        Location_textbox.insert(tk.END, location_info)

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
        return location_info
    else:
        # 如果没有找到 "Location Information"，提取 "LTL Expression" 之前的所有信息
        general_info_pattern = re.compile(
            r"([\s\S]*?)(?=LTL Expression:)",
            re.DOTALL
        )
        match = general_info_pattern.search(response_text)
        if match:
            general_info = match.group(1)
            return general_info
        else:
            return "No relevant information found in the response."

def generate_and_display_ltl():
    global ltl_1_global

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
    ltl_1 = gpt_transform(ltl_prompt)
    ltl_1_global = ltl_1  # 保存 ltl_1 到全局变量

    ltl_expression = extract_ltl_expression(ltl_1)

    prompt_1 = f"""
    Transform the following LTL formula into a natural language driving instruction as a professional LTL expert:
    {ltl_expression}
    Requirement: Please ensure that the original traffic instruction information is preserved as much as possible. Please output only the natural language parts; no additional content is needed.
    """
    raw_nl_1 = gpt_transform(prompt_1)

    prompt_2 = f"""
        Transform the following natural language driving instruction back into an LTL formula as a professional LTL expert:
        {raw_nl_1}
        LTL Expression Requirements: Include multiple nested "eventually" (F), "globally" (G), "next" (X), "implies"(->), "equivalent"(<->), "and"(&), "or"(|),"not"(!) operators. Logically represent the navigation sequence, ensuring the expression accurately reflects the instructions and conditions. Ensure that the movements of the vehicle are reflected in the LTL.pay attention to the matching relationships between the parentheses.
        Please output without adding any text display symbols, such as (*#), only pure LTL expression text is needed. Don't generate an overly long LTL, since LatencyInfo vector size 113 is too big.
        """
    ltl_2 = gpt_transform(prompt_2)

    corrected_ltl = correct_ltl_formula(ltl_2)

    # Step 5: GPT-3将LTL-2转换为原始自然语言描述NL-2
    prompt_3 = f"""Transform the following LTL formula into a natural language driving instruction as a professional LTL expert:
    {ltl_2}
    Requirement: Please ensure that the original traffic instruction information is preserved as much as possible. Please output only the natural language parts; no additional content is needed.
    """
    raw_nl_2 = gpt_transform(prompt_3)

    output_textbox.delete(1.0, tk.END)
    output_textbox.insert(tk.END, raw_nl_2)

def generate_ltl():
    global ltl_2_global
    # 获取 input_textbox 和 output_textbox 中的内容
    input_text = input_textbox.get(1.0, tk.END).strip()
    output_text = output_textbox.get(1.0, tk.END).strip()

    # 判断哪个文本框有内容
    if input_text:
        raw_nl = input_text
    elif output_text:
        raw_nl = output_text
    else:
        raw_nl = ""  # 如果两个文本框都是空的，不做处理

    if raw_nl:
        # 调用 generate_LTL2 函数并将结果显示在 LTL_textbox 中
        ltl_2 = generate_LTL2(raw_nl)
        ltl_2_global = ltl_2  # 保存 ltl_2 到全局变量
        LTL_textbox.delete(1.0, tk.END)
        LTL_textbox.insert(tk.END, ltl_2)

def generate_LTL2(raw_nl):
    prompt_2 = f"""
        Transform the following natural language driving instruction back into an LTL formula as a professional LTL expert:
        {raw_nl}
        LTL Expression Requirements: Include multiple nested "eventually" (F), "globally" (G), "next" (X), "implies"(->), "equivalent"(<->), "and"(&), "or"(|),"not"(!) operators. Logically represent the navigation sequence, ensuring the expression accurately reflects the instructions and conditions. Ensure that the movements of the vehicle are reflected in the LTL.pay attention to the matching relationships between the parentheses.
        Please output without adding any text display symbols, such as (*#), only pure LTL expression text is needed. Don't generate an overly long LTL, since LatencyInfo vector size 113 is too big.
        """
    ltl_2 = gpt_transform(prompt_2)
    return ltl_2

def check_safety():
    if ltl_2_global:
        is_correct = check_syntactic_correctness(ltl_2_global)
        syntax_textbox.delete(1.0, tk.END)
        if is_correct:
            syntax_textbox.insert(tk.END, "syntactically correct")
        else:
            syntax_textbox.insert(tk.END, "Syntax Error: Unmatched parentheses")

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

def resize_background(event=None):
    new_width = root.winfo_width()
    new_height = root.winfo_height()

    resized_image = original_image.resize((new_width, new_height), Image.ANTIALIAS)
    background_photo = ImageTk.PhotoImage(resized_image)

    canvas.create_image(0, 0, image=background_photo, anchor="nw")
    canvas.image = background_photo  # Prevent garbage collection


def minimize_window():
    root.iconify()


def toggle_fullscreen():
    global is_fullscreen
    is_fullscreen = not is_fullscreen
    root.attributes("-fullscreen", is_fullscreen)


def quit_app():
    root.destroy()


# Create the main window
root = tk.Tk()
root.title("LTL checker")
root.geometry("1200x800")


# Load the background image
original_image = Image.open("C:/Users/dell/Desktop/11.png")

# Create a canvas
canvas = tk.Canvas(root)
canvas.pack(fill="both", expand=True)

# Bind the canvas to the window resize event
canvas.bind("<Configure>", resize_background)

# Set the initial background
resize_background()

# Input Label and Textbox
input_label = tk.Label(root, text="输入导航语言：", bg="#f0f0f0", font=("Helvetica", 12))
input_label.place(x=30, y=50)
input_textbox = tk.Text(root, wrap=tk.WORD, width=40, height=3, font=("Helvetica", 12))
input_textbox.place(x=150, y=50)

# Output Label and Textbox
output_label = tk.Label(root, text="生成导航语言：", bg="#f0f0f0", font=("Helvetica", 12))
output_label.place(x=580, y=50)
output_textbox = tk.Text(root, wrap=tk.WORD, width=40, height=3, font=("Helvetica", 12))
output_textbox.place(x=700, y=50)

# Generate Button
generate_button = tk.Button(root, text="生成", command=generate_and_display_ltl, bg="#D5E6E8",fg="#000000",
                            font=("微软雅黑", 11),relief="raised",bd=2)
generate_button.place(x=1100, y=50, width=80, height=30)

# Generate LTL Button
LTL_textbox = tk.Text(root, wrap=tk.WORD, width=100, height=3, font=("Helvetica", 12))
LTL_textbox.place(x=40, y=160)
generate_ltl_button = tk.Button(root, text="生成LTL", command=generate_ltl, bg="#D5E6E8",fg="#000000",
                            font=("微软雅黑", 11),relief="raised",bd=2)
generate_ltl_button.place(x=1000, y=160, width=80, height=30)

# Generate Location Info Button
Location_textbox = tk.Text(root, wrap=tk.WORD, width=100, height=5, font=("Helvetica", 12))
Location_textbox.place(x=40, y=250)
generate_location_button = tk.Button(root, text="生成位置信息", command=generate_location_info, bg="#D5E6E8",fg="#000000",
                            font=("微软雅黑", 11),relief="raised",bd=2)
generate_location_button.place(x=1000, y=250, width=100, height=30)

# Syntax Check Result Label and Textbox
syntax_label = tk.Label(root, text="语法正确性检测结果：", bg="#f0f0f0", font=("Helvetica", 12))
syntax_label.place(x=50, y=380)
syntax_textbox = tk.Text(root, wrap=tk.WORD, width=50, height=10, font=("Helvetica", 12))
syntax_textbox.place(x=50, y=420)

# Semantic Check Result Label and Textbox
semantic_label = tk.Label(root, text="语义正确性检测结果:", bg="#f0f0f0", font=("Helvetica", 12))
semantic_label.place(x=600, y=380)
semantic_textbox = tk.Text(root, wrap=tk.WORD, width=50, height=10, font=("Helvetica", 12))
semantic_textbox.place(x=600, y=420)

# Safety Check Button
safety_check_button = tk.Button(root, text="安全性检测", command=check_safety, bg="#D5E6E8",fg="#000000",
                            font=("微软雅黑", 11),relief="raised",bd=2)
safety_check_button.place(x=1100, y=380, width=90, height=30)

# Feedback and Correct Button
feedback_button = tk.Button(root, text="反馈及修正", command=generate_and_display_ltl, bg="#D5E6E8",fg="#000000",
                            font=("微软雅黑", 11),relief="raised",bd=2)
feedback_button.place(x=1100, y=490, width=90, height=30)

root.mainloop()