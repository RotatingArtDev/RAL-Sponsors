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
import os
import hashlib
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple

# Pillow for avatar generation
from PIL import Image, ImageDraw, ImageFont

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


# GitHub/Gitee 仓库 raw 地址
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/RotatingArtDev/RAL-Sponsors/main"
GITEE_RAW_BASE = "https://gitee.com/daohei/RAL-Sponsors/raw/main"

# 头像文件夹
AVATARS_DIR = "avatars"

# 头像颜色方案（美观的渐变色）
AVATAR_COLORS = [
    ("#667eea", "#764ba2"),  # 紫蓝渐变
    ("#f093fb", "#f5576c"),  # 粉红渐变
    ("#4facfe", "#00f2fe"),  # 青蓝渐变
    ("#43e97b", "#38f9d7"),  # 绿青渐变
    ("#fa709a", "#fee140"),  # 粉黄渐变
    ("#a8edea", "#fed6e3"),  # 淡彩渐变
    ("#ff9a9e", "#fecfef"),  # 粉嫩渐变
    ("#ffecd2", "#fcb69f"),  # 暖橙渐变
    ("#667eea", "#43e97b"),  # 蓝绿渐变
    ("#5ee7df", "#b490ca"),  # 青紫渐变
    ("#d299c2", "#fef9d7"),  # 淡紫渐变
    ("#89f7fe", "#66a6ff"),  # 天蓝渐变
]


def get_initials(name: str) -> str:
    """获取名称的首字母/首字"""
    if not name:
        return "?"
    
    # 过滤掉"爱发电用户_"前缀
    if name.startswith("爱发电用户_"):
        return name[-1].upper() if name else "?"
    
    # 中文名取第一个字
    for char in name:
        if '\u4e00' <= char <= '\u9fff':
            return char
    
    # 英文名取首字母
    first_char = name[0].upper()
    if first_char.isalpha():
        return first_char
    
    return name[0] if name else "?"


def generate_avatar(user_id: str, name: str, output_dir: str, size: int = 200) -> str:
    """
    生成头像图片并保存
    返回文件名
    """
    # 根据user_id确定颜色
    color_index = sum(ord(c) for c in user_id) % len(AVATAR_COLORS)
    color1, color2 = AVATAR_COLORS[color_index]
    
    # 创建渐变背景
    img = Image.new('RGB', (size, size), color1)
    draw = ImageDraw.Draw(img)
    
    # 简单的垂直渐变
    c1 = tuple(int(color1.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    c2 = tuple(int(color2.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    
    for y in range(size):
        ratio = y / size
        r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
        g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
        b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
        draw.line([(0, y), (size, y)], fill=(r, g, b))
    
    # 获取首字母
    initials = get_initials(name)
    
    # 绘制文字
    try:
        # 尝试使用系统字体
        font_size = size // 2
        try:
            # Windows 中文字体
            font = ImageFont.truetype("msyh.ttc", font_size)
        except:
            try:
                # macOS 中文字体
                font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", font_size)
            except:
                try:
                    # Linux 字体
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                except:
                    font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # 计算文字位置（居中）
    bbox = draw.textbbox((0, 0), initials, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - bbox[1]
    
    # 绘制白色文字
    draw.text((x, y), initials, fill='white', font=font)
    
    # 保存文件
    filename = f"{user_id[:12]}.png"
    filepath = os.path.join(output_dir, filename)
    img.save(filepath, 'PNG', optimize=True)
    
    return filename


def get_avatar_url(user_id: str, filename: str) -> str:
    """
    获取头像的仓库URL
    使用GitHub raw地址
    """
    return f"{GITHUB_RAW_BASE}/{AVATARS_DIR}/{filename}"


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


def generate_sponsors_json(sponsors_data: Dict[str, dict], output_dir: str) -> dict:
    """生成赞助商JSON数据并生成头像"""
    sponsors_list = []
    
    # 创建头像目录
    avatars_dir = os.path.join(output_dir, AVATARS_DIR)
    os.makedirs(avatars_dir, exist_ok=True)
    print(f"[INFO] 头像保存目录: {avatars_dir}")
    
    for user_id, data in sponsors_data.items():
        tier_id = get_tier_id(data["total_amount"])
        
        # 清理名称
        name = data["name"] or f"匿名支持者_{user_id[:5]}"
        
        # 生成头像
        avatar_filename = generate_avatar(user_id, name, avatars_dir)
        
        sponsor = {
            "id": user_id,
            "name": name,
            "avatarUrl": get_avatar_url(user_id, avatar_filename),
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
    
    # 获取输出目录
    output_dir = os.path.dirname(os.path.abspath(output_path)) or "."
    
    # 生成JSON和头像
    result, tier_counts, total_amount = generate_sponsors_json(sponsors_data, output_dir)
    
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
    print(f"[INFO] 头像已保存到: {os.path.join(output_dir, AVATARS_DIR)}/")
    print(f"\n[TIP] 推送到 GitHub 后，头像URL将生效:")
    print(f"      git add . && git commit -m 'update sponsors' && git push")


if __name__ == "__main__":
    main()
