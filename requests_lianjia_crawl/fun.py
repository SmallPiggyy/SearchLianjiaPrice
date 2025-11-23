def get_house_info(house):
    dit={}
    # 1. 房源标题（如“整租·绿地东岸涟城 5室1厅 南/北”）
    title = house.css('p.content__list--item--title a::text').get().strip()
    # 2. 房源链接（补全绝对路径）
    link = house.css('a.content__list--item--aside::attr(href)').get()
    link = f'https://sh.lianjia.com{link}'
    # 3. 价格（如“8900 元/月”）
    price = house.css('span.content__list--item-price em::text').get()
    price = f'{price} 元/月'
    # 4. 区域信息（浦东-临港新城-绿地东岸涟城）

    area_info = house.css('p.content__list--item--des a::text').getall()
    # 处理格式：['浦东', '临港新城', '绿地东岸涟城'] → "浦东-临港新城-绿地东岸涟城"
    area = '-'.join(area_info) if area_info else '无区域信息'
    # -------------------------- 2. 提取房屋详情（面积、朝向、户型、楼层） --------------------------
    # 思路：先获取 <p> 标签内所有文本（含 <i>/</i> 和 <span> 内的楼层），再按规则分类
    # 步骤1：获取 <p> 标签下所有文本节点（包括 <span> 内的楼层）
    all_details = house.css('p.content__list--item--des *::text').getall()
    # 步骤2：清洗文本（去除空字符串、无用的“/”分隔符、多余空格）
    clean_details = []
    for d in all_details:
        d_clean = d.strip()  # 去除前后空格
        if d_clean and d_clean != '/':  # 过滤空值和“/”
            clean_details.append(d_clean)
    # 步骤3：从清洗后的列表中排除区域信息（因为区域已通过 <a> 标签单独提取，避免重复）
    # 区域信息是前3个元素（如 ['浦东', '临港新城', '保利玲珑公馆']），需从 clean_details 中剔除
    house_details = clean_details[len(area_info):]  # 截取区域之后的详情（面积、朝向、户型、楼层）
    # 步骤4：按特征分类提取（通过关键词匹配，避免顺序错位）
    area_size = '无面积'    # 特征：包含“㎡”
    direction = '无朝向'    # 特征：包含“东/南/西/北”
    layout = '无户型'       # 特征：包含“室”“厅”“卫”
    floor = '无楼层'        # 特征：包含“楼层”
    for detail in house_details:
        if '㎡' in detail:
            area_size = detail
        elif any(dir_key in detail for dir_key in ['东', '南', '西', '北']):
            direction = detail
        elif any(layout_key in detail for layout_key in ['室', '厅', '卫']):
            layout = detail
        elif '楼层' in detail:
            floor = detail  # 匹配“高楼层（14层）”这类格式
    # 6. 房屋标签（如“官方核验”“精装”）
    tags = house.css('p.content__list--item--bottom i::text').getall()
    tags = ', '.join(tags) if tags else '无标签'
    #列表取值
    dit ={'标题': title,
          '价格': price,
          '区域': area,
          '房子面积':area_size,
          '朝向':direction,
          '房屋类型':layout,
          '楼层':floor,
          '链接': link
          }
    return dit

