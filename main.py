import plotly.graph_objects as go
import streamlit as st
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import numpy as np
from datetime import datetime

st.title("YF strat marker")

upload = st.file_uploader("Enter a file containing OHLC data from MT5", ['txt', 'csv'])
if upload:
    data = pd.read_csv(upload)
    st.write(len(data))
    if "time" in data.columns:
        data["time"] = pd.to_datetime(data["time"])
        data.set_index("time", inplace=True)
    elif "Date" in data.columns:
        data["Date"] = pd.to_datetime(data["Date"])
        data.set_index("Date", inplace=True)


    @st.cache_data
    def turtle_soup(df):
        events = []
        low = df["low"].to_numpy()
        close = df["close"].to_numpy()
        high = df["high"].to_numpy()
        open = df["open"].to_numpy()
        for i in range(1, len(df) - 3):
            prev_low = low[i - 1]
            current_low = low[i]
            next_low = low[i + 1]
            if current_low < prev_low and current_low < next_low:
                if low[i + 2] < current_low:
                    if close[i + 3] > current_low:
                        events.append({'candle_index': i})
        return events


    @st.cache_data
    def bullFVG(df):
        events = []
        low = df["low"].to_numpy()
        close = df["close"].to_numpy()
        high = df["high"].to_numpy()
        open = df["open"].to_numpy()
        for i in range(1, len(df) - 1):
            prev_high = high[i - 1]
            next_low = low[i + 1]
            gap = next_low - prev_high
            if gap > 10.0:
                events.append({'candle_index': i})
        return events


    @st.cache_data
    def bearFVG(df):
        events = []
        low = df["low"].to_numpy()
        close = df["close"].to_numpy()
        high = df["high"].to_numpy()
        open = df["open"].to_numpy()
        for i in range(1, len(df) - 1):
            prev_low = low[i - 1]
            next_high = high[i + 1]
            gap = prev_low - next_high
            if gap > 10.0:
                events.append({'candle_index': i})
        return events


    @st.cache_data
    def liquidity_pool_short_term_high(df, barrier=15):
        events = []
        low = df["low"].to_numpy()
        close = df["close"].to_numpy()
        high = df["high"].to_numpy()
        open = df["open"].to_numpy()
        for i in range(barrier, len(df) - barrier):
            current_high = high[i]
            left_side = high[i - barrier:i].max()
            right_side = high[i + 1:i + barrier + 1].max()
            if current_high > left_side and current_high > right_side:
                events.append({'candle_index': i})
        return events


    @st.cache_data
    def liquidity_pool_short_term_low(df, barrier=15):
        events = []
        low = df["low"].to_numpy()
        close = df["close"].to_numpy()
        high = df["high"].to_numpy()
        open = df["open"].to_numpy()
        for i in range(barrier, len(df) - barrier):
            current_low = low[i]
            left_side = low[i - barrier:i].min()
            right_side = low[i + 1:i + barrier + 1].min()
            if current_low < left_side and current_low < right_side:
                events.append({'candle_index': i})
        return events


    @st.cache_data
    def ob_bear(df):
        events = []
        low = df["low"].to_numpy()
        close = df["close"].to_numpy()
        high = df["high"].to_numpy()
        open = df["open"].to_numpy()
        for i in range(1, len(df) - 5):
            previous_candle = low[i - 1]
            current = low[i]
            next_low = low[i + 1]
            nexter = low[i + 2]
            if previous_candle > current and next_low < current and nexter < next_low:
                next_bull = low[i + 3]
                nexter_bull = low[i + 4]
                next_gen = low[i + 5]
                if next_bull > nexter_bull and next_gen < next_low:
                    events.append({'candle_index': i})
        return events


    @st.cache_data
    def ob_bull(df):
        events = []
        low = df["low"].to_numpy()
        close = df["close"].to_numpy()
        high = df["high"].to_numpy()
        open = df["open"].to_numpy()
        for i in range(2, len(df) - 3):
            was_falling = close[i - 1] < close[i - 2]
            is_strong_up = close[i] > open[i]
            skipped_step = low[i + 2] > high[i]
            if was_falling and is_strong_up and skipped_step:
                events.append({'candle_index': i})
        return events

    @st.cache_data
    def silver_bullet(df):
        events = []
        low = df["low"].to_numpy()
        close = df["close"].to_numpy()
        high = df["high"].to_numpy()
        open = df["open"].to_numpy()
        for i in range(1, len(df) - 4):
            candle_time = df.index[i].time()
            is_am_bullet = (candle_time >= datetime.strptime('14:00:00', '%H:%M:%S').time() and
                            candle_time <= datetime.strptime('14:59:59', '%H:%M:%S').time())
            is_pm_bullet = (candle_time >= datetime.strptime('18:00:00', '%H:%M:%S').time() and
                            candle_time <= datetime.strptime('18:59:59', '%H:%M:%S').time())
            if is_am_bullet or is_pm_bullet:
                bull_prev = high[i - 1]
                present = low[i]
                next = high[i + 1]
                nexter = high[i + 2]
                if bull_prev > present and present > nexter:
                    next_gen = high[i + 3]
                    nexter_gen = high[i + 4]
                    if nexter_gen > next_gen:
                        events.append({'candle_index': i})
        return events

    @st.cache_data
    def Judas_swing(df):
        events = []
        low = df["low"].to_numpy()
        close = df["close"].to_numpy()
        high = df["high"].to_numpy()
        open = df["open"].to_numpy()
        for i in range(1, len(df) - 1):
            prev_candle = close[i - 1]
            present = close[i]
            if prev_candle > present:
                events.append({'candle_index': i})
        return events


    # Execute Strategy Functions
    soup_data = turtle_soup(data)
    bull_fvg_data = bullFVG(data)
    bear_fvg_data = bearFVG(data)
    liq_high_data = liquidity_pool_short_term_high(data)
    liq_low_data = liquidity_pool_short_term_low(data)
    bear_ob_data = ob_bear(data)
    bull_ob_data = ob_bull(data)
    silver_bullet_data = silver_bullet(data)
    judas_data = Judas_swing(data)

    # -------------------------------------------------------------
    # FIXED MACHINE LEARNING FRAMEWORK
    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # TRUE ML PREDICTION: NO MANUAL LABELLING
    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # FIXED: HISTORICAL STRATEGY PROFITABILITY CLASSIFIER
    # -------------------------------------------------------------
    st.header("ML Strategy Optimization Dashboard")

    # 1. Calculate future profit over a set horizon (e.g., 5 candles later)
    # This evaluates how much money a trade actually made
    horizon = 5
    data['future_close'] = data['close'].shift(-horizon)
    data['raw_profit'] = data['future_close'] - data['close']

    # 2. Initialize tracking columns for each strategy's absolute profit
    # If a strategy did not trigger on a candle, its profit is 0
    data['profit_soup'] = 0.0
    data['profit_bull_fvg'] = 0.0
    data['profit_bear_fvg'] = 0.0
    data['profit_bull_ob'] = 0.0
    data['profit_bear_ob'] = 0.0

    # 3. Map your calculated historical event indices to their actual profits
    for item in soup_data:
        idx = data.index[item["candle_index"]]
        data.at[idx, 'profit_soup'] = data.at[idx, 'raw_profit']  # Long trade

    for item in bull_fvg_data:
        idx = data.index[item["candle_index"]]
        data.at[idx, 'profit_bull_fvg'] = data.at[idx, 'raw_profit']  # Long trade

    for item in bear_fvg_data:
        idx = data.index[item["candle_index"]]
        data.at[idx, 'profit_bear_fvg'] = -data.at[idx, 'raw_profit']  # Short trade (inverted profit)

    for item in bull_ob_data:
        idx = data.index[item["candle_index"]]
        data.at[idx, 'profit_bull_ob'] = data.at[idx, 'raw_profit']  # Long trade

    for item in bear_ob_data:
        idx = data.index[item["candle_index"]]
        data.at[idx, 'profit_bear_ob'] = -data.at[idx, 'raw_profit']  # Short trade (inverted profit)

    # 4. Filter the data to ONLY rows where AT LEAST ONE strategy triggered
    # We ignore empty candles because we only care about comparing active strategies
    strat_profit_columns = ['profit_soup', 'profit_bull_fvg', 'profit_bear_fvg', 'profit_bull_ob', 'profit_bear_ob']
    active_trades_mask = (data[strat_profit_columns] != 0).any(axis=1)
    ml_data = data[active_trades_mask].dropna(subset=['raw_profit']).copy()

    if len(ml_data) > 5:
        # 5. DYNAMIC TARGET LABELLING (0 to 4 based on who made the most money)
        # argmax automatically finds the index of the highest value column per row
        ml_data['best_strat_index'] = ml_data[strat_profit_columns].values.argmax(axis=1)

        # 6. Define Market Conditions (Features) and the Profitable Target (Y)
        X_features = ['open', 'high', 'low', 'close']
        X = ml_data[X_features]
        Y = ml_data['best_strat_index']

        # 7. Train the Classifier to map Market Conditions -> Best Strategy
        model = RandomForestClassifier(random_state=42)
        model.fit(X, Y)

        # 8. Generate Predictions back onto the dataset
        ml_data['ml_recommended_strat_index'] = model.predict(X)

        # Map integer indices back to strategy names for clear UI presentation
        strat_mapping = {
            0: "🍲 Turtle Soup",
            1: "🟢 Bull FVG",
            2: "🔴 Bear FVG",
            3: "🐂 Bull Order Block",
            4: "🐻 Bear Order Block",
            5: "Liquidity Pool High",
            6: "Liquidity Pool Low",
            7: "Silver Bullet",
            8: "Judas swing"
        }
        ml_data['Winning_Strat_Actual'] = ml_data['best_strat_index'].map(strat_mapping)
        ml_data['Winning_Strat_Predicted'] = ml_data['ml_recommended_strat_index'].map(strat_mapping)

        # Display Data Output
        st.write("### Historical Trade Performance & ML Classifications")
        display_cols = X_features + strat_profit_columns + ['Winning_Strat_Actual', 'Winning_Strat_Predicted']
        st.dataframe(ml_data[display_cols].tail(15))

    else:
        st.warning("Not enough overlapping strategy triggers in this dataset to build a comparison matrix.")