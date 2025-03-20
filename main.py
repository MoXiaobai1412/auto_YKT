import requests
import base64
import os
import json
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By



url = 'https://changjiang.yuketang.cn'
global driver,API_KEY, timeSkip, model, driverType
def initConfig():
    global API_KEY, timeSkip, model, driverType

    with open("config.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        API_KEY = data["API_KEY"]
        if API_KEY == "":
            print("bot:未添加API_KEY，请前往config.json添加。")

        timeSkip = data["timeSkip"]

        model = data["model"]
        if model == "":
            print("bot:未设置模型，请前往config.json添加。")
        driverType = data["driverType"]
        if driverType == "":
            print("bot:未设置驱动类型，请前往config.json设置。")
    print("bot:当前配置如下\nAPI:" + API_KEY + "\n检测间隔:" + str(timeSkip) + "\n大模型:" + model + "\n浏览器驱动："+driverType)
    return 0
API_URL = "https://api.siliconflow.cn/v1/chat/completions"  # 根据文档确认接口地址

def solve_question():
    print("正在执行做题任务")
    # 构造带data URL的base64图片
    with open("screen-shot.png", "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")
        image_url = f"data:image/png;base64,{base64_image}"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "请仔细解答图片中的题目并给出最终答案，只给出答案即可，如果是单选则只给出一个字母，多选题则连续给出多个字母（中间不加标点），选择题则给出T或F。注意，结尾也不要加标点"},
                {
                    "type": "image_url",  # 修改为image_url类型
                    "image_url": {"url": image_url}  # 符合接口要求的嵌套结构
                }
            ]
        }],
        "temperature": 0.5
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        os.remove("screen-shot.png")
        print("bot:这题我选择了"+response.json()['choices'][0]['message']['content'])
        return response.json()['choices'][0]['message']['content']
    else:
        print(f"bot:请求失败（{response.status_code}）:", response.text)
        return 0


def getCookies():
    global driverType, driver
    if driverType == "Edge":
        driver = webdriver.Edge()
    elif driverType == "Firefox":
        driver = webdriver.Firefox()
    elif driverType == "Chrome":
        driver = webdriver.Chrome()
    elif driverType == "Safari":
        driver = webdriver.Safari()
    else:
        raise ValueError("bot:不支持的浏览器类型: " + driverType)
    driver.get(url)
    WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.ID, 'tab-student')))
    cookies = driver.get_cookies()
    with open("cookies.txt", "w") as f1:
        f1.write(json.dumps(cookies))
    driver.close()


def getIntoClass():
    global driverType, driver
    now_time = time.strftime("%H:%M", time.localtime())
    if driverType == "Edge":
        driver = webdriver.Edge()
    elif driverType == "Firefox":
        driver = webdriver.Firefox()
    elif driverType == "Chrome":
        driver = webdriver.Chrome()
    elif driverType == "Safari":
        driver = webdriver.Safari()
    else:
        raise ValueError("bot:不支持的浏览器类型: " + driverType)
    driver.get(url)
    with open("cookies.txt") as f2:
        cookies = json.loads(f2.read())
    for cook in cookies:
        driver.add_cookie(cook)
    driver.refresh()
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, 'onlesson')))
        driver.find_element(By.CLASS_NAME, "onlesson").click()  # 更新为新版本
        print(now_time, "bot:我去上课啦")
        print("bot:我将会每"+str(timeSkip)+"s检测一次有没有随堂测试")
        driver.switch_to.window(driver.window_handles[-1])
        while True:
            answer(driver)
            time.sleep(timeSkip)
    except TimeoutException:
        print(now_time, "bot:你现在没课")
        driver.close()


def autoRun():
    scheduler = BlockingScheduler()
    scheduler.add_job(getIntoClass, 'cron', hour='6-21', minute='58', max_instances=20)
    scheduler.start()


def answer(driver):
    driver.refresh()
    time.sleep(3)
    try:
        driver.find_element(By.CSS_SELECTOR, "div.slide__shape.submit-btn")  # 更新为新版本
        driver.save_screenshot("screen-shot.png")
        time.sleep(2)
        answer = solve_question()
        if answer == 'A' or answer == 'B' or answer == 'C' or answer == 'D' or answer == 'T' or answer == 'F':
            choose(driver,answer)
            time.sleep(2)
        elif answer == 0:
            time.sleep(2)
        else:
            for i in answer:
                choose(driver,i)


        time.sleep(2)
        newElement = WebDriverWait(driver,10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.slide__shape.submit-btn.can"))
        )
        newElement.click()

        print(time.strftime("%H:%M:%S", time.localtime()), "bot:我完成了一道题")
    except NoSuchElementException:
        print("bot:暂时无答题任务")



def choose(driver,answer):
    number = "1"
    print("选择了选项"+answer)
    if answer == 'A':
        number = "1"
    elif answer == 'B':
        number = "2"
    elif answer == 'C':
        number = "3"
    elif answer == 'D':
        number = "4"
    choose = driver.find_element(By.XPATH, '//*[@id="app"]/section/section[1]/section[2]/section/section/section/section[1]/section/section/section/section/p['+number+']')
    choose.click()
    time.sleep(2)


if __name__ == "__main__":
    try:
        if os.path.exists("cookies.txt"):
            initConfig()
            getIntoClass()
        else:
            input("bot:Hello，初次相遇需要先做一些设置，手动扫码登录一次，让我获取你的cookies。按 Enter 以继续")
            initConfig()
            getCookies()
            print("bot:完成了, 现在我将在每个整点自动登录一次，如果发现有课就会进入教室上课。")
            print("bot:挂在后台就好, 去做点真正有用的事情吧。\n")
            time.sleep(2)
            getIntoClass()
    except Exception as ex:  # don't you ever stop!
        print(ex)
