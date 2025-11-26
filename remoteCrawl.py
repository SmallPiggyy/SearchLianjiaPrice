# 创建爬取二手房价格的功能
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import random
from parsel import Selector
# 1. 配置Chrome选项
chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:8872")  # 连接已开的浏览器
chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # 隐藏自动化标识
chrome_options.add_argument(
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
# 用于存储所有页面的房源数据
all_results = []
current_page  =  1
URL = "https://sh.lianjia.com/ershoufang/pg34rs%E4%B8%B4%E6%B8%AF/"

def parse_page_data(page_source, existing_count):
    """解析当前页面的二手房数据"""
    selector = Selector(text=page_source)
    # 定位房源列表容器（适配新的li标签结构）
    house_elements = selector.css('li.clear.LOGCLICKDATA')
    page_results = []

    for idx, house in enumerate(house_elements, 1):
        global_id = existing_count + idx
        # 提取房源标题
        name = house.css('div.title a::text').get(default='').strip()
        # 提取位置信息
        community = house.css('div.positionInfo a:first-child::text').get(default='').strip()
        region = house.css('div.positionInfo a:last-child::text').get(default='').strip()
        full_location = f"{community} - {region}" if (community or region) else ''
        # 提取户型和面积信息
        house_info = house.css('div.houseInfo::text').get(default='').strip()
        # 提取关注信息
        follow_info = house.css('div.followInfo::text').get(default='').strip()
        # 提取标签信息
        tags = house.css('div.tag span::text').getall()
        tags_str = '/'.join(tags) if tags else ''
        # 提取价格信息
        total_price = house.css('div.totalPrice span::text').get(default='')
        total_price_unit = house.css('div.totalPrice i::text').get(default='')
        full_total_price = f"{total_price}{total_price_unit}" if total_price else ''
        avg_price = house.css('div.unitPrice span::text').get(default='')
        # 提取链接信息
        link = house.css('div.title a::attr(href)').get(default='')

        # 解析户型和面积（从house_info中提取）
        room_type = ''
        area = ''
        if house_info:
            info_parts = [part.strip() for part in house_info.split('|')]
            if len(info_parts) >= 1:
                room_type = info_parts[0]
            if len(info_parts) >= 2:
                area = info_parts[1]

        formatted_result = {
            '序号': global_id,
            '标题': name,
            '位置': full_location,
            '户型': room_type,
            '面积': area,
            '均价': avg_price,
            '总价': full_total_price,
            '标签': tags_str,
            '关注信息': follow_info,
            '链接': link
        }

        page_results.append(formatted_result)

    return page_results


def check_for_captcha():
    """检查是否存在验证码"""
    try:
        captcha_elements = driver.find_elements(By.XPATH,
                                                '//*[contains(@class, "captcha") or contains(@id, "captcha") or contains(text(), "人机验证")]')
        return len(captcha_elements) > 0
    except Exception:
        return False


try:
    print("尝试连接到已打开的浏览器实例...")
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(1)
    print("成功连接到浏览器！")

    if not driver.current_url.startswith(URL):
        print("导航到链家网站...")
        driver.get(URL)
        input("请完成：1.登录 2.人机验证 3.确认房源显示 → 按Enter继续...")

    # 分页爬取循环（基于next定位翻页按钮）
    while True:
        print(f"\n===== 正在爬取第 {current_page} 页 =====")

        if check_for_captcha():
            print("检测到验证码，请手动完成验证")
            input("验证完成后按Enter继续...")

        page_source = driver.page_source
        page_results = parse_page_data(page_source, len(all_results))
        all_results.extend(page_results)
        print(f"第 {current_page} 页爬取完成，获取 {len(page_results)} 条房源信息")

        try:
            # 核心优化：通过"next"文本和class定位翻页按钮
            # 匹配包含"next"文本且未禁用的按钮（处理中文/英文按钮文本）
            next_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable(
                    (By.XPATH,
                     '//a[contains(text(), "next") or contains(text(), "下一页") and not(contains(@class, "disabled"))]')
                )
            )

            # 验证按钮可交互性
            if next_button and next_button.is_enabled() and next_button.is_displayed():
                wait_time = random.uniform(1, 2)
                print(f"随机暂停 {wait_time:.2f} 秒后翻页...")
                time.sleep(wait_time)

                # 点击前滚动到按钮位置（避免被遮挡）
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                time.sleep(0.5)  # 等待滚动完成

                # 执行点击
                driver.execute_script("arguments[0].click();", next_button)
                current_page += 1
                print(f"正在跳转到第 {current_page} 页...")

                # 等待页面更新（适配新的房源标签结构）
                try:
                    # 等待列表容器更新
                    WebDriverWait(driver, 2).until(
                        EC.staleness_of(driver.find_element(By.CSS_SELECTOR, 'li.clear.LOGCLICKDATA'))
                    )
                    # 确认新页面加载完成
                    WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'li.clear.LOGCLICKDATA'))
                    )
                    print(f"第 {current_page} 页加载完成")
                except:
                    print("页面加载检测超时，继续执行...")

                time.sleep(random.uniform(0.5, 1.5))
            else:
                print("下一页按钮不可用，已到最后一页")
                break

        except Exception as e:
            print(f"翻页按钮定位失败: {e}")
            print("未找到可用的下一页按钮，停止爬取")
            break

    # 保存数据
    fieldnames = ['序号', '标题', '位置', '户型', '面积', '均价', '总价', '标签', '关注信息', '链接']
    with open('链家二手房数据3.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)

    print(f"\n===== 爬取完成！=====")
    print(f"总计获取 {len(all_results)} 条房源信息")
    for item in all_results[:5]:
        print(f"\n{item['序号']}. {item['标题']} | 总价：{item['总价']}")

except Exception as e:
    print(f"发生错误: {e}")
    if all_results:
        print(f"保存已爬取的 {len(all_results)} 条数据...")
        fieldnames = ['序号', '标题', '位置', '户型', '面积', '均价', '总价', '标签', '关注信息', '链接']
        with open('链家二手房数据3.csv', 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)
