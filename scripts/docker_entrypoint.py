"""Docker 容器入口：无数据时生成演示库，然后启动 uvicorn。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    has_db = (DATA / "gov_data.db").exists()
    has_csv = (DATA / "cases.csv").exists()
    if not has_db and not has_csv:
        print("[entrypoint] 未检测到数据，正在运行 generate_data.py ...")
        subprocess.check_call([sys.executable, str(ROOT / "generate_data.py")], cwd=str(ROOT))
    else:
        print("[entrypoint] 已检测到本地数据，跳过生成")

    print("[entrypoint] 启动 FastAPI ...")
    os_exec = ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
    raise SystemExit(subprocess.call(os_exec, cwd=str(ROOT)))


if __name__ == "__main__":
    main()
