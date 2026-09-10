# 守井者骨骼适配

来源是用户确认的 `SourceAssets/WardenHQ` 分件模型。原 GLB 约 25 万三角形；现游戏身体 153,773 三角形，独立锤子约 10,616，合计约 16.4 万。外观、贴图和左右关系保留。

`Scripts/prepare_warden_rig.py` 从 WardenHQ_Prepared.blend 新建独立工作场景。13 个骨骼节点包括 root、身体、成对上臂/前臂、大腿/小腿/脚和预留 Hammer；锤子实际继续是独立静态部件。硬甲刚性权重，8 处肩肘/髋膝连接附近 261 个顶点做有限混合。相机、灯光和参考物不在 FBX 导出集合。

这是**由部件变换驱动的骨架**，不是标准人形重定向骨架：骨骼在同一原点、并列从属 root；UE 将已计算的躯干、两段 IK 部件变换写入 component-space。这样避免未经处理的非人形铠甲套人形动画后变形。后续若转标准 Animation Blueprint/人体动作库，需要另做解剖关节层级与重定向；当前没有声称已经完成。

- `SK_WardenRig.fbx`：身体蒙皮，UE PoseableMesh 驱动。
- `WardenRig.blend`：只保存制作工作场景。
- `manifest.json`：骨骼、三角形、权重和坐标合同。
- `Scripts/import_warden_rig.py`：导入 /Game/AshWell/Combat/WardenRig，并启用 PBR 材质对骨骼网格的支持。
- `AshWellWardenVisual.cpp`：保留锤长，驱动刚性装甲、关节和权重；真实锤头位置供伤害扫掠。

新增蓄力/落锤膝部承重、追击迈步和过载的局部抽动。普通行走脚部的线性支撑段与角色移动匹配，当前地面为平面；不声称具有任意地形脚部 IK 或电影级软组织变形。
