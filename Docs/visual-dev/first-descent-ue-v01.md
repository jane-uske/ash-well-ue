# 第一眼深井 · UE 视觉样片 v01

> 历史记录（2026-09-10）：以下内容记录当时的样片、实现与评价。当前美术目标见[最新规范](../ArtDirection/art-direction-v1.md)；本文旧工业主导、检修工外观或永夜要求不再作为后续制作标准，原有测试与实现状态仍按原日期理解。

日期：2026-09-05。

用户认可转向 UE 进行画质验证，延续“小步、可见成果”的开发方式。本轮交付独立 UE 工程与一个真实场景镜头。

- 工程：[AshWell.uproject](../../unreal/AshWell/AshWell.uproject)
- 使用与重建：[UE 工程说明](../../unreal/AshWell/README.md)
- 本机启动：[launch_editor.command](../../unreal/AshWell/Scripts/launch_editor.command)
- 原始视觉目标：[AI 概念图](../../assets/concepts/first-descent-v01.png)
- 本轮真实截图：`output/ue-first-descent-v01.png`

## 已实现

使用本机已安装的 Unreal Engine 5.7.4。单独通过启动进程的 DEVELOPER_DIR 选择 Xcode Beta，未修改全局开发工具选择。

地图包含 20 个环境网格块、两名静态远征者、可编辑 PBR 材质、三套 2K 贴图、冷色环境灯与手灯、体积雾。构图已经过实际 UE 截图调整，包括洞口宽度、相机位置、完整人物入画、同伴在弯曲栈桥上的站位、远景亮度和岩壁几何。

环境与人物保留 Blender 源文件、生成脚本、FBX 和往返验证结果。贴图来自 Poly Haven 的 CC0 素材，完整来源与校验信息见 UE 工程 SourceAssets/Textures。

## 判断与范围

该样片证明本机能够打开工程并实际渲染这组资产。它仍是第一轮视觉资产，人物衣料、岩壁和巨构的建筑细节尚未达到概念图精度。

这是静态视觉样片，尚未添加 UE 游戏角色控制、骨骼动画、碰撞路线或 AI Agent。编辑器可自由观察三维空间，不能将其等同于完成游戏行走。静态截图采用常规 UE 实时渲染路径，未用 Path Tracer、Blender 成片或 AI 后修代替；不据此声称达到某个实时帧率。

## 下一步

先让用户判断构图、尺度、冷暖光和材质是否符合“震撼、压抑、沉浸”的方向。根据反馈只优先改善最重要的一处，获得认可后再恢复短距离角色行走，并记录真实运行性能。
