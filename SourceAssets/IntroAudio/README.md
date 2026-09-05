# 第一眼深井：入场音效

本目录的 14 个 WAV 均由 `generate_intro_audio.py` 原创合成，没有使用第三方录音、付费素材或语音服务。种子固定，可重复生成。正式运行音效 13 个，另有一个 30 秒声音编排预览。

统一格式：48 kHz、16 bit PCM WAV。两个环境底层为立体声，其余事件为单声道，便于 UE 定位。文件名、用途、时长、峰值、RMS、哈希与建议初始音量见 `manifest.json`。

| 文件 | 用法 |
| --- | --- |
| `AW_Amb_MachineryLoop.wav` | 24 秒无缝低频机械底层，初始音量 0.85；保持持续。 |
| `AW_Amb_WellAirLoop.wav` | 24 秒无缝井内气流，初始音量 0.65；低于机器声。 |
| `AW_Foley_WetStoneStep_01..06.wav` | 湿石板靴声；跟随实际位移触发，玩家初始音量 0.80；同伴明显更轻。 |
| `AW_Foley_LanternGear_01..03.wav` | 灯笼提手和装备轻微摩擦；每 3–5 步偶发一次，或停步时一次。 |
| `AW_Foley_HushedBreath.wav` | 可选的无声带短呼气；不是可辨认的台词，也不应标成录制的人声。 |
| `AW_Event_DistantLoadShift.wav` | 一次远处巨大结构受力的低响，约 5.5 秒；定位前方及下方。 |
| `AW_Intro30s_AudioPreview.wav` | 30 秒编排参考；已有轻微早期反射，不能和游戏中单独音效叠播。 |

建议节奏：0–1.5 秒建立空间；1.5–14 秒行走；约 13.9 秒出现远处受力声；14.45 秒同伴停步、装备落定；约 15 秒一口低声呼气；余下时间让脚步的消失露出井里的机器声。实际脚步跟随移动，而不是锁死到这些秒数。

UE 导入位置建议 `/Game/AshWell/Audio/Intro`。环境 WAV 启用循环并作为不定位的立体声底层；单声道脚步、装备、呼气和事件使用空间衰减。干声故意没有很长的混响，避免再加 UE 混响后模糊。可以先用一处暗色洞穴混响，脚步保留明确近声，远方事件提高混响占比；低通其反射、减少亮尾音。

程序检查见 `verification.json`：实际 WAV 文件头、校验值、零削波、循环边界连续性全部检查。30 秒预览经 ffmpeg EBU R128 测得 −22.5 LUFS、真峰值 −6.0 dBFS。原始事件峰值保留 10–23 dB 余量；环境底层 RMS 为 −29.0 / −37.3 dBFS。上述是信号测量，不代表已做人工听感验收。

重建：

```sh
/Users/rare/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 generate_intro_audio.py
/Users/rare/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 verify_audio.py
```

生成器只依赖 Python 和 NumPy；检查器另使用本机 `/opt/homebrew/bin/ffmpeg` 测量响度。
