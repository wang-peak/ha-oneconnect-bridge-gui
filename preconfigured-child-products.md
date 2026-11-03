# 预置子设备模型

以下模型是华为为 Home Assistant 提供的专属物模型（`haTest*` / `test20`），设备 Profile 包含对应的 H5 页面标识。
默认配置会启用 9MU7 智控灯泡和 9MTX 智控断路器，但仍需将其中的 HA 实体占位符替换为实际实体；其他模型仍以注释示例提供。

| `prod_id` | `DeviceNameSpreading` | `Profile` |
| --- | --- | --- |
| `9MU7` | [智控灯泡](https://smarthome-drcn.dbankcdn.com/device/guide/9MU7/h5_001/index.html) | [9MU7 Profile](https://smarthome-drcn.dbankcdn.com/device/guide/9MU7/9MU7.json) |
| `9MXO` | [智控空调](https://smarthome-drcn.dbankcdn.com/device/guide/9MXO/h5_001/index.html) | [9MXO Profile](https://smarthome-drcn.dbankcdn.com/device/guide/9MXO/9MXO.json) |
| `9MY5` | [智控窗帘](https://smarthome-drcn.dbankcdn.com/device/guide/9MY5/h5_001/index.html) | [9MY5 Profile](https://smarthome-drcn.dbankcdn.com/device/guide/9MY5/9MY5.json) |
| `9MTJ` | [智控夜灯](https://smarthome-drcn.dbankcdn.com/device/guide/9MTJ/h5_001/index.html) | [9MTJ Profile](https://smarthome-drcn.dbankcdn.com/device/guide/9MTJ/9MTJ.json) |
| `9MTL` | [智控床头灯](https://smarthome-drcn.dbankcdn.com/device/guide/9MTL/h5_001/index.html) | [9MTL Profile](https://smarthome-drcn.dbankcdn.com/device/guide/9MTL/9MTL.json) |
| `9MTM` | [智控压力传感器](https://smarthome-drcn.dbankcdn.com/device/guide/9MTM/h5_001/index.html) | [9MTM Profile](https://smarthome-drcn.dbankcdn.com/device/guide/9MTM/9MTM.json) |
| `9MTR` | [智控水壶](https://smarthome-drcn.dbankcdn.com/device/guide/9MTR/h5_001/index.html) | [9MTR Profile](https://smarthome-drcn.dbankcdn.com/device/guide/9MTR/9MTR.json) |
| `9MTV` | [智控灭蚊器](https://smarthome-drcn.dbankcdn.com/device/guide/9MTV/h5_001/index.html) | [9MTV Profile](https://smarthome-drcn.dbankcdn.com/device/guide/9MTV/9MTV.json) |
| `9MTW` | [智控电饭煲](https://smarthome-drcn.dbankcdn.com/device/guide/9MTW/h5_001/index.html) | [9MTW Profile](https://smarthome-drcn.dbankcdn.com/device/guide/9MTW/9MTW.json) |
| `9MTX` | [智控断路器](https://smarthome-drcn.dbankcdn.com/device/guide/9MTX/h5_001/index.html) | [9MTX Profile](https://smarthome-drcn.dbankcdn.com/device/guide/9MTX/9MTX.json) |

## 服务覆盖一览

「可投影」指该 Profile 的服务在现有服务适配器中已有对应实现；未列出的服务可以整条不写进
`mapping.yaml`，不会影响注册，也不会报错。

| `prod_id` | 可投影服务 | 暂不支持的服务 |
| --- | --- | --- |
| `9MU7` 智控灯泡 | `switch`、`brightness`、`cct` | — |
| `9MXO` 智控空调 | `switch`、`mode`、`temperature`、`fan` | — |
| `9MY5` 智控窗帘 | `leftAction`、`opener` | — |
| `9MTJ` 智控夜灯 | `switch`、`brightness`、`cct`、`status` | — |
| `9MTL` 智控床头灯 | `switch`、`brightness`、`cct` | — |
| `9MTM` 智控压力传感器 | — | `alarmBell`（上游暂无适配器，映射里只保留产品标识） |
| `9MTR` 智控水壶 | `switch`、`mode`、`temperature` | `commonFaultDetection` |
| `9MTV` 智控灭蚊器 | `switch` | `delay`（定时） |
| `9MTW` 智控电饭煲 | `switch`、`action` | `cooker`（烹饪模式）、`leftTime`（剩余时间）、`status`（工作状态）、`commonFaultDetection` |
| `9MTX` 智控断路器 | `switch`、`electric` | — |

## 各模型的实体约束

实体占位符写在 `default_mapping.yaml` 的注释示例里，取消注释后替换为实际实体即可。

### 9MTJ 智控夜灯

`status` 服务的语义是**「有无人」**而不是开关，绑定 `binary_sensor`：
`on`=有人（上报 1），`off`=无人（上报 0）。

### 9MTM 智控压力传感器

Profile 里的 `serviceId` 是 `alarmBell`、`serviceType` 是 `mode`、特性名也是 `mode`，
上游适配器目前**没有实现 `alarmBell`**：把 `alarmBell` 写进 `services` 会让
`load_enabled_mapping` 直接拒绝整份映射（`child ... service alarmBell is not supported`）。
因此模板与 `default_mapping.yaml` 只保留产品标识、`services: []`，设备可以注册但不会上报状态；
等上游补上适配器后再添加 `services` / `bindings`。

### 9MTR 智控水壶

`mode` 适配器**只接受 `climate` 实体**，水壶本身没有 climate 语义，
这里用 `climate` 承载「工作模式」的读写；`contract.values` 把 HA 的 HVAC 模式
映射到 Profile 枚举（开水 1、温水 2 等）。

`temperature` 服务的三个特性（`preserveTarget` / `current` / `heatingTarget`）
在示例里只投影了 `current` 与 `preserveTarget` 两个。

### 9MTW 智控电饭煲

`action` 服务的 Profile 枚举是 `0=暂停 1=开始 2=取消`，绑定 `switch` 实体，
通过 `contract.commands` 把这三个值映射成 `pause` / `start` / `cancel` 角色。

### 9MTX 智控断路器

绑定 5 个 HA 实体：

| 服务 | `sid` | 特性 | HA 实体 | 说明 |
| --- | --- | --- | --- | --- |
| 开关 | `switch` | `on` | `switch.*` | 电源开关通断 |
| 电力电量 | `electric` | `totalConsum` | `sensor.*` | 累计用电量，单位 kWh |
| 电力电量 | `electric` | `currentElectric1` | `sensor.*` | 当前电流，单位 A |
| 电力电量 | `electric` | `currentVoltage1` | `sensor.*` | 当前电压，单位 V |
| 电力电量 | `electric` | `currentPower1` | `sensor.*` | 当前功率，单位 W |

`electric` 服务的四个特性都是 `float`、步长 0.01，因此 `contract.fields` 声明它们的顺序，
并且不列入 `contract.integers`——整数上报会把小数四舍五入成 0。
`contract.fields` 的顺序必须与 `bindings` 中实体的顺序一一对应。

## 编写 `mapping.yaml` 时的缩进要求

`bindings` 必须与 `product` **同级**（同为 4 个空格缩进），不能放进 `product` 内部：

```yaml
children:
  color_bulb_9mu7:
    product:
      prod_id: 9MU7
      services:
        - st: switch
          sid: switch
    bindings:          # 与 product 同级
      - sid: switch
        entities: [light.REPLACE_WITH_COLOR_BULB]
```

如果把 `bindings` 缩进到 `product` 内部，加载器**不会报错**，但绑定列表会解析为空，
子设备不会向云端上报任何状态，也不会接收命令。修改映射后建议检查日志中
每个服务都有对应的 `dataSync` 记录。
