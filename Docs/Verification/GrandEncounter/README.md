# 大场地 / 音乐接入验证

2026-09-09，UE 5.8.2，当前 Mac，1600 × 900。

- 原入口路线到检修站、开门、到控制台送电：实际 QA 行走完成（Saved/GrandEncounter/second-route.log）；该次机器人战斗失败，不作为战斗通过证据。
- 原机器人侧闪试验失败：station-first-failed.json。保留失败记录。
- 更新机器人的闪避时机及体力预留后，站内正常战斗通关，触发二阶段、读取记录、乘升降机完成：station-fight-passed.json。生命 100，Boss 0，victory / record_read / slice_completed 为 true；没有击杀作弊。
- 门前预览入口完整流程也通过：gate-to-ending-passed.json，约 152 秒，开门到战斗、记录及升降机完成。
- 编译成功；Scripts/verify_polish_rules.py 的 21 项玩家规则检查通过。
- Suno 导入成功：music-import.json，149.7735 秒。运行快照确认 suno_music=true。
- 当前游戏中已加载的角色攻击与闪避动画依旧是此前版本，Meshy 新动作未接入。

启动报错已处理：移除未使用的 GameFeatureData 资源扫描项（对应插件未加载、项目无此类资产），修复前该 ensure 会触发 CrashReportClientEditor；macOS 报告确认该报告程序发生 EXC_BAD_ACCESS。正常门前启动日志 Saved/GrandEncounter/startup-fixed.log 未再出现该 ensure 或 fatal。

死亡重试回归未完成：本轮该测试窗口在生成新的死亡/重置结果前被关闭，旧文件仍为 9 月 7 日，不能算本轮通过。
未做真人试玩、音频主观试听、30 分钟稳定性或跨设备性能验收。仅凭当前自动通关不能声明最终难度、公平性或镜头已全面验收。
