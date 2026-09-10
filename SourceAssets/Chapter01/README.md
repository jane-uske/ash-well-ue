# 第一章《下井》模块资产 v01

2026-09-07。按用户确认的第一章概念图制作，保持配给街 → 矿道 → 断崖栈桥 → 检修站 → 升降机顺序。

## 源文件和导入

- `Chapter01_Kit.blend`：Blender MCP 中新建的独立模块场景；原有动画检查场景没有被覆盖。
- `SM_C1_*.fbx`：10 个原创模块，合计 14,036 三角面。详细统计见 `manifest.json`。这个数字仅指新模块，不包括复用的巨构、岩石、角色和 Boss。
- 模块：住宅立面、布棚、水泵、水罐、矿道支架、栈桥板、栏杆、出发门框、闸门、笼灯。栏杆模块已导出备用，关卡坡道实际用连续扶手与转角安全碰撞。
- 厘米制，UE 实例缩放为 1；FBX 只导出网格，不导出相机与灯光。关卡灯光由 UE 独立配置。
- 重建脚本：`../../Scripts/chapter01_blender.py`；导入：`../../Scripts/chapter01_import.py`；摆放：`../../Scripts/chapter01_build.py`。
- 游戏资产：`/Game/AshWell/Chapter01/`。Blender 工程是模块库，完整关卡布局保存在 UE 地图里。

## 材质与来源

几何由本项目创建。UE 复用项目已有的工业金属、混凝土、岩石和角色素材，没有购买或下载新商业资产。

地面 Slate Floor 03、金属 Rusty Metal 04 为项目已收录的 Poly Haven CC0 贴图，来源、作者及文件校验见 `../SurfaceV2/texture_manifest.json` 和 `../SurfaceV2/README.md`；扫描石块沿用 `../ScansV2/manifest.json`。新增世界坐标地面贴图每 1.5 米重复，避免长地板 UV 拉伸。粗糙度使用 Masks 采样，与项目纹理压缩类型匹配。

`Signs/*.png` 为原创中文路牌，使用项目内 `Content/AshWell/Intro/Fonts/NotoSansSC-Regular.otf` 渲染；字体许可见同目录 `OFL.txt`。路牌文案、贴图生成脚本为 `../../Scripts/chapter01_signs.py`。

这是可继续编辑的第一版模块套件。居民暂时共用已有角色与待机动作，布棚为静态网格，门窗没有可进入的室内。
