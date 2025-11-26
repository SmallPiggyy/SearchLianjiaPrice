# 创建爬取新房售卖价格的功能
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
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
# 用于存储所有页面的房源数据
all_results = []
current_page = 1
URL = "https://sh.lianjia.com/ershoufang/pg25rs%E4%B8%B4%E6%B8%AF/"


def parse_page_data(page_source, existing_count):
    """
    解析当前页面的新房数据
    :param page_source: 页面源码
    :param existing_count: 已爬取的房源总数（用于生成正确序号）
    :return: 解析后的房源列表
    """
    selector = Selector(text=page_source)
    # 修复：移除has-results类，匹配所有房源列表项
    house_elements = selector.css('li.resblock-list.post_ulog_exposure_scroll')
    page_results = []

    for idx, house in enumerate(house_elements, 1):
        global_id = existing_count + idx  # 修复序号：基于已爬总数生成（核心优化）
        # 提取房屋名称
        name = house.css('div.resblock-name h2 a::text').get(default='')
        # 提取位置信息
        location_parts = house.css('div.resblock-location span::text').getall()
        location = '/'.join(location_parts) if location_parts else ''
        # 提取详细地址
        address = house.css('div.resblock-location a::text').get(default='')
        full_location = f"{location} {address}" if address else location
        # 提取面积信息
        area = house.css('div.resblock-area span::text').get(default='')
        # 提取户型信息
        room_type = house.css('a.resblock-room span::text').getall()
        room_type_str = '/'.join(room_type) if room_type else ''
        # 提取均价
        avg_price = house.css('div.main-price .number::text').get(default='')
        avg_price_unit = house.css('div.main-price .desc::text').get(default='')
        full_avg_price = f"{avg_price}{avg_price_unit}" if avg_price else ''
        # 提取总价
        total_price = house.css('div.second::text').get(default='')
        # 提取标签信息
        tags = house.css('div.resblock-tag span::text').getall()
        tags_str = '/'.join(tags) if tags else ''
        # 提取链接
        link = house.css('a.resblock-img-wrapper::attr(href)').get(default='')
        full_link = f"https://sh.fang.lianjia.com{link}" if link else ''
        # 组织数据
        formatted_result = {
            '序号': global_id,
            '名称': name,
            '位置': full_location,
            '户型': room_type_str,
            '面积': area,
            '均价': full_avg_price,
            '总价': total_price,
            '标签': tags_str,
            '链接': full_link
        }

        page_results.append(formatted_result)

    return page_results


def check_for_captcha():
    """检查是否存在验证码"""
    try:
        captcha_elements = driver.find_elements(By.XPATH,
                                                '//*[contains(text(), "人机验证")]')
        return len(captcha_elements) > 0
    except Exception:
        return False


try:
    # 尝试连接到现有浏览器
    print("尝试连接到已打开的浏览器实例...")
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(3)  # 缩短全局隐式等待
    print("成功连接到浏览器！")

    # 检查当前URL，如果不是目标URL则导航到目标页面
    if not driver.current_url.startswith(URL):
        print("导航到链家网站...")
        driver.get(URL)
        input("请完成：1.登录 2.人机验证 3.确认房源显示 → 按Enter继续...")

    # 分页爬取循环
    while True:
        print(f"\n===== 正在爬取第 {current_page} 页 =====")

        # 检查验证码
        if check_for_captcha():
            print("检测到验证码，请手动完成验证")
            input("验证完成后按Enter继续...")

        # 获取当前页面源码并解析（传入已爬总数生成正确序号）
        page_source = driver.page_source
        page_results = parse_page_data(page_source, len(all_results))
        all_results.extend(page_results)

        print(f"第 {current_page} 页爬取完成，获取 {len(page_results)} 条房源信息")


        try:
            # 核心优化：通过"next"文本和class定位翻页按钮
            # 匹配包含"next"文本且未禁用的按钮（处理中文/英文按钮文本）
            next_button = WebDriverWait(driver, 5).until(
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

                # 等待页面更新
                try:
                    # 等待列表容器更新
                    WebDriverWait(driver, 5).until(
                        EC.staleness_of(driver.find_element(By.CLASS_NAME, 'SellListContent'))
                    )
                    # 确认新页面加载完成
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.SellListContent div.info.clear'))
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
    fieldnames = ['序号', '名称', '位置', '户型', '面积', '均价', '总价', '标签', '链接']
    with open('链家新房数据_Selenium2.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)

    print(f"\n===== 爬取完成！=====")
    print(f"总计获取 {len(all_results)} 条房源信息")
    print("前5条数据预览：")
    for item in all_results[:5]:
        print(f"\n{item['序号']}. {item['名称']} | 均价：{item['均价']} | 位置：{item['位置']}")

    print("程序执行完成，浏览器保持打开状态")

except Exception as e:
    print(f"发生错误: {e}")
    # 保存已爬取数据
    if all_results:
        print(f"保存已爬取的 {len(all_results)} 条数据...")
        fieldnames = ['序号', '名称', '位置', '户型', '面积', '均价', '总价', '标签', '链接']
        with open('链家新房数据_备份.csv', 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)

