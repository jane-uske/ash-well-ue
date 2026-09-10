# 第一章地图：实机验证 v01

2026-09-07，UE 5.8.2，Mac 开发窗口，1600 × 900。完整说明见 [chapter01-map.md](../../Implementation/chapter01-map.md)。

## 实际游戏截图

![配给街](ration-street.png)
![矿道](mine-tunnel.png)
![矿道出口](mine-exit.png)
![断崖栈桥](cliff-walkway.png)
![检修站入口](station-entrance.png)

这些是 UE 游戏内截图，没有后期生成或美化。当前建筑与居民有明显复用，近景细节还不等于概念图；预览图保留在 `../../Concepts/Chapter01/`。

## 记录

- `map-build.json`：实际保存的地图、路线与模块列表。
- `blender-manifest.json`：10 个新增模块，14,036 三角面；不是全场景三角面统计。
- `mcp-results.json`：原生 MCP 导入/建图返回状态。完整本机响应在 `Saved/Chapter01/`。
- `player-invariants.json`：保留的 21 项玩家规则源码检查通过。
- `route-complete.json`：完整流程中路线 18/18，到达站区、Boss 已击败；每秒采样的最后一条恰在电梯移动中。
- `fight-ending-complete.json`：同一完整流程在退出前的最终快照，20 次命中击败 800 生命 Boss，二阶段、记录和电梯结尾完成；`slice_completed=true`。
- `warden-death-result.json` / `warden-reset-result.json`：另一轮完整步行后站内死亡与重试；回到站区坐标，玩家和 Boss 资源与状态重置。机器人在重试后会自动送电，所以 reset 的 powered 为 true。
- `final-display-check.json`：最终地图再次到站与重试，新增地面和玩家锤子材质编译失败数为 0，路牌已复查正向显示。
- `hammer-bounds.json`：已修复材质的玩家锤子仍沿原握持轴，网格边界与此前导入记录一致。

没有将自动测试视为真人试玩，没有完成该新地图的 30 分钟性能验收。本轮没有重跑此前所有战斗专项探针。开发启动仍记录已有 GameFeatureData 类加载的 handled ensure，但进程继续运行并完成测试；没有据此宣称日志零告警。最后画面检查另行确认新增地面与玩家锤子不再出现材质编译失败。
