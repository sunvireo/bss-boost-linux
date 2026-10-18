"""Linux alarm state independent of overlay visibility and Python/Windows speech."""
from bss_booster import linux_notifier


def test_linux_notifier_tracks_and_clears_alarm_without_sound_tools(tmp_path, monkeypatch):
    monkeypatch.setattr(linux_notifier.shutil, 'which', lambda cmd: None)
    notifier = linux_notifier.AlarmNotifier(tmp_path / 'absent.wav')
    try:
        alarm = {'id': 'test-1', 'name': 'Glitter', 'alert_mode': 'Sound', 'enabled': True}
        notifier.trigger(alarm)
        assert notifier.is_alerting('test-1')
        notifier.acknowledge('test-1')
        assert not notifier.is_alerting('test-1')
        notifier.trigger(alarm)
        notifier.sync([])
        assert not notifier.is_alerting('test-1')
    finally:
        notifier.close()
