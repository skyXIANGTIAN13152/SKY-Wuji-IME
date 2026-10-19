# 构建与验证

正式构建在 GitHub Actions 的 **Build SKY Wuji → Run workflow** 手动运行。它只生成待验收安装包，不自动发布 Release；公开版本在实机验收后发布。

自动检查包括：内置文件的 SHA-256 清单、个人设备文件排除、主题资源完整性、APK 中的资源复制清单、两种 ARM 架构引擎、APK 签名验证。原生引擎直接取自与源码版本一致的官方 Trime 3.3.12 APK，固定并核对下载哈希。

发布版本以 `app/build.gradle.kts` 为唯一来源，构建时自动设置内部版本和 APK 文件名，并核对最终 APK 的包名、版本名、版本号、原项目签名，以及 `queries/intent/action` 下的 `android.view.InputMethod` 声明。没有申请 `QUERY_ALL_PACKAGES` 权限。这样可在构建阶段阻止版本信息不一致、签名错误或语音查询声明被误删的安装包进入验收。

`python3 script/check-user-data-upgrade.py` 使用 Gradle 发行包内的 Kotlin 编译器，独立编译实际的用户配置更新策略并运行 11 项临时文件测试，不依赖旧 Android JVM 测试套件。覆盖新装、更新时缺失目标、未修改内置文件、个人修改、外部导入、新增同名文件冲突、缺失或空旧哈希、共享资源、不支持的目录目标与读取失败。仅 `rime/` 用户目录的同名既有文件受保护，共享资源正常更新。已保存的个人配置不会自动合并新版主题改动。

本项目未修改原生引擎。上游的 `testReleaseUnitTest` 在当前 AGP 默认配置中不存在，其旧 `GeneralStyleTest` 还引用了已经移除的 `Theme.decodeByConfigId`。发布流程不声称这些上游 JVM 测试已通过；首版采用构建、安装包检查和实际设备验收，验收结果单独记录。

设备验收项目：全新安装后的自动配置、已确认 V6 外观、中英文输入、退格、数字键盘、离线 wiki、切换到已启用的说点啥。语音识别模型在独立应用中配置，本项目不宣称测试了所有语音模型。
