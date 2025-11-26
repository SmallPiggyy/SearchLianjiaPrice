from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import csv
import random
# 1. 配置Chrome选项
chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9527")  # 连接已开的浏览器
chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # 隐藏自动化标识
# 用于存储所有页面的房源数据
all_results = []
current_page = 1
URL="https://sh.lianjia.com/zufang/rs%E4%B8%B4%E6%B8%AF/"
def parse_page_data(page_source, page_number):
    """解析当前页面的房源数据"""
    soup = BeautifulSoup(page_source, 'html.parser')
    house_items = soup.find_all('div', class_='content__list--item')

    page_results = []
    for idx, item in enumerate(house_items, 1):
        global_id = (page_number - 1) * 30 + idx  # 全局序号
        title = item.find('a', class_='twoline').get_text(strip=True) if item.find('a', class_='twoline') else '无'
        location_els = item.select('.content__list--item--des a')
        location = '-'.join([el.get_text(strip=True) for el in location_els]) if location_els else '无'
        des_text = item.find('p', class_='content__list--item--des').get_text(strip=True) if item.find('p',
                                                                                                       class_='content__list--item--des') else ''
        des_parts = [part for part in des_text.split('/') if part.strip()]

        area = next((p for p in des_parts if '㎡' in p), '无').strip()
        direction = next((p for p in des_parts if any(c in p for c in '南北东西')), '无').strip()
        layout = next((p for p in des_parts if '室' in p and '厅' in p), '无').strip()

        page_results.append({
            '序号': global_id,
            '标题': title,
            '位置': location,
            '面积': area,
            '朝向': direction,
            '户型': layout
        })

    return page_results

def check_for_captcha():
    """检查是否存在验证码"""
    try:
        # 检查常见验证码相关元素
        captcha_elements = driver.find_elements(By.XPATH,
                                                '//*[contains(@class, "captcha") or contains(@id, "captcha") or contains(text(), "人机验证")]')
        return len(captcha_elements) > 0
    except Exception:
        return False

try:
    # 尝试连接到现有浏览器
    print("尝试连接到已打开的浏览器实例...")
    driver = webdriver.Chrome(options=chrome_options)
    print("成功连接到浏览器！")

    # 检查当前URL，如果不是目标URL则导航到目标页面
    if not driver.current_url.startswith(URL):
        print("导航到链家网站...")
        url2 = 'https://sh.lianjia.com/'
        driver.get(URL)
        input("请在打开的浏览器中完成：1. 登录 2. 人机验证（若有） 3. 确认页面显示房源列表完成后请回到终端按Enter继续...")

    # 分页爬取循环
    while True:
        print(f"正在爬取第 {current_page} 页数据...")

        # 检查是否需要验证码
        if check_for_captcha():
            print("检测到验证码，请在浏览器中手动完成验证")
            input("完成验证后，请按Enter继续...")

        # 获取当前页面源码并解析
        page_source = driver.page_source
        page_results = parse_page_data(page_source, current_page)
        all_results.extend(page_results)

        print(f"第 {current_page} 页爬取完成，获取 {len(page_results)} 条房源信息")

        try:
            # 尝试查找并点击下一页按钮
            # 使用XPath和class两种方式查找，提高兼容性
            next_button = None
            try:
                # 尝试使用class查找
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'next'))
                )
            except:
                print("未找到下一页按钮，可能已到达最后一页")
                break

            # 检查下一页按钮是否可用
            if next_button.is_enabled() and next_button.is_displayed():
                # 记录当前页面源码或某个唯一标识，用于后续验证是否成功翻页
                current_page_source = driver.page_source

                # 随机暂停1-3秒
                wait_time = random.uniform(1, 3)
                print(f"随机暂停 {wait_time:.2f} 秒后继续...")
                time.sleep(wait_time)

                # 点击下一页
                next_button.click()
                current_page += 1
                print(f"正在跳转到第 {current_page} 页...")

                # 改进的等待逻辑：等待页面内容变化或新内容加载
                # 方法1：等待房源列表元素更新或变化
                try:
                    WebDriverWait(driver, 10).until(
                        lambda d: d.page_source != current_page_source
                    )
                    print(f"页面已更新，确认跳转到第 {current_page} 页")
                except:
                    print("页面可能未更新，尝试另一种等待方式...")
                    # 方法2：等待房源列表中的某些元素重新出现
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'content__list--item'))
                    )

                # 额外的随机等待，模拟人类浏览行为
                time.sleep(random.uniform(1, 2))
            else:
                print("下一页按钮不可点击，已到达最后一页")
                break

        except Exception as e:
            print(f"翻页时出错: {e}")
            print("已到达最后一页或遇到问题，停止爬取")
            break

    # 保存所有结果
    with open('链家租房数据_Selenium.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['序号', '标题', '位置', '面积', '朝向', '户型'])
        writer.writeheader()
        writer.writerows(all_results)
    print(f"\n数据爬取全部完成！共获取 {len(all_results)} 条房源信息")
    print("前5条数据预览：")
    for item in all_results[:5]:
        print(f"\n{item['序号']}. 标题：{item['标题']}")
        print(f"   位置：{item['位置']}")
        print(f"   面积：{item['面积']} | 朝向：{item['朝向']} | 户型：{item['户型']}")
    print("程序执行完成，浏览器保持打开状态")

except Exception as e:
    print(f"发生错误: {e}")
    # 保存已爬取的数据
    if all_results:
        print("正在保存已爬取的数据...")
        with open('链家租房数据_Selenium.csv', 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['序号', '标题', '位置', '面积', '朝向', '户型'])
            writer.writeheader()
            writer.writerows(all_results)
        print(f"已保存 {len(all_results)} 条房源信息")