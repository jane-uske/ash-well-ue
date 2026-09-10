# 检修站声音

- `AW_Polish_Ambient/Combat/Overload.wav`：本项目原创、固定种子的程序合成，16 秒循环。脚本 `Scripts/generate_polish_audio.py`。
- `AW_Polish_Voice.wav`：本地 Kokoro-82M，官方预设中文男声 `zm_yunxi`，文本“别……再送电了。”；未克隆真人声音、未调用收费接口。24 kHz，5.425 秒，轻微机械调制和短延迟。模型不随游戏分发。
- Kokoro 模型及许可：https://huggingface.co/hexgrad/Kokoro-82M （Apache-2.0）。运行库：https://github.com/hexgrad/kokoro 。声线表：https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md 。
- 字幕出现在停机后 2–7 秒；人声在停机后 2 秒播放。当前为合成配音，需要真人试听后决定是否重录。
- `manifest.json` 保存输出时长、来源和 SHA-256。旧的脚步、装备摩擦和战斗音效也来自项目原创合成，分别见 IntroAudio 和 CombatAudio。

作者免费近战包 Kevin Iglesias Human Melee Animations FREE 2.0.2 已检查，**没有导入或分发**：双手大剑动作不直接适合守井者单侧重锤。来源 https://kevdev.itch.io/human-melee-animatons-free ，许可说明 https://www.keviniglesias.com/#license （Standard Asset Store EULA，不是 CC0）。本地审核 ZIP 位于 Saved/Polish，SHA-256 `bcd47d323e40419d4dda188d51bd5d91021e6ca42d8dc0c30f1e5053401244f5`。

已有 Quaternius Standard CC0 动作库继续保留在独立试验区；本轮战斗玩家动作仍为已存在的原创检修工动作，Boss 由姿态状态机与骨架驱动。没有将“大剑减速”冒充重锤成品动作。
