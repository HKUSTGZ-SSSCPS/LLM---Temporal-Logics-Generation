from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time


url = 'https://spot.lre.epita.fr/app/'

def automate_web_interaction():
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
        input = 'F blue_room ∧ F yellow_room'
        input_element.clear()  # 清空输入框
        input_element.send_keys(input)

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

if __name__ == "__main__":
    automate_web_interaction()
