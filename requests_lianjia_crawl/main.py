import requests
import parsel
import csv
from urllib.parse import quote  # 处理中文区域名URL编码
from fun import *
#北京区域列表 https://sh.lianjia.com/zufang/pg3rs%E4%B8%B4%E6%B8%AF/#contentList
TARGET_REGION=["临港","奉贤","浦东"]
# 1.2 分页范围（1-19页）
PAGE_START = 1
PAGE_END = 3
pages = range(PAGE_START, PAGE_END + 1)
f = open('data.csv', mode='w', encoding='utf-8', newline='')
csv_writer = csv.DictWriter(f,fieldnames=['标题','价格','区域','房子面积','朝向','房屋类型','楼层','链接'])
csv_writer.writeheader()

#模拟浏览器
headers={
    'cookie':'',
    'referer':'https://sh.lianjia.com/',
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0'
}

#发送请求

def crawl_lingang(page,TARGET_REGION):
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
        session.headers.update(headers)
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
        for house in house_list:
            dit = get_house_info(house)
            csv_writer.writerow(dit)  #写入数据
            print(dit)
    except:
        print("请求失败或触发验证码，尝试点击验证码！")
        print(f"状态码：{response.status_code}")
        print("响应内容：", response.text[:500])  # 打印部分响应内容用于调试


if __name__ == "__main__":
    print("🚀  开始临港区域1-19页租房数据爬取任务！")
    # 循环爬取1到19页
    for page in pages:
        crawl_lingang(page,TARGET_REGION[0])
    print(f"🎉  临港区域{page}页爬取任务全部完成！数据已保存至 lingang_rent_data.csv")

