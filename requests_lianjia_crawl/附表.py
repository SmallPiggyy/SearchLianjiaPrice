import requests
import parsel
import csv
import time
import random
from urllib.parse import quote  # 处理中文区域名URL编码

# -------------------------- 1. 基础配置 --------------------------
# 1.1 目标区域（固定为“临港”）
TARGET_REGION = "临港"
# 1.2 分页范围（1-19页）
PAGE_START = 1
PAGE_END = 19
# 1.3 请求头（模拟浏览器，保持Cookie有效性）
HEADERS = {
    'cookie': 'lianjia_uuid=e8418c57-bd1b-432f-89ec-c44a63b81444; select_city=310000; crosSdkDT2019DeviceId=-vpowgi--t2f7fy-ixcq06uypztkpmy-pfii0dau1; lianjia_ssid=f8289001-1e7b-47d3-85a7-da56c54876cf; Hm_lvt_46bf127ac9b856df503ec2dbf942b67e=1763354894; HMACCOUNT=8FF0B3D99D026356; _jzqc=1; _jzqx=1.1763354896.1763354896.1.jzqsr=bing%2Ecom|jzqct=/.-; _jzqckmp=1; _ga=GA1.2.1344929102.1763354911; _gid=GA1.2.671216030.1763354911; hip=iLLlmtmVUulqQB2CgDfjPjn__iLH0QRXv2NY3OoyrHeT8FNjYXRzGCRfc5az1Fi7RPAx60Z7h0EU5Rj4_Ncc8gMePZQOr0mHouYrGbCEEwmYZyEgJZNQn25uluDqWo7CuQxO4qO4fPAYE1n21BCvtkCONOgXXUwrr0BKtZjpivCTNh72QHxxTJr459-tF6FHydP0ojmx-CKzo7ypPxQ79QllP7K3TrgFZTdY5VaqdVWr2hEw_SU0LUQOX79TISLxB-ndlQ%3D%3D; login_ucid=2000000513410548; lianjia_token=2.001326377848175f60028b1e49b7ac454a; lianjia_token_secure=2.001326377848175f60028b1e49b7ac454a; security_ticket=KpSEG9G0qBKNelBGhN5RxI++UNNiKtn3G/OMTr3w3sL4xi3y8YBiEEHKmY8Ja3+hcoIy+7Me0nSpTH95nsIko5I3XpbbJakXhlI4YW/vP7A2mRQuWQrEYXAkTVf6pns+UKykUmO4N76kYZBEH6RzWWOWk8mYWTgb+JaJ52UlX80=; ftkrc_=65b3bd39-1b00-4ae0-8648-601582529b99; lfrc_=f9ee1408-7ecd-49e5-b74a-702032ae48a6; session_id=c48a01a8-d798-0929-8aa6-36ff63e426f2; beikeBaseData=%7B%22parentSceneId%22%3A%22%22%7D; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2219a640ec95dad6-0bf3b8b8603e2c8-4c657b58-2710825-19a640ec95ee89%22%2C%22%24device_id%22%3A%2219a640ec95dad6-0bf3b8b8603e2c8-4c657b58-2710825-19a640ec95ee89%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_referrer%22%3A%22%22%2C%22%24latest_referrer_host%22%3A%22%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_utm_source%22%3A%22biying%22%2C%22%24latest_utm_medium%22%3A%22pinzhuan%22%2C%22%24latest_utm_campaign%22%3A%22wybeijing%22%2C%22%24latest_utm_content%22%3A%22biaotimiaoshu%22%2C%22%24latest_utm_term%22%3A%22biaoti%22%7D%7D; Hm_lpvt_46bf127ac9b856df503ec2dbf942b67e=1763357722; _jzqa=1.1208091033271271200.1763354896.1763354896.1763357723.2; _jzqb=1.1.10.1763357723.1; _ga_GVYN2J1PCG=GS2.2.s1763357734$o2$g0$t1763357734$j60$l0$h0; _ga_LRLL77SF11=GS2.2.s1763357734$o2$g0$t1763357734$j60$l0$h0',
    'referer': 'https://sh.lianjia.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0'
}
# 1.4 初始化CSV文件（追加模式，避免覆盖数据）
with open('lingang_rent_data.csv', mode='a', encoding='utf-8', newline='') as f:
    csv_writer = csv.DictWriter(f, fieldnames=[
        '页码', '标题', '价格', '区域', '房子面积', '朝向', '房屋类型', '楼层', '链接', '爬取时间'
    ])
    # 仅在文件为空时写入表头（防止重复）
    if f.tell() == 0:
        csv_writer.writeheader()
block_page=[]

# -------------------------- 2. 核心爬取函数 --------------------------
def crawl_lingang(page):
    """
    爬取临港区域单个页码的租房数据
    :param page: 页码（1-19）
    """
    # 处理“临港”的URL编码（避免中文乱码：临港 → %E4%B8%B4%E6%B8%AF）
    encoded_region = quote(TARGET_REGION, encoding='utf-8')
    # 构造分页URL（遵循链家格式：pg+页码+rs+区域）
    url = f'https://sh.lianjia.com/zufang/pg{page}rs{encoded_region}/#contentList'

    try:
        # 初始化会话（保持Cookie持久化，降低验证码触发概率）
        session = requests.Session()
        session.headers.update(HEADERS)

        # 发送请求（超时15秒，避免网络卡顿卡死）
        response = session.get(url, timeout=15)
        response.raise_for_status()  # 状态码非200时抛出HTTP错误

        # 检测是否触发验证码
        if "人机验证" in response.text:

            print(f"⚠️  临港第{page}页触发验证码，跳过该页！")
            return

        # 解析HTML
        selector = parsel.Selector(response.text)
        # 定位有效房源节点（过滤无效元素，仅保留带data-el="listItem"的房源）
        house_list = selector.css('div.content__list--item[data-el="listItem"]')

        if not house_list:
            print(f"ℹ️  临港第{page}页未找到房源，已无更多数据！")
            return

        print(f"✅  开始爬取临港第{page}页，共{len(house_list)}条房源")

        # 遍历解析每条房源
        for house in house_list:
            # 2.1 基础信息提取
            # 标题（如“整租·绿地东岸涟城 5室1厅 南/北”）
            title = house.css('p.content__list--item--title a::text').get()
            title = title.strip() if title else '无标题'
            # 价格（如“8900 元/月”）
            price = house.css('span.content__list--item-price em::text').get()
            price = f'{price} 元/月' if price else '无价格'
            # 区域详情（浦东-临港新城-小区名）
            area_info = house.css('p.content__list--item--des a::text').getall()
            area = '-'.join(area_info) if area_info else '无区域信息'
            # 房源链接（补全绝对路径）
            link = house.css('a.content__list--item--aside::attr(href)').get()
            link = f'https://sh.lianjia.com{link}' if link else '无链接'
            # 爬取时间（便于数据追溯）
            crawl_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            # 2.2 房屋详情提取（面积、朝向、户型、楼层）
            # 获取<p>标签下所有文本（包括隐藏的楼层信息）
            all_details = house.css('p.content__list--item--des *::text').getall()
            # 清洗文本：去除空值、“/”分隔符、多余空格
            clean_details = []
            for d in all_details:
                d_clean = d.strip()
                if d_clean and d_clean != '/':
                    clean_details.append(d_clean)
            # 排除已提取的区域信息（避免重复解析）
            house_details = clean_details[len(area_info):] if area_info else clean_details

            # 按关键词分类提取详情（避免顺序错位）
            area_size = '无面积'  # 含“㎡”
            direction = '无朝向'  # 含“东/南/西/北”
            layout = '无户型'  # 含“室/厅/卫”
            floor = '无楼层'  # 含“楼层”

            for detail in house_details:
                if '㎡' in detail:
                    area_size = detail
                elif any(dir_key in detail for dir_key in ['东', '南', '西', '北']):
                    direction = detail
                elif any(layout_key in detail for layout_key in ['室', '厅', '卫']):
                    layout = detail
                elif '楼层' in detail:
                    floor = detail  # 匹配“高楼层（14层）”格式

            # 2.3 保存数据到CSV
            house_data = {
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
            }

            # 追加写入CSV
            with open('lingang_rent_data.csv', mode='a', encoding='utf-8', newline='') as f:
                csv_writer = csv.DictWriter(f, fieldnames=house_data.keys())
                csv_writer.writerow(house_data)

            # 打印单条数据（可选，用于实时查看进度）
            print(f"📄  保存：{title} | {price} | {area}")

        # 随机睡眠1-3秒（模拟人类浏览，降低反爬检测）
        sleep_time = random.uniform(1, 3)
        print(f"💤  临港第{page}页爬取完成，随机睡眠{sleep_time:.2f}秒...\n")
        time.sleep(sleep_time)

    except requests.exceptions.HTTPError as e:
        print(f"❌  临港第{page}页HTTP错误：{e}")
    except requests.exceptions.Timeout as e:
        print(f"❌  临港第{page}页请求超时：{e}")
    except Exception as e:
        print(f"❌  临港第{page}页未知错误：{str(e)}")


# -------------------------- 3. 批量爬取1-19页 --------------------------


block_pages=[10,13,15,18]
if __name__ == "__main__":
    print("🚀  开始临港区域1-19页租房数据爬取任务！")
    # 循环爬取1到19页
    for block_pages in block_pages:
        crawl_lingang(block_pages)
    print(f"🎉  临港区域{block_page}页爬取任务全部完成！数据已保存至 lingang_rent_data.csv")

