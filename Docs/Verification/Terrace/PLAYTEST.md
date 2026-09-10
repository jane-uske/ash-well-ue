# 断链台原生 UE 验证

2026-09-06，UE 5.8.2。本次验证没有修改既有 Boss 源码、地图或模型。

- 上层路线：从升降机出口经观景台、上层栈道、吊臂到侧门背面，使用真实 CharacterMovement 输入走完，记录在 `upper-route-before-key-fix.json`。此记录早于 E 键绑定修正，不能用它证明开门交互。
- 交互专项：MCP 启动 PIE，分别覆盖出生在门正面与背面的用例。通过实际键盘按 E，正面保持关闭、背面 GateOpen 为 true 且门抬升 420 cm。记录 `gate-front-after-E.json`、`gate-back-after-E.json`。这两项使用出生位置覆盖，不算连续步行证明。
- 下层和回程：从已打开的门背面穿门返回观景台，再走下坡、低 8 米的管廊、上坡、吊臂端和回程捷径，7 个目标点全部到达，无卡住或跌落，见 `lower-and-open-shortcut.json`。
- 路线检查临时使用 180 cm/s，最终角色默认 90 cm/s，Shift 沿用基类 45 cm/s；完成后测试驱动恢复默认速度。自动路线属于碰撞和连通性验证，不能代替真实玩家的节奏评价。
- 最后一轮改动仅给指示牌增加可从另一方向阅读的背面，牌子无碰撞，未改变上述路径的地面和栏杆。
- MCP 实际完成 initialize、tools/list、工具发现、读取当前地图和 5 个复用实例，以及 StartPIE / StopPIE；原始结果留在 `Saved/Terrace/mcp-*.json`。

未完成：Boss 战后自动切图、共享生命/装备/剧情状态、最终美术、性能验收和独立发行打包。远景城镇、炉骸和山脊不可到达。

原生 `-game` 启动已加载断链台及 `BP_TerraceGameMode_C`。启动日志出现 GameFeatures.GameFeatureData 主资产类型缺类的非致命 ensure，随后地图正常加载，未因此修改共享配置；记录见 `native-startup.json`。独立游戏窗口启动检查结束后已关闭测试进程，编辑器保留在入口的正常 PIE 游玩状态，自动路线驱动已结束。
