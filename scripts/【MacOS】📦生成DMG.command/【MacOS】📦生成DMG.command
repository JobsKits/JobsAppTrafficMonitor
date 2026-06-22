#!/bin/zsh
# 脚本自述：双击构建 JobsAppTrafficMonitor macOS 安装包；先打印内置说明并等待确认，再检查构建环境、生成自包含 App 并封装 DMG。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")" && pwd)"
SCRIPT_PATH="${SCRIPT_DIR}/$(basename -- "$0")"
SCRIPT_BASENAME=$(basename "$0" | sed 's/\.[^.]*$//')
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LOG_FILE="/tmp/${SCRIPT_BASENAME}.log"
# 打印写死在脚本内部的自述，并在安装依赖或生成构建产物前等待确认。
show_script_intro_and_wait() {
  clear
  echo "============================== 脚本自述 =============================="
  echo "脚本名称：${SCRIPT_PATH}"
  echo "核心用途：构建自包含 JobsAppTrafficMonitor.app，并封装为 macOS DMG 安装包。"
  echo "影响范围：缺少依赖时会安装 Homebrew、Python、PySide6、PyInstaller；项目 build/dist 会生成构建产物。"
  echo "运行策略：确认前不修改环境或文件；按 Ctrl+C 可取消。"
  echo "签名边界：仅执行本机临时签名，不包含 Developer ID 和苹果公证。"
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
# 检查 DMG 构建所需的全部 Homebrew formula 和系统工具。
check_build_environment() {
  ensure_homebrew
  ensure_brew_formula python
  ensure_brew_formula pyside
  ensure_brew_formula pyinstaller

  PYTHON_BIN="$(find_brew_python)"
  PYINSTALLER_BIN="$("$BREW_BIN" --prefix)/bin/pyinstaller"
  if [[ -z "$PYTHON_BIN" ]] || ! verify_python_module "$PYTHON_BIN" PySide6; then
    error_echo "Python / PySide6 环境验证失败。"
    return 1
  fi
  if [[ ! -x "$PYINSTALLER_BIN" ]]; then
    error_echo "未找到 PyInstaller：${PYINSTALLER_BIN}"
    return 1
  fi
  if [[ ! -x "/usr/bin/hdiutil" ]]; then
    error_echo "系统缺少 hdiutil，无法生成 DMG。"
    return 1
  fi
  QT_PLUGINS_DIR="$("$PYTHON_BIN" -c 'from PySide6.QtCore import QLibraryInfo; print(QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath))')"
  QT_PLATFORMS_DIR="${QT_PLUGINS_DIR}/platforms"
  if [[ ! -f "${QT_PLATFORMS_DIR}/libqcocoa.dylib" ]]; then
    error_echo "未找到 Qt macOS 平台插件：${QT_PLATFORMS_DIR}/libqcocoa.dylib"
    return 1
  fi
  success_echo "DMG 构建环境体检通过。"
}
# 读取项目版本号，用于生成稳定的安装包文件名。
read_project_version() {
  PYTHONPATH="${PROJECT_ROOT}/src" "$PYTHON_BIN" -c "from jobs_app_traffic_monitor import __version__; print(__version__)"
}
# 使用 PyInstaller 生成自包含 macOS App。
build_macos_app() {
  info_echo "正在生成自包含 macOS App……"
  mkdir -p "${PROJECT_ROOT}/build/pyinstaller-spec" "${PROJECT_ROOT}/build/pyinstaller-work" "${PROJECT_ROOT}/dist"
  "$PYINSTALLER_BIN" \
    --noconfirm \
    --clean \
    --windowed \
    --name "JobsAppTrafficMonitor" \
    --paths "${PROJECT_ROOT}/src" \
    --add-binary "${QT_PLATFORMS_DIR}:platforms" \
    --specpath "${PROJECT_ROOT}/build/pyinstaller-spec" \
    --workpath "${PROJECT_ROOT}/build/pyinstaller-work" \
    --distpath "${PROJECT_ROOT}/dist" \
    "${PROJECT_ROOT}/src/jobs_app_traffic_monitor/__main__.py" 2>&1 | tee -a "$LOG_FILE"

  APP_PATH="${PROJECT_ROOT}/dist/JobsAppTrafficMonitor.app"
  if [[ ! -d "$APP_PATH" ]]; then
    error_echo "PyInstaller 未生成目标 App：${APP_PATH}"
    return 1
  fi

  if ! find "$APP_PATH" -type f -path '*/platforms/libqcocoa.dylib' -print -quit | grep -Fq 'libqcocoa.dylib'; then
    error_echo "App 缺少 Qt cocoa 平台插件，已终止 DMG 封装。"
    return 1
  fi

  /usr/bin/codesign --force --deep --sign - "$APP_PATH" 2>&1 | tee -a "$LOG_FILE"
  /usr/bin/codesign --verify --deep --strict "$APP_PATH" 2>&1 | tee -a "$LOG_FILE"
  success_echo "macOS App 已生成：${APP_PATH}"
}
# 仅清理当前脚本创建的临时 DMG 目录。
cleanup_staging_directory() {
  if [[ -n "${STAGING_DIR:-}" && "$STAGING_DIR" == /tmp/JobsAppTrafficMonitor.* && -d "$STAGING_DIR" ]]; then
    /bin/rm -rf -- "$STAGING_DIR"
  fi
}
# 将 App 与 Applications 快捷入口封装成压缩 DMG。
build_dmg() {
  local version=""
  local architecture=""
  version="$(read_project_version)"
  architecture="$(get_cpu_arch)"
  DMG_PATH="${PROJECT_ROOT}/dist/JobsAppTrafficMonitor-${version}-macOS-${architecture}.dmg"

  if [[ -e "$DMG_PATH" ]]; then
    local backup_path="${DMG_PATH%.dmg}-$(date +%Y%m%d-%H%M%S).dmg"
    warn_echo "目标 DMG 已存在，旧文件移动为：${backup_path}"
    mv "$DMG_PATH" "$backup_path"
  fi

  STAGING_DIR="$(mktemp -d "/tmp/JobsAppTrafficMonitor.XXXXXX")"
  trap cleanup_staging_directory EXIT INT TERM
  /usr/bin/ditto "$APP_PATH" "${STAGING_DIR}/JobsAppTrafficMonitor.app"
  ln -s "/Applications" "${STAGING_DIR}/Applications"

  /usr/bin/hdiutil create \
    -volname "JobsAppTrafficMonitor" \
    -srcfolder "$STAGING_DIR" \
    -format UDZO \
    -ov \
    "$DMG_PATH" 2>&1 | tee -a "$LOG_FILE"

  success_echo "DMG 已生成：${DMG_PATH}"
  /usr/bin/open -R "$DMG_PATH"
}
# 编排内置自述、初始化、环境体检、App 构建与 DMG 封装。
main() {
  show_script_intro_and_wait # 首先打印脚本内置自述并等待用户确认。
  initialize_script_environment # 确认后初始化 Shell 选项、日志和共享函数。
  check_build_environment # 检查并按需安装完整 macOS 构建环境。
  build_macos_app # 使用 PyInstaller 生成自包含 macOS App。
  build_dmg # 将 App 与 Applications 快捷入口封装为 DMG。
}

main "$@"
