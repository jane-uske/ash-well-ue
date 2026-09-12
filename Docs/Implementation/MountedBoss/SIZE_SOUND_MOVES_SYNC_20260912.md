> 最新：代码c62edc2。下列c2e44ae录音录像及32项回归保留；之后修正马蹄接地采样比例与复位缓存，补测5项通过。Mac重新锁屏，c62edc2窗口补录受阻，已请求解锁。A/B未获动态验收，C未初测。

# 人马尺寸、声音与招式同步候选

用户最新指令：声音、招式、原版大小一起同步。此条恢复制作，替代上一轮暂停；分支 `codex/mounted-charge-standard`，回退基线 `8a78f76`。目标仍是普通大树守卫，不能把本次候选称为完整复刻。

## 当前代码 c2e44ae，22项运行回归通过，动态验收未完成

- 完整人马组件及实体碰撞统一乘 1.30。原局部骑士 1.60 / 马 1.30 对应世界 2.08 / 1.69；斧全长 364 cm、盾模型高度约 195 cm。它们是对本地资产的制作尺寸，不是原作模型测量值。相机与参考人物所处深度不同，不能只凭画面像素宣称精确一致。
- 旋转与位移碰撞统一读取缩放后的真实箱体。冲锋向玩家侧面的偏移随马宽变化；没有缩小马身阻挡或扩大武器判定半径来换取通过。
- 放大后的第一轮发现：低扫依然命中但马身被玩家拦住；改偏移后能掠过但低扫错过玩家。保留两轮失败报告。该问题涉及变大的可见武器与原位移曲线的配合，后续将行进曲线缩至旧版 72%，并重做马步与 Blender 原生 IK 支撑。六段持续时间仍是 5.8 秒；位移是制作估计，不能称为提取的原作数据。
- 冲锋音效改由真实 Montage 的 Strike Notify 触发，移除 Launch 时提前约 0.58 秒的挥击声；其他五招仍保留原兼容动画驱动。马蹄跟随实际接地，击中/落地跟随伤害或落地事件。
- 24 个声音变体、8 个 UE SoundCue：玩家挥剑、长柄挥击、铠甲命中、武器命中、盾挡、马体撞击、落地、马蹄。来自 CC0 音源，保留原始档案、作者/许可、选段与处理记录；没有购买，也没有使用《艾尔登法环》的游戏音频。
- 盾面使用可见模型三角形接受剑刃查询，单次被挡只播放盾挡声，不扣 Boss 生命，不作为马身位移碰撞。原剑击/重击/生命/体力/重试仍保留。
- 自然 AI 保留六招和阶段规则，在合适距离角度内选择可用招式，并降低上次招式的重复权重；不让固定优先顺序长期压住其余近战。没有强制循环六招的正式战斗逻辑。

## 招式与原作覆盖

| 动作族 | 当前工程 | 本次状态 |
|---|---|---|
| 冲锋横扫 | 已有原生 AnimBP / 双 Montage / Notify / 曲线 | 尺寸、步幅、声音联动候选，需新录像验收 |
| 近身横扫 | 已有兼容动画与真实刃缘扫掠 | 保留、重测声音/尺寸/选择；未宣称动作还原 |
| 过顶下劈 | 已有兼容动画与真实刃缘扫掠 | 同上；39–44 秒原片复查可见扬马、下劈及后续收势 |
| 马体肩撞 | 已有真实马身扫掠接触 | 保留，接独立身体冲击声 |
| 前蹄震地 | 已有实验动作 | 保留；原片119秒一带不足以确认它是独立纯蹄击 |
| 跃起盾砸 | 已有真实离地/盾底接地门限 | 保留，接落地声；不等于原作全部盾击变体 |
| 直刺、上挑、回身/反向斩 | 缺失或未做对应正式动作 | 不改名冒充已有动作；后续须逐项原生制作 |
| 地面盾击/追击盾撞 | 缺少独立对应动作 | 盾挡接触机制不是盾击招式完成 |
| 魔法反制 | 缺失 | 当前没有玩家法术/投射物，不能用播放盾光冒充反射 |

攻略给出不同分类，Game8 为8类、GameSkinny为7类；这不是官方唯一招数。出处及完整缺口见 `TREE_SENTINEL_RESEARCH_20260912.md`。本次不以新增枚举数量作为完成标准，也未批量迁移其他五招。

## 验证与交付边界

当前冻结模块：22/22运行fixtures通过，含六招成对命中/闪避、玩家轻重击/空挥/马身阻挡、可见盾面格挡、前摇取消/中断清理/重试/死亡/脚本交锋。证据 `Docs/Verification/MountedChargeSample/SyncSizeSoundMoves/FinalRegression`。同一c2e44ae候选的坡面冲锋8/8、原守井者2/2也通过。随后c62edc2仅修蹄声/采样，movement、冲锋命中/闪避、清理、重试5/5通过；两版证据分别保存。

`capture_mounted_native_review.py size` 展示真人尺寸参照的环绕；`moves` 依次重置展示六个动作，明确为制作检查，绝不作为普通输入实战；`charge` 保留正常速度原片固定偏移对照。原录像和真实时间戳保留。

正式入口仍为 `Scripts/launch_mounted_charge_sample.command`。真人 C 初测入口为 `Scripts/launch_mounted_human_test.command`，正式按键/自然 AI/完整血量。C仍需用户亲自输入10–15分钟；本轮制作检查不替代C，不替代最终验收。

## 导入失败记录

本轮 SoundCue 构建在 `SetChildNodes` 后未重建编辑器输入接口，触发 `SoundCueGraph.cpp:61` 断言。PID31590 的引擎日志和崩溃记录保存在 `Docs/Verification/MountedChargeSample/SyncSizeSoundMoves/ImportFailure`；仅正常终止对应CrashReportClient与其TraceServer。修正为先重建接口、检查数量再连接。后续修正资产重复导入时未先加载已有对象的流程。最后一次导入正常退出，未出现上述断言/Ensure；见同目录sync-import-verified.log。游戏中声音播放已进入22项运行回归，不据此认定游戏存在性能故障。

## 回退

原件不覆盖。源码/UE资产完整回退使用工作分支基线8a78f76另建工作树；不要强制重置有新改动的工作区。单独 `-MountedAssemblyScale=1` 只能查看旧尺寸，不能替代完整回退，因为本次马步和位移已经改变。音频、动画和判定验收必须绑定同一版本。


## 可看结果与对应版本

以下录像均是 **c2e44ae**，正常速度、原始窗口时间戳，无剪辑、变速或插帧。`moves` 在一段连续录像中按单招重置；反馈检查调用明确的QA动作，二者均不能当作普通输入C。

- [大小与主角参照，30秒](../../Verification/MountedChargeSample/ReferenceProduction/Native-size-220130/window-uncut.mp4)
- [带声音六招展示，52秒](../../Verification/MountedChargeSample/ReferenceProduction/Native-moves-220741/window-uncut.mp4)
- [冲锋窗口原片，30秒](../../Verification/MountedChargeSample/ReferenceProduction/Native-charge-221032/window-uncut.mp4)
- [原片左/当前右，正常速度5.8秒](../../Verification/MountedChargeSample/ReferenceProduction/Native-charge-221032/original-left-current-right-1x.mp4)
- [主角剑击命中反馈](../../Verification/MountedChargeSample/SyncSizeSoundMoves/Feedback-221345/light/window-uncut.mp4) / [剑击盾挡反馈](../../Verification/MountedChargeSample/SyncSizeSoundMoves/Feedback-221345/shield_block/window-uncut.mp4)

窗口采集实测约54–57缓冲帧/秒，所有五段原始时间戳/音画封装审计通过。它们**不是UE运行帧率**。六招整段音频平均-43.8dBFS、峰值-17.0dBFS；包含大量待机间隔，混音力度尚需试听验收。对照原片在本地没有音轨，因此并排片仅保留当前游戏声，不宣称已复制原版音色。

1080p原生UE CSV采样对应c2e44ae：排除前300帧，保留后900帧，平均12.81ms、p95 20.95ms、p99 22.16ms，主要受GPU/渲染限制。**未达稳定60FPS**。这不是真人10–15分钟持续性能验收；c62edc2没有新的帧时间验收。

## 马蹄采样修正及剩余缺口

核查c2e44ae的B时，346.21cm/s滑移代理仅来自0.244秒支撑足采样，不能据此评定全招步态。扩大人马后，马蹄骨点的高度偏移也扩大，旧世界空间门限漏掉接地。c62edc2将门限随整体缩放，并在重试/复位后重新初始化世界空间采样，避免瞬移混入落蹄与漂移。补测movement记录18次落蹄；支撑样本覆盖仍有限，**没有认定马蹄已无滑移**。原始骨点/几何检查保存在SyncSizeSoundMoves/hoof-geometry.json，继续制作应以可见蹄底接触核准。

c62edc2补录的预检发现Mac锁屏，录像链路没有启动。旧录像不能冒充这一补丁的动态验收；待用户解锁后补录。截止交付整理，自己启动的UE、录像器、崩溃报告器及TraceServer均已退出或清理，原始崩溃档案仍保留。

当前未达到原片质量：其余五招仍是兼容动作；直刺、上挑/回身攻击、盾击变体和魔法反制未完整制作；马匹重量/制动、骑士受击姿态、死亡离鞍穿插与偏强命中闪光仍需视觉修正。当前复刻目标保持，不把上述缺口划成完成。

启动使用 [launch_mounted_boss_current.command](../../../Scripts/launch_mounted_boss_current.command)。正式C初测仍用launch_mounted_human_test.command，由用户按正式按键连续试玩10–15分钟，初测与最终验收分别记录。

回退示例：在新目录建立8a78f76工作树并重新构建，再使用该工作树的入口。不要在有未保存改动的当前目录执行强制重置。完整版本/录像/检查索引为 `Docs/Verification/MountedChargeSample/SyncSizeSoundMoves/delivery.json`。
