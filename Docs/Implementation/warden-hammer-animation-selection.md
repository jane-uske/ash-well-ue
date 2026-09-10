# 守井者重锤动作素材筛选

核查日期：2026-09-06。用户明确偏好：社区免费素材优先。状态：已确认免费来源和作者授权；没有购买或接入付费动作。当前战斗与 AnimationTrial 未修改。

## 当前首选：免费素材

[Human Melee Animations FREE / Kevin Iglesias](https://kevdev.itch.io/human-melee-animatons-free) 提供 Godot/Unreal 版本（约 12 MB），包括左右手单手攻击、双手攻击、长柄攻击、受击、死亡和移动。下载弹窗的 “No thanks, just take me to the downloads” 可以零元进入下载页，无需支付信息。已确认该流程；本轮浏览器触发了下载，但尚未确认本地文件落盘，不视为已经导入或验收。

[作者授权说明](https://www.keviniglesias.com/#license)明确免费资产也可用于商业项目，适用 Standard Asset Store EULA，不能作为独立素材重新分发；不是 CC0。后续先检查单手与双手攻击的完整姿态，再决定哪段适配守井者。94 个文件包含男女和移动变体，不是 94 种攻击。暂不能认定它包含合格的专用重锤动作。

[Quaternius Universal Animation Library Standard](https://quaternius.com/packs/universalanimationlibrary.html) 作为已有 CC0 免费底库继续保留。当前 AnimationTrial 使用其中的单手劈砍；它已证明导入链路，不代表重锤风格已达标。完整版与免费 Standard 内容有区别。

开发顺序：先试免费现成动作，再做少量关键姿态修正；不把购买付费包作为继续开发的前提。

## 付费资料留档，不再作为首选

[2Handed Hammer AnimSet / wemakethegame](https://www.fab.com/listings/1f4b567e-595a-4f8c-a6d3-cf6f83b36ed9)

[作者演示，从 1:09 附近查看攻击](https://www.youtube.com/watch?v=9XMyRKXDhe4&t=69s)

Fab 技术详情当前列出 Epic skeleton、81 段根运动动画、UE 4.18–4.27 / 5.0–5.8；开发与目标平台仅列 Windows。没有在本机验证该包，不能据此承诺 Mac 兼容。搜索索引显示起价 USD 69.99；当前未登录页面按地区显示 PHP 4,911.28 起，最终价格及许可档位以账户结算为准。

通过浏览器抽查作者视频的待机与攻击画面：可见双手长柄握持、屈膝与转体；1:20 附近还可见标注 attack_1H_around 的动作。只做了预览抽查，不等于逐段动作质量验收，也未取得动画文件或确认每段时长。大幅度组合攻击可作研究，第一版只筛一记原地砸击。

## 备选

- [Heavy Hammer / KrystalAnimation](https://www.fab.com/listings/7cd78186-3869-4de6-a922-3c6039b0f30b)：页面列出 20 段攻击及移动、受击等动作；搜索索引起价 USD 29.99。已找到[官方预览](https://www.youtube.com/watch?v=wswZ_QQIBJc)，本轮未做视频动作审查，不据此判断比首选更好。
- [Human Melee Animations FREE / Kevin Iglesias](https://kevdev.itch.io/human-melee-animatons-free)：免费包包含一段双手攻击，作者提供 Godot/Unreal 下载。可用于双手握持适配试验，但不是专门的重锤动作包；不能把 94 个文件说成 94 种独立攻击，也不能沿用 Quaternius 的 CC0 授权判断。本轮未下载。

## 与当前守井者的适配决定

当前模型是十二个刚性部件驱动，没有标准人体蒙皮骨骼，不能直接挂到 Epic 骨骼动画上。肩甲不对称、单侧持锤、手臂比例和锤柄长度均应保留。

取得合适源动作后的最小接入范围：

1. 在独立试验资产中检查源动画完整姿态、根位移、持锤手与实际锤长，再决定截取哪段砸击。不要只按素材名称挑片段。
2. 用 Blender 建立测试骨架，先让已有刚性部件跟随相应骨骼；手指与衣摆的正式蒙皮不在本轮范围。
3. 修正肩肘碰撞和持锤握点。双手长柄动作无法合理适配时放弃该片段，不为动作改变已确认外观。
4. UE 试验先锁定/移除源根位移，由现有战斗代码继续负责角色移动。把起手、落锤、恢复分段对齐现有 1.05 / 0.22 / 1.25 秒，伤害仍由原逻辑触发；不要用整体慢放代替节奏匹配。
5. 检查背面、侧面、命中瞬间、挥空与恢复，随后验证攻击、闪避、锁定和伤害规则。保留原程序动画回退路径。

购买决策尚未授权；素材的实际 Mac 导入和单手姿态适配仍是待验证项。本记录只支持选择下一份试验素材，不代表动画接入完成。
