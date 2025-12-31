#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爱发电API获取赞助者信息（含真实头像）

用法:
    1. 复制 config.example.ini 为 config.ini
    2. 填入你的 user_id 和 token
    3. python fetch_from_api.py

配置获取: https://afdian.com/dashboard/dev
"""

import json
import hashlib
import time
import requests
import configparser
import os
from typing import Dict, List, Optional

# API地址
API_URL = "https://afdian.com/api/open/query-sponsor"

# 赞助级别定义
TIERS = [
    {"id": "galaxy_guardian", "name": "银河守护者", "nameEn": "Galaxy Guardian", 
     "color": "#9B59B6", "particleType": "galaxy", "order": 100, "minAmount": 200},
    {"id": "starlight_patron", "name": "星空探索家", "nameEn": "Starlight Patron", 
     "color": "#E74C3C", "particleType": "firework", "order": 80, "minAmount": 100},
    {"id": "cosmic_supporter", "name": "极致合伙人", "nameEn": "Cosmic Supporter", 
     "color": "#3498DB", "particleType": "stars", "order": 60, "minAmount": 50},
    {"id": "beta_scout", "name": "星光先锋", "nameEn": "Starlight Pioneer", 
     "color": "#2ECC71", "particleType": "sparkle", "order": 40, "minAmount": 18},
    {"id": "early_supporter", "name": "爱心维护员", "nameEn": "Early Supporter", 
     "color": "#F39C12", "particleType": "none", "order": 20, "minAmount": 5},
]


def load_config() -> tuple:
    """从config.ini加载API配置"""
    config_path = os.path.join(os.path.dirname(__file__), "config.ini")
    
    if not os.path.exists(config_path):
        print("[ERROR] 找不到 config.ini 文件!")
        print("[TIP] 请复制 config.example.ini 为 config.ini 并填入API配置")
        return None, None
    
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    
    try:
        user_id = config.get('afdian', 'user_id')
        token = config.get('afdian', 'token')
        
        if '你的' in user_id or '你的' in token:
            print("[ERROR] 请在 config.ini 中填入真实的 user_id 和 token!")
            return None, None
            
        return user_id, token
    except Exception as e:
        print(f"[ERROR] 读取配置失败: {e}")
        return None, None


def generate_sign(user_id: str, token: str, params: dict, ts: int) -> str:
    """生成API签名"""
    params_str = json.dumps(params, separators=(',', ':'))
    kv_string = f"params{params_str}ts{ts}user_id{user_id}"
    sign = hashlib.md5((token + kv_string).encode()).hexdigest()
    return sign


def fetch_sponsors(user_id: str, token: str) -> List[dict]:
    """从爱发电API获取所有赞助者"""
    all_sponsors = []
    page = 1
    
    while True:
        ts = int(time.time())
        params = {"page": page}
        sign = generate_sign(user_id, token, params, ts)
        
        request_data = {
            "user_id": user_id,
            "params": json.dumps(params, separators=(',', ':')),
            "ts": ts,
            "sign": sign
        }
        
        try:
            response = requests.post(
                API_URL,
                json=request_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            data = response.json()
            
            if data.get('ec') != 200:
                print(f"[ERROR] API返回错误: {data.get('em', '未知错误')}")
                break
            
            sponsors = data.get('data', {}).get('list', [])
            if not sponsors:
                break
                
            all_sponsors.extend(sponsors)
            print(f"[INFO] 获取第{page}页，{len(sponsors)}位赞助者")
            
            # 检查是否还有下一页
            total_page = data.get('data', {}).get('total_page', 1)
            if page >= total_page:
                break
            page += 1
            
        except Exception as e:
            print(f"[ERROR] API请求失败: {e}")
            break
    
    return all_sponsors


def get_tier_id(total_amount: float) -> str:
    """根据总金额确定赞助级别"""
    for tier in TIERS:
        if total_amount >= tier["minAmount"]:
            return tier["id"]
    return "early_supporter"


def process_sponsors(api_sponsors: List[dict]) -> dict:
    """处理API返回的赞助者数据"""
    sponsors_list = []
    
    for sponsor in api_sponsors:
        user = sponsor.get('user', {})
        user_id = user.get('user_id', '')
        
        if not user_id:
            continue
        
        # 获取真实头像URL
        avatar_url = user.get('avatar', '')
        if not avatar_url:
            avatar_url = "https://pic1.afdiancdn.com/default/avatar/avatar-purple.png"
        
        # 获取累计金额
        total_amount = float(sponsor.get('all_sum_amount', 0))
        
        sponsor_data = {
            "id": user_id,
            "name": user.get('name', f'匿名_{user_id[:5]}'),
            "avatarUrl": avatar_url,  # 真实头像！
            "bio": "",
            "tier": get_tier_id(total_amount),
            "joinDate": sponsor.get('first_pay_time', '')[:7] if sponsor.get('first_pay_time') else "",
            "website": f"https://afdian.com/u/{user_id}"
        }
        sponsors_list.append(sponsor_data)
    
    # 按金额排序
    sponsors_list.sort(key=lambda x: next(
        (t['order'] for t in TIERS if t['id'] == x['tier']), 0
    ), reverse=True)
    
    return {
        "version": 1,
        "name": "RAL Sponsors",
        "description": f"RotatingArt Launcher 赞助者名单",
        "lastUpdated": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tiers": TIERS,
        "sponsors": sponsors_list
    }


def main():
    print("=" * 50)
    print("爱发电API获取赞助者（含真实头像）")
    print("=" * 50)
    
    # 加载配置
    user_id, token = load_config()
    if not user_id or not token:
        return
    
    print(f"[INFO] User ID: {user_id[:8]}...")
    
    # 获取赞助者
    print("\n[INFO] 正在从API获取赞助者列表...")
    api_sponsors = fetch_sponsors(user_id, token)
    
    if not api_sponsors:
        print("[ERROR] 未获取到任何赞助者数据")
        return
    
    print(f"\n[SUCCESS] 共获取 {len(api_sponsors)} 位赞助者")
    
    # 处理数据
    result = process_sponsors(api_sponsors)
    
    # 保存JSON
    output_path = os.path.join(os.path.dirname(__file__), "sponsors.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    
    print(f"[SUCCESS] 已保存到: {output_path}")
    
    # 显示头像示例
    print("\n[示例] 前3位赞助者头像:")
    for s in result['sponsors'][:3]:
        print(f"  - {s['name']}: {s['avatarUrl'][:60]}...")


if __name__ == "__main__":
    main()

