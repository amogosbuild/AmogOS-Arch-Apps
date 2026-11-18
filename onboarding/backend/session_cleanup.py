# End only the validated temporary account's processes before removing its home directory.
import subprocess
import time


def stop_temporary_session(uid, run=subprocess.run, sleep=time.sleep):
    if type(uid) is not int or uid <= 0:
        raise ValueError("Refusing to stop an invalid temporary account.")
    identity = str(uid)
    run(["loginctl", "terminate-user", identity], check=False)

    def active():
        return run(["pgrep", "-u", identity], stdout=subprocess.DEVNULL,
                   check=False).returncode == 0

    for attempt in range(15):
        if not active():
            return
        sleep(1)
    run(["pkill", "-KILL", "-u", identity], check=False)
    for attempt in range(10):
        if not active():
            return
        sleep(.5)
    raise RuntimeError("The temporary setup session is still busy. Restart to finish cleanup.")
