# `JobsAppTrafficMonitor macOS DMG 构建入口`

![Jobs出品，必属精品](https://picsum.photos/1500/400)

[toc]

---

## 🔥 <font id=前言>前言</font>

双击 `【MacOS】📦生成DMG.command`，即可生成包含完整 Python、PySide6 和 Qt macOS 平台插件的安装包。运行时自述固定写在脚本内部，不读取本 README。

## 一、环境体检

脚本检查并按需安装：

- [**Homebrew**](https://brew.sh/)
- [**Python**](https://www.python.org/)
- [**PySide6**](https://doc.qt.io/qtforpython-6/)
- [**PyInstaller**](https://pyinstaller.org/)

缺少 Homebrew 时会调用官方安装脚本，过程中可能要求输入管理员密码。已安装的软件不会被自动升级。

## 二、输出结果

安装包输出到项目的 `dist` 目录，文件名格式为：

```text
JobsAppTrafficMonitor-版本号-macOS-架构.dmg
```

构建完成后 Finder 会自动定位该文件。DMG 内包含 `JobsAppTrafficMonitor.app` 和 `Applications` 快捷入口：可在 DMG 中直接双击 App 运行，也可将 App 拖到 `Applications` 完成安装。

## 三、签名边界

脚本执行本机临时签名，方便本机测试；没有使用 Apple Developer ID，也没有执行苹果公证。分发给其他 Mac 时，Gatekeeper 仍可能显示来源警告。正式公开分发需要开发者证书和公证流程。

## 四、日志

日志写入 `/tmp/【MacOS】📦生成DMG.log`。

## 五、未执行声明

脚本允许修改构建机的 Homebrew 环境并生成较大的构建产物，应由用户双击确认后执行；代码维护阶段只做静态检查，不自动运行真实构建。
