# 今日热闻 - 定时邮件推送

自动抓取微博热搜、知乎热榜、百度热搜等内容，通过邮件定时推送到你邮箱。

## 功能

- 🔴 **微博热搜** — 抓取微博实时热搜榜（含热度值、爆/沸/新标签）
- 💡 **知乎热榜** — 抓取知乎热榜话题（含链接）
- 🔵 **百度热搜** — 抓取百度实时热搜榜（含热度值）
- 📬 **定时推送** — 支持早晚报定时发送（如 09:00 / 18:00）
- 🖥️ **美观 HTML** — 移动端友好的邮件模板
- 🔍 **预览模式** — 终端预览内容，确认无误再发

## 快速开始

### 1. 安装依赖

```bash
cd hotmail
pip install -r requirements.txt
```

### 2. 配置邮箱

编辑 `config.yaml`，填入你的邮箱信息：

```yaml
mail:
  smtp_server: "smtp.qq.com"
  smtp_port: 465
  sender_email: "your_email@qq.com"
  sender_password: "your_auth_code"   # 不是登录密码！
  recipients:
    - "your_email@qq.com"
```

**获取 SMTP 授权码：**

| 邮箱 | SMTP 服务器 | 端口 | 获取方式 |
|------|-------------|------|----------|
| QQ邮箱 | smtp.qq.com | 465 | 设置 → 账户 → POP3/SMTP → 生成授权码 |
| 163邮箱 | smtp.163.com | 465 | 设置 → POP3/SMTP/IMAP → 开启 → 授权码 |
| Gmail | smtp.gmail.com | 587 | Google 账户 → 安全性 → App Passwords |
| Outlook | smtp.office365.com | 587 | 开启双重验证 → App Password |

### 3. 测试

```bash
# 预览模式（只抓取，不发送）
python main.py --dry

# 立即发送一次
python main.py --now
```

### 4. 运行

```bash
# 定时模式（按 config.yaml 配置的时间发送）
python main.py
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `(无)` | 定时模式，按 yaml 配置时间发送 |
| `--now` | 立即抓取并发送一次 |
| `--dry` | 仅抓取并打印到终端预览 |

## 配置说明

```yaml
mail:
  smtp_server: "smtp.qq.com"    # SMTP 服务器
  smtp_port: 465                 # 端口 (465=SSL, 587=TLS)
  sender_email: "xxx@qq.com"     # 发件邮箱
  sender_password: "xxx"         # SMTP 授权码
  sender_name: "今日热闻"          # 发件人名称
  recipients: ["xxx@qq.com"]     # 收件人列表

content:
  weibo: true                    # 开启微博热搜
  zhihu: true                    # 开启知乎热榜
  baidu: false                   # 开启百度热搜
  limit: 20                      # 每个来源显示前 N 条

schedule:
  enabled: true                  # 开启定时
  times: ["09:00", "18:00"]     # 发送时间
```

## 项目结构

```
hotmail/
├── main.py              # 主入口
├── config.yaml          # 配置文件
├── requirements.txt     # 依赖
├── README.md            # 说明文档
└── src/
    ├── __init__.py
    ├── config.py        # 配置加载
    ├── scheduler.py     # 定时调度
    ├── scraper/
    │   ├── __init__.py
    │   ├── weibo.py     # 微博热搜抓取
    │   ├── zhihu.py     # 知乎热搜抓取
    │   └── baidu.py     # 百度热搜抓取
    └── mail/
        ├── __init__.py  # 邮件发送 (SMTP)
        └── template.py  # HTML 邮件模板
```

## 定时任务

程序会保持前台运行，按配置的时间自动发送。如果需要后台运行：

- **Linux/Mac**: 使用 `nohup` 或 `screen`
- **Windows**: 使用任务计划程序，定时运行 `python main.py --now`
