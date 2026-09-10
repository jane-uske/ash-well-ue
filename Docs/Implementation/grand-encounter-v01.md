# 七号检修站：大场地与开门亮相 v01

日期：2026-09-09。当前为 UE 5.8 本地开发版本，不打包。

## 本轮变更

- 仅第一章检修站战斗甲板扩大到 23.1 × 21.45 米；保留栈桥连接锚点和地面高度。旧独立战斗地图保留原尺寸。
- 增加遮挡大厅的双扇铁门。门前按 E，2.7 秒滑开，进入后继续按原供电流程唤醒 Boss。
- 守井者统一放大 1.5 倍；匹配起始高度、攻击选择距离、锤头扫掠半径、步态与锁定镜头。保留当前外观、动画、800 生命和三招时序/伤害。
- 玩家伤害、攻击与闪避体力成本、无敌窗口不变。测试机器人改为较晚闪避并预留体力，不修改玩家规则。
- 轮廓灯与正面阴影灯加强巨型体积；闭门时取消锁定，交互标记显示铁门。

## 音乐

通过用户 Suno Free 网页账户生成 Iron Gate Awakens（v4.5-all），选用约 2 分 30 秒版本。

来源：https://suno.com/song/8213b76d-66e7-455f-a0ad-3fea7fa9f51e

原始 M4A、标准化 WAV、来源记录保存在 `SourceAssets/SunoWarden/`。
通过 UE 原生 MCP 的 `grandassets` 导入步骤生成 `Content/AshWell/Combat/GrandEncounter/AW_Suno_Warden_Combat.uasset`。
48 kHz 双声道，标准化目标 -22 LUFS，加入首尾短淡变。
开门低音量渐入、送电后抬升，二阶段沿用已有叠层。胜利保留机械停机和人声结尾。
目前不是按小节剪辑的无缝音乐循环；运行验证加载与状态切换，听感仍需用户实听。

Suno Free 本次下载仅用于个人非商业原型，当前在非 Shipping 构建加载；未购买订阅。
授权来源：https://help.suno.com/en/articles/13876865

## Meshy 动作暂缓

`AW_Warden_RightHammer_Slam_v01` 已在 Meshy 网页生成并保存（Motion Prime，3 秒，10 点）。
用户明确要求先完成场景和音乐，动作保留待接入。未下载 FBX、未替换游戏动画、未购买 Pro。
记录：`meshy_output/20260909_warden_motion_web/metadata.json`。

## 启动与回退

门前快速预览：双击 `Scripts/launch_station_gate.command`，无通关或无敌作弊，开门后照常战斗。

正常启动：双击 `Scripts/launch_chapter01.command`。WASD 移动，E 开门/送电，左键攻击，空格闪避，Tab 锁定，R 重试。
本轮前 Source/Scripts/Config 快照：`Saved/GrandEncounter/before-grand-encounter.zip`。
不要直接覆盖整个工作树：此前已有其他未提交的章节与资产工作。

测试记录见 `Docs/Verification/GrandEncounter/`。自动测试不能替代真人试玩、完整镜头验收或 30 分钟性能验证。
