# Factor Design

## 1. 因子設計目的

本模組的目標是將 daily_prices 中的原始股價與成交量資料，轉換成可用於股票比較、排序與分群的量化因子。

## 2. 使用資料欄位

- stock_id
- date
- close
- volume

## 3. 核心因子

### return_20d
近 20 個交易日報酬率，用來衡量短期動能。

公式：
return_20d = 今日收盤價 / 20 個交易日前收盤價 - 1

### return_60d
近 60 個交易日報酬率，用來衡量中期趨勢。

公式：
return_60d = 今日收盤價 / 60 個交易日前收盤價 - 1

### volatility_20d
近 20 日每日報酬率的標準差，用來衡量短期價格波動程度。

### max_drawdown
近 60 日期間內，股價從高點下跌到低點的最大跌幅，用來衡量下跌風險。

### volume_ratio
近 5 日平均成交量 / 近 20 日平均成交量，用來觀察近期交易熱度是否提高。

## 4. health_score 設計

health_score 是綜合分數，範圍為 0 到 100。

分數包含：
- return_20d_score：30%
- return_60d_score：25%
- volatility_score：20%
- drawdown_score：15%
- volume_score：10%

此分數僅作為資料分析與比較用途，不代表投資建議。

## 5. K-means 分群

本專題使用 K-means 將股票依照量化特徵分群。

使用特徵：
- return_20d
- return_60d
- volatility_20d
- max_drawdown
- volume_ratio
- health_score

由於各因子的尺度不同，因此分群前使用 StandardScaler 進行標準化。

## 6. 分析限制

- 因子僅基於歷史股價與成交量資料
- 未納入財報、法人買賣超與總體經濟資料
- health_score 權重為專題設計，可依未來研究調整
- K-means 分群結果會受到特徵選擇與群數設定影響