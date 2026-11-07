# OneConnect Bridge GUI

> 非官方 Home Assistant 自定义集成，与华为、OneConnect 官方无关。使用前请阅读上游项目的免责声明。

给 [OneConnect Bridge](https://github.com/xiasi0/ha-oneconnect-bridge) 用的图形配置界面：在 Home Assistant 里添加、编辑、删除子设备，选择 HA 实体，填写 contract，不再手写 `.storage/oneconnect_bridge/gateways/<serial>/mapping.yaml`。

本集成只读写上游的 `mapping.yaml`，不修改上游代码，所以 OneConnect Bridge 仍然可以通过 HACS 正常更新。

## 功能

- **产品模板**：9MU7 智控灯泡、9MTJ 智控夜灯、9MTL 智控床头灯、9MTM 智控压力传感器、9MTR 智控水壶、9MTV 智控灭蚊器、9MTW 智控电饭煲、9MTX 智控断路器、9MXO 智控空调、9MY5 智控窗帘、ZJ0V 探针；另有「自定义」模板，粘贴设备 Profile JSON 即可自动识别产品参数。
- **子设备管理**：添加、编辑、删除，支持查看和直接编辑 YAML。
- **实体绑定**：每个华为服务单独一页选择 HA 实体，实体选择器按服务过滤域。
- **contract 覆盖**：按 Profile 调整枚举、量程、字段名，支持 YAML 和 JSON。
- **字段中英文对照**：服务页会按当前 contract 的 `fields` / `field` / `target_field` 自动列出「字段名 — 中文含义」，`electric` 还带序号，方便把实体顺序和字段顺序对齐。
- **保存前校验**：调用上游 `load_enabled_mapping()`，校验失败不会覆盖现有文件。
- **自动备份**：每次保存前生成 `mapping.yaml.bak`。
- **自动生效**：保存后按上游“重载子设备配置”按钮，不需要重启 HA。
- **中文界面**：字段名、说明、错误提示均为中文。

## 前置条件

- 已安装并配置 **OneConnect Bridge**（上游集成），并且父网关已完成配对。
- Home Assistant ≥ 2024.11；上游本身按 2026.10.x 验证。
- 上游的局域网要求仍然适用：HA 主机与华为智慧生活 App 在同一 IPv4 局域网，UDP 5683 可用，网卡允许组播。

## 安装

### 方式一：HACS（推荐）

先安装上游 OneConnect Bridge：

```text
HACS → 集成 → 右上角 ⋮ → 自定义存储库
添加 https://github.com/xiasi0/ha-oneconnect-bridge
类型选 Integration → 下载 → 重启 Home Assistant
```

再安装本集成：

```text
HACS → 集成 → 右上角 ⋮ → 自定义存储库
添加 https://github.com/wang-peak/ha-oneconnect-bridge-gui
类型选 Integration → 搜索 OneConnect Bridge GUI → 下载 → 重启 Home Assistant
```

### 方式二：手动

把 `custom_components/oneconnect_bridge_gui/` 整个复制到：

```text
config/custom_components/oneconnect_bridge_gui/
```

重启 Home Assistant。也可以从 [Releases](https://github.com/wang-peak/ha-oneconnect-bridge-gui/releases) 下载 `oneconnect_bridge_gui-<版本号>.zip`，解压到 `config/`。

## 使用

### 打开配置界面

```text
设置 → 设备与服务 → 添加集成 → OneConnect Bridge GUI
```

选择要管理的 OneConnect 网关（按序列号列出）。之后在该条目上点 **配置**，进入菜单：

| 菜单 | 作用 |
| --- | --- |
| 添加子设备（含实体绑定） | 选模板 → 填身份和服务 → 逐个服务选 HA 实体 |
| 编辑子设备与实体 | 选已有子设备，改产品身份、服务选择和绑定 |
| 删除子设备 | 二次确认后从 YAML 移除；重载时上游会同步删除云端子设备 |
| 直接编辑 YAML | 内置文本编辑器，保存前同样走上游校验 |
| 设置 | 启用 / 停用该网关的映射（`enabled`）；停用会触发重载，并让上游删除已注册的云端子设备 |
| 立即重载 | 不修改文件，只让上游重新应用当前 YAML |

### 添加子设备

**第 1 步：选产品模板。** 模板会自动填好 `prod_id / device_type / model / sub_prod_id / 服务列表`。

| 模板 | prod_id | device_type | model | 默认服务 |
| --- | --- | --- | --- | --- |
| 智控灯泡（9MU7） | 9MU7 | 119 | haTest10 | switch / brightness / cct |
| 智控夜灯（9MTJ） | 9MTJ | 21F | haTest1 | switch / brightness / cct / status |
| 智控床头灯（9MTL） | 9MTL | 10E | haTest2 | switch / brightness / cct |
| 智控压力传感器（9MTM） | 9MTM | 1F1 | haTest4 | 无（上游暂无 alarmBell 适配器，只注册设备） |
| 智控水壶（9MTR） | 9MTR | 09A | haTest5 | switch / mode / temperature |
| 智控灭蚊器（9MTV） | 9MTV | 0B0 | haTest6 | switch |
| 智控电饭煲（9MTW） | 9MTW | 026 | haTest7 | switch / action |
| 智控断路器（9MTX） | 9MTX | 211 | haTest8 | switch / electric |
| 智控空调（9MXO） | 9MXO | 012 | test20 | switch / mode / temperature / fan |
| 智控窗帘（9MY5） | 9MY5 | 01C | haTest23 | leftAction / opener |
| 探针：尊界S800（ZJ0V） | ZJ0V | 347 | MAEXTRO-S800 Grand Design | 无（只验证网关） |
| 自定义 | 自动识别 | 自动识别 | 自动识别 | 自动识别 / 手选 |

选「自定义」后会先打开「粘贴设备 Profile」页：把华为设备的 Profile JSON 整段粘进去，会自动识别 `prod_id`、`device_type`、`model`、`manufacturer`、`protocol_type`，带入能识别的服务并预填各服务的 contract；解析成功后下一页顶部会显示识别摘要。也可以留空直接手填。

**第 2 步：产品身份与服务。** 模板值已带入，可按华为 Profile 修改；然后勾选要投影的服务。**HA 实体不在这一页**，提交后才会进入实体选择。

**第 3 步起：逐个服务选 HA 实体。** 每个选中的服务单独一页，实体选择器只列出该服务允许的域（例如 `brightness` 只列 `light.*`，`mode`/`fan` 只列 `climate.*`）。**必须至少选择一个实体**，否则该服务无法提交。`contract` 可以留空，使用适配器默认值。页面顶部会按 contract 里的字段自动显示中英文对照；改动 `contract` 并重新提交后，对照会一起刷新。

### 子设备列表怎么认

「编辑子设备」「删除子设备」的下拉列表显示：

```text
显示名称（key） · 房间
```

例如：

```text
客厅吸顶灯（living_room_lamp） · 客厅
书房灯带（study_strip） · 书房
device_1
```

- 显示名称来自 `product.friendly_name`（华为智慧生活 App 里看到的名称），房间来自 `product.room`；没填的部分就不显示。
- 想给已有设备加中文名：编辑该子设备 → 在「显示名称」里填中文 → 保存。列表立刻带上它；只改显示名，key 和云端设备都不受影响。
- 同名设备用房间区分；编辑页标题、删除确认和保存通知也会显示「名称（key）」，提交/删除前能再核对一次。

### 字段说明

| 表单字段 | 中文含义 | 默认 / 来源 |
| --- | --- | --- |
| `template` | 产品模板 | 默认 9MU7，决定下面大部分参数 |
| `key` | 子设备标识，网关内唯一 | 可留空，自动生成 `device_1` |
| `friendly_name` | 华为 App 里的显示名 | 模板带入，可改 |
| `room` | 华为 App 里的房间 | 可留空 |
| `prod_id` | 华为产品 ID | 模板带入；对应 Profile 文件名 / 目录的 DeviceId |
| `sub_prod_id` | 子产品 ID | `00` |
| `device_type` | 设备类型 | 模板带入；Profile 的 `deviceTypeId` |
| `manufacturer` | 厂商 ID | 通常 `002`；Profile 的 `manufacturerId` |
| `model` | 设备型号 | 模板带入；Profile 的 `deviceModel` |
| `protocol_type` | 协议类型 | `6`（蓝牙 Mesh）；Profile 的 `protocolType`，取值见下 |
| `setup_type` | 配网类型 | `0`；Profile 的 `setupType` |
| `known_fields_only` | 只上报 Profile 已知字段 | 关；`sub_prod_id` 为空时必须开 |
| `services` | 要投影的华为服务 | 模板带入，可增减 |
| `st` | 服务类型 | 按 sid 自动匹配，一般不用改（`switch` 可改 `binarySwitch`，`gasSensor` 固定 `gas`） |
| `entities` | 对应的 HA 实体 | 必填，实体选择器 |
| `contract` | 协议覆盖（枚举/量程/字段名） | 可留空 |


`protocol_type` 取值与协议对应：`0` 无效、`1` Wi-Fi、`2` Z-Wave、`3` Zigbee、`4` 蓝牙、`5` PLC 电力线、`6` 蓝牙 Mesh、`7` NFC、`8` 以太网、`9` 蜂窝移动、`10` USB、`11` PLC+Wi-Fi、`12` 蓝牙+Wi-Fi、`13` HiBeacon、`16` 星闪、`100` 虚拟设备。填错会被云端以 15013 拒绝注册。

### contract 怎么写

文本框接受 **YAML 或 JSON**。YAML 的好处是支持整数键（`action.commands` 需要）：

```yaml
commands:
  0: close
  1: open
  2: stop
```

常见示例：

```yaml
# brightness / openLevel / opener
min: 0
max: 100
step: 1
```

```yaml
# cct：色温单位是 Kelvin，不是 0-100
min: 2000
max: 6500
step: 1
```

```yaml
# switch 绑定 climate 时
on_type: int
on_mode: cool

# mode：HA hvac_mode -> 华为枚举
values:
  cool: 2
  heat: 3
  fan_only: 4

# fan
gear_values:
  auto: 0
  low: 1
  medium: 2
  high: 3
direction_enabled: false

# status：至少配 states 或 fallback 之一
states:
  open: 2
  closed: 1
fallback: 0
```

各服务允许的 key 见表单上方提示；填错会在保存时由上游适配器报错，精确到字段。

`action` 的 `commands` 角色必须匹配实体域：cover 用 `open/close/stop`，开关类用 `on/off`，扫地机用 `start/pause/cancel`；`status` 绑定 cover 时 `states` 用 `open/closed`（不是 `on/off`）。GUI 会在提交服务页时校验这些组合。

`action` 的表单会预填 `0=关 1=开 2=停`（窗帘类 Profile 的常见顺序，9MY5 即如此）；如果设备 Profile 是 `0=开 1=关`，请按 Profile 改掉预填值。contract 留空时上游按自己的默认 `0=开 1=关 2=停` 处理。

YAML 里 `on` / `off` / `yes` / `no` 作为键或 `commands`/`states` 的值时必须加引号（如 `'on': 1`、`0: 'off'`），否则会被 YAML 解析成布尔值；GUI 会给出明确错误。

### 自定义产品参数去哪查

模板里没有的产品，需要到华为 IoT 资料库查 `prod_id / device_type / model`：

- 华为Iot产品库：https://hispec.dxdgo.com/
- 全量目录（按产品名或 DeviceId 搜索）：
  https://smarthome-drcn.dbankcdn.com/device/guide/ver_202609_hmos/mainHelp.json
- 单品 Profile（把 `9MU7` 换成你的产品 ID）：
  https://smarthome-drcn.dbankcdn.com/device/guide/9MU7/9MU7.json


## 项目结构

```text
ha-oneconnect-bridge-gui/
├── custom_components/oneconnect_bridge_gui/（集成本体）
│   ├── __init__.py（集成入口）
│   ├── manifest.json（HA 元数据）
│   ├── config_flow.py（配置流与校验）
│   ├── const.py（常量、子设备上限）
│   ├── profile.py（mapping 读写与备份）
│   ├── mapping_ops.py（子设备增删改）
│   ├── runtime.py（触发上游重载）
│   ├── product_templates.py（内置产品模板）
│   ├── services_catalog.py（服务目录与提示）
│   ├── contract_fields.py（字段中文对照）
│   ├── device_profile.py（Profile 解析）
│   ├── strings.json（默认中文文案）
│   ├── translations/（中英文翻译）
│   │   ├── en.json
│   │   └── zh-Hans.json
│   └── brand/（图标与 logo）
│       ├── icon.png
│       └── logo.png
├── default_mapping.yaml（mapping 示例）
├── CHANGELOG.md（版本记录）
└── README.md（使用说明）
```

## 文件与行为说明

- 写入路径（与上游读取的完全一致）：
  `config/.storage/oneconnect_bridge/gateways/<serial>/mapping.yaml`
- 每次保存前备份：同目录 `mapping.yaml.bak`（只保留上一版；首次保存时文件还不存在，所以不会生成备份）。
- **停用映射**：`enabled: false` 只校验顶层字段，允许先停用再修坏掉的 `children`；重新启用时会重新做完整校验。
- **停用会删除云端子设备**：停用后触发重载，上游会把已注册的子设备从云端删除；重新启用后会重新注册，但云端设备 ID 可能变化。
- **注释会被覆盖**：保存时文件被重新格式化，仅保留固定说明头。需要保留注释就用“直接编辑 YAML”。
- **未知字段保留**：编辑已有子设备时，只更新 GUI 管理的字段（product 的已知键、services 列表、bindings），其他键原样保留；但 `services` 列表会按本次选择整体重写。
- **未收录的 sid**：上游以后新增的服务不在内置目录时，仍会出现在“编辑”表单里，用通用实体选择器和 contract 文本框编辑，保存时由已安装的上游适配器校验。
- 子设备上限 64，网关内 key 唯一，key 只允许字母、数字、`_`、`-`。

## 排错

- 保存失败时会弹出持久通知，内容就是上游校验的原文。
- 校验失败不会改动现有 `mapping.yaml`；修好后重新提交即可。
- 若提示“自动重载未成功”，到 **设置 → 设备与服务 → OneConnect Bridge** 手动点“重新加载”。
- HACS 搜索不到集成时，点 HACS 页面右上角“重新加载”或重启 HA，清除 HACS 缓存。
- 日志：`custom_components.oneconnect_bridge_gui`；上游日志仍是 `custom_components.oneconnect_bridge`。

## 卸载

删除 OneConnect Bridge GUI 的配置条目即可，不会删除 `mapping.yaml` 或云端设备。要彻底清理，请删除对应的 OneConnect Bridge 网关（上游会先删云端子设备再删本地数据）。

## 许可

Apache License 2.0，详见 [LICENSE](LICENSE)。集成图标来自 OneConnect Bridge 项目，归属说明见 [NOTICE](NOTICE)。
