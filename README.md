<div align="center">

<img src="cover.png" alt="clippin-jimmy" width="360" />

# clippin-jimmy

终端聊天与剪贴板同步

[![npm](https://img.shields.io/npm/v/clippin-jimmy.svg)](https://www.npmjs.com/package/clippin-jimmy)
[![license](https://img.shields.io/npm/l/clippin-jimmy.svg)](https://www.npmjs.com/package/clippin-jimmy)
[![node](https://img.shields.io/node/v/clippin-jimmy.svg)](https://www.npmjs.com/package/clippin-jimmy)

</div>

需要 Node.js 18+ 和 Python 3.10+。

## 安装

### npm（需要 Node.js 18+）

```bash
npm install -g clippin-jimmy
```

安装后会自动创建 Python 虚拟环境并安装依赖。

npm 11+ 默认会拦截 install 脚本，若安装失败或警告 `allow-scripts`，可先执行：

```bash
npm config set allow-scripts=clippin-jimmy --location=user
npm install -g clippin-jimmy
```

### GitHub 安装脚本（推荐，无需 Node.js）

仅需 Git 与 Python 3.10+，可绕过 npm 的脚本限制：

```bash
curl -fsSL https://raw.githubusercontent.com/2p1c/clippin-jimmy/main/install.sh | bash
```

脚本会将项目克隆到 `~/.clippin-jimmy`，并在 `~/.local/bin` 创建 `clippin-jimmy` 与 `jimmy` 命令。安装完成后请确认 `~/.local/bin` 在 PATH 中：

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## 启动

中继：

```bash
clippin-jimmy
```

客户端：

```bash
jimmy --cheat http://127.0.0.1:8000 --room 口令 --name 显示名
```
