import pandas as pd
import os
import json
from tqdm import tqdm
from glob import glob


def calculate_macd(df, fast=12, slow=26, signal=9):
    ema_fast = df['收盘'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['收盘'].ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    return dif, dea


def detect_macd_golden_cross(df):
    dif, dea = calculate_macd(df)
    golden_cross = (dif > dea) & (dif.shift(1) <= dea.shift(1))
    return golden_cross


def detect_morning_star(df):
    # 第一天阴线
    day1 = (df['收盘'].shift(2) < df['开盘'].shift(2))
    # 第二天十字星
    day2_body = abs(df['收盘'].shift(1) - df['开盘'].shift(1))
    day2_range = df['最高'].shift(1) - df['最低'].shift(1)
    day2_doji = (day2_body / (day2_range + 1e-5)) < 0.1  # 防止除零
    # 第三天阳线且收盘超第一天中点
    day3 = (df['收盘'] > df['开盘']) & (df['收盘'] > (df['开盘'].shift(2) + df['收盘'].shift(2)) / 2)
    return day1 & day2_doji & day3


def detect_sanyang_kaitai(df):
    # 三阳开泰：连续三根阳线且收盘价递增
    cond1 = (df['收盘'] > df['开盘'])
    cond2 = (df['收盘'].shift(1) > df['开盘'].shift(1)) & (df['收盘'] > df['收盘'].shift(1))
    cond3 = (df['收盘'].shift(2) > df['开盘'].shift(2)) & (df['收盘'].shift(1) > df['收盘'].shift(2))
    return cond1 & cond2 & cond3


def detect_chushui_furong(df):
    # 出水芙蓉：突破30日均线且涨幅>5%
    ma30 = df['收盘'].rolling(30).mean()
    cond1 = (df['收盘'] > ma30) & (df['收盘'].shift(1) <= ma30.shift(1))
    cond2 = (df['收盘'] / df['开盘'] - 1) >= 0.05
    cond3 = df['成交量'] > df['成交量'].rolling(30).mean().shift(1)
    return cond1 & cond2 & cond3


def detect_xuri_dongsheng(df):
    # 旭日东升
    day1_close = df['收盘'].shift(1)
    day1_open = df['开盘'].shift(1)
    day1_cond = (day1_close < day1_open) & ((day1_open - day1_close) / day1_open > 0.03)
    day2_open_cond = df['开盘'] < day1_close
    day2_close_cond = df['收盘'] > day1_open
    return day1_cond & day2_open_cond & day2_close_cond


def detect_duofangpao(df):
    # 多方炮：两阳夹一阴
    day1 = (df['收盘'].shift(2) > df['开盘'].shift(2))
    day2_body = (df['收盘'].shift(1) < df['开盘'].shift(1))
    day2_size = (df['开盘'].shift(1) - df['收盘'].shift(1)) / df['开盘'].shift(1) < 0.03
    day3 = (df['收盘'] > df['开盘']) & (df['收盘'] > df['收盘'].shift(2))
    return day1 & day2_body & day2_size & day3


def generate_report(stock_code, stock_name, results, output_dir):
    content = f"# {stock_code}-{stock_name} 技术指标分析报告\n\n"
    content += "## 技术指标统计\n\n"
    table = "| 指标名称   | 出现次数 | 胜率   | 平均5日收益 |\n"
    table += "|------------|----------|--------|-------------|\n"
    for res in results:
        name = res['name']
        count = res['count']
        win_rate = f"{res['win_rate'] * 100:.2f}%" if count > 0 else "N/A"
        avg_return = f"{res['avg_return'] * 100:.2f}%" if count > 0 else "N/A"
        table += f"| {name} | {count} | {win_rate} | {avg_return} |\n"
    content += table
    filename = f"{stock_code}-{stock_name}.md"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


def calculate_indicator_stats(df, indicator_func):
    """返回三元组 (出现次数, 胜率, 平均收益)"""
    try:
        signals = df.loc[indicator_func(df)].index
    except KeyError as e:
        print(f"数据列缺失错误: {str(e)}")
        return 0, 0.0, 0.0

    profits = []
    for idx in signals:
        if idx + 5 >= len(df):
            continue
        try:
            buy_price = df.iloc[idx + 1]['开盘']
            sell_price = df.iloc[idx + 5]['收盘']
            profit = (sell_price - buy_price) / buy_price
            profits.append(profit)
        except IndexError:
            continue

    if not profits:
        return 0, 0.0, 0.0

    wins = sum(1 for p in profits if p > 0)
    win_rate = wins / len(profits)
    avg_return = sum(profits) / len(profits)
    return len(profits), win_rate, avg_return  # 确保返回三元组


def generate_summary_report(all_results, output_dir):
    """修正后的汇总统计逻辑"""
    summary = {}

    # 初始化指标
    indicator_names = [name for name, _ in [
        ('三阳开泰', None),
        ('出水芙蓉', None),
        ('旭日东升', None),
        ('多方炮', None),
        ('早晨之星', None),
        ('MACD金叉', None)
    ]]

    for name in indicator_names:
        summary[name] = {
            'total_signals': 0,
            'total_wins': 0,
            'total_return': 0.0
        }

    # 聚合数据
    for stock_data in all_results:
        for indicator in stock_data['results']:
            name = indicator['name']
            count = indicator['count']
            win_rate = indicator['win_rate']
            avg_return = indicator['avg_return']

            summary[name]['total_signals'] += count
            summary[name]['total_wins'] += int(count * win_rate)
            summary[name]['total_return'] += avg_return * count

    # 生成报告内容
    content = "# 全市场技术指标汇总分析\n\n"
    content += "| 指标名称 | 总出现次数 | 胜率 | 平均5日收益 |\n"
    content += "|----------|------------|------|-------------|\n"

    for name, data in summary.items():
        total = data['total_signals']
        if total == 0:
            row = f"| {name} | 0 | N/A | N/A |"
        else:
            win_rate = data['win_count'] / total
            avg_return = data['total_return'] / total
            row = f"| {name} | {total} | {win_rate * 100:.2f}% | {avg_return * 100:.2f}% |"
        content += row + "\n"

    # 保存文件
    filepath = os.path.join(output_dir, "全市场汇总分析.md")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    stock_codes = config['stock_codes']
    data_dir = config['data_dir']
    output_dir = config['output_dir']
    os.makedirs(output_dir, exist_ok=True)

    indicators = [
        ('三阳开泰', detect_sanyang_kaitai),
        ('出水芙蓉', detect_chushui_furong),
        ('旭日东升', detect_xuri_dongsheng),
        ('多方炮', detect_duofangpao),
        ('早晨之星', detect_morning_star),
        ('MACD金叉', detect_macd_golden_cross),
    ]

    # 添加总进度条
    with tqdm(total=len(stock_codes),
              desc="🔄 股票分析进度",
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:

        for idx, code in enumerate(stock_codes, 1):
            pattern = os.path.join(data_dir, f"{code}-*.csv")
            files = glob(pattern)

            # 更新进度条描述
            pbar.set_postfix_str(f"当前股票: {code}")

            if not files:
                tqdm.write(f"\n⚠️ 未找到股票 {code} 的数据文件")
                pbar.update(1)
                continue

            filepath = files[0]
            try:
                df = pd.read_csv(filepath)
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.sort_values('日期').reset_index(drop=True)

                # if df.empty:
                #     tqdm.write(f"\n⚠️ 股票 {code} 数据为空")
                #     pbar.update(1)
                #     continue
                #
                # stock_name = df.iloc[0]['stock_name']
                #
                # # 分析指标（移除内层进度条）
                # results = []
                # for name, func in indicators:
                #     count, win_rate, avg_ret = calculate_indicator_stats(df, func)
                #     results.append({
                #         'name': name,
                #         'count': count,
                #         'win_rate': win_rate,
                #         'avg_return': avg_ret
                #     })
                #
                # generate_report(code, stock_name, results, output_dir)
                #
                # # 更新进度信息
                # pbar.set_postfix_str(f"已完成: {code}-{stock_name[:4]}...")

            except Exception as e:
                tqdm.write(f"\n❌ 处理 {code} 时发生错误：{str(e)}")
            finally:
                pbar.update(1)

    print(f"\n✅ 分析完成！报告已保存至：{os.path.abspath(output_dir)}")

    all_results = []  # 新增：存储所有股票结果

    with tqdm(total=len(stock_codes), desc="分析进度") as pbar:
        for code in stock_codes:
            # ... [保持原有文件加载代码不变]

            stock_name = df.iloc[0]['stock_name']
            stock_result = {
                'code': code,
                'name': stock_name,
                'results': []
            }

            for name, func in indicators:
                profits = calculate_indicator_stats(df, func)  # 修改为获取明细
                stock_result['results'].append({
                    'name': name,
                    'profits': profits
                })

            generate_report(code, stock_name, [
                {
                    'name': res['name'],
                    'count': len(res['profits']),
                    'win_rate': sum(1 for p in res['profits'] if p > 0) / len(res['profits']) if res['profits'] else 0,
                    'avg_return': sum(res['profits']) / len(res['profits']) if res['profits'] else 0
                }
                for res in stock_result['results']
            ], output_dir)

            all_results.append(stock_result)
            pbar.update(1)

    # 生成汇总报告
    generate_summary_report(all_results, output_dir)
    print(f"\n全市场汇总报告已生成：{os.path.join(output_dir, '全市场汇总分析.md')}")


if __name__ == '__main__':
    main()
