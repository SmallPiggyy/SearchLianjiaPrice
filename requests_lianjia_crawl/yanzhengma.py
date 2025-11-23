from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
from PIL import Image
import pytesseract  # 需安装：pip install pytesseract，且配置Tesseract-OCR环境


def handle_lianjia_captcha(driver):
    """
    处理链家人机验证：点击初始按钮 → 识别汉字顺序 → 依次点击图片 → 确认提交
    :param driver: Selenium的WebDriver实例（已打开目标页面）
    :return: bool - 验证是否成功
    """
    try:
        # -------------------------- 1. 点击初始验证按钮（id="captcha"内的触发区域） --------------------------
        print("🔍  检测到验证码，准备点击初始按钮...")
        # 等待验证码容器加载（id="captcha"）
        captcha_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "captcha"))
        )
        # 点击验证按钮（.geetest_btn_click 是可点击区域）
        verify_btn = captcha_container.find_element(
            By.CSS_SELECTOR, ".geetest_btn_click"  # 初始按钮选择器
        )
        driver.execute_script("arguments[0].click();", verify_btn)  # 用JS点击规避元素遮挡
        time.sleep(1.5)  # 等待弹窗加载

        # -------------------------- 2. 等待验证弹窗出现 --------------------------
        print("🔍  等待验证码弹窗加载...")
        # 弹窗容器选择器（根据提供的HTML结构）
        popup_selector = "div.geetest_popup_wrap.geetest_boxShow"
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, popup_selector))
        )
        popup = driver.find_element(By.CSS_SELECTOR, popup_selector)

        # -------------------------- 3. 提取需要点击的汉字顺序（提示文字） --------------------------
        print("🔍  识别汉字点击顺序...")
        # 提示文字通常在弹窗内的.geetest_tip_content或类似元素
        try:
            tip_element = popup.find_element(
                By.CSS_SELECTOR, ".geetest_tip_content"  # 提示文字选择器
            )
            tip_text = tip_element.text.strip()
            # 提取汉字（假设格式："请依次点击：汉、字、顺、序"）
            if "请依次点击：" in tip_text:
                target_chars = [c.strip() for c in tip_text.split("：")[-1].split("、")]
                print(f"✅  识别到需点击汉字：{target_chars}")
            else:
                print("❌  提示文字格式异常，无法提取汉字顺序")
                return False
        except NoSuchElementException:
            print("❌  未找到提示文字元素，验证失败")
            return False

        # -------------------------- 4. 定位验证码图片区域（.geetest_bg） --------------------------
        print("🔍  定位验证码图片区域...")
        bg_element = popup.find_element(
            By.CSS_SELECTOR, ".geetest_window .geetest_bg"  # 图片容器选择器
        )
        # 获取图片区域的坐标和尺寸（用于计算点击位置）
        bg_location = bg_element.location  # 相对浏览器窗口的坐标
        bg_size = bg_element.size  # 图片宽高
        print(f"📐  图片区域：位置{x=}, {y=}，尺寸{width=}, {height=}".format(
            x=bg_location['x'], y=bg_location['y'],
            width=bg_size['width'], height=bg_size['height']
        ))

        # -------------------------- 5. 截取图片并识别汉字位置（核心步骤） --------------------------
        print("🔍  识别图片中汉字位置...")
        # 截取验证码图片并保存
        screenshot = driver.get_screenshot_as_png()
        with Image.open(BytesIO(screenshot)) as img:
            # 计算图片在截图中的绝对坐标（考虑浏览器缩放）
            left = bg_location['x']
            top = bg_location['y']
            right = left + bg_size['width']
            bottom = top + bg_size['height']
            # 裁剪图片
            captcha_img = img.crop((left, top, right, bottom))
            captcha_img.save("captcha_temp.png")  # 保存临时图片

        # 识别图片中的汉字及位置（使用pytesseract，需提前训练模型提高准确率）
        # 注意：实际需结合OCR工具优化，此处为简化示例
        def get_char_positions(image_path):
            """识别图片中每个汉字的坐标（返回 {汉字: (x, y)}）"""
            # 实际项目中需替换为更精准的识别逻辑（如百度OCRAPI）
            # 这里模拟识别结果（假设汉字在图片中的相对坐标）
           模拟位置 = {
                "汉": (50, 50),
                "字": (100, 80),
                "顺": (150, 40),
                "序": (80, 100)
            }
            return 模拟位置

        char_positions = get_char_positions("captcha_temp.png")
        print(f"✅  识别到汉字位置：{char_positions}")

        # -------------------------- 6. 按顺序点击图片中的汉字 --------------------------
        print("🔍  按顺序点击汉字...")
        for char in target_chars:
            if char not in char_positions:
                print(f"❌  未找到汉字「{char}」的位置，验证失败")
                return False
            # 获取汉字在图片中的相对坐标
            x, y = char_positions[char]
            # 计算相对于浏览器的绝对点击坐标（加随机偏移量模拟人工点击）
            click_x = bg_location['x'] + x + random.randint(-5, 5)
            click_y = bg_location['y'] + y + random.randint(-5, 5)
            # 执行点击（用JS模拟鼠标点击）
            driver.execute_script(f"""
                var event = new MouseEvent('click', {{
                    'clientX': {click_x},
                    'clientY': {click_y},
                    'bubbles': true
                }});
                document.elementFromPoint({click_x}, {click_y}).dispatchEvent(event);
            """)
            print(f"✅  已点击「{char}」（坐标：{click_x}, {click_y}）")
            time.sleep(random.uniform(0.8, 1.2))  # 模拟人工点击间隔

        # -------------------------- 7. 点击确认按钮 --------------------------
        print("🔍  点击确认按钮...")
        submit_btn = popup.find_element(
            By.CSS_SELECTOR, ".geetest_submit .geetest_submit_tips"  # 确认按钮选择器
        )
        submit_btn.click()
        time.sleep(2)  # 等待验证结果

        # -------------------------- 8. 验证是否成功（弹窗关闭则视为成功） --------------------------
        if not driver.find_elements(By.CSS_SELECTOR, popup_selector):
            print("✅  人机验证成功！")
            return True
        else:
            print("❌  验证失败，弹窗未关闭")
            return False

    except TimeoutException:
        print("⏰  验证码元素加载超时")
        return False
    except Exception as e:
        print(f"❌  验证处理异常：{str(e)}")
        return False


# -------------------------- 使用示例 --------------------------
if __name__ == "__main__":
    # 初始化浏览器
    driver = webdriver.Chrome()
    driver.get("https://sh.lianjia.com/zufang/rs临港/")  # 打开目标页面

    # 检测到验证码时调用处理函数
    if driver.find_elements(By.ID, "captcha"):
        success = handle_lianjia_captcha(driver)
        if success:
            print("继续爬取数据...")
        else:
            print("验证失败，退出程序")
    else:
        print("未触发验证码，直接爬取...")

    # 关闭浏览器
    time.sleep(3)
    driver.quit()