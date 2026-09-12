"""Read recording availability without changing macOS security or lock state."""
import subprocess

def screen_locked():
    state=subprocess.check_output(['/usr/sbin/ioreg','-n','Root','-d1'],text=True)
    return '"CGSSessionScreenIsLocked"=Yes' in state

def require_unlocked():
    if screen_locked():
        raise SystemExit('Mac 已锁屏，无法录制游戏窗口。请手动解锁后重新启动；未尝试绕过锁屏。')
