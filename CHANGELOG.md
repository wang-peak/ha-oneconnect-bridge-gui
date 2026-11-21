# Changelog

## 0.2.12

- 新增 `status`、`mode`、`fan` 三个服务的 Profile 自动解析：粘贴 Profile 后按 `enumList` 生成 `states`/`values`/`gear_values` 的占位符预填（键统一写「HA实体显示的状态」，行尾注释保留 Profile 原始描述），用户只需替换键名。
- 服务页底部新增「⬅ 返回上一步」开关：勾选后提交回到上一个服务，第一个服务时返回产品设置页；返回产品页会保留已填写的产品信息和服务勾选。
- 添加子设备的模板下拉把「自定义」排到最上方，并设为默认选中，粘贴 Profile 成为默认路径。
- 服务页顶部提示按适配器实际能力重写：`switch`、`brightness`、`temperature`、`humidity`、`action`、`status`、`electric` 精简为分点说明；`fan` 明确 `direction_enabled` 默认 true。
- 删除 9MTX 模板里手写的 electric `contract_notes`，字段对照统一由 `contract_fields.py` 按预填的 `fields` 自动生成，避免两段重复说明。
- 修复 `fan` 自动解析把 `speed` 的 `min`/`max` 写进 contract 的问题：上游 fan 适配器只接受 `gear_values`/`direction_enabled`，此前会因非法键导致整份映射被拒绝。
- 服务目录的别名表与上游适配器对齐：补齐 `switchPTC`（电辅热）、`inchingSwitch`（点动循环）、`boostMode`（增压洗）三个开关变体；移除上游并不存在的 `motorLeft`/`motorRight`/`openLevelLeft`/`openLevelRight`/`openerLeft`/`openerRight`（此前选用会被上游以「service not supported」拒绝保存）。别名表改为由 `_ALIAS_TABLE` 统一生成 `_ALIASES` 与 `ALIAS_BASE`，避免两者失配。
- 修复服务页「⬅ 返回上一步」到产品页后重新提交会丢弃已选实体与 contract 的问题：现在按子设备标识保留上一次填写的服务内容（仅 add/edit 同一子设备时复用）。
- `action` 模板不再预填 `commands`：留空走上游默认，避免非 cover/valve 域被误判为「必须配置」，也避免 0=开、1=关 的设备被模板反转。
- `temperature`/`humidity` 解析 target 时优先按字段名匹配 `target`，并排除 `preserveTarget`、`keepTarget` 等记忆字段，三特性 Profile 不再把记忆温度当成目标温度。
- `status`/`mode`/`fan` 的占位符（「HA实体显示的状态」）未替换时直接报错 `placeholder_unfilled`，不再静默保存成永不命中的映射。
- 修复添加子设备时 `status`/`mode`/`fan` 的 contract 直接显示成 Profile 描述（看起来像可直接提交）的问题：添加流程不再把预填内容当成已保存 contract，服务页改为显示占位符并附原始描述注释；编辑旧映射时，如果保存的 contract 与预填完全相同，也按未配置显示占位符。
- `fan` 的占位符预填保留 `direction_enabled: false`（只有档位、没有摆风特性的 Profile，避免上游默认 true 恒报 direction=1）。
- 上游校验错误翻译为中文：不再把 `child c1 service xxx is not supported` 这类英文原样弹给用户，原始信息写日志便于排查。
- mapping 保存改为唯一临时文件 + fsync + 目录 fsync，校验副本放到系统临时目录；双保存/断电不再可能损坏 `mapping.yaml`。
- 子设备标识放宽为与上游一致的安全单段名：允许中文、空格、点号，仍拒绝 `/`、`\`、控制字符和 `.`/`..`。
- 上游 `button.<serial>_reload_children` 按下失败时回退为整条配置条目重载，不再直接报错。
- 缺少 GUI 翻译的告警只在简体中文环境提示；其它语言回退到键名属预期行为。
- 移除英文翻译文件（`translations/en.json`）与已失效的 CI workflow：本集成只提供简体中文界面，README 目录树同步更新。

## 0.2.11

- 更新适配器：新增功率 `power` 适配（只读，读取 HA 数值实体作为功率 W 上报）。

## 0.2.10

- 适配 HA 2026.11 内置 Marketplace：README 安装章节改为「设置 → Marketplace → 从链接添加」，并用 `ha-marketplace:exclude` 标记包裹，Marketplace 仓库页自动隐藏；排错条目同步更新。
- `manifest.json` 键序按 hassfest 规范重排（`domain`、`name`，其余字母序）；无功能变化。
- 无运行时改动，升级后行为与 0.2.9 一致。

## 0.2.9

- 新增「粘贴设备 Profile」流程：添加子设备选「自定义」模板后，先进入 Profile 页粘贴华为单品 Profile JSON，自动识别 `prod_id`、`device_type`、`manufacturer`、`model`、`protocol_type` 和可投影服务，并在下一页预填；留空提交则直接手动填写；解析失败给出中文提示（`profile_invalid`）。
- 新增 `device_profile.py`（解析单品 Profile、合并服务与 contract 默认值）和 `contract_fields.py`（contract 字段名 → 中文含义），electric 服务页按当前 contract 显示字段对照，提交时提示 fields 与实体的对应关系。
- 添加子设备页显示 Profile 摘要占位 `{profile_note}`，方便核对识别到的产品信息。
- `action` 的 commands 校验放宽到 cover/valve（留空可用上游默认），其它域仍需显式配置；提示示例改为扫地机 `0=start`、`1=pause`、`2=cancel`。
- 服务提示按 Profile 重写：`on_mode` 必须是实体 `hvac_modes` 里存在的模式；`sid=warmSwitch/heatSwitch/lightSwitch` 这类变体不支持，需整条省略；`protocol_type` 给出 1 Wi-Fi、3 Zigbee、6 蓝牙 Mesh 对照；`st` 通常不用改，switch 可按 Profile 改成 binarySwitch。
- `status` 提示重写：states 的键必须是实体实际 state 文本（YAML 中 `on`/`off` 要加引号），states 与 fallback 至少一项；`electric` 的 fields 必须与绑定实体数量、顺序严格一致，integers/scales 的键只能是 fields 中已有字段。
- 量程与枚举提示补全：cover/valve 量程必须在 0–100 内且 step 能整除量程；`direction` 只能 1 或 2；`level_map` 的 max 必须递增；dimmer 上游默认 0–255，预填 0–100 仅是示例；light 不接受 contract，颜色取 `rgb_color`（0–255）。
- 自定义模板名称改为「自定义（粘贴设备 Profile JSON 自动识别）」；9MTX 模板补充 totalElectricity/current/voltage 仅为别名提示，实际 contract 仍用 totalConsum/currentElectric1/currentVoltage1/currentPower1。
- 适配 HA 2026.11 内置 Marketplace：README 安装章节改为 Marketplace 流程并加 `ha-marketplace:exclude` 标记，manifest 键序按 hassfest 规范排序。

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

