import plotly.graph_objects as go
import streamlit as st
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
from datetime import datetime

st.title("YF strat marker")

upload = st.file_uploader("Enter a file containing OHLC data from MT5", ['txt','csv'])
if upload:
    data = pd.read_csv(upload)

    # <-- FIX 2: Convert date/time column to index so .time() works.
    # Replace 'time' with your actual column name (e.g., 'Date', 'Timestamp') if different.
    if "time" in data.columns:
        data["time"] = pd.to_datetime(data["time"])
        data.set_index("time", inplace=True)
    elif "Date" in data.columns:
        data["Date"] = pd.to_datetime(data["Date"])
        data.set_index("Date", inplace=True)
    def turtle_soup(df):
        # We create a for loop to loop each item.
        events = []
        for i in range(1, len(df) - 3):
            # we define previous low, current low and next_low.
            prev_low = df['low'].iloc[i - 1]
            current_low = df['low'].iloc[i]
            next_low = df['low'].iloc[i + 1]

            # STEP 1: find short-term low
            # Here, we says "If the current low is downer than the previous low and if current_low is smaller than the next low:"
            if current_low < prev_low and current_low < next_low:
                # We grab the index 2.
                # STEP 2: liquidity sweep (break below)
                if df['low'].iloc[i + 2] < current_low:

                    # STEP 3: reversal confirmation
                    if df['close'].iloc[i + 3] > current_low:
                        events.append({'candle_index': i})
        return events


    # Let's write the FVG func!
    def bullFVG(df):
        events = []
        # We say for every item in the range 1 to len df - 1.
        for i in range(1, len(df) - 1):
            # A bullish FVG has these conditions: so first. let's understand the parts of a bullish FVG.
            # PARTS: 1st candle, 2nd and 3rd.
            # the rule that makes it a FVG: the low of the 3rd candle must be above the high of the 1st candle. the gap it leaves is called a bullish FVG.
            # SO for it, we need: gap, middle candle, the prev high, the next low.
            prev_high = df['high'].iloc[i - 1]
            middle_candle = df.iloc[i]
            next_low = df['low'].iloc[i + 1]
            gap = next_low - prev_high
            # So we say: if the gap is 10: because if we leave it, it'll print tiny numbers like 0.95, 0.87 so i have setted a gap of 10.
            # If the Gap is 10, we write the candle number and write the gap.
            if gap > 10.0:
                events.append({'candle_index': i})
        return events


    def bearFVG(df):
        events = []
        # We say for every item in the range 1 to len df - 1.
        for i in range(1, len(df) - 1):
            # A bearish FVG has these conditions: so first. let's understand the parts of a bearish FVG.
            # PARTS: 1st candle, 2nd and 3rd.
            # the rule that makes it a FVG: the low of the 3rd candle must be above the high of the 1st candle. the gap it leaves is called a bullish FVG.
            # SO for it, we need: gap, middle candle, the prev high, the next low.
            prev_low = df['low'].iloc[i - 1]
            middle_candle = df.iloc[i]
            next_high = df['high'].iloc[i + 1]
            gap = prev_low - next_high
            # So we say: if the gap is 20: because if we leave it, it'll print tiny numbers like 0.95, 0.87 so i have setted a gap of 10.
            # If the Gap is 20, we write the candle number and write the gap.
            if gap > 10.0:
                events.append({'candle_index': i})
        return events


    def liquidity_pool_short_term_high(data, barrier=15):
        events = []
        for i in range(barrier, len(data) - barrier):
            current_high = data['high'].iloc[i]

            # Check if current candle is the absolute highest in the left and right windows
            left_side = data['high'].iloc[i - barrier:i].max()
            right_side = data['high'].iloc[i + 1:i + barrier + 1].max()

            if current_high > left_side and current_high > right_side:
                events.append({'candle_index': i})
        return events


    def liquidity_pool_short_term_low(data, barrier=15):
        events = []
        for i in range(barrier, len(data) - barrier):
            current_low = data['low'].iloc[i]

            left_side = data['low'].iloc[i - barrier:i].min()
            right_side = data['low'].iloc[i + 1:i + barrier + 1].min()

            if current_low < left_side and current_low < right_side:
                events.append({'candle_index': i})
        return events


    def ob_bear(data):
        events = []
        for i in range(1, len(data) - 5):
            previous_candle = data['low'].iloc[i - 1]
            current = data['low'].iloc[i]
            next_low = data['low'].iloc[i + 1]
            nexter = data['low'].iloc[i + 2]

            # Detects price breaking heavily downward below previous lows
            if previous_candle > current and next_low < current and nexter < next_low:
                next_bull = data['low'].iloc[i + 3]
                nexter_bull = data['low'].iloc[i + 4]
                next_gen = data['low'].iloc[i + 5]

                if next_bull > nexter_bull and next_gen < next_low:
                    events.append({'candle_index': i})
        return events


    def ob_bull(data):
        events = []
        # Loop through data, leaving room to check candles behind and ahead
        for i in range(2, len(data) - 3):

            # 1. THE "U-TURN" CHECK (Change of Character)
            # Was the market actually falling before this candle?
            # (Previous candle's close is lower than the one before it)
            was_falling = data['close'].iloc[i - 1] < data['close'].iloc[i - 2]

            # 2. THE EXPANSION CHECK
            # Is this candle a strong green candle moving upward?
            is_strong_up = data['close'].iloc[i] > data['open'].iloc[i]

            # 3. THE "SKIPPED STEP" CHECK (Fair Value Gap)
            # Did the next candles move up so fast they left empty vertical space?
            # We check if the LOW of candle i+2 is higher than the HIGH of candle i
            skipped_step = data['low'].iloc[i + 2] > data['high'].iloc[i]

            # Only trigger an Order Block if ALL THREE friendly rules are met!
            if was_falling and is_strong_up and skipped_step:
                events.append({
                    'candle_index': i
                })

        return events


    def silver_bullet(data):
        events = []

        for i in range(1, len(data) - 4):
            # 1. Get the actual timestamp of the current candle
            candle_time = data.index[i].time()

            # 2. Check if the candle time is inside the AM or PM Silver Bullet windows
            # Note: 10:00-11:00 AM NY time is 14:00-15:00 UTC (matching your code)
            is_am_bullet = (candle_time >= datetime.strptime('14:00:00', '%H:%M:%S').time() and
                            candle_time <= datetime.strptime('14:59:59', '%H:%M:%S').time())

            is_pm_bullet = (candle_time >= datetime.strptime('18:00:00', '%H:%M:%S').time() and
                            candle_time <= datetime.strptime('18:59:59', '%H:%M:%S').time())

            # 3. Only run your math if the candle is within the allowed windows!
            if is_am_bullet or is_pm_bullet:
                bull_prev = data['high'].iloc[i - 1]
                present = data['low'].iloc[i]
                next = data['high'].iloc[i + 1]
                nexter = data['high'].iloc[i + 2]

                if bull_prev > present and present > nexter:
                    next_gen = data['high'].iloc[i + 3]
                    nexter_gen = data['high'].iloc[i + 4]
                    if nexter_gen > next_gen:
                        events.append({
                            'candle_index': i
                        })

        return events


    def Judas_swing(data):
        events = []
        for i in range(1, len(data) - 1):
            candle_time = data.index[i].time()

            # 2. Check if the candle time is inside the AM or PM Silver Bullet windows
            # Note: 10:00-11:00 AM NY time is 14:00-15:00 UTC (matching your code)
            is_am_bullet = (candle_time >= datetime.strptime('14:00:00', '%H:%M:%S').time() and
                            candle_time <= datetime.strptime('14:59:59', '%H:%M:%S').time())

            is_pm_bullet = (candle_time >= datetime.strptime('18:00:00', '%H:%M:%S').time() and
                            candle_time <= datetime.strptime('18:59:59', '%H:%M:%S').time())
            prev_candle = data['close'].iloc[i - 1]
            present = data['close'].iloc[i]
            if prev_candle > present:
                events.append({'candle_index': i})
        return events
    soup_data = turtle_soup(data)
    bull_fvg_data = bullFVG(data)
    bear_fvg_data = bearFVG(data)
    liq_high_data = liquidity_pool_short_term_high(data)
    liq_low_data = liquidity_pool_short_term_low(data)
    bear_ob_data = ob_bear(data)
    bull_ob_data = ob_bull(data)
    silver_bullet_data = silver_bullet(data)

    import plotly.graph_objects as go

    fig = go.Figure()

    # Candles
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data["open"],
        high=data["high"],
        low=data["low"],
        close=data["close"],
        name="Price"
    ))

    # -------------------------
    # Bull FVG
    # -------------------------
    for item in bull_fvg_data:
        idx = item["candle_index"]

        fig.add_annotation(
            x=data.index[idx],
            y=data["low"].iloc[idx],
            text="🟢 Bull FVG",
            showarrow=True,
            arrowhead=2,
            arrowcolor="lime",
            arrowsize=1.5,
            arrowwidth=2,
            ax=0,
            ay=40,
            font=dict(color="lime", size=10)
        )

    # -------------------------
    # Bear FVG
    # -------------------------
    for item in bear_fvg_data:
        idx = item["candle_index"]

        fig.add_annotation(
            x=data.index[idx],
            y=data["high"].iloc[idx],
            text="🔴 Bear FVG",
            showarrow=True,
            arrowhead=2,
            arrowcolor="red",
            arrowsize=1.5,
            arrowwidth=2,
            ax=0,
            ay=-40,
            font=dict(color="red", size=10)
        )

    # -------------------------
    # Turtle Soup
    # -------------------------
    for item in soup_data:
        idx = item["candle_index"]

        fig.add_annotation(
            x=data.index[idx],
            y=data["low"].iloc[idx],
            text="🍲",
            showarrow=True,
            arrowhead=2,
            arrowcolor="orange",
            ax=0,
            ay=40,
            font=dict(color="orange", size=12)
        )

    # -------------------------
    # Liquidity High
    # -------------------------
    for item in liq_high_data:
        idx = item["candle_index"]

        fig.add_annotation(
            x=data.index[idx],
            y=data["high"].iloc[idx],
            text="💧H",
            showarrow=True,
            arrowhead=2,
            arrowcolor="cyan",
            ax=0,
            ay=-40,
            font=dict(color="cyan")
        )

    # -------------------------
    # Liquidity Low
    # -------------------------
    for item in liq_low_data:
        idx = item["candle_index"]

        fig.add_annotation(
            x=data.index[idx],
            y=data["low"].iloc[idx],
            text="💧L",
            showarrow=True,
            arrowhead=2,
            arrowcolor="magenta",
            ax=0,
            ay=40,
            font=dict(color="magenta")
        )

    # -------------------------
    # Bull Order Block
    # -------------------------
    for item in bull_ob_data:
        idx = item["candle_index"]

        fig.add_annotation(
            x=data.index[idx],
            y=data["low"].iloc[idx],
            text="🐂 OB",
            showarrow=True,
            arrowhead=2,
            arrowcolor="green",
            ax=0,
            ay=40,
            font=dict(color="green")
        )

    # -------------------------
    # Bear Order Block
    # -------------------------
    for item in bear_ob_data:
        idx = item["candle_index"]

        fig.add_annotation(
            x=data.index[idx],
            y=data["high"].iloc[idx],
            text="🐻 OB",
            showarrow=True,
            arrowhead=2,
            arrowcolor="red",
            ax=0,
            ay=-40,
            font=dict(color="red")
        )

    # -------------------------
    # Silver Bullet
    # -------------------------
    for item in silver_bullet_data:
        idx = item["candle_index"]

        fig.add_annotation(
            x=data.index[idx],
            y=data["high"].iloc[idx],
            text="⚡",
            showarrow=True,
            arrowhead=2,
            arrowcolor="yellow",
            ax=0,
            ay=-40,
            font=dict(color="yellow", size=14)
        )

    # -------------------------
    # Judas Swing
    # -------------------------
    judas_data = Judas_swing(data)

    for item in judas_data:
        idx = item["candle_index"]

        fig.add_annotation(
            x=data.index[idx],
            y=data["high"].iloc[idx],
            text="💀",
            showarrow=True,
            arrowhead=2,
            arrowcolor="white",
            ax=0,
            ay=-40,
            font=dict(color="white", size=14)
        )

    # -------------------------
    # Layout
    # -------------------------
    fig.update_layout(

        title="ICT Master Chart",

        template="plotly_dark",

        height=900,

        xaxis_title="Time",

        yaxis_title="Price",

        xaxis_rangeslider_visible=False

    )

    st.plotly_chart(fig, use_container_width=True)