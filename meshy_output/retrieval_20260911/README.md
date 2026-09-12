# Meshy 已有资源下载清单

核对日期：2026-09-11。已同时查看 API 和网页工作区；本次只下载已有结果，没有创建生成、绑定或动画任务。

## 最新两个贴图模型

- **Tree Sentinel Shield**：[GLB](/Users/rare/dev/ash-well-ue/meshy_output/20260911_201130_tree-sentinel-shield_cad64068/model.glb)。已另存基础色、金属度、粗糙度、法线贴图。
- **Tree Sentinel Halberd**：[GLB](/Users/rare/dev/ash-well-ue/meshy_output/20260911_201214_tree-sentinel-halberd_87d0ac80/model.glb)。已另存基础色、金属度、粗糙度、法线贴图。

## 动画分类中最新两个成功资产

- **Gilded Warhorse**：[战马骨骼模型](/Users/rare/dev/ash-well-ue/meshy_output/20260911_201320_gilded-warhorse_01a08f11/rigged.glb)。文件已验证：有骨骼蒙皮，没有材质贴图，也没有动画片段；不能视为已经完成马匹动作。
- **Gilded Sentinel**：[人物骨骼模型](/Users/rare/dev/ash-well-ue/meshy_output/20260911_201322_gilded-sentinel_01a08e8e/rigged.glb)；已有[走路](/Users/rare/dev/ash-well-ue/meshy_output/20260911_201322_gilded-sentinel_01a08e8e/walking.glb)、[跑步](/Users/rare/dev/ash-well-ue/meshy_output/20260911_201322_gilded-sentinel_01a08e8e/running.glb)两份动作文件。动作文件仅含骨架节点与曲线，需要配合对应骨骼模型使用。

网页列表中间的一次骨骼绑定失败已排除。GLB 文件长度、网格、材质、骨骼和动作通道已检查；尚未导入或替换 UE 资产，未做游戏内变形质量验收。各资源目录有 task.json、metadata.json、validation.json；本目录的 download-manifest.json 汇总文件路径与校验值。

动作导入时选 `retarget_clip`：走路约 1.03 秒，跑步约 0.70 秒；两份文件还各含一个约 0.067 秒的基础层片段，不应作为完整动作。动作目标骨骼名称均能在对应人物模型中找到。
