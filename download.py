import os
import json
import re
import akshare as ak
from tqdm import tqdm
from datetime import datetime


# ----------------- 文件名清洗函数 -----------------
def sanitize_filename(name):
    """去除文件名中的非法字符"""
    # 替换Windows系统非法字符
    cleaned = re.sub(r'[\\/*?:"<>|]', '', str(name))
    # 替换空格和特殊空白字符
    return cleaned.replace(' ', '_').replace('\u3000', '_')


# ----------------- 修改后的StockMapper类 -----------------
class StockMapper:
    def __init__(self):
        self.code_name_map = {}
        self._init_stock_map()

    def _init_stock_map(self):
        try:
            df = ak.stock_zh_a_spot_em()
            self.code_name_map = df.set_index('代码')['名称'].apply(sanitize_filename).to_dict()
        except Exception as e:
            print(f"股票代码表初始化失败: {str(e)}")

    def get_stock_name(self, code):
        """安全获取股票名称"""
        return self.code_name_map.get(code, f"未知股票_{code}")

    def get_clean_name(self, code):
        return self.code_name_map.get(code, f"未知股票_{code}")


# ----------------- 修改后的保存逻辑 -----------------
def generate_filename(code, stock_mapper):
    """生成标准文件名"""
    name = stock_mapper.get_clean_name(code)
    return f"{code}-{name}.csv"


# ----------------- 修改后的下载函数 -----------------
def download_and_save(config):
    os.makedirs(config['save_path'], exist_ok=True)
    stock_mapper = StockMapper()

    # 获取有效代码列表（自动过滤无效代码）
    valid_codes = [code for code in config['stock_codes'] if code in stock_mapper.code_name_map]
    if not valid_codes:
        print("警告：配置中的股票代码均无效！")
        return

    for code in tqdm(valid_codes, desc="下载进度"):
        try:
            # 下载数据
            df = retry_download(code, config)

            # 清洗数据
            df = clean_dataframe(df, code, stock_mapper)

            # 生成安全文件名
            filename = generate_filename(code, stock_mapper)
            save_path = os.path.join(config['save_path'], filename)

            # 保存文件（增加编码处理）
            df.to_csv(save_path, index=False, encoding='utf_8_sig')

        except Exception as e:
            error_msg = f"{code} 处理失败: {str(e)}"
            print(f"\n[ERROR] {error_msg}")
            log_error(code, error_msg)


# ----------------- 修改后的清洗函数 -----------------
def clean_dataframe(df, code, stock_mapper):
    """增强型数据清洗"""
    # 统一列名格式
    df.columns = df.columns.str.replace(' ', '')

    # 删除可能冲突的列
    conflict_cols = ['股票代码', '代码', '股票名称', '名称']
    df = df.drop(columns=[col for col in conflict_cols if col in df.columns], errors='ignore')

    # 插入新信息
    df.insert(0, 'stock_code', code)
    df.insert(1, 'stock_name', stock_mapper.get_stock_name(code))
    return df


def load_config(config_path='config.json'):
    """加载配置并设置默认值"""
    default_config = {
        "stock_codes": [],
        "start_date": "20100101",
        "end_date": datetime.now().strftime("%Y%m%d"),
        "save_path": "./stock_data",
        "adjust_type": "hfq",
        "period": "daily"
    }

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
        return {**default_config, **user_config}
    except FileNotFoundError:
        print(f"警告: 配置文件 {config_path} 不存在，使用默认配置")
        return default_config
    except Exception as e:
        print(f"配置读取失败: {str(e)}")
        exit(1)


def get_all_a_stock():
    """获取全量A股代码"""
    try:
        df = ak.stock_zh_a_spot_em()
        return df['代码'].tolist()
    except Exception as e:
        print(f"获取股票列表失败: {str(e)}")
        return []


def retry_download(code, config, retries=3):
    """带重试的数据下载"""
    for i in range(retries):
        try:
            df = ak.stock_zh_a_hist(
                symbol=code,
                period=config['period'],
                start_date=config['start_date'],
                end_date=config['end_date'],
                adjust=config['adjust_type']
            )
            return df
        except Exception as e:
            if i == retries - 1:
                raise e
            print(f"第{i + 1}次重试 {code}...")


def log_error(code, message):
    """错误日志记录"""
    with open("download_errors.log", "a") as f:
        f.write(f"{datetime.now()} | {code} | {message}\n")


if __name__ == "__main__":
    config = load_config()
    print("有效配置参数:", json.dumps(config, indent=2, ensure_ascii=False))
    download_and_save(config)
