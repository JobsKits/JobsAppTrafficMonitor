# `JobsAppTrafficMonitor macOS 源码启动入口`

![Jobs出品，必属精品](https://picsum.photos/1500/400)

[toc]

---

## 🔥 <font id=前言>前言</font>

双击同目录的 `【MacOS】▶️运行项目.command` 即可启动项目，不需要手动创建虚拟环境或输入 Python 命令。运行时自述固定写在脚本内部，不读取本 README。

## 一、环境体检

脚本会依次检查：

1. [**Homebrew**](https://brew.sh/)
2. [**Python**](https://www.python.org/)
3. [**PySide6**](https://doc.qt.io/qtforpython-6/)

缺少 [**Homebrew**](https://brew.sh/) 时调用官方脚本安装；缺少 Python 或 PySide6 时分别执行对应的 Homebrew formula 安装。Homebrew 安装过程可能要求输入本机管理员密码。

## 二、运行方式

双击 `【MacOS】▶️运行项目.command`，阅读脚本打印的内置自述后按回车继续。关闭 App 后脚本结束。

## 三、日志

日志写入 `/tmp/【MacOS】▶️运行项目.log`。

## 四、风险说明

- 已存在的 Homebrew formula 不会自动升级。
- 仅在缺少依赖时安装，不执行 `brew update`、`brew upgrade` 或 `brew cleanup`。
- 最终 `.dmg` 成品自带运行依赖，普通用户运行成品时不会触发这些安装操作。
