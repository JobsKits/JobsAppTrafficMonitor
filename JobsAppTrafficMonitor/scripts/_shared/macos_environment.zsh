#!/bin/zsh
# 脚本自述：提供 JobsAppTrafficMonitor macOS 入口共用的 Homebrew、Python、PySide6 环境检查与彩色日志函数；仅供其它脚本 source，不独立执行。
# 同步输出到终端与脚本日志。
log()            { echo -e "$1" | tee -a "$LOG_FILE"; }
# 输出普通信息。
info_echo()      { log "\033[1;34mℹ $1\033[0m"; }
# 输出成功信息。
success_echo()   { log "\033[1;32m✔ $1\033[0m"; }
# 输出警告信息。
warn_echo()      { log "\033[1;33m⚠ $1\033[0m"; }
# 输出错误信息。
error_echo()     { log "\033[1;31m✖ $1\033[0m"; }
# 输出高亮信息。
highlight_echo() { log "\033[1;36m🔹 $1\033[0m"; }
# 输出次要说明。
gray_echo()      { log "\033[0;90m$1\033[0m"; }
# 返回当前 Mac 的 CPU 架构。
get_cpu_arch() {
  [[ "$(uname -m)" == "arm64" ]] && echo "arm64" || echo "x86_64"
}
# 按 Jobs 约定顺序查找 Homebrew。
find_brew() {
  if command -v brew >/dev/null 2>&1; then
    command -v brew
  elif [[ -x "/opt/homebrew/bin/brew" ]]; then
    echo "/opt/homebrew/bin/brew"
  elif [[ -x "/usr/local/bin/brew" ]]; then
    echo "/usr/local/bin/brew"
  fi
}
# 缺少 Homebrew 时调用官方安装脚本。
install_homebrew() {
  warn_echo "未检测到 Homebrew，将调用官方安装脚本。过程中可能要求输入本机管理员密码。"
  NONINTERACTIVE=1 /bin/bash -c "$(/usr/bin/curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
}
# 确保 Homebrew 存在，并让当前终端立即加载 shellenv。
ensure_homebrew() {
  BREW_BIN="$(find_brew)"
  if [[ -z "$BREW_BIN" ]]; then
    install_homebrew || {
      error_echo "Homebrew 安装失败，请查看日志：${LOG_FILE}"
      return 1
    }
    BREW_BIN="$(find_brew)"
  fi

  if [[ -z "$BREW_BIN" ]]; then
    error_echo "Homebrew 安装完成后仍无法定位 brew。"
    return 1
  fi

  eval "$("$BREW_BIN" shellenv)"
  success_echo "Homebrew 可用：${BREW_BIN}（$(get_cpu_arch)）"
}
# 缺少指定 formula 时通过 Homebrew 自动安装。
ensure_brew_formula() {
  local formula_name="$1"
  if "$BREW_BIN" list --formula --versions "$formula_name" >/dev/null 2>&1; then
    success_echo "环境已存在：${formula_name}"
    return 0
  fi

  info_echo "正在安装缺失环境：${formula_name}"
  "$BREW_BIN" install "$formula_name" 2>&1 | tee -a "$LOG_FILE"
}
# 返回 Homebrew Python 的稳定入口。
find_brew_python() {
  local python_prefix=""
  python_prefix="$("$BREW_BIN" --prefix python 2>/dev/null)"
  if [[ -n "$python_prefix" && -x "${python_prefix}/libexec/bin/python3" ]]; then
    echo "${python_prefix}/libexec/bin/python3"
  elif command -v python3 >/dev/null 2>&1; then
    command -v python3
  fi
}
# 验证 Python 能导入指定模块。
verify_python_module() {
  local python_bin="$1"
  local module_name="$2"
  "$python_bin" -c "import ${module_name}" >/dev/null 2>&1
}
