<p align="center">
  <img src="https://img.shields.io/badge/Python-3.7+-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/status-active-success?style=flat-square" alt="Status">
</p>

<h1 align="center">📰 今日热闻</h1>
<p align="center"><b>自动抓取微博 · 知乎 · 百度热搜，邮件定时推送</b></p>

<p align="center">
  每天早上 8:00 准时送达热点速报<br>
  每天晚上 19:00 推送当日要闻回顾
</p>

---

## ✨ 功能

| 来源 | 数据 | 标签 |
|------|------|------|
| 🔴 **微博热搜** | 实时热搜榜 Top50 | 爆 / 沸 / 新 / 荐 + 热度值 |
| 💡 **知乎热榜** | 热榜话题 Top30 | 沸 / 热 / 新 + 回答数·关注数 |
| 🔵 **百度热搜** | 实时热搜榜 Top50 | 热度值 |
| 📬 **定时推送** | 早报 08:00 / 晚报 19:00 | 可自定义时间和频率 |
| 🖥️ **精美模板** | 移动端适配的 HTML 邮件 | 响应式设计，阅读体验佳 |
| 🔍 **预览模式** | 终端预览内容，确认无误再发 | 不浪费邮件配额 |

---

## 🚀 快速开始

### 1️⃣ 安装依赖

```bash
cd hotmail
pip install -r requirements.txt
```

### 2️⃣ 配置邮箱

复制配置模板并编辑：

```bash
cp config.yaml.example config.yaml   # Linux / Mac
copy config.yaml.example config.yaml  # Windows
```

编辑 `config.yaml`，填入你的邮箱信息：

```yaml
mail:
  smtp_server: "smtp.qq.com"        # SMTP 服务器
  smtp_port: 465                     # 465=SSL, 587=TLS
  sender_email: "your_email@qq.com"
  sender_password: "your_auth_code"   # ⚠️ 不是登录密码！
  recipients:
    - "your_email@qq.com"
```

<details>
<summary><b>📮 获取 SMTP 授权码</b></summary>
<br>

| 邮箱 | SMTP 服务器 | 端口 | 获取方式 |
|------|-------------|------|----------|
| **QQ邮箱** | `smtp.qq.com` | 465 | 设置 → 账户 → POP3/SMTP → 生成授权码 |
| **163邮箱** | `smtp.163.com` | 465 | 设置 → POP3/SMTP/IMAP → 开启 → 授权码 |
| **Gmail** | `smtp.gmail.com` | 587 | Google 账户 → 安全性 → App Passwords |
| **Outlook** | `smtp.office365.com` | 587 | 开启双重验证 → App Password |

</details>

### 3️⃣ 测试

```bash
# 预览模式 — 只抓取，不发送（推荐先试试这个）
python main.py --dry

# 立即发送 — 抓取 + 发邮件
python main.py --now
```

### 4️⃣ 运行

```bash
# 定时模式 — 按 config.yaml 配置的时间自动发送
python main.py
```

---

## 📋 命令行参数

| 参数 | 说明 |
|------|------|
| `(无参数)` | 定时模式，按配置时间（默认 08:00 / 19:00）自动发送 |
| `--now` | 立即抓取并发送一次 |
| `--dry`  | 仅终端预览，不发送邮件 |

---

## ⚙️ 配置详解

```yaml
mail:
  smtp_server: "smtp.qq.com"      # SMTP 服务器地址
  smtp_port: 465                   # 端口: 465=SSL, 587=TLS
  sender_email: "xxx@qq.com"      # 发件邮箱
  sender_password: "xxx"          # SMTP 授权码
  sender_name: "今日热闻"          # 发件人显示名称
  recipients: ["xxx@qq.com"]      # 收件人列表（可多个）

content:
  weibo: true                      # 微博热搜
  zhihu: true                      # 知乎热榜
  baidu: false                     # 百度热搜（默认关闭）
  limit: 20                        # 每个来源显示前 N 条

schedule:
  enabled: true                    # 是否启用定时发送
  times:                           # 发送时间（24小时制）
    - "08:00"                      # 早报
    - "19:00"                      # 晚报
```

---

## 📁 项目结构

```
hotmail/
├── main.py                 # 🚀 主入口
├── config.yaml             # 🔒 配置文件（已加入 .gitignore）
├── config.yaml.example     # 📝 配置模板
├── requirements.txt        # 📦 依赖
├── LICENSE                 # 📄 MIT 许可证
├── README.md               # 📖 说明文档
└── src/
    ├── __init__.py
    ├── config.py            # 配置加载
    ├── scheduler.py         # 定时调度
    ├── scraper/
    │   ├── __init__.py      # HotItem 数据模型 + BaseHotScraper 基类
    │   ├── weibo.py         # 微博热搜抓取
    │   ├── zhihu.py         # 知乎热榜抓取
    │   └── baidu.py         # 百度热搜抓取
    └── mail/
        ├── __init__.py      # SMTP 邮件发送
        └── template.py      # HTML 邮件模板
```

---

## 🌙 后台运行

| 平台 | 方式 |
|------|------|
| **Linux / Mac** | `nohup python main.py &` 或 `screen` / `tmux` |
| **Windows** | 任务计划程序 → 定时运行 `python main.py --now` |

---

## 🛠️ 自定义开发

想增加新的热搜来源？只需三步：

1. 在 `src/scraper/` 下新建爬虫文件（参考 `zhihu.py` 的 API + HTML 双渠道模式）
2. 继承 `BaseHotScraper`，实现 `fetch()` 方法
3. 在 `main.py` 的 `fetch_all_hot()` 中注册爬虫

---

## 📄 许可证

[MIT License](LICENSE)
