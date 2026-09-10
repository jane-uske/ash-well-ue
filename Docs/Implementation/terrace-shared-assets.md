# 断链台：共用资产与开发边界

2026-09-06。沿用 `/Users/rare/dev/ash-well-ue/AshWell.uproject`，本机引擎 UE 5.8.2。地图 `/Game/AshWell/Terrace/L_BrokenChainTerrace` 是独立的可游玩探索草模。

## 直接复用

| 内容 | 原资产或实现 | 断链台用途 |
| --- | --- | --- |
| 提灯主角、行走、脚步声 | `AAshWellIntroCharacter`、`/Game/AshWell/Intro/Characters`、`/Game/AshWell/Intro/Audio` | `BP_TerraceWalker` 继承已有探索角色。Boss 战角色同样继承该基类 |
| 旧钢、锈铁、湿石、混凝土 | `/Game/AshWell/Materials/V2/M_OldSteel`、`M_Rust`、`M_WetStone`、`M_Concrete` | 平台、栏杆、吊臂、设备、建筑；与 `AshWellCombatArena.cpp` 加载的资产路径相同 |
| 层叠钢构、管道接头 | `/Game/AshWell/Meshes/ArchitectureV2/Foreground/SM_AV2_FG_LayeredSteel`、`SM_AV2_FG_PipeJoints` | 出口矿道钢构和下层管廊细节 |
| 扫描岩石 | `/Game/AshWell/Meshes/ScansV2/SM_Scan_Boulder01_LOD0` 与原配 `M_Scan_boulder_01` | 近景岩石；未修改网格、贴图和原材质 |

共享网格的部分默认材质槽仍为引擎棋盘材质，因此本关在组件实例上指定已有钢铁、锈蚀和岩石材质。源资产不被重写。主角沿用原有正常速度 90 cm/s 和 Shift 轻步速度 45 cm/s。

## 风格延续

沿用检修站的冷灰环境、暖色提灯和维护灯、锈蚀钢构、湿石地面、承重梁与多层管线。户外需要更远的可见距离，曝光和雾参数在本关单独调整，不直接复制室内参数。共用资产只是基础，建筑比例、灯光和构图仍需视觉验收。

目前可走区域包含出口、观景台、上层栈道、下层管廊、断裂吊臂、从背面开启的回程门。远处城镇、炉骸和天线脊是空间关系草模，尚不可到达。

## 与 Boss 开发分工

- 本任务只写 `Content/AshWell/Terrace`、`SourceAssets/Terrace`、`Scripts/terrace_*`、`Scripts/launch_terrace.command` 和本关记录。
- 现有 Boss 地图、`Source/AshWell`、`Config`、守井者模型、检修锤、战斗动画和战斗音轨由 Boss 任务维护。
- 检修站的部分平台和设备由 `AAshWellCombatArena` 在运行时组装，当前不是可拖放的完整预制件。断链台参照其材料和构造语言，未实例化该战斗场景控制器。
- 两张地图尚未做战后自动切图、生命/装备/剧情状态传递。此时让两个任务分别稳定各自关卡；之后在明确的升降机出口接入。
- 本关直接引用共享资产，后续共享资产更改会影响它；那时需重新检查本关。共同基类仍可能随另一任务演进。

## 体验

双击 `Scripts/launch_terrace.command` 打开原生 UE 游戏窗口。WASD 移动，鼠标转向，Shift 轻步。侧门只能绕到背面、走近后按 E 开启。当前关卡只测试探索路线，没有放置 Boss。

开发版依赖本机 UE 5.8 与当前项目二进制，未打包成独立发行应用。浏览器版本是此前路线误解产生的草稿，已经停止，不是本轮交付。

## 本轮工具实测

最初使用 UE 编辑器 Python 构建原生关卡和 Blueprint。随后按用户提出的工作流，连接 UE 5.8 自带 ModelContextProtocol 服务，地址仅监听本机 `127.0.0.1:19852/mcp`，通过真实 MCP 完成初始化、工具发现、当前关卡与共用实例读取、PIE 启动。没有改写全局 Codex 配置；服务绑定本次编辑器进程，关闭编辑器后需重新连接。

Blender MCP 已实际响应，当前是 `SourceAssets/AnimationTrial/CommunityAnimationTrial.blend` 且带未保存修改，因此只读取文件状态。本轮没有通过 Blender 改模型，也没有覆盖它。后续新资产采用独立文件。
