# logger_config.py
import logging
from pathlib import Path
import sys

Path("logs_scenarios").mkdir(exist_ok=True)

inter_logs = logging.getLogger("scenarios_workflow")
inter_logs.setLevel(logging.DEBUG)
inter_logs.propagate = True

# File handler
fh = logging.FileHandler("logs_scenarios/workflow.log", mode="w")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
inter_logs.addHandler(fh)

# Console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
ch.flush = sys.stdout.flush
inter_logs.addHandler(ch)
