# Quantrador

Quantrador 是一个开源量化分析脚本。

目前支持对 A 股历史数据进行技术指标分析。

## 下载历史数据

下载脚本 `src/download.py` 从 `akshare` 库下载得到 A 股日 K 线数据。考虑到股价数据量大，将数据另外存储在项目目录以外的 `../stock_data` 目录下。

### 配置文件

`download_config.json` 是下载脚本的配置文件：

```json
{
  "stock_codes": [
    "000768",
    "002023",
    "002132",
    "002305",
    "002455",
    "600036",
    "600406",
    "600882"
  ],
  "start_date": "20150101",
  "end_date": "20250327",
  "save_path": "../stock_data",
  "adjust_type": "qfq",
  "period": "daily"
}
```

### 示例数据

`../stock_data/002023-海特高新.csv` 内容如下：

```csv
stock_code,stock_name,日期,开盘,收盘,最高,最低,成交量,成交额,振幅,涨跌幅,涨跌额,换手率
002023,海特高新,2015-01-05,10.72,10.77,10.89,10.53,62683,136649238.0,3.34,0.0,0.0,2.3
002023,海特高新,2015-01-06,10.77,11.39,11.5,10.67,125213,286451760.0,7.71,5.76,0.62,4.59
002023,海特高新,2015-01-07,11.43,11.17,11.43,11.07,67126,153281362.0,3.16,-1.93,-0.22,2.46
002023,海特高新,2015-01-08,11.18,11.22,11.35,11.08,64628,148323888.0,2.42,0.45,0.05,2.37
```

## 技术指标分析

分析脚本 `./src/analysis.py` 用于分析股票技术指标。

### 配置文件

分析脚本从 `./config.json` 读取配置：

```json
{
  "stock_codes": [
    "000768",
    "002023",
    "002132",
    "002305",
    "002455",
    "600036",
    "600406",
    "600882"
  ],
  "data_dir": "../stock_data",
  "output_dir": "./report"
}
```

### 技术指标分析报告

`002023-海特高新.md` 内容如下：

```
# 002023-海特高新 技术指标分析报告

- 起始日期：2004-07-21
- 终止日期：2025-03-28

## 技术指标统计

| 指标名称   | 出现次数 | 胜率   | 平均5日收益 |
|------------|----------|--------|-------------|
| 三阳开泰 | 485 | 49.69% | 0.52% |
| 出水芙蓉 | 47 | 65.96% | 2.97% |
| 旭日东升 | 17 | 58.82% | 0.78% |
| 多方炮 | 238 | 42.86% | -0.06% |
| 早晨之星 | 70 | 51.43% | 0.36% |
| MACD金叉 | 200 | 52.50% | 0.50% |
```

## 股价预测

股价预测的输入数据是 `../stock_data` 目录下的单个 `.csv` 文件，例如 `../stock_data/002023-海特高新.csv` 内容如下：

```csv
stock_code,stock_name,日期,开盘,收盘,最高,最低,成交量,成交额,振幅,涨跌幅,涨跌额,换手率
002023,海特高新,2015-01-05,10.72,10.77,10.89,10.53,62683,136649238.0,3.34,0.0,0.0,2.3
002023,海特高新,2015-01-06,10.77,11.39,11.5,10.67,125213,286451760.0,7.71,5.76,0.62,4.59
002023,海特高新,2015-01-07,11.43,11.17,11.43,11.07,67126,153281362.0,3.16,-1.93,-0.22,2.46
002023,海特高新,2015-01-08,11.18,11.22,11.35,11.08,64628,148323888.0,2.42,0.45,0.05,2.37
```

脚本 `predicate.py` 完成以下任务：根据过往股价预测 5 日后的股价。

将预测结果输出到 `./predicated/002023-海特高新.csv` 并展示可视化数据到 `./predicated/002023-海特高新.png`。 
