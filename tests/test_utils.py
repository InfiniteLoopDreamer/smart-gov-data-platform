"""dashboard/src/utils 工具函数测试。"""

from src import utils


def test_clean_html_dedents_and_strips():
    raw = "\n        <div>\n            <span>hi</span>\n        </div>\n    "
    cleaned = utils.clean_html(raw)
    assert cleaned.startswith("<div>")
    assert cleaned.endswith("</div>")
    assert "\n        " not in cleaned
