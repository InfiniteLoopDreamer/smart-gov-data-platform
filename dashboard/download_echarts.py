"""
下载 ECharts 到本地，实现图表离线渲染。

运行（需联网一次）：
    python download_echarts.py

下载后 charts.py 会自动优先内联本地 assets/echarts.min.js，
断网环境下图表也能正常渲染；若本地文件缺失则回退 CDN。
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

URL = "https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"
TARGET = Path(__file__).resolve().parent / "assets" / "echarts.min.js"


def main() -> None:
    """下载 echarts.min.js 到 assets/ 目录。"""
    print(f"下载中：{URL}")
    urllib.request.urlretrieve(URL, TARGET)
    size = TARGET.stat().st_size
    print(f"已保存至：{TARGET.resolve()}（{size:,} 字节）")
    print("现在可以断网运行 `streamlit run app.py`，图表仍正常显示。")


if __name__ == "__main__":
    main()
