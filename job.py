import time
import sys
import subprocess
from datetime import datetime, timedelta
def daily_job(debug=False):
    run_hour = 17  # 5 PM
    log_file = "main_run.log"
    script_to_run = "core.daily_calc"

    if not debug:
        now = datetime.now()
        target_time = now.replace(hour=run_hour, minute=0, second=0, microsecond=0)

        if now >= target_time:
            target_time += timedelta(days=1)

        wait_seconds = (target_time - now).total_seconds()
        print(f"Waiting {int(wait_seconds)} seconds until 5 PM...")
        time.sleep(wait_seconds)
    else:
        print("DEBUG MODE: Skipping wait and running daily_calc.py immediately")

    start = datetime.now()

    with open(log_file, "a", encoding="utf-8") as log:
        log.write(f"\n[{start.strftime('%Y-%m-%d %H:%M:%S')}] Running daily_calc.py\n")

        result = subprocess.run([sys.executable, "-m", script_to_run], stdout=log, stderr=log)

        end = datetime.now()
        duration_seconds = round((end - start).total_seconds(), 2)

        log.write(f"[{end.strftime('%Y-%m-%d %H:%M:%S')}] Finished with exit code {result.returncode}\n")
        log.write(f"⏱️Time taken: {duration_seconds} seconds\n")


if __name__ == "__main__":
    # Set debug=True to skip waiting for 5 PM
    daily_job(debug=False)

