# 旅人长剑与动作接入 v01 — 2026-09-10

后续角色与操作更新见 [主角动作与布料 v02](hero-complete-v02.md)。本文成本与验证记录描述 v01 当时状态。

外观基准是 `Docs/ArtDirection/Characters/hero-turnaround-v01.png`，不是旧工人角色。原三视图保留，生成的无披风躯干仅是绑定中间资产。本轮不修改故事，不打包。

## 可玩改动

- 左键横劈零体力，伤害 40；右键重击消耗 34，伤害 55；Shift 闪避消耗 28；空格跳跃。零体力仍可普通攻击。
- WASD 常速跑，Ctrl 慢走，空格跳跃，Shift 点按闪避/长按冲刺；锁定或战斗时切换持剑戒备与战斗移动。Tab 锁定，E 交互，R 重试。
- 独立长剑和剑鞘；探索背负，战斗握持；剑刃分段扫掠，每次攻击最多造成一次伤害。
- 守井者重砸前摇 1.55 秒、踢击 1.15 秒、追击 1.65 秒；提高举锤姿态，提前完成蓄力姿势，保留快速落锤、恢复及既有音效反馈。
- 既有 Meshy 翻滚继续使用；本轮没有购买另一套翻滚。

## 角色制作与社区动作

原创的是外观，不要求所有动作从零手搓。实际路线：三视图 → 分离披风/武器的可绑定底模 → Meshy 生成与自动绑定 → Blender 转换骨架、权重和握持 → 社区动作重定向及接触修正 → UE 状态、位移、伤害与镜头验证。

本轮实际使用已有 Quaternius Standard CC0 动作库，分离 Idle / Walk / Run / Sprint / Guard / CombatWalk；横劈和重击上身用本地关键姿态、手部目标及两段 IK 重新适配长剑。不是只把同一动画旋转方向。Meshy 基础走跑文件已保存，但本轮游戏中的走跑来自 Quaternius。

- [Quaternius Universal Animation Library](https://quaternius.com/packs/universalanimationlibrary.html)：本地 Standard 免费库 45 个动作，授权见 `SourceAssets/AnimationTrial/License.txt`。
- [Adobe Mixamo FAQ](https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html)：可用免费 Adobe ID 获取用于商业项目的动作；本轮未下载接入。
- [Epic Game Animation Sample](https://dev.epicgames.com/documentation/en-us/unreal-engine/game-animation-sample-project-in-unreal-engine)：是可研究的 Motion Matching 移动方案，不能直接代替武器握持、攻击读招和伤害规则；本轮未迁移整个系统。

## 成本和资产

本轮余额实测 2390 → 2355，使用 35 Meshy 积分：模型 30，绑定 5。没有追加付费动作。凭据仅从用户指定 `/Users/rare/blender/.env` 读取，不写入项目文档或资产。

- 模型任务：`01a08b48-d2d6-77fb-ab13-6a59677b3b0d`
- 绑定任务：`01a08b53-5a67-7288-b94d-3b81566abc50`
- 源资产：`SourceAssets/SwordPass/`；UE 资产：`Content/AshWell/Combat/SwordPass/`。
- 原始 Meshy 输出：`meshy_output/20260910_203249_ashwell-traveller-sword-v01_01a08b48/`。

## 验证与边界

编译成功；16 个不同的实际 UE 渲染运行用例（包含镜头五点检查和结束流程）通过，包括攻击、挥空、三招伤害与闪避、身体阻挡和贴墙闪避。`Scripts/test_sword_pass.py` 进一步检查零体力普通攻击、重击与闪避消耗、六种移动状态、人物尺度和五个姿态的剑身距离。完整记录见 `Docs/Verification/SwordPass/`。

通过无光照贴图与几何法线对照，定位到蒙皮切线光照异常。本版使用变形后表面几何法线，恢复深色衣物并消除主要碎片亮斑；源法线贴图仍保留，后续需整理骨架单位与切线数据。这是可玩兼容处理，不是人物美术定稿。

这些检查不等于最终美术验收。披风是独立蒙皮而非布料模拟；没有独立手指骨骼，握持为静态手套姿态；脸部、披风轮廓、极端动作穿插与移动脚底贴合仍需逐项打磨。本轮未做 30 分钟性能复测、真人试玩或打包。

运行 `Scripts/launch_station_gate.command`。用启动参数 `-SwordBaseline` 对照上一版玩家资产与 Boss 前摇。源代码回退备份 `Saved/SwordPass/before-sword-pass.zip` 仅在本机，不能代替 Git 提交。
