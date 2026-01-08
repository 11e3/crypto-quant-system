"""
Windows Task Scheduler setup for real-time monitoring.

Creates an automatic monitoring task that runs daily.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "real_time_monitor.py"
PYTHON_PATH = sys.executable


def create_monitoring_task(
    task_name: str = "CryptoQuantMonitoring",
    schedule_time: str = "10:00",  # 매일 10:00에 실행
    tickers: list[str] = None,
    output_dir: str = None,
    slack_webhook: str = None,
):
    """
    Create Windows Task Scheduler task for monitoring.

    Args:
        task_name: Task name in Scheduler
        schedule_time: Time to run daily (HH:MM format)
        tickers: List of tickers to monitor
        output_dir: Output directory for reports
        slack_webhook: Slack webhook URL for alerts
    """
    if tickers is None:
        tickers = ["KRW-BTC", "KRW-ETH"]

    if output_dir is None:
        output_dir = str(PROJECT_ROOT / "reports")

    # Build command
    cmd_args = [
        str(PYTHON_PATH),
        "-m",
        "scripts.real_time_monitor",
        "--tickers",
        *tickers,
        "--output",
        output_dir,
    ]

    if slack_webhook:
        cmd_args.extend(["--slack", slack_webhook])

    # Build Task Scheduler command
    # PowerShell syntax for Register-ScheduledTask
    ps_script = f"""
    # Get the current user
    $user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

    # Create trigger (daily at specified time)
    $trigger = New-ScheduledTaskTrigger -Daily -At {schedule_time}

    # Create action
    $action = New-ScheduledTaskAction -Execute '{PYTHON_PATH}' `
        -Argument '-m scripts.real_time_monitor --tickers {" ".join(tickers)} --output "{output_dir}"' `
        -WorkingDirectory '{PROJECT_ROOT}'

    # Create task settings
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

    # Register task
    Register-ScheduledTask -TaskName "{task_name}" `
        -Trigger $trigger `
        -Action $action `
        -Settings $settings `
        -User $user `
        -Force -RunLevel Highest `
        -ErrorAction Stop

    Write-Host "Task created successfully: {task_name}"
    Write-Host "Scheduled to run daily at {schedule_time}"
    """

    if slack_webhook:
        ps_script = ps_script.replace(
            f'--output "{output_dir}"', f'--output "{output_dir}" --slack "{slack_webhook}"'
        )

    print("Windows Task Scheduler Setup")
    print("=" * 80)
    print(f"Task name: {task_name}")
    print(f"Schedule: Daily at {schedule_time}")
    print(f"Script: {SCRIPT_PATH}")
    print(f"Python: {PYTHON_PATH}")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Output: {output_dir}")
    print(f"Slack: {'Enabled' if slack_webhook else 'Disabled'}")
    print("\n" + "=" * 80)
    print("PowerShell command to run (as Administrator):\n")
    print(ps_script)

    # Save script to file for easy execution
    script_file = PROJECT_ROOT / "scripts" / "setup_task_scheduler.ps1"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(ps_script)

    print(f"\nScript saved to: {script_file}")
    print("\nTo run, execute in PowerShell (as Administrator):")
    print(f"powershell -ExecutionPolicy Bypass -File '{script_file}'")
    return ps_script


def remove_monitoring_task(task_name: str = "CryptoQuantMonitoring") -> str:
    """Remove scheduled task."""
    ps_script = f"""
    # Remove task
    Unregister-ScheduledTask -TaskName "{task_name}" -Confirm:$false -ErrorAction Stop
    Write-Host "Task removed: {task_name}"
    """

    script_file = PROJECT_ROOT / "scripts" / "remove_task_scheduler.ps1"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(ps_script)

    print(f"Removal script saved to: {script_file}")
    print("\nTo remove task, run in PowerShell (as Administrator):")
    print(f"powershell -ExecutionPolicy Bypass -File '{script_file}'")
    return ps_script


def get_task_status(task_name: str = "CryptoQuantMonitoring") -> str:
    """Get current task status."""
    ps_script = f"""
    $task = Get-ScheduledTask -TaskName "{task_name}" -ErrorAction SilentlyContinue
    if ($task) {{
        Write-Host "Task found: {task_name}"
        Write-Host "State: $($task.State)"
        Write-Host "Last run time: $($task.LastRunTime)"
        Write-Host "Last result: $($task.LastTaskResult)"
    }} else {{
        Write-Host "Task not found: {task_name}"
    }}
    """

    script_file = PROJECT_ROOT / "scripts" / "check_task_scheduler.ps1"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(ps_script)

    print(f"Status check script saved to: {script_file}")
    print("\nTo check task status, run in PowerShell:")
    print(f"powershell -ExecutionPolicy Bypass -File '{script_file}'")
    return ps_script


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Windows Task Scheduler setup for monitoring")
    parser.add_argument(
        "--action",
        choices=["create", "remove", "status"],
        default="create",
        help="Action to perform",
    )
    parser.add_argument("--task-name", default="CryptoQuantMonitoring", help="Task name")
    parser.add_argument("--schedule-time", default="10:00", help="Daily schedule time (HH:MM)")
    parser.add_argument(
        "--tickers", nargs="+", default=["KRW-BTC", "KRW-ETH"], help="Tickers to monitor"
    )
    parser.add_argument("--output-dir", help="Output directory for reports")
    parser.add_argument("--slack-webhook", help="Slack webhook URL")

    args = parser.parse_args()

    if args.action == "create":
        create_monitoring_task(
            task_name=args.task_name,
            schedule_time=args.schedule_time,
            tickers=args.tickers,
            output_dir=args.output_dir,
            slack_webhook=args.slack_webhook,
        )
    elif args.action == "remove":
        remove_monitoring_task(task_name=args.task_name)
    elif args.action == "status":
        get_task_status(task_name=args.task_name)
