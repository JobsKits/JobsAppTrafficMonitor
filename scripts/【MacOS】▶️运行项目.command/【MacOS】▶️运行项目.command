#!/bin/zsh
# 脚本自述：双击启动 JobsAppTrafficMonitor 源码；先打印内置说明并等待确认，再检查并按需安装 Homebrew、Python、PySide6，最后启动桌面 App。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")" && pwd)"
SCRIPT_PATH="${SCRIPT_DIR}/$(basename -- "$0")"
SCRIPT_BASENAME=$(basename "$0" | sed 's/\.[^.]*$//')
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LOG_FILE="/tmp/${SCRIPT_BASENAME}.log"
# 打印写死在脚本内部的自述，并在任何环境安装或项目启动前等待确认。
show_script_intro_and_wait() {
  clear
  echo "============================== 脚本自述 =============================="
  echo "脚本名称：${SCRIPT_PATH}"
  echo "核心用途：自动检查运行环境并启动 JobsAppTrafficMonitor 桌面界面。"
  echo "影响范围：缺少依赖时会安装 Homebrew、Python 和 PySide6；不会自动升级已安装软件。"
  echo "运行策略：确认前不修改环境；按 Ctrl+C 可取消。"
  echo "日志位置：${LOG_FILE}"
  echo "======================================================================="
  echo ""
  read -r "?👉 已了解脚本用途与影响，按回车继续；按 Ctrl+C 取消：" _
}
# 初始化 Shell 选项、日志文件和共享环境函数。
initialize_script_environment() {
  setopt NO_NOMATCH
  setopt PIPE_FAIL
  setopt ERR_EXIT
  : > "$LOG_FILE"
  source "${PROJECT_ROOT}/scripts/_shared/macos_environment.zsh"
}
# 检查源码运行所需的 Homebrew、Python 与 PySide6。
check_runtime_environment() {
  ensure_homebrew
  ensure_brew_formula python
  ensure_brew_formula pyside

  PYTHON_BIN="$(find_brew_python)"
  if [[ -z "$PYTHON_BIN" ]]; then
    error_echo "未找到 Homebrew Python。"
    return 1
  fi
  if ! verify_python_module "$PYTHON_BIN" PySide6; then
    error_echo "已安装 pyside，但 ${PYTHON_BIN} 无法导入 PySide6。"
    return 1
  fi
  success_echo "运行环境体检通过。"
}
# 使用项目源码启动桌面界面，不要求用户手动进入虚拟环境。
launch_application() {
  info_echo "正在启动 JobsAppTrafficMonitor……"
  cd "$PROJECT_ROOT" || return 1
  PYTHONPATH="${PROJECT_ROOT}/src" "$PYTHON_BIN" -m jobs_app_traffic_monitor 2>&1 | tee -a "$LOG_FILE"
}
# 编排内置自述、初始化、环境体检和项目启动。
main() {
  show_script_intro_and_wait # 首先打印脚本内置自述并等待用户确认。
  initialize_script_environment # 确认后初始化 Shell 选项、日志和共享函数。
  check_runtime_environment # 检查并按需安装 Homebrew、Python 与 PySide6。
  launch_application # 环境就绪后启动 JobsAppTrafficMonitor 桌面界面。
}

main "$@"
