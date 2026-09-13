# pytest 配置：将项目根目录与 dashboard 目录加入 sys.path，
# 便于 `from shared import ...` 与 `from src import ...` 导入。
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "dashboard"))
