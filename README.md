# clippin-jimmy

两个人用终端聊天，复制或划选文本后会自动发给对方并在对方终端显示。两边都连同一台中继，不需要公网 IP。划词不会弹出浮窗或提示，只是把选中内容写入剪贴板。

## 安装（一次即可）

在项目目录里，用**准备用来运行的那个** `python` 安装：

```bash
python -m pip install -e .
```

装完后，这个 Python 环境里就可以直接运行 `jimmy` / `clippin-jimmy`（或继续用 `python -m client` / `python -m app`）。不要用 A 环境安装、B 环境运行。

## 本机试跑

终端 1 起中继：

```bash
clippin-jimmy
```

若 8000 端口已被占用：

```bash
clippin-jimmy --port 8765
```

并把客户端里的 `--cheat` 改成对应端口。

终端 2、3 各开一个客户端（显示名不同，房间口令相同）：

```bash
jimmy --cheat http://127.0.0.1:8000 --room jimmy --name 朱工
jimmy --cheat http://127.0.0.1:8000 --room jimmy --name 对方
```

- 输入一行回车：对方终端出现 `[chat] ...`
- 切到别的 App 复制文本：对方终端出现 `[clip] ...`
- 切到别的 App 划选文本：自动写入剪贴板，对方终端同样出现 `[clip] ...`
- 关终端即停止剪贴板与划词监听

划词依赖本机 Node.js（用于 [selection-hook](https://github.com/0xfullex/selection-hook)）。macOS 还需在「系统设置 > 隐私与安全性 > 辅助功能」中勾选运行 `jimmy` 的应用（Terminal / iTerm / Cursor），然后重启客户端。

Linux 若读不到剪贴板，需安装 `xclip` 或 `xsel`。

## 部署到国内云主机

1. 把代码拷到阿里云 / 腾讯云轻量等机器。
2. `python -m pip install -e .`
3. 云厂商控制台把安全组入站放行 `8000`。
4. 运行 `clippin-jimmy`
5. 把 `http://公网IP:8000` 发给对方，两边都执行：

```bash
jimmy --cheat http://公网IP:8000 --room 你们的口令 --name 自己的名字
```

用 IP + 端口即可，不必先备案。以后若绑域名并走 80/443，再考虑备案。

## 以后加插件

在 `client/plugins/` 里加一个类，实现 `start(bus)` 和 `on_message(msg)`，再把它加入 `client/plugins/__init__.py` 的 `ENABLED` 列表。`bus.send(type, text)` 会发到中继。
