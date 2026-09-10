# 骑乘 Boss 首轮实验入口

2026-09-11。当前审计、验收及未完成范围统一维护在 [CURRENT_STATE.md](MountedBoss/CURRENT_STATE.md)，本页只保留入口，避免旧五招参数与现有六招实现并存。

- [当前状态与逐项审计](MountedBoss/CURRENT_STATE.md)
- [战斗规则与调参方式](MountedBoss/combat_spec.md)
- [完整目标的招式和支持动作目录](MountedBoss/move_catalog.json)
- [资产来源、许可、骨架与实测清单](MountedBoss/asset_manifest.json)
- [验收矩阵与证据](MountedBoss/qa_matrix.json)
- [参考视频观察与设计假设](../Design/mounted-boss-reference-v01.md)

本地运行 `Scripts/launch_mounted_boss.command`。E 进入，WASD 移动，Tab 锁定，Shift 短按松开翻滚、长按冲刺，Ctrl 慢走，空格跳跃，左/右键轻击/重击，R 重试。

F1 调试面板，F2 暂停，F3 切换 0.25/1 倍速度，F4 快速复位，F5 恢复自然 AI，数字 1–6 分别触发横扫、下劈、冲锋横扫、马肩撞、前蹄震地、跃起盾砸。F8 开始/停止连续游戏画面和主混音录制，保存于 `Saved/MountedBoss/Recordings/`；`Scripts/assemble_mounted_recording.py` 按真实时间戳封装，不剪接、不改变游戏速度。

原守井者继续使用 `Scripts/launch_station_gate.command`。不要用早期网页原型替代 UE 工程，也不要把 `before-mounted-20260910-233144.zip` 当完整项目备份或覆盖后续主角更新。

本轮没有新增付费生成。占位马、场地与程序骑姿仍需视觉改进；六招和三个生产验收样本都不代表完整大树守卫参考目标已完成，魔法反制等缺项保留在目录中。
