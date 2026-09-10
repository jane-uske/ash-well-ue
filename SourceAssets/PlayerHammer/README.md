# 检修工武器修整

原创 Blender 几何，未使用第三方资产。替换玩家原来的圆柱柄/方块锤头，保留工业检修锤身份与原碰撞规则。

- 柄 62 cm、锤头中心位于握持点本地 +Y 54 cm。
- 头部含钢制撞击面、固定螺栓和赭色护片；柄增加防滑握把与金属箍。
- 两个独立静态网格共 4,512 三角形。头部碰撞仍使用既有武器中心与 24 cm 扫掠球，未扩大攻击范围。
- Blender -Y 对应 UE 本地 +Y，FBX 导入不再转换场景或单位，导入脚本断言尺寸与方向。
- 材质为新建钢、撞击面、橡胶、赭色层，粗糙度复用项目已有 rusty_metal_04 表面（原来源/许可见 SourceAssets/SurfaceV2）。
- `Scripts/build_player_hammer.py` 可重建模型；`Scripts/import_player_hammer.py` 导入至 /Game/AshWell/Combat/PlayerHammer。
- Blender 工作图不是 UE 实机效果；游戏中的材质与握持另行检查。
