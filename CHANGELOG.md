# Changelog

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

