[app]
title = 极速换肤2.0.0  # APP名称
version = 2.0.0  # 版本号（与功能逻辑一致）
package.name = gameskinmod  # 包名（小写无空格，匹配代码逻辑）
package.domain = org.yourname  # 替换为你的自定义域名（如org.username）
source.dir = .  # 源码根目录（与main.py位置一致）
source.include_exts = py,png,jpg,kv,atlas,bin,lh,lmat  # 包含游戏资源文件后缀
source.exclude_exts = pyc,pyo,pyd,gitignore,md,__pycache__  # 排除无用文件
source.include_dirs = assets  # 必须保留，匹配代码中内置文件提取逻辑
source.exclude_dirs = .git,.buildozer,bin,temp  # 排除构建/缓存目录

# 依赖配置（严格匹配代码中使用的库版本）
requirements = python3,kivy==2.3.0,plyer==2.1.0,python-dateutil==2.8.2,pillow==10.2.0,cython==0.29.36

# 安卓配置（解决参数弃用+权限适配，关键！）
android.minapi = 24  # 替代弃用的android.sdk，指定最低安卓版本（安卓7+）
android.api = 33  # 目标安卓版本（适配安卓13，兼容性最优）
android.ndk = 25b  # 与Kivy 2.3.0兼容的NDK版本
android.buildtools = 33.0.2  # 匹配API 33的构建工具
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE  # 安卓13+存储权限
android.request_legacy_external_storage = True  # 安卓10+兼容旧存储模式
android.gradle_dependencies = androidx.core:core-ktx:1.12.0  # 支持动态权限申请
android.icon = icon.png  # 确保仓库根目录有512x512的icon.png（无后缀错误）
android.release = False  # Debug模式（便于测试）

[buildozer]
log_level = 2  # 日志级别（2=详细，便于排查错误）
warn_on_root = 1  # 根目录警告（避免权限问题）
build_dir = .buildozer  # 构建缓存目录（集中管理）
android.sdk_path = ~/.buildozer/android/platform  # 固定SDK路径，减少下载次数