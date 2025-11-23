from selenium import webdriver
driver = webdriver.Chrome()  # 自动从环境变量中查找驱动
driver.get("https://baidu.com")
print(driver.title)
