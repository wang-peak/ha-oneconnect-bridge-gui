# OneConnect Bridge GUI

缁?[ha-oneconnect-bridge](https://github.com/xiasi0/ha-oneconnect-bridge) 鐢ㄧ殑**鐙珛鍥惧舰閰嶇疆闆嗘垚**锛氬湪 Home Assistant 鐣岄潰閲屾坊鍔?/ 缂栬緫 / 鍒犻櫎瀛愯澶囥€侀€夋嫨 HA 瀹炰綋銆佸～鍐?contract锛屼笉鍐嶆墜鍐?`.storage/.../mapping.yaml`銆?
瀹?*涓嶄慨鏀逛笂娓镐换浣曟枃浠?*锛屾墍浠ヤ笂娓镐粛鐒跺彲浠ラ€氳繃 HACS 姝ｅ父鏇存柊銆?
## 涓轰粈涔堝彲浠ュ仛鍒扳€滀笉鍔ㄤ笂娓糕€?
- 涓婃父闆嗘垚鏈綋鍦?`config/custom_components/oneconnect_bridge/`锛孒ACS 鏇存柊浼氭暣鐩綍瑕嗙洊锛屼笉鑳芥敼銆?- `config/.storage/oneconnect_bridge/gateways/<serial>/mapping.yaml` 鏄繍琛屾湡鏁版嵁锛屼笂娓稿彧鍦ㄩ娆″垱寤烘椂鍐欎竴娆★紝涔嬪悗鍙锛屽閮ㄥ彲浠ュ畨鍏ㄦ敼鍐欍€?- 涓婃父璁惧涓婂凡鏈夆€滈噸杞藉瓙璁惧閰嶇疆鈥濇寜閽紙unique_id 鍥哄畾涓?`<serial>_reload_children`锛夛紝鍐欏畬鏂囦欢鎸変竴涓嬪嵆鍙簲鐢紝鏃犻渶閲嶅惎 HA銆?
鏈泦鎴愬彧鍋氫笁浠朵簨锛氳 YAML 鈫?鐢ㄨ〃鍗曟敼 YAML 鈫?璋冪敤涓婃父鏍￠獙骞惰Е鍙戦噸杞姐€?
## 宸ヤ綔鏂瑰紡

```
HA 琛ㄥ崟  ->  mapping.yaml  ->  涓婃父 load_enabled_mapping() 鏍￠獙
                                      |
                                      v
                         鎸変笂娓告寜閽?/ 閲嶈浇閰嶇疆鏉＄洰锛屼娇鏂拌鍒掔敓鏁?```

- 淇濆瓨鍓嶅厛鍐欎复鏃舵枃浠讹紝璋冪敤涓婃父 `business.mapping_config.load_enabled_mapping()` 鍋?*涓庝笂娓稿畬鍏ㄤ竴鑷?*鐨勬牎楠岋紱鏍￠獙澶辫触涓嶄細瑕嗙洊鐜版湁鏂囦欢銆?- 鏍￠獙閫氳繃鍚庡浠藉師鏂囦欢涓?`mapping.yaml.bak`锛屽啀鍘熷瓙鏇挎崲銆?- 缃戝叧鍦ㄧ嚎鏃舵寜涓婃父鈥滈噸杞藉瓙璁惧閰嶇疆鈥濇寜閽紙涓嶉噸杩炰簯绔級锛涙寜閽笉瀛樺湪锛堢綉鍏崇绾匡級鏃堕€€鍖栦负閲嶈浇璇ラ厤缃潯鐩€?
## 瀹夎

瑕佹眰锛氬凡瀹夎骞堕厤缃?OneConnect Bridge锛汬ome Assistant 鈮?2024.11锛堜笂娓告湰韬寜 2026.10.x 楠岃瘉锛夈€?
### 鏂瑰紡涓€锛欻ACS锛堟帹鑽愶級

1. 鎶婃湰鐩綍鎺ㄩ€佸埌浣犺嚜宸辩殑 GitHub 浠撳簱锛堜繚鎸?`custom_components/oneconnect_bridge_gui/` 鍦ㄤ粨搴撴牴鐩綍锛夈€?2. HACS 鈫?闆嗘垚 鈫?鍙充笂瑙掕彍鍗?鈫?鑷畾涔夊瓨鍌ㄥ簱銆?3. 娣诲姞浠撳簱鍦板潃锛岀被鍨嬮€?`Integration`銆?4. 鎼滅储 `OneConnect Bridge GUI`锛屼笅杞藉苟閲嶅惎 Home Assistant銆?
### 鏂瑰紡浜岋細鎵嬪姩

鎶?`custom_components/oneconnect_bridge_gui/` 鏁翠釜澶嶅埗鍒帮細

```text
config/custom_components/oneconnect_bridge_gui/
```

閲嶅惎 Home Assistant銆?
> 涔熷彲浠ョ洿鎺ヤ娇鐢ㄦ湰鐩綍涓嬫墦鍖呭ソ鐨?`oneconnect_bridge_gui-0.2.4.zip`锛岃В鍘嬪埌 `config/` 鍗冲彲銆?>
> 0.2.2 璧蜂负**涓枃浼樺厛**锛歚zh-Hans`銆乣zh-CN` 浠ュ強 `en` 鍥為€€鏂囦欢閮芥槸涓枃锛岄伩鍏?HA 璇█涓嶆槸 `zh-Hans` 鏃剁晫闈㈠洖閫€鎴愯嫳鏂囥€?>
> 0.2.3 璧凤細鏄剧ず鍚嶇О銆佹埧闂寸Щ鍒般€屽瓙璁惧鏍囪瘑銆嶄笅鏂癸紝甯告敼瀛楁闆嗕腑鍦ㄤ竴璧凤紱闆嗘垚鍥炬爣浣跨敤 OneConnect Bridge 鍚屾鍥炬爣銆?>
> 0.2.4 璧凤細妯℃澘椤靛拰浜у搧椤电洿鎺ョ粰鍑哄崕涓?IoT 璧勬枡搴撻摼鎺ワ紝鐐瑰紑鍗冲彲鏌ヨ鑷畾涔変骇鍝佸弬鏁般€?
## 浣跨敤

1. **璁剧疆 鈫?璁惧涓庢湇鍔?鈫?娣诲姞闆嗘垚 鈫?OneConnect Bridge GUI**銆?2. 閫夋嫨瑕佺鐞嗙殑 OneConnect 缃戝叧锛堟寜搴忓垪鍙峰垪鍑猴級銆?3. 鍦ㄨ鏉＄洰涓婄偣 **閰嶇疆**锛岃繘鍏ヨ彍鍗曪細

| 鑿滃崟 | 浣滅敤 |
| --- | --- |
| 娣诲姞瀛愯澶囷紙鍚疄浣撶粦瀹氾級 | 閫夋ā鏉?鈫?濉韩浠藉拰鏈嶅姟 鈫?閫愪釜鏈嶅姟閫?HA 瀹炰綋 |
| 缂栬緫瀛愯澶囦笌瀹炰綋 | 閫夊凡鏈夊瓙璁惧锛屾敼浜у搧韬唤銆佹湇鍔￠€夋嫨鍜岀粦瀹?|
| 鍒犻櫎瀛愯澶?| 浜屾纭鍚庝粠 YAML 绉婚櫎锛涢噸杞芥椂涓婃父浼氬悓姝ュ垹闄や簯绔瓙璁惧 |
| 鐩存帴缂栬緫 YAML | 鍐呯疆鏂囨湰缂栬緫鍣紝淇濆瓨鍓嶅悓鏍疯蛋涓婃父鏍￠獙 |
| 璁剧疆 | 鍚敤 / 鍋滅敤璇ョ綉鍏崇殑鏄犲皠锛坄enabled`锛?|
| 绔嬪嵆閲嶈浇 | 涓嶄慨鏀规枃浠讹紝鍙涓婃父閲嶆柊搴旂敤褰撳墠 YAML |

### 娣诲姞瀛愯澶囷細涓ゆ + 瀹炰綋缁戝畾

**绗?1 姝ワ細閫変骇鍝佹ā鏉裤€?* 妯℃澘浼氳嚜鍔ㄥ～濂?`prod_id / device_type / model / sub_prod_id / 鏈嶅姟鍒楄〃`銆?
| 妯℃澘 | prod_id | device_type | model | 榛樿鏈嶅姟 |
| --- | --- | --- | --- | --- |
| 鏅烘帶鐏场锛?MU7锛?| 9MU7 | 119 | haTest10 | switch / brightness / cct |
| 鏅烘帶绌鸿皟锛?MXO锛?| 9MXO | 012 | test20 | switch / mode / temperature / fan |
| 鏅烘帶绐楀笜锛?MY5锛?| 9MY5 | 01C | haTest23 | leftAction / opener |
| 鎺㈤拡锛氬皧鐣孲800锛圸J0V锛?| ZJ0V | 347 | MAEXTRO-S800 Grand Design | 鏃狅紙鍙獙璇佺綉鍏筹級 |
| 鑷畾涔?| 鎵嬪～ | 鎵嬪～ | 鎵嬪～ | 鎵嬮€?|

**绗?2 姝ワ細浜у搧韬唤涓庢湇鍔°€?* 妯℃澘鍊煎凡甯﹀叆锛屽彲鎸夊崕涓?Profile 淇敼锛涚劧鍚庡嬀閫夎鎶曞奖鐨勬湇鍔°€?*HA 瀹炰綋涓嶅湪杩欎竴椤?*锛屾彁浜ゅ悗鎵嶄細杩涘叆瀹炰綋閫夋嫨銆?
**绗?3 姝ヨ捣锛氶€愪釜鏈嶅姟閫?HA 瀹炰綋銆?* 姣忎釜閫変腑鐨勬湇鍔″崟鐙竴椤碉紝瀹炰綋閫夋嫨鍣ㄥ彧鍒楀嚭璇ユ湇鍔″厑璁哥殑鍩燂紙渚嬪 `brightness` 鍙垪 `light.*`锛宍mode`/`fan` 鍙垪 `climate.*`锛夈€?*蹇呴』鑷冲皯閫夋嫨涓€涓疄浣?*锛屽惁鍒欒鏈嶅姟鏃犳硶鎻愪氦鈥斺€旇繖姝ｆ槸鍙屽悜鍚屾鐨勭粦瀹氬叧绯汇€俙contract` 鍙互鐣欑┖锛岀敤閫傞厤鍣ㄩ粯璁ゅ€笺€?
### 瀛楁閫熸煡

| 琛ㄥ崟瀛楁 | 涓枃鍚箟 | 榛樿 / 鏉ユ簮 |
| --- | --- | --- |
| `template` | 浜у搧妯℃澘 | 榛樿 9MU7锛屽喅瀹氫笅闈㈠ぇ閮ㄥ垎鍙傛暟 |
| `key` | 瀛愯澶囨爣璇嗭紝缃戝叧鍐呭敮涓€ | 鍙暀绌猴紝鑷姩鐢熸垚 `device_1` |
| `friendly_name` | 鍗庝负 App 閲岀殑鏄剧ず鍚?| 妯℃澘甯﹀叆锛屽彲鏀?|
| `room` | 鍗庝负 App 閲岀殑鎴块棿 | 鍙暀绌?|
| `prod_id` | 鍗庝负浜у搧 ID | 妯℃澘甯﹀叆锛涘搴?Profile 鏂囦欢鍚?/ 鐩綍鐨?DeviceId |
| `sub_prod_id` | 瀛愪骇鍝?ID | `00` |
| `device_type` | 璁惧绫诲瀷 | 妯℃澘甯﹀叆锛汸rofile 鐨?`deviceTypeId` |
| `manufacturer` | 鍘傚晢 ID | `002` |
| `model` | 璁惧鍨嬪彿 | 妯℃澘甯﹀叆锛汸rofile 鐨?`deviceModel` |
| `protocol_type` | 鍗忚绫诲瀷 | `6` |
| `setup_type` | 閰嶇綉绫诲瀷 | `0` |
| `known_fields_only` | 鍙笂鎶?Profile 宸茬煡瀛楁 | 鍏筹紱`sub_prod_id` 涓虹┖鏃跺繀椤诲紑 |
| `services` | 瑕佹姇褰辩殑鍗庝负鏈嶅姟 | 妯℃澘甯﹀叆锛屽彲澧炲噺 |
| `st` | 鏈嶅姟绫诲瀷 | 鎸?sid 鑷姩鍖归厤锛屼竴鑸笉鐢ㄦ敼锛坄switch` 鍙敼 `binarySwitch`锛?|
| `entities` | 瀵瑰簲鐨?HA 瀹炰綋 | 蹇呭～锛屽疄浣撻€夋嫨鍣?|
| `contract` | 鍗忚瑕嗙洊锛堟灇涓?閲忕▼/瀛楁鍚嶏級 | 鍙暀绌?|

姣忎釜瀛楁鍦ㄨ〃鍗曚笅鏂硅繕鏈変竴琛岀伆鑹茶鏄庯紙HA 鐨?`data_description`锛夛紝榧犳爣鍋滃湪杈撳叆妗嗕笂涔熻兘鐪嬪埌銆?
## contract 鎬庝箞鍐?
鏂囨湰妗嗘帴鍙?**YAML 鎴?JSON**銆俌AML 鐨勫ソ澶勬槸鏀寔鏁存暟閿紙`action.commands` 闇€瑕侊級锛?
```yaml
commands:
  0: close
  1: open
  2: stop
```

甯歌绀轰緥锛?
```yaml
# brightness / cct / openLevel / opener
min: 0
max: 100
step: 1

# switch 缁戝畾 climate 鏃?on_type: int
on_mode: cool

# mode锛欻A hvac_mode -> 鍗庝负鏋氫妇
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

# status锛氳嚦灏戦厤 states 鎴?fallback 涔嬩竴
states:
  open: 2
  closed: 1
fallback: 0
```

鍚勬湇鍔″厑璁哥殑 key 瑙佽〃鍗曚笂鏂规彁绀猴紱濉敊浼氬湪淇濆瓨鏃剁敱涓婃父閫傞厤鍣ㄦ姤閿欙紝绮剧‘鍒板瓧娈点€?
## 鑷畾涔変骇鍝佸弬鏁板幓鍝煡

妯℃澘閲屾病鏈夌殑浜у搧锛岄渶瑕佸埌鍗庝负 IoT 璧勬枡搴撴煡 `prod_id / device_type / model`锛?
- 鍏ㄩ噺鐩綍锛堟寜浜у搧鍚嶆垨 DeviceId 鎼滅储锛夛細
  https://smarthome-drcn.dbankcdn.com/device/guide/ver_202609_hmos/mainHelp.json
- 鍗曞搧 Profile锛堟妸 `9MU7` 鎹㈡垚浣犵殑浜у搧 ID锛夛細
  https://smarthome-drcn.dbankcdn.com/device/guide/9MU7/9MU7.json

Profile 瀛楁瀵瑰簲鍏崇郴锛?
| Profile 瀛楁 | YAML / 琛ㄥ崟瀛楁 |
| --- | --- |
| `DeviceId` | `prod_id` |
| `deviceTypeId` | `device_type` |
| `deviceModel` | `model` |
| `manufacturerId` | `manufacturer`锛堥€氬父鏄?`002`锛?|
| `protocolType` | `protocol_type` |
| `setupType` | `setup_type` |

0.2.4 璧凤紝妯℃澘椤靛拰浜у搧椤甸噷涔熺洿鎺ユ斁浜嗚繖涓や釜閾炬帴锛岀偣寮€灏辫兘鏌ャ€?
## 鏂囦欢涓庤涓鸿鏄?
- 鍐欏叆璺緞锛堜笌涓婃父璇诲彇鐨勫畬鍏ㄤ竴鑷达級锛?  `config/.storage/oneconnect_bridge/gateways/<serial>/mapping.yaml`
- 姣忔淇濆瓨鍓嶅浠斤細鍚岀洰褰?`mapping.yaml.bak`锛堝彧淇濈暀涓婁竴鐗堬級銆?- **娉ㄩ噴浼氳瑕嗙洊**锛氫繚瀛樻椂鏂囦欢琚噸鏂版牸寮忓寲锛屼粎淇濈暀鍥哄畾璇存槑澶淬€傞渶瑕佷繚鐣欐敞閲婂氨鐢ㄢ€滅洿鎺ョ紪杈?YAML鈥濓紝鎴栨帴鍙?GUI 鐨勬牸寮忓寲銆?- **鏈煡瀛楁淇濈暀**锛氱紪杈戝凡鏈夊瓙璁惧鏃讹紝鍙洿鏂?GUI 绠＄悊鐨勫瓧娈碉紙product 鐨勫凡鐭ラ敭銆乻ervices 鍒楄〃銆乥indings锛夛紝鍏朵粬閿師鏍蜂繚鐣欙紱浣?`services` 鍒楄〃浼氭寜鏈閫夋嫨鏁翠綋閲嶅啓銆?- **鏈敹褰曠殑 sid**锛氫笂娓镐互鍚庢柊澧炵殑鏈嶅姟涓嶅湪鍐呯疆鐩綍鏃讹紝浠嶄細鍑虹幇鍦ㄢ€滅紪杈戔€濊〃鍗曢噷锛岀敤閫氱敤瀹炰綋閫夋嫨鍣ㄥ拰 contract 鏂囨湰妗嗙紪杈戯紝淇濆瓨鏃剁敱宸插畨瑁呯殑涓婃父閫傞厤鍣ㄦ牎楠屻€?- 瀛愯澶囦笂闄?64锛岀綉鍏冲唴 key 鍞竴锛宬ey 鍙厑璁稿瓧姣嶃€佹暟瀛椼€乣_`銆乣-`銆?
## 鎺掗敊

- 淇濆瓨澶辫触鏃朵細寮瑰嚭鎸佷箙閫氱煡锛屽唴瀹瑰氨鏄笂娓告牎楠岀殑鍘熸枃锛堜緥濡?`child x service status is invalid: status requires states or fallback`锛夈€?- 鏍￠獙澶辫触涓嶄細鏀瑰姩鐜版湁 `mapping.yaml`锛涗慨濂藉悗閲嶆柊鎻愪氦鍗冲彲銆?- 鑻ユ彁绀衡€滆嚜鍔ㄩ噸杞芥湭鎴愬姛鈥濓紝鍒?**璁剧疆 鈫?璁惧涓庢湇鍔?鈫?OneConnect Bridge** 鎵嬪姩鐐光€滈噸鏂板姞杞解€濄€?- 鏃ュ織锛歚custom_components.oneconnect_bridge_gui`锛屼笂娓告棩蹇椾粛鏄?`custom_components.oneconnect_bridge`銆?
## 鍗歌浇

鍒犻櫎 OneConnect Bridge GUI 鐨勯厤缃潯鐩嵆鍙紝涓嶄細鍒犻櫎 `mapping.yaml` 鎴栦簯绔澶囥€傝褰诲簳娓呯悊锛岃鍒犻櫎瀵瑰簲鐨?OneConnect Bridge 缃戝叧锛堜笂娓镐細鍏堝垹浜戠瀛愯澶囧啀鍒犳湰鍦版暟鎹級銆?
## 鍙戝竷鍒?GitHub / HACS

鎯宠鍒汉鍦?HACS 閲屾悳绱㈠苟瀹夎锛岄渶瑕佹妸鏈洰褰曞彂甯冩垚涓€涓?*鍏紑 GitHub 浠撳簱**銆傛湁涓ょ绾у埆锛?
| 鏂瑰紡 | 鍒汉鎬庝箞瑁?| 鏄惁闇€瑕佸鏍?|
| --- | --- | --- |
| 鑷畾涔夊瓨鍌ㄥ簱 | HACS 鈫?娣诲姞浣犵殑浠撳簱 URL 鈫?涓嬭浇 | 涓嶉渶瑕侊紝鏈€蹇?|
| HACS 榛樿鍟嗗簵 | HACS 閲岀洿鎺ユ悳绱㈠畨瑁?| 闇€瑕佸悜 `hacs/default` 鎻?PR 骞堕€氳繃瀹℃牳 |

### 1. 寤轰粨搴撳苟涓婁紶

1. 鍦?GitHub 鏂板缓**鍏紑**浠撳簱锛屽悕绉板缓璁?`ha-oneconnect-bridge-gui`銆?2. 涓婁紶鏈洰褰曞唴瀹癸紝淇濇寔涓嬮潰鐨勭粨鏋勶紙**涓嶈**鍙笂浼?zip锛夛細
   ```text
   hacs.json
   README.md
   LICENSE
   NOTICE
   CHANGELOG.md
   .github/workflows/validate.yml
   custom_components/oneconnect_bridge_gui/
   ```
3. 鎶?`custom_components/oneconnect_bridge_gui/manifest.json` 閲岀殑 `wang-peak` 鏇挎崲鎴愪綘鐨?GitHub 鐢ㄦ埛鍚嶏紝骞惰ˉ涓?`codeowners`锛?   ```json
   "documentation": "https://github.com/浣犵殑鐢ㄦ埛鍚?ha-oneconnect-bridge-gui",
   "issue_tracker": "https://github.com/浣犵殑鐢ㄦ埛鍚?ha-oneconnect-bridge-gui/issues",
   "codeowners": ["@浣犵殑鐢ㄦ埛鍚?]
   ```
4. 浠撳簱璁剧疆閲屽～涓€鍙ユ弿杩帮紝骞舵坊鍔?topics锛歚home-assistant`銆乣hacs`銆乣integration`銆?
### 2. 鍙戜竴涓?Release锛圚ACS 鐢ㄥ畠鍒ゆ柇鐗堟湰锛?
1. GitHub 鈫?Releases 鈫?Draft a new release銆?2. Tag 濉?`v0.2.4`锛堜笌 `manifest.json` 鐨?`version` 涓€鑷达級銆?3. 鏍囬濉?`OneConnect Bridge GUI 0.2.4`锛岃鏄庡彲浠?`CHANGELOG.md` 澶嶅埗銆?4. 鍙戝竷銆?
HACS 鐢ㄦ渶鏂?Release 鐨?tag 浣滀负鍙敤鐗堟湰锛泃ag 鍜?manifest 鐗堟湰涓嶄竴鑷翠細鎻愮ず鏇存柊寮傚父銆?
### 3. 绛夋牎楠岄€氳繃

浠撳簱鐨?**Actions 鈫?Validate** 浼氳繍琛?HACS 瀹樻柟鏍￠獙銆傜豢鑹插嵆鍙紱濡傛灉绾簡锛屾寜鏃ュ織鏀?`hacs.json` / `manifest.json` 鍚庨噸鏂板彂鐗堛€?
### 4. 鍒汉鎬庝箞瀹夎

鍏堣涓婃父 OneConnect Bridge锛堝畠涔熸槸鑷畾涔夊瓨鍌ㄥ簱锛夛細

```text
HACS 鈫?闆嗘垚 鈫?鍙充笂瑙?鈰?鈫?鑷畾涔夊瓨鍌ㄥ簱
娣诲姞 https://github.com/xiasi0/ha-oneconnect-bridge
绫诲瀷閫?Integration 鈫?涓嬭浇 鈫?閲嶅惎
```

鍐嶈鏈?GUI锛?
```text
HACS 鈫?闆嗘垚 鈫?鍙充笂瑙?鈰?鈫?鑷畾涔夊瓨鍌ㄥ簱
娣诲姞 https://github.com/浣犵殑鐢ㄦ埛鍚?ha-oneconnect-bridge-gui
绫诲瀷閫?Integration 鈫?鎼滅储 OneConnect Bridge GUI 鈫?涓嬭浇 鈫?閲嶅惎
```

> 涓や釜鏄嫭绔嬮泦鎴愶細涓婃父璐熻矗鍗忚鍜岀綉鍏筹紝GUI 鍙礋璐ｇ紪杈?`mapping.yaml`銆傚彧瑁?GUI 涓嶈涓婃父浼氱敤涓嶄簡銆?
### 5. 鎯宠繘 HACS 榛樿鍟嗗簵

鍦ㄨ嚜瀹氫箟瀛樺偍搴撹兘琚畨瑁呫€佷笖绋冲畾浣跨敤涓€娈垫椂闂村悗锛屽啀鍚?[hacs/default](https://github.com/hacs/default) 鎻愪氦 PR锛屾妸 `oneconnect_bridge_gui` 鍔犺繘 integration 鍒楄〃銆傞渶瑕侊細鍏紑浠撳簱銆丷elease銆佸搧鐗屽浘锛堟湰浠撳簱宸插甫 `brand/icon.png` 鍜?`brand/logo.png`锛夈€丷EADME銆両ssue 寮€鍚€丠ACS 鏍￠獙閫氳繃銆?
## 寮€鍙戜笌鑷祴

`tools/selftest.py` 鐩存帴璋冪敤涓婃父 `business.mapping_config`锛堣鍖呬笉渚濊禆 Home Assistant锛夐獙璇侊細

```bash
python tools/selftest.py
```

瑕嗙洊锛氬啓鍏?3 涓瓙璁惧銆佷笂娓哥湡瀹炶В鏋愩€佹暣鏁伴敭 contract 寰€杩斻€佸浠姐€侀潪娉?contract 鎷掔粷銆乣enabled: false` 鏃朵粛鍋氱粨鏋勬牎楠屻€?
`tools/flowtest.py` 鐢ㄦ渶灏?HA 妗╄窇瀹屾暣鐨勯€夐」娴佺姸鎬佹満锛?
```bash
python tools/flowtest.py
```

瑕嗙洊锛氭坊鍔犲瓙璁惧銆侀噸澶?key銆乣st` 瑕嗙洊銆侀潪娉?contract 涓嶈惤鐩樸€佺紪杈戜繚鐣欐湭鐭ュ瓧娈点€佸垹闄ょ‘璁ゃ€佺洿鎺ョ紪杈?YAML銆佸惎鍋滃紑鍏炽€?
---

闈炲畼鏂归」鐩紝涓庡崕涓恒€丱neConnect 瀹樻柟鏃犲叧銆備娇鐢ㄥ墠璇烽槄璇讳笂娓搁」鐩殑鍏嶈矗澹版槑銆?