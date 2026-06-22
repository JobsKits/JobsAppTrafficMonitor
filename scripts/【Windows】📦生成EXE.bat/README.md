# `JobsAppTrafficMonitor Windows EXE 构建入口`

![Jobs出品，必属精品](https://picsum.photos/1500/400)

[toc]

---

## 🔥 <font id=前言>前言</font>

把完整项目放到 Windows 电脑，双击 `【Windows】📦生成EXE.bat` 即可构建自包含 EXE。脚本运行时打印自身内置说明，不读取本 README。macOS 无法直接生成可靠的 Windows EXE。

## 一、环境体检

- 优先查找 Windows Python Launcher 或 `python`。
- 缺少 Python 时通过 `winget` 安装 Python 3.13。
- 自动在项目 `build/windows-venv` 创建内部构建环境。
- 自动安装 PySide6 与 PyInstaller，用户不需要手动输入 Python 命令。

## 二、输出结果

```text
dist/windows/JobsAppTrafficMonitor.exe
```

EXE 包含 Python 与 PySide6 运行环境，复制到其他 Windows 电脑运行时不需要再安装它们。

## 三、功能边界

Windows ETW 流量采集器仍处于接口阶段。构建入口可以生成 EXE，但在 Windows 实现完整的按 App 流量统计前，不应把该 EXE 作为正式版本分发。

## 四、风险说明

- 环境缺失时会安装 Python，并从 PyPI 下载 PySide6 与 PyInstaller。
- 未进行 Windows 代码签名，SmartScreen 可能提示未知发布者。
- 构建必须在 Windows 上执行，当前 macOS 维护环境不会实际运行此脚本。
