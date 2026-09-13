"""generate_data 可复现性测试（固定随机种子）。"""

import random

import numpy as np

from generate_data import RANDOM_SEED, generate_cases, generate_appeals, generate_regions


def test_generate_cases_reproducible():
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    df1 = generate_cases(50)

    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    df2 = generate_cases(50)

    assert df1.equals(df2)


def test_generate_cases_count():
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    df = generate_cases(50)
    assert len(df) == 50
    assert len(df["case_id"].unique()) == 50  # 编号唯一


def test_generate_appeals_count():
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    df = generate_appeals(30)
    assert len(df) == 30


def test_generate_regions_deterministic():
    # regions 不依赖随机数，两次调用应完全一致
    assert generate_regions().equals(generate_regions())
