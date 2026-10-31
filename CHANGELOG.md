# Changelog

## 0.2.5

- 修复 9MU7 默认 cct contract 非法（0–100 → 2000–6500K），默认添加不再保存失败。
- 修复 `gasSensor` 的 `st`（`gasSensor` → `gas`），燃气服务可以正常保存。
- 停用映射时明确提示：上游重载会删除已注册的云端子设备。
- 允许保存 `enabled: false` 的损坏映射，便于先停用再修；重新启用时仍做完整校验。
- 重载失败不再误报成功（检查 `async_reload()` 返回值）。
- 保存时的文件系统错误包装成持久通知，不再显示 “Unknown error”。
- 校验网关 serial，禁止回退用 `gateway.title` 拼存储路径。
- `action` / `status` 增加实体域与 contract 角色校验；`electric` 缺少 `fields` 时在服务页直接报错；YAML `on`/`off` 布尔键给出明确错误。
- 自定义子设备允许不选服务；`sub_prod_id` 改为可选，兼容 ZJ0V 探针。
- ZJ0V 探针 `protocol_type` 与上游自带样例对齐为 `1`。
- 补充上述场景的 selftest/flowtest；发布 zip 改用正斜杠路径。

## 0.2.4

- 模板选择页、产品身份页直接提供华为 IoT 全量目录和单品 Profile 链接。
- 自定义产品参数可在界面内跳转查询。

## 0.2.3

- 显示名称、房间移到「子设备标识」下方。
- 集成图标使用 OneConnect Bridge 同款图标（`brand/icon.png`、`brand/logo.png`）。

## 0.2.2

- 中文优先：`zh-Hans`、`zh-CN`、`en` 回退文件全部为中文。
- 修复读取 `manifest.json` 时的事件循环阻塞警告。
- 启动日志增加语言与翻译命中诊断。

## 0.2.1

- `key` 可留空，自动生成 `device_1`。
- 补充中文字段说明，提示实体在下一步选择。

## 0.2.0

- 添加子设备改为「产品模板 → 产品身份 → 逐个服务选实体」。
- 预置 9MU7 / 9MXO / 9MY5 / ZJ0V 模板并自动填参数。
- 每个服务必须选择 HA 实体。

## 0.1.0

- 首个版本：图形化编辑 `mapping.yaml`，支持添加、编辑、删除、直接编辑 YAML、启停和重载。
