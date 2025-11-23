from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import random
import csv
from urllib.parse import quote


# -------------------------- 处理极验验证的核心函数 --------------------------
def handle_geetest():
    """处理极验点选验证码：点击初始按钮 → 识别汉字顺序 → 依次点击 → 确认"""
    try:
        # 1. 等待并点击初始验证按钮（id="captcha"内的点击区域）
        captcha_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#captcha .geetest_btn_click"))
        )
        captcha_btn.click()
        time.sleep(1)

        # 2. 等待验证弹窗出现（.geetest_window 是验证码窗口）
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".geetest_window"))
        )

        # 3. 获取需要点击的汉字顺序（通常在弹窗顶部的提示文字中，如“请依次点击：国、家、人”）
        # 注意：实际文字位置可能随版本变化，需通过开发者工具确认
        try:
            tip_text = driver.find_element(By.CSS_SELECTOR, ".geetest_tip_content").text
            # 提取汉字（假设格式为“请依次点击：X、Y、Z”）
            target_chars = [c.strip() for c in tip_text.split("：")[-1].split("、")]
            print(f"需要点击的汉字顺序：{target_chars}")
        except:
            print("无法识别汉字顺序，可能需要手动干预")
            target_chars = []

        # 4. 定位验证码图片区域（.geetest_bg 是图片容器）
        bg_element = driver.find_element(By.CSS_SELECTOR, ".geetest_bg")
        # 获取图片区域的坐标和尺寸（用于计算点击位置）
        bg_location = bg_element.location
        bg_size = bg_element.size

        # 5. 遍历目标汉字，依次点击（核心：需要识别图片中每个汉字的位置，这里简化为模拟点击）
        # 注意：实际需结合图片识别（如OCR）定位汉字位置，此处仅为流程示例
        if target_chars:
            for char in target_chars:
                # 模拟点击图片区域内的随机位置（实际需替换为OCR识别的坐标）
                x = bg_location['x'] + random.randint(50, bg_size['width'] - 50)
                y = bg_location['y'] + random.randint(50, bg_size['height'] - 50)
                driver.execute_script(f"arguments[0].click();", bg_element)  # 点击图片
                time.sleep(0.5)

        # 6. 点击确认按钮（.geetest_submit 是确认按钮）
        submit_btn = driver.find_element(By.CSS_SELECTOR, ".geetest_submit")
        submit_btn.click()
        time.sleep(2)  # 等待验证结果

        # 7. 验证是否成功（若验证窗口消失，则视为成功）
        if not driver.find_elements(By.CSS_SELECTOR, ".geetest_window"):
            print("✅  验证码验证成功")
            return True
        else:
            print("❌  验证码验证失败，重试...")
            return False

    except TimeoutException:
        print("⏰  验证码元素加载超时")
        return False
    except Exception as e:
        print(f"❌  验证处理错误：{str(e)}")
        return False

# -------------------------- 爬取函数 --------------------------
def crawl_page(page):
    if page in BLOCKED_PAGES:
        print(f"⚠️  跳过已知验证页：{page}")
        return

    # 构造URL
    encoded_region = quote(TARGET_REGION, encoding='utf-8')
    url = f'https://sh.lianjia.com/zufang/pg{page}rs{encoded_region}/#contentList'
    driver.get(url)
    time.sleep(random.uniform(1, 2))  # 随机延迟

    # 检查是否触发验证码
    try:
        # 若存在id="captcha"元素，说明触发验证
        if driver.find_elements(By.ID, "captcha"):
            print(f"⚠️  页码{page}触发验证码，开始处理...")
            # 最多尝试3次验证
            for _ in range(3):
                if handle_geetest():
                    break
                time.sleep(2)
            else:
                print(f"❌  页码{page}验证失败，标记为 blocked")
                BLOCKED_PAGES.add(page)
                return
    except:
        pass

    # 验证通过后，解析页面数据
    try:
        # 等待房源列表加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.content__list--item[data-el='listItem']"))
        )
        house_list = driver.find_elements(By.CSS_SELECTOR, "div.content__list--item[data-el='listItem']")
        print(f"✅  页码{page}找到{len(house_list)}条房源")

        for house in house_list:
            # 提取数据（与之前逻辑一致，改用Selenium的元素定位）
            title = house.find_element(By.CSS_SELECTOR, "p.content__list--item--title a").text.strip()
            price = house.find_element(By.CSS_SELECTOR, "span.content__list--item-price em").text + " 元/月"
            area_info = [a.text for a in house.find_elements(By.CSS_SELECTOR, "p.content__list--item--des a")]
            area = '-'.join(area_info) if area_info else '无区域信息'
            link = house.find_element(By.CSS_SELECTOR, "a.content__list--item--aside").get_attribute("href")
            crawl_time = time.strftime("%Y-%m-%d %H:%M:%S")

            # 提取房屋详情
            details = [d.text.strip() for d in house.find_elements(By.CSS_SELECTOR, "p.content__list--item--des *") 
                      if d.text.strip() and d.text.strip() != '/']
            house_details = details[len(area_info):] if area_info else details

            area_size = '无面积'
            direction = '无朝向'
            layout = '无户型'
            floor = '无楼层'
            for d in house_details:
                if '㎡' in d:
                    area_size = d
                elif any(k in d for k in ['东', '南', '西', '北']):
                    direction = d
                elif any(k in d for k in ['室', '厅', '卫']):
                    layout = d
                elif '楼层' in d:
                    floor = d

            # 保存到CSV
            with open(CSV_FILE, mode='a', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    '页码', '标题', '价格', '区域', '房子面积', '朝向', '房屋类型', '楼层', '链接', '爬取时间'
                ])
                writer.writerow({
                    '页码': page,
                    '标题': title,
                    '价格': price,
                    '区域': area,
                    '房子面积': area_size,
                    '朝向': direction,
                    '房屋类型': layout,
                    '楼层': floor,
                    '链接': link,
                    '爬取时间': crawl_time
                })
            print(f"📄  保存：{title} | {price}")

        time.sleep(random.uniform(2, 4))  # 爬取后延迟，降低反爬

    except Exception as e:
        print(f"❌  页码{page}解析错误：{str(e)}")

# -------------------------- 执行爬取 --------------------------
if __name__ == "__main__":
    try:
        print(f"🚀  开始爬取临港1-{PAGE_END}页")
        for page in range(PAGE_START, PAGE_END + 1):
            crawl_page(page)
        print(f"🎉  爬取完成！blocked页码：{BLOCKED_PAGES}")
    finally:
        driver.quit()  # 关闭浏览器