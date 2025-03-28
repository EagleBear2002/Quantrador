import akshare as ak
import json
from pathlib import Path

def get_all_a_etf_codes():
    """获取全A股和ETF代码清单"""
    all_codes = []

    # 获取A股代码（含沪深京）
    try:
        stock_df = ak.stock_info_a_code_name()
        a_shares = stock_df['code'].astype(str).tolist()
        all_codes.extend(a_shares)
        print(f"获取A股代码成功：{len(a_shares)}条")
    except Exception as e:
        print(f"A股代码获取失败：{str(e)}")
        return None

    # 获取ETF代码
    # try:
    #     etf_df = ak.fund_etf_category_sina(symbol="ETF基金")
    #     etfs = etf_df['symbol'].str[:6].tolist()
    #     all_codes.extend(etfs)
    #     print(f"获取ETF代码成功：{len(etfs)}条")
    # except Exception as e:
    #     print(f"ETF代码获取失败：{str(e)}")
    #     return None

    # 清洗数据
    valid_codes = sorted(list({
        code.zfill(6)  # 统一为6位数字
        for code in all_codes
        if isinstance(code, str) and code.isdigit()
    }))

    return valid_codes

def save_to_json(codes, filename="./allcode.json"):
    """保存代码到JSON文件"""
    data = {"stock_codes": codes}
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\n文件已保存至：{Path(filename).resolve()}")
        return True
    except Exception as e:
        print(f"保存文件失败：{str(e)}")
        return False

if __name__ == '__main__':
    # 获取代码
    codes = get_all_a_etf_codes()

    if codes:
        # 保存结果
        if save_to_json(codes):
            # 打印示例
            print("\n示例数据：")
            print(json.dumps(
                {"stock_codes": codes[:8]},
                indent=4,
                ensure_ascii=False
            ))