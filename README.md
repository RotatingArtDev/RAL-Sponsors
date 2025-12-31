# RAL Sponsors Repository

这是 RotatingArt Launcher 赞助者数据仓库的示例结构。

## 📁 仓库结构

```
RAL-Sponsors/
├── README.md           # 本说明文档
└── sponsors.json       # 赞助者数据
```

## 📋 数据格式说明

### sponsors.json

```json
{
    "version": 1,                    // 数据版本号
    "name": "RAL Sponsors",          // 仓库名称
    "description": "...",            // 描述
    "lastUpdated": "2026-01-01T...", // 最后更新时间 (ISO 8601)
    "tiers": [...],                  // 赞助级别定义
    "sponsors": [...]                // 赞助者列表
}
```

### 赞助级别 (tiers)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 级别唯一标识 |
| `name` | string | 中文名称 |
| `nameEn` | string | 英文名称 |
| `color` | string | 主题颜色 (HEX 格式) |
| `particleType` | string | 粒子效果类型 |
| `order` | int | 排序权重 (越高越靠前) |
| `minAmount` | int | 最低赞助金额 |

### 粒子效果类型 (particleType)

| 类型 | 效果描述 |
|------|----------|
| `none` | 无特效 |
| `sparkle` | 闪光点效果 - 基础级别 |
| `stars` | 星空效果 - 带流星 |
| `firework` | 烟花效果 - 星空背景 + 烟花绽放 |
| `galaxy` | 银河效果 - 旋转星系 |

### 赞助者 (sponsors)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 唯一标识 |
| `name` | string | 显示名称 |
| `avatarUrl` | string | 头像 URL (支持 GitHub 头像) |
| `bio` | string | 个人简介 (可选) |
| `tier` | string | 所属级别 ID |
| `joinDate` | string | 加入日期 (YYYY-MM 格式) |
| `website` | string | 个人网站 (可选) |

## 🎯 赞助级别对应关系

根据 [爱发电](https://afdian.com/a/RotatingartLauncher) 的赞助方案：

| 爱发电级别 | 对应 tier ID | 粒子效果 |
|-----------|-------------|----------|
| 银河守护者 | `galaxy_guardian` | 银河 (galaxy) |
| 星空探索家 | `starlight_patron` | 烟花 (firework) |
| 极致合伙人 | `cosmic_supporter` | 星空 (stars) |
| 星光先锋 | `beta_scout` | 闪光 (sparkle) |
| 爱心维护员 | `early_supporter` | 无 (none) |

## 🔗 仓库 URL 配置

应用会从以下地址获取数据：

- **GitHub**: `https://raw.githubusercontent.com/RotatingArtDev/RAL-Sponsors/main/sponsors.json`
- **Gitee (国内镜像)**: `https://gitee.com/daohei/RAL-Sponsors/raw/main/sponsors.json`

## 🤝 如何添加赞助者

1. Fork 本仓库
2. 编辑 `sponsors.json`
3. 在 `sponsors` 数组中添加新条目
4. 提交 Pull Request

---

Made with ❤️ by RotatingArtDev

