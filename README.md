# OneConnect Bridge GUI

给 [ha-oneconnect-bridge](https://github.com/xiasi0/ha-oneconnect-bridge) 用的**独立图形配置集成**：在 Home Assistant 界面里添加 / 编辑 / 删除子设备、选择 HA 实体、填写 contract，不再手写 `.storage/.../mapping.yaml`。

它**不修改上游任何文件**，所以上游仍然可以通过 HACS 正常更新。

## 为什么可以做到“不动上游”

- 上游集成本体在 `config/custom_components/oneconnect_bridge/`，HACS 更新会整目录覆盖，不能改。
- `config/.storage/oneconnect_bridge/gateways/<serial>/mapping.yaml` 是运行期数据，上游只在首次创建时写一次，之后只读，外部可以安全改写。
- 上游设备上已有“重载子设备配置”按钮（unique_id 固定为 `<serial>_reload_children`），写完文件按一下即可应用，无需重启 HA。

本集成只做三件事：读 YAML → 用表单改 YAML → 调用上游校验并触发重载。

## 工作方式

```
HA 表单  ->  mapping.yaml  ->  上游 load_enabled_mapping() 校验
                                      |
                                      v
                         按上游按钮 / 重载配置条目，使新计划生效
```

- 保存前先写临时文件，调用上游 `business.mapping_config.load_enabled_mapping()` 做**与上游完全一致**的校验；校验失败不会覆盖现有文件。
- 校验通过后备份原文件为 `mapping.yaml.bak`，再原子替换。
- 网关在线时按上游“重载子设备配置”按钮（不重连云端）；按钮不存在（网关离线）时退化为重载该配置条目。

## 安装

要求：已安装并配置 OneConnect Bridge；Home Assistant ≥ 2024.11（上游本身按 2026.10.x 验证）。

### 方式一：HACS（推荐）

1. 把本目录推送到你自己的 GitHub 仓库（保持 `custom_components/oneconnect_bridge_gui/` 在仓库根目录）。
2. HACS → 集成 → 右上角菜单 → 自定义存储库。
3. 添加仓库地址，类型选 `Integration`。
4. 搜索 `OneConnect Bridge GUI`，下载并重启 Home Assistant。

### 方式二：手动

把 `custom_components/oneconnect_bridge_gui/` 整个复制到：

```text
config/custom_components/oneconnect_bridge_gui/
```

重启 Home Assistant。

> 也可以直接使用本目录下打包好的 `oneconnect_bridge_gui-0.2.4.zip`，解压到 `config/` 即可。
>
> 0.2.2 起为**中文优先**：`zh-Hans`、`zh-CN` 以及 `en` 回退文件都是中文，避免 HA 语言不是 `zh-Hans` 时界面回退成英文。
>
> 0.2.3 起：显示名称、房间移到「子设备标识」下方，常改字段集中在一起；集成图标使用 OneConnect Bridge 同款图标。
>
> 0.2.4 起：模板页和产品页直接给出华为 IoT 资料库链接，点开即可查询自定义产品参数。

## 使用

1. **设置 → 设备与服务 → 添加集成 → OneConnect Bridge GUI**。
2. 选择要管理的 OneConnect 网关（按序列号列出）。
3. 在该条目上点 **配置**，进入菜单：

| 菜单 | 作用 |
| --- | --- |
| 添加子设备（含实体绑定） | 选模板 → 填身份和服务 → 逐个服务选 HA 实体 |
| 编辑子设备与实体 | 选已有子设备，改产品身份、服务选择和绑定 |
| 删除子设备 | 二次确认后从 YAML 移除；重载时上游会同步删除云端子设备 |
| 直接编辑 YAML | 内置文本编辑器，保存前同样走上游校验 |
| 设置 | 启用 / 停用该网关的映射（`enabled`） |
| 立即重载 | 不修改文件，只让上游重新应用当前 YAML |

### 添加子设备：两步 + 实体绑定

**第 1 步：选产品模板。** 模板会自动填好 `prod_id / device_type / model / sub_prod_id / 服务列表`。

| 模板 | prod_id | device_type | model | 默认服务 |
| --- | --- | --- | --- | --- |
| 智控灯泡（9MU7） | 9MU7 | 119 | haTest10 | switch / brightness / cct |
| 智控空调（9MXO） | 9MXO | 012 | test20 | switch / mode / temperature / fan |
| 智控窗帘（9MY5） | 9MY5 | 01C | haTest23 | leftAction / opener |
| 探针：尊界S800（ZJ0V） | ZJ0V | 347 | MAEXTRO-S800 Grand Design | 无（只验证网关） |
| 自定义 | 手填 | 手填 | 手填 | 手选 |

**第 2 步：产品身份与服务。** 模板值已带入，可按华为 Profile 修改；然后勾选要投影的服务。**HA 实体不在这一页**，提交后才会进入实体选择。

**第 3 步起：逐个服务选 HA 实体。** 每个选中的服务单独一页，实体选择器只列出该服务允许的域（例如 `brightness` 只列 `light.*`，`mode`/`fan` 只列 `climate.*`）。**必须至少选择一个实体**，否则该服务无法提交——这正是双向同步的绑定关系。`contract` 可以留空，用适配器默认值。

### 字段速查

| 表单字段 | 中文含义 | 默认 / 来源 |
| --- | --- | --- |
| `template` | 产品模板 | 默认 9MU7，决定下面大部分参数 |
| `key` | 子设备标识，网关内唯一 | 可留空，自动生成 `device_1` |
| `friendly_name` | 华为 App 里的显示名 | 模板带入，可改 |
| `room` | 华为 App 里的房间 | 可留空 |
| `prod_id` | 华为产品 ID | 模板带入；对应 Profile 文件名 / 目录的 DeviceId |
| `sub_prod_id` | 子产品 ID | `00` |
| `device_type` | 设备类型 | 模板带入；Profile 的 `deviceTypeId` |
| `manufacturer` | 厂商 ID | `002` |
| `model` | 设备型号 | 模板带入；Profile 的 `deviceModel` |
| `protocol_type` | 协议类型 | `6` |
| `setup_type` | 配网类型 | `0` |
| `known_fields_only` | 只上报 Profile 已知字段 | 关；`sub_prod_id` 为空时必须开 |
| `services` | 要投影的华为服务 | 模板带入，可增减 |
| `st` | 服务类型 | 按 sid 自动匹配，一般不用改（`switch` 可改 `binarySwitch`） |
| `entities` | 对应的 HA 实体 | 必填，实体选择器 |
| `contract` | 协议覆盖（枚举/量程/字段名） | 可留空 |

每个字段在表单下方还有一行灰色说明（HA 的 `data_description`），鼠标停在输入框上也能看到。

## contract 怎么写

文本框接受 **YAML 或 JSON**。YAML 的好处是支持整数键（`action.commands` 需要）：

```yaml
commands:
  0: close
  1: open
  2: stop
```

常见示例：

```yaml
# brightness / cct / openLevel / opener
min: 0
max: 100
step: 1

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

## 自定义产品参数去哪查

模板里没有的产品，需要到华为 IoT 资料库查 `prod_id / device_type / model`：

- 全量目录（按产品名或 DeviceId 搜索）：
  https://smarthome-drcn.dbankcdn.com/device/guide/ver_202609_hmos/mainHelp.json
- 单品 Profile（把 `9MU7` 换成你的产品 ID）：
  https://smarthome-drcn.dbankcdn.com/device/guide/9MU7/9MU7.json

Profile 字段对应关系：

| Profile 字段 | YAML / 表单字段 |
| --- | --- |
| `DeviceId` | `prod_id` |
| `deviceTypeId` | `device_type` |
| `deviceModel` | `model` |
| `manufacturerId` | `manufacturer`（通常是 `002`） |
| `protocolType` | `protocol_type` |
| `setupType` | `setup_type` |

0.2.4 起，模板页和产品页里也直接放了这两个链接，点开就能查。

## 文件与行为说明

- 写入路径（与上游读取的完全一致）：
  `config/.storage/oneconnect_bridge/gateways/<serial>/mapping.yaml`
- 每次保存前备份：同目录 `mapping.yaml.bak`（只保留上一版）。
- **注释会被覆盖**：保存时文件被重新格式化，仅保留固定说明头。需要保留注释就用“直接编辑 YAML”，或接受 GUI 的格式化。
- **未知字段保留**：编辑已有子设备时，只更新 GUI 管理的字段（product 的已知键、services 列表、bindings），其他键原样保留；但 `services` 列表会按本次选择整体重写。
- **未收录的 sid**：上游以后新增的服务不在内置目录时，仍会出现在“编辑”表单里，用通用实体选择器和 contract 文本框编辑，保存时由已安装的上游适配器校验。
- 子设备上限 64，网关内 key 唯一，key 只允许字母、数字、`_`、`-`。

## 排错

- 保存失败时会弹出持久通知，内容就是上游校验的原文（例如 `child x service status is invalid: status requires states or fallback`）。
- 校验失败不会改动现有 `mapping.yaml`；修好后重新提交即可。
- 若提示“自动重载未成功”，到 **设置 → 设备与服务 → OneConnect Bridge** 手动点“重新加载”。
- 日志：`custom_components.oneconnect_bridge_gui`，上游日志仍是 `custom_components.oneconnect_bridge`。

## 卸载

删除 OneConnect Bridge GUI 的配置条目即可，不会删除 `mapping.yaml` 或云端设备。要彻底清理，请删除对应的 OneConnect Bridge 网关（上游会先删云端子设备再删本地数据）。

## 发布到 GitHub / HACS

想让别人在 HACS 里搜索并安装，需要把本目录发布成一个**公开 GitHub 仓库**。有两种级别：

| 方式 | 别人怎么装 | 是否需要审核 |
| --- | --- | --- |
| 自定义存储库 | HACS → 添加你的仓库 URL → 下载 | 不需要，最快 |
| HACS 默认商店 | HACS 里直接搜索安装 | 需要向 `hacs/default` 提 PR 并通过审核 |

### 1. 建仓库并上传

1. 在 GitHub 新建**公开**仓库，名称建议 `ha-oneconnect-bridge-gui`。
2. 上传本目录内容，保持下面的结构（**不要**只上传 zip）：
   ```text
   hacs.json
   README.md
   LICENSE
   NOTICE
   CHANGELOG.md
   .github/workflows/validate.yml
   custom_components/oneconnect_bridge_gui/
   ```
3. 把 `custom_components/oneconnect_bridge_gui/manifest.json` 里的 `wang-peak` 替换成你的 GitHub 用户名，并补上 `codeowners`：
   ```json
   "documentation": "https://github.com/wang-peak/ha-oneconnect-bridge-gui",
   "issue_tracker": "https://github.com/wang-peak/ha-oneconnect-bridge-gui/issues",
   "codeowners": ["@wang-peak"]
   ```
4. 仓库设置里填一句描述，并添加 topics：`home-assistant`、`hacs`、`integration`。

### 2. 发一个 Release（HACS 用它判断版本）

1. GitHub → Releases → Draft a new release。
2. Tag 填 `v0.2.4`（与 `manifest.json` 的 `version` 一致）。
3. 标题填 `OneConnect Bridge GUI 0.2.4`，说明可从 `CHANGELOG.md` 复制。
4. 发布。

HACS 用最新 Release 的 tag 作为可用版本；tag 和 manifest 版本不一致会提示更新异常。

### 3. 等校验通过

仓库的 **Actions → Validate** 会运行 HACS 官方校验。绿色即可；如果红了，按日志改 `hacs.json` / `manifest.json` 后重新发版。

### 4. 别人怎么安装

先装上游 OneConnect Bridge（它也是自定义存储库）：

```text
HACS → 集成 → 右上角 ⋮ → 自定义存储库
添加 https://github.com/xiasi0/ha-oneconnect-bridge
类型选 Integration → 下载 → 重启
```

再装本 GUI：

```text
HACS → 集成 → 右上角 ⋮ → 自定义存储库
添加 https://github.com/wang-peak/ha-oneconnect-bridge-gui
类型选 Integration → 搜索 OneConnect Bridge GUI → 下载 → 重启
```

> 两个是独立集成：上游负责协议和网关，GUI 只负责编辑 `mapping.yaml`。只装 GUI 不装上游会用不了。

### 5. 想进 HACS 默认商店

在自定义存储库能被安装、且稳定使用一段时间后，再向 [hacs/default](https://github.com/hacs/default) 提交 PR，把 `oneconnect_bridge_gui` 加进 integration 列表。需要：公开仓库、Release、品牌图（本仓库已带 `brand/icon.png` 和 `brand/logo.png`）、README、Issue 开启、HACS 校验通过。

## 开发与自测

`tools/selftest.py` 直接调用上游 `business.mapping_config`（该包不依赖 Home Assistant）验证：

```bash
python tools/selftest.py
```

覆盖：写入 3 个子设备、上游真实解析、整数键 contract 往返、备份、非法 contract 拒绝、`enabled: false` 时仍做结构校验。

`tools/flowtest.py` 用最小 HA 桩跑完整的选项流状态机：

```bash
python tools/flowtest.py
```

覆盖：添加子设备、重复 key、`st` 覆盖、非法 contract 不落盘、编辑保留未知字段、删除确认、直接编辑 YAML、启停开关。

---

非官方项目，与华为、OneConnect 官方无关。使用前请阅读上游项目的免责声明。
