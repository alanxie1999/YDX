# 配置指南

## 快速配置步骤

### 1. 创建全局配置

```bash
cp config/global_config.example.json config/global_config.json
```

编辑 `config/global_config.json`：

```json
{
    "groups": {
        "zq_group": [群 ID],  // 盘口群 ID
        "zq_bot": 机器人 ID    // 开奖机器人 ID
    }
}
```

### 2. 创建用户配置

```bash
mkdir -p users/你的账号名
cp users/_template/example_config.json users/你的账号名/你的账号名_config.json
cp users/_template/presets.json.default users/你的账号名/presets.json
cp users/_template/state.json.default users/你的账号名/state.json
```

编辑 `users/你的账号名/你的账号名_config.json`，必填字段：

```json
{
    "telegram": {
        "api_id": 从 my.telegram.org 获取，
        "api_hash": "从 my.telegram.org 获取",
        "session_name": "会话名（不带 .session）",
        "user_id": 你的 Telegram user_id"
    },
    "account": {
        "name": "账号展示名"
    },
    "zhuque": {
        "cookie": "你的 cookie",
        "x_csrf": "你的 csrf"
    },
    "admin_console": {
        "mode": "telegram_id",
        "telegram_id": {
            "chat_id": 管理员 chat_id"
        }
    }
}
```

### 3. 放置 session 文件

将 `.session` 文件放到 `users/你的账号名/` 目录下。

### 4. 启动

```bash
python3 main_multiuser.py
```

## 获取必要信息的步骤

### Telegram api_id/api_hash

1. 访问 https://my.telegram.org
2. 登录你的 Telegram 账号
3. 点击 "API development tools"
4. 创建一个新应用
5. 复制 `api_id` 和 `api_hash`

### Telegram user_id 和 chat_id

1. 在 Telegram 中搜索 @userinfobot
2. 发送任意消息，它会返回你的 user_id
3. chat_id 可以是你的 private chat ID 或群组 ID

### 朱雀 cookie 和 csrf

1. 浏览器登录朱雀
2. 打开开发者工具（F12）
3. 在 Network 标签任意请求中查看 Headers
4. 复制 `cookie` 中的 `socute` 值
5. 复制 `x-csrf` header 值

## 常见问题

### 没有 AI 配置能启动吗？

**可以！** 当前版本使用简单跟随策略，不需要 AI 配置。

### Session 文件在哪里？

首次运行时如果没有 session 文件，脚本会提示你进行电话登录。登录后会自动生成 session 文件。

### 如何配置多个账号？

重复步骤 2，创建多个用户目录即可：
- `users/user1/user1_config.json`
- `users/user2/user2_config.json`
- ...
