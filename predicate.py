import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

def predict_stock_price(input_file):
    # 读取并预处理数据
    original_data = pd.read_csv(input_file)
    original_data['日期'] = pd.to_datetime(original_data['日期'])
    original_data = original_data.sort_values('日期').reset_index(drop=True)

    # 准备数据集
    data = original_data.copy()
    data['label'] = data['收盘'].shift(-5)
    data = data.dropna(subset=['label']).reset_index(drop=True)
    data['original_index'] = data.index  # 记录原始索引

    # 检查数据是否足够
    if len(data) < 30:
        print(f"数据不足({len(data)}行)，至少需要30行有效数据")
        return

    # 特征和标签
    features = data[['开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅', '换手率']]
    labels = data['label'].values.reshape(-1, 1)

    # 归一化处理
    scaler_features = MinMaxScaler()
    scaler_labels = MinMaxScaler()
    scaled_features = scaler_features.fit_transform(features)
    scaled_labels = scaler_labels.fit_transform(labels)

    # 创建时间序列数据集
    n_input = 300
    X, y = [], []
    for i in range(len(scaled_features) - n_input + 1):
        X.append(scaled_features[i:i+n_input])
        y.append(scaled_labels[i + n_input - 1])

    X = np.array(X)
    y = np.array(y)

    # 划分训练集和测试集
    train_size = int(len(X) * 0.8)
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]

    # 构建LSTM模型
    model = Sequential()
    model.add(LSTM(64, activation='relu', input_shape=(n_input, X.shape[2])))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')

    # 训练模型
    model.fit(X_train, y_train, epochs=100, validation_data=(X_test, y_test), verbose=0, batch_size=32)

    # 预测
    y_pred = model.predict(X_test)
    y_pred = scaler_labels.inverse_transform(y_pred)
    y_test = scaler_labels.inverse_transform(y_test.reshape(-1, 1))

    # 获取预测日期
    test_window_indices = [i + n_input - 1 for i in range(train_size, len(X))]
    test_indices = data.loc[test_window_indices, 'original_index'].values
    predicted_dates = original_data.loc[test_indices + 5, '日期'].values

    # 创建结果DataFrame
    results = pd.DataFrame({
        '日期': predicted_dates,
        '预测收盘价': y_pred.flatten(),
        '实际收盘价': y_test.flatten()
    })

    # 确保输出目录存在
    output_dir = './predicated'
    os.makedirs(output_dir, exist_ok=True)

    # 获取股票代码和名称
    stock_code = data['stock_code'].iloc[0]
    stock_name = data['stock_name'].iloc[0]

    # 保存结果
    output_csv = os.path.join(output_dir, f"{stock_code}-{stock_name}.csv")
    results.to_csv(output_csv, index=False)

    # 可视化结果
    plt.rcParams['font.sans-serif'] = ['SimHei']  # Windows系统字体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    plt.figure(figsize=(12, 6))
    plt.plot(predicted_dates, y_test, label='实际收盘价')
    plt.plot(predicted_dates, y_pred, ':', label='预测收盘价')
    plt.title(f'{stock_name} ({stock_code}) 收盘价预测')
    plt.xlabel('日期')
    plt.ylabel('收盘价')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    output_png = os.path.join(output_dir, f"{stock_code}-{stock_name}.png")
    plt.savefig(output_png, dpi=300)
    plt.close()

if __name__ == "__main__":
    input_file = '../stock_data/002023-海特高新.csv'
    predict_stock_price(input_file)