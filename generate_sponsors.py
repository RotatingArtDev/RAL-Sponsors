#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爱发电交易CSV转赞助商JSON生成器

用法:
    python generate_sponsors.py <csv文件路径> [输出json路径]

示例:
    python generate_sponsors.py afdian-transaction.csv sponsors.json
"""

import csv
import json
import sys
import re
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple

# 爱发电CSV列索引 (固定格式)
COL_URL = 2        # 网页地址
COL_BIO = 3        # 备注/留言
COL_USERNAME = 4   # 用户名
COL_TIER_NAME = 6  # 档位名称
COL_AMOUNT = 7     # 金额
COL_DATE = 17      # 创建时间

# 赞助级别定义
TIERS = [
    {
        "id": "galaxy_guardian",
        "name": "银河守护者",
        "nameEn": "Galaxy Guardian",
        "color": "#9B59B6",
        "particleType": "galaxy",
        "order": 100,
        "minAmount": 200
    },
    {
        "id": "starlight_patron",
        "name": "星空探索家",
        "nameEn": "Starlight Patron",
        "color": "#E74C3C",
        "particleType": "firework",
        "order": 80,
        "minAmount": 100
    },
    {
        "id": "cosmic_supporter",
        "name": "极致合伙人",
        "nameEn": "Cosmic Supporter",
        "color": "#3498DB",
        "particleType": "stars",
        "order": 60,
        "minAmount": 50
    },
    {
        "id": "beta_scout",
        "name": "星光先锋",
        "nameEn": "Starlight Pioneer",
        "color": "#2ECC71",
        "particleType": "sparkle",
        "order": 40,
        "minAmount": 18
    },
    {
        "id": "early_supporter",
        "name": "爱心维护员",
        "nameEn": "Early Supporter",
        "color": "#F39C12",
        "particleType": "none",
        "order": 20,
        "minAmount": 5
    }
]


def extract_user_id_from_url(url: str) -> str:
    """从爱发电用户URL中提取用户ID"""
    match = re.search(r'/u/([a-f0-9]+)', url)
    return match.group(1) if match else ""


# 爱发电头像CDN地址
AFDIAN_AVATAR_CDN = "https://pic1.afdiancdn.com/user/{user_id}/avatar/{user_id}_w.jpeg"
AFDIAN_DEFAULT_AVATAR = "https://pic1.afdiancdn.com/default/avatar/avatar-purple.png"


def get_avatar_url(user_id: str) -> str:
    """
    获取爱发电用户头像URL
    格式: https://pic1.afdiancdn.com/user/{user_id}/avatar/{user_id}_w.jpeg
    """
    if not user_id:
        return AFDIAN_DEFAULT_AVATAR
    
    return AFDIAN_AVATAR_CDN.format(user_id=user_id)


def get_tier_id(total_amount: float) -> str:
    """根据总金额确定赞助级别"""
    for tier in TIERS:
        if total_amount >= tier["minAmount"]:
            return tier["id"]
    return "early_supporter"


def safe_get(fields: list, index: int) -> str:
    """安全获取列表元素"""
    if index < len(fields):
        return fields[index].strip().strip('"')
    return ""


def parse_csv_line(line: str) -> list:
    """解析CSV行，正确处理引号"""
    fields = []
    current_field = ""
    in_quotes = False
    
    for char in line:
        if char == '"':
            in_quotes = not in_quotes
        elif char == ',' and not in_quotes:
            fields.append(current_field.strip().strip('"'))
            current_field = ""
        else:
            current_field += char
    fields.append(current_field.strip().strip('"'))
    
    return fields


def parse_csv(csv_path: str) -> Dict[str, dict]:
    """
    解析爱发电交易CSV文件
    返回: {user_id: {name, total_amount, bio, join_date, url}}
    """
    sponsors = defaultdict(lambda: {
        "name": "",
        "total_amount": 0.0,
        "bio": "",
        "join_date": "",
        "url": ""
    })
    
    # 尝试不同编码读取
    encodings = ['gbk', 'gb2312', 'gb18030', 'utf-8', 'utf-8-sig', 'cp936']
    content = None
    used_encoding = None
    
    for encoding in encodings:
        try:
            with open(csv_path, 'r', encoding=encoding, errors='ignore') as f:
                content = f.read()
            used_encoding = encoding
            break
        except Exception:
            continue
    
    if content is None:
        print("[ERROR] 无法读取CSV文件")
        return {}
    
    print(f"[INFO] 使用编码: {used_encoding}")
    
    lines = content.strip().split('\n')
    print(f"[INFO] 共 {len(lines)} 行数据")
    
    # 跳过表头
    for line_num, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        
        fields = parse_csv_line(line)
        
        try:
            url = safe_get(fields, COL_URL)
            user_id = extract_user_id_from_url(url)
            
            if not user_id:
                continue
            
            name = safe_get(fields, COL_USERNAME)
            amount_str = safe_get(fields, COL_AMOUNT)
            bio = safe_get(fields, COL_BIO)
            date_str = safe_get(fields, COL_DATE)
            
            # 清理金额
            amount = float(re.sub(r'[^\d.]', '', amount_str) or "0")
            
            # 更新用户数据
            sponsor = sponsors[user_id]
            sponsor["total_amount"] += amount
            sponsor["url"] = f"https://afdian.com/u/{user_id}"
            
            # 使用更有意义的名称
            if name and (not sponsor["name"] or sponsor["name"].startswith("爱发电用户_")):
                sponsor["name"] = name
            
            # 保留有内容的留言（过滤掉乱码）
            if bio and len(bio) > 1:
                # 只保留可打印字符
                bio_clean = ''.join(c for c in bio if c.isprintable() and ord(c) < 65536)
                if len(bio_clean) > len(sponsor.get("bio", "")):
                    sponsor["bio"] = bio_clean[:200]
            
            # 记录最早日期
            if date_str:
                date_match = re.search(r'(\d{4}-\d{2})', date_str)
                if date_match:
                    month = date_match.group(1)
                    if not sponsor["join_date"] or month < sponsor["join_date"]:
                        sponsor["join_date"] = month
            
        except Exception as e:
            print(f"[WARN] 第{line_num}行解析失败: {e}")
            continue
    
    return dict(sponsors)


def generate_sponsors_json(sponsors_data: Dict[str, dict]) -> dict:
    """生成赞助商JSON数据"""
    sponsors_list = []
    
    for user_id, data in sponsors_data.items():
        tier_id = get_tier_id(data["total_amount"])
        
        # 清理名称
        name = data["name"] or f"匿名支持者_{user_id[:5]}"
        
        sponsor = {
            "id": user_id,
            "name": name,
            "avatarUrl": get_avatar_url(user_id),  # 直接使用爱发电头像
            "bio": data.get("bio", ""),
            "tier": tier_id,
            "joinDate": data.get("join_date", datetime.now().strftime("%Y-%m")),
            "website": f"https://afdian.com/u/{user_id}"
        }
        sponsors_list.append(sponsor)
    
    # 按金额排序（高到低）
    sponsors_list.sort(key=lambda x: sponsors_data[x["id"]]["total_amount"], reverse=True)
    
    # 统计各级别人数
    tier_counts = defaultdict(int)
    total_amount = 0
    for s in sponsors_list:
        tier_counts[s["tier"]] += 1
        total_amount += sponsors_data[s["id"]]["total_amount"]
    
    return {
        "version": 1,
        "name": "RAL Sponsors",
        "description": f"RotatingArt Launcher 赞助者名单 - {datetime.now().strftime('%Y年%m月')}",
        "lastUpdated": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tiers": TIERS,
        "sponsors": sponsors_list
    }, tier_counts, total_amount


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n请提供CSV文件路径!")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "sponsors.json"
    
    print(f"[INFO] 读取CSV: {csv_path}")
    sponsors_data = parse_csv(csv_path)
    
    if not sponsors_data:
        print("[ERROR] 未能解析到任何赞助者数据")
        sys.exit(1)
    
    print(f"[INFO] 解析到 {len(sponsors_data)} 位独立赞助者")
    
    # 生成JSON（使用爱发电官方头像）
    result, tier_counts, total_amount = generate_sponsors_json(sponsors_data)
    
    # 显示统计
    print(f"\n[STATS] 赞助总额: {total_amount:.2f} CNY")
    print("[STATS] 各级别人数:")
    for tier in TIERS:
        count = tier_counts.get(tier["id"], 0)
        if count > 0:
            print(f"  - {tier['name']}: {count} 人")
    
    # 保存JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    
    print(f"\n[SUCCESS] 已生成: {output_path}")
    print(f"[INFO] 共 {len(result['sponsors'])} 位赞助者")
    print(f"[INFO] 头像使用爱发电官方CDN: pic1.afdiancdn.com")


if __name__ == "__main__":
    main()
