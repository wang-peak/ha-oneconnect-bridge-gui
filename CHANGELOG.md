# Changelog

## 0.2.8

- 新增 9MTJ 智控夜灯、9MTL 智控床头灯、9MTM 智控压力传感器、9MTR 智控水壶、9MTV 智控灭蚊器、9MTW 智控电饭煲、9MTX 智控断路器模板，并为已有模板预填房间。
- 移除上游不支持的 `alarmBell` 服务：9MTM 只注册设备（`services: []`），不再写出会让整份映射被 `load_enabled_mapping` 拒绝的服务。
- 修正 `status` 校验：改回上游规则「`states` 与 `fallback` 至少一项」，允许 `states: {}` + `fallback`（21DA 类设备），并新增 `states`/`fallback` 类型的中文错误。
- 修复编辑子设备时清空「显示名称」「房间」不生效——旧值不再被合并保留。
- 允许编辑已存在的非规范子设备 key（例如手写 YAML 里的 `bad.key`），新建 key 仍按 1-64 位字母/数字/下划线/连字符校验，错误提示改为中文。
- `airDetector` 必须 2 个不同 sensor、`gasSensor` 1-2 个 sensor，服务页直接给出中文错误，不再等到保存时透出英文。
- 补 `config.abort.already_configured` 中文翻译（重复添加同一网关时的提示）。
- `action` 表单提示明确：预填的是窗帘类 `0=关 1=开 2=停`，留空则用上游默认 `0=开 1=关 2=停`。
- 自测脚本自动识别上游目录（`ha-oneconnect-bridge` 或 `ha-oneconnect-bridge-main`）；装了上游时 `flowtest` 按真实校验结果断言。
- 9MTX 模板预置 electric contract：`fields: [totalConsum, currentElectric1, currentVoltage1, currentPower1]`，新建 9MTX 时自动预填，不再因为 contract 为空卡在服务页；编辑已有 9MTX 子设备时按 `prod_id` 反查模板，空 contract 也会自动预填同样四个字段。
- 服务页提示按产品给出「实体 ↔ 字段」顺序：9MTX 明确第 1~4 个实体分别对应 totalConsum（累计用电量）、currentElectric1（电流）、currentVoltage1（电压）、currentPower1（功率）；`electric` 通用提示强调 fields 顺序必须与实体顺序一致、数量必须相同，只上报部分字段时删掉多余字段并保持剩余顺序。
- `electric` 的 `fields` 数量与绑定实体数不一致时直接报错（上游此时只告警并跳过上报，界面不拦就是「填了没数据」），中文提示点明第 N 个实体对应 fields 第 N 项。
- 翻译同步更新 `electric_fields_required`，新增 `electric_fields_entities_mismatch`。

## 0.2.7

- 「编辑子设备」「删除子设备」的下拉列表不再只显示 key：改为「显示名称（key）· 房间」，未填显示名称时保留 key。
- 编辑页标题显示当前子设备（如「编辑子设备：客厅吸顶灯（living_room_lamp）」），删除确认和保存通知也显示同一个名称，避免选错设备。
- 表单里补充说明：想加中文名，编辑该子设备时填「显示名称」即可，列表会自动带上。
- flowtest 增加下拉标签与编辑页占位符的断言。

## 0.2.6

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

