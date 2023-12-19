import logging
import math
import random
import statistics
# import sys
from collections.abc import Callable
from typing import NamedTuple, Self, Sequence

# from loguru import logger
import yaml

# default_format: str = (
#     "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
#     "[<level>{level}</level>] "
#     # "<cyan><underline>{name}</underline></cyan>:"
#     # "<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
#     "<level><normal>{message}</normal></level>"
#     # "<level>{message}</level>"
# )

# logger.remove()
# logger_id: int = logger.add(
#     sys.stderr,
#     level="INFO",
#     format=default_format,
# )

logger = logging.getLogger(__name__)


def linear_interpolation(x0, x1, /, t):
    return x0 + (x1 - x0) * t


class 订单详情(NamedTuple):
    概率: float
    需要秒基础工时: float
    消耗赤金: int
    获得龙门币: int


class 贸易站数据:
    def __init__(self,
                 订单列表: list[订单详情],
                 订单概率函数: Callable[[float], Sequence[float]] | None = None) -> None:
        self.订单列表: list[订单详情] = 订单列表
        self.订单概率函数: Callable[[float], Sequence[float]] | None = 订单概率函数

    @property
    def 每秒基础工时获得龙门币(self) -> float:
        return (sum(订单.概率 * 订单.获得龙门币 for 订单 in self.订单列表)
                / sum(订单.概率 * 订单.需要秒基础工时 for 订单 in self.订单列表))

    @property
    def 每秒基础工时消耗赤金(self) -> float:
        return sum(订单.概率 * 订单.消耗赤金 for 订单 in self.订单列表) / sum(订单.概率 * 订单.需要秒基础工时 for 订单 in self.订单列表)

    @property
    def 平均每赤金获得龙门币(self) -> float:
        return self.每秒基础工时获得龙门币 / self.每秒基础工时消耗赤金

    @property
    def 生产1龙门币需要的秒基础工时(self) -> float:
        return 1 / self.每秒基础工时获得龙门币 + 4320 / self.平均每赤金获得龙门币

    @property
    def 钱书基础工时成本比(self) -> float:
        return self.生产1龙门币需要的秒基础工时 / (54 / 5)

    @classmethod
    def new(cls, 贸易站等级: int, 但书: bool, 龙舌兰: bool, 裁缝: str | None) -> Self:
        需要秒基础工时列表: list[int] = [8640, 12600, 16560]
        订单概率函数: Callable[[float], Sequence[float]] | None = None
        if 贸易站等级 == 1:
            订单概率列表: list[float] = [100 / 100]
        elif 贸易站等级 == 2:
            订单概率列表 = [60 / 100, 40 / 100]
        elif 贸易站等级 == 3:
            if 裁缝 is None:
                订单概率列表 = [30 / 100, 50 / 100, 20 / 100]
            elif 裁缝 in ('α', 'alpha'):
                订单概率列表 = [15 / 100, 30 / 100, 55 / 100]
                订单概率函数 = 裁缝·α订单概率函数
            elif 裁缝 in ('β', 'beta'):
                订单概率列表 = [5 / 100, 10 / 100, 85 / 100]
                订单概率函数 = 裁缝·β订单概率函数
            else:
                raise ValueError
        else:
            raise ValueError
        获得龙门币列表: list[int] = [1000, 1500, 2000]
        消耗赤金列表: list[int] = [2, 3, 4]
        if 但书:
            获得龙门币列表[0] += 1000
            获得龙门币列表[1] += 1000
            消耗赤金列表[0] += 2
            消耗赤金列表[1] += 2
        if 龙舌兰:
            获得龙门币列表[2] += 500
        订单列表: list[订单详情] = []
        for 概率, 需要秒基础工时, 消耗赤金, 获得龙门币 in zip(订单概率列表, 需要秒基础工时列表, 消耗赤金列表, 获得龙门币列表):
            订单列表.append(订单详情(概率, 需要秒基础工时, 消耗赤金, 获得龙门币))
        return cls(订单列表, 订单概率函数=订单概率函数)

    def 生成订单(self, 暖机时间: float) -> 订单详情:
        if self.订单概率函数 is None:
            各订单概率: Sequence[float] = tuple(订单.概率 for 订单 in self.订单列表)
        else:
            各订单概率 = self.订单概率函数(暖机时间)
        return random.choices(self.订单列表, 各订单概率)[0]


_3级龙门币贸易站订单初始概率: tuple[float, float, float] = (30 / 100, 50 / 100, 20 / 100)
进驻裁缝·α时3级龙门币贸易站订单最终概率: tuple[float, float, float] = (15 / 100, 30 / 100, 55 / 100)
裁缝·α暖机时间 = 3 * 3600
进驻裁缝·β时3级龙门币贸易站订单最终概率: tuple[float, float, float] = (5 / 100, 10 / 100, 85 / 100)
裁缝·β暖机时间 = 5 * 3600


def 裁缝·α订单概率函数(暖机时间: float) -> tuple[float, float, float]:
    '''假设概率线性变化'''
    return tuple(linear_interpolation(初始概率, 最终概率, 暖机时间 / 裁缝·α暖机时间)
                 for 初始概率, 最终概率
                 in zip(_3级龙门币贸易站订单初始概率, 进驻裁缝·α时3级龙门币贸易站订单最终概率))  # type: ignore


def 裁缝·β订单概率函数(暖机时间: float) -> tuple[float, float, float]:
    '''假设概率线性变化'''
    return tuple(linear_interpolation(初始概率, 最终概率, 暖机时间 / 裁缝·β暖机时间)
                 for 初始概率, 最终概率
                 in zip(_3级龙门币贸易站订单初始概率, 进驻裁缝·β时3级龙门币贸易站订单最终概率))  # type: ignore


def 模拟1次(
        贸易站等级: int,
        无法跑单时的贸易站: 贸易站数据,
        无法跑单的时间: float,
        初始订单: 订单详情 | None,
        初始订单进度: float | None,
        无法跑单时的效率: float,
        本来的效率: float,
) -> tuple[float, float]:
    if 初始订单 is None:
        初始订单 = 贸易站数据.new(贸易站等级=贸易站等级, 但书=True, 龙舌兰=True, 裁缝=None).生成订单(0)
    if 初始订单进度 is None:
        初始订单进度 = random.random()
    总共获得龙门币: float = 0
    总共消耗赤金: float = 0
    当前时间: float = 0
    当前订单: 订单详情 = 初始订单
    当前订单进度: float = 初始订单进度
    while 当前时间 < 无法跑单的时间:
        订单剩余实际时间: float = 当前订单.需要秒基础工时 * (1 - 当前订单进度) / 无法跑单时的效率
        if 当前时间 + 订单剩余实际时间 <= 无法跑单的时间:
            当前时间 += 订单剩余实际时间
        else:
            当前时间 = 无法跑单的时间 + (当前订单.需要秒基础工时 * (1 - 当前订单进度)
                              - (无法跑单的时间 - 当前时间) * 无法跑单时的效率) / 本来的效率
        总共获得龙门币 += 当前订单.获得龙门币 * (1 - 当前订单进度)
        总共消耗赤金 += 当前订单.消耗赤金 * (1 - 当前订单进度)
        logger.debug(f'当前时间: {当前时间:.2f}, 当前获得龙门币: {总共获得龙门币:.2f}, 当前消耗赤金: {总共消耗赤金:.2f}')
        if 当前时间 < 无法跑单的时间:
            当前订单 = 无法跑单时的贸易站.生成订单(当前时间)
            当前订单进度 = 0
            logger.debug(f'生成订单: {当前订单}')

    本来能获得龙门币: float = 贸易站数据.new(
        贸易站等级=贸易站等级, 但书=True, 龙舌兰=True, 裁缝=None).每秒基础工时获得龙门币 * 当前时间 * 本来的效率
    本来能消耗赤金: float = 贸易站数据.new(
        贸易站等级=贸易站等级, 但书=True, 龙舌兰=True, 裁缝=None).每秒基础工时消耗赤金 * 当前时间 * 本来的效率
    多获得龙门币: float = 总共获得龙门币 - 本来能获得龙门币  # 负的
    多消耗赤金: float = 总共消耗赤金 - 本来能消耗赤金  # 负的
    return 多获得龙门币, 多消耗赤金


def 模拟n次(
    贸易站等级: int,
    模拟次数: int,
    无法跑单时的贸易站: 贸易站数据,
    无法跑单的时间: float,
    初始订单: 订单详情 | None,
    初始订单进度: float | None,
    无法跑单时的效率: float,
    本来的效率: float,
) -> tuple[float, float, float, float]:
    多获得龙门币列表: list[float] = []
    多消耗赤金列表: list[float] = []
    for _ in range(模拟次数):
        多获得龙门币, 多消耗赤金 = 模拟1次(
            贸易站等级,
            无法跑单时的贸易站,
            无法跑单的时间,
            初始订单,
            初始订单进度,
            无法跑单时的效率,
            本来的效率,
        )
        多获得龙门币列表.append(多获得龙门币)
        多消耗赤金列表.append(多消耗赤金)
    多获得龙门币平均: float = statistics.mean(多获得龙门币列表)
    多消耗赤金平均: float = statistics.mean(多消耗赤金列表)
    多获得龙门币标准差: float = statistics.pstdev(多获得龙门币列表)
    多消耗赤金标准差: float = statistics.pstdev(多消耗赤金列表)
    return 多获得龙门币平均, 多消耗赤金平均, 多获得龙门币标准差, 多消耗赤金标准差


def parse_percentage(s: str | float | int) -> float:
    if isinstance(s, str) and s.endswith('%'):
        return float(s.rstrip('%')) / 100
    return float(s)


if __name__ == '__main__':
    with open('示例 153.yaml', 'r', encoding='utf-8') as fp:
        data = yaml.safe_load(fp)

    模拟次数: int = data['模拟次数']
    赤金价值除以龙门币价值: float = data['赤金的价值除以龙门币的价值']
    无法跑单的时间: float = data['无法跑单的时间']
    贸易站等级列表: list[int] = data['贸易站等级']
    跑单时的效率列表: list[str | float] = data['跑单时的效率']
    if '当前正在进行的订单' in data and data['当前正在进行的订单'] is not None:
        # 从文件读取
        初始订单列表: list[订单详情] | list[None] = []
        初始订单进度列表: list[float] | list[None] = []
        for 初始订单 in data['当前正在进行的订单']:
            初始订单类型 = 初始订单['订单类型']
            初始订单列表.append(订单详情(0, 初始订单类型['需要秒基础工时'], 初始订单类型['消耗赤金'], 初始订单类型['获得龙门币']))
            初始订单进度列表.append(1 - 初始订单['剩余时间'] / 初始订单类型['需要秒基础工时'])
    else:
        初始订单列表 = [None for _ in 贸易站等级列表]
        初始订单进度列表 = [None for _ in 贸易站等级列表]

    print(f'无法跑单的时间: {无法跑单的时间:.0f} 秒')

    对比 = data['对比']
    for plan_name, plan in 对比.items():
        多获得龙门币列表: list[float] = []
        多消耗赤金列表: list[float] = []
        多获得龙门币标准差列表: list[float] = []
        多消耗赤金标准差列表: list[float] = []
        for 贸易站等级, 贸易站情况, 初始订单, 初始订单进度, 跑单时的效率字符串 in zip(
                贸易站等级列表, plan, 初始订单列表, 初始订单进度列表, 跑单时的效率列表):
            多获得龙门币, 多消耗赤金, 多获得龙门币标准差, 多消耗赤金标准差 = 模拟n次(
                贸易站等级=贸易站等级,
                模拟次数=模拟次数,
                无法跑单时的贸易站=贸易站数据.new(
                    贸易站等级,
                    但书=贸易站情况.get('但书', False),
                    龙舌兰=贸易站情况.get('龙舌兰', False),
                    裁缝=贸易站情况.get('裁缝', None),
                ),
                无法跑单的时间=无法跑单的时间,
                初始订单=初始订单,
                初始订单进度=初始订单进度,
                无法跑单时的效率=parse_percentage(贸易站情况['效率']),
                本来的效率=parse_percentage(跑单时的效率字符串),
            )
            多获得龙门币列表.append(多获得龙门币)
            多消耗赤金列表.append(多消耗赤金)
            多获得龙门币标准差列表.append(多获得龙门币标准差)
            多消耗赤金标准差列表.append(多消耗赤金标准差)
        多获得龙门币平均: float = statistics.mean(多获得龙门币列表)
        多消耗赤金平均: float = statistics.mean(多消耗赤金列表)
        多获得龙门币标准差: float = math.hypot(*多获得龙门币标准差列表)  # 贸易站之间是独立的
        多消耗赤金标准差: float = math.hypot(*多消耗赤金标准差列表)

        print(f'== {plan_name} ==')
        print(f'多获得龙门币: {多获得龙门币平均:.4f}    标准差: {多获得龙门币标准差:.4f}')
        print(f'多消耗赤金: {多消耗赤金平均:.4f}    标准差: {多消耗赤金标准差:.4f}')
        print(f'综合评价: {多获得龙门币平均 - 多消耗赤金平均 * 赤金价值除以龙门币价值:.4f}')
