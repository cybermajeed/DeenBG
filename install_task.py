"""
DeenBG — Task Scheduler Installer
===================================
Registers DeenBG with Windows Task Scheduler.

Usage:
    python install_task.py                   # run at every logon only
    python install_task.py --interval 60     # logon + repeat every 60 minutes
    python install_task.py --remove          # remove the task
"""

import sys
import argparse
import subprocess
from pathlib import Path

TASK_NAME = "DeenBG"
BASE_DIR = Path(__file__).parent.resolve()
SCRIPT = BASE_DIR / "wallpaper_generator.py"


def find_pythonw() -> str:
    import os

    py = Path(sys.executable)
    for candidate in [py.parent / "pythonw.exe", py.parent / "Scripts" / "pythonw.exe"]:
        if candidate.exists():
            return str(candidate)
    return sys.executable  # fallback


def build_xml(python_exe: str, script_path: str, interval_minutes: int | None) -> str:
    """
    Build Task Scheduler XML with a SINGLE LogonTrigger.
    If interval is set, a Repetition block is added INSIDE the same trigger
    — this avoids the "multiple triggers not allowed" restriction on some
    Windows editions and keeps the task clean.
    """

    if interval_minutes:
        iso = _to_iso(interval_minutes)
        repetition = f"""
        <Repetition>
          <Interval>{iso}</Interval>
          <StopAtDurationEnd>false</StopAtDurationEnd>
        </Repetition>"""
    else:
        repetition = ""

    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>DeenBG: sets a random Quran ayah as the desktop wallpaper.</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>{repetition}
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT5M</ExecutionTimeLimit>
    <Priority>7</Priority>
    <StartWhenAvailable>true</StartWhenAvailable>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{python_exe}</Command>
      <Arguments>"{script_path}"</Arguments>
      <WorkingDirectory>{BASE_DIR}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""


def _to_iso(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    if h and m:
        return f"PT{h}H{m}M"
    if h:
        return f"PT{h}H"
    return f"PT{m}M"


def install(interval_minutes: int | None):
    if sys.platform != "win32":
        print("Task Scheduler is only available on Windows.")
        sys.exit(1)

    python_exe = find_pythonw()
    xml_path = BASE_DIR / "_deenbg_task.xml"

    print(f"\n  Executable : {python_exe}")
    print(f"  Script     : {SCRIPT}")
    if interval_minutes:
        print(f"  Trigger    : logon + every {interval_minutes} min")
    else:
        print(f"  Trigger    : logon only")

    xml_content = build_xml(python_exe, str(SCRIPT), interval_minutes)

    with open(xml_path, "w", encoding="utf-16") as f:
        f.write(xml_content)

    try:
        # Remove existing task silently first
        subprocess.run(
            ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"], capture_output=True
        )
        result = subprocess.run(
            ["schtasks", "/Create", "/XML", str(xml_path), "/TN", TASK_NAME],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"\n  ✓ Task '{TASK_NAME}' registered in Task Scheduler.")
        else:
            print(f"\n      ✗ Registration failed:\n      {result.stderr}", end=" ")
            input("     TRY RUNNING AS ADMINISTRATOR IF THIS PERSISTS ")
    finally:
        try:
            xml_path.unlink()
        except Exception:
            pass


def remove():
    if sys.platform != "win32":
        print("Task Scheduler is only available on Windows.")
        sys.exit(1)
    result = subprocess.run(
        ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"], capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"  ✓ Task '{TASK_NAME}' removed.")
    else:
        print(f"  ✗ Could not remove task:\n{result.stderr}")


def main():
    parser = argparse.ArgumentParser(description="Install DeenBG scheduled task.")
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        metavar="MINUTES",
        help="Also repeat every N minutes after logon.",
    )
    parser.add_argument("--remove", action="store_true", help="Remove the task.")
    args = parser.parse_args()

    print("\n" + "═" * 50)
    print("  DeenBG — Task Scheduler Installer")
    print("═" * 50)

    if args.remove:
        remove()
    else:
        install(args.interval)

    print("═" * 50 + "\n")


if __name__ == "__main__":
    main()
