import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
from matplotlib.backends.backend_pdf import PdfPages

# மொபைலுக்கு ஏற்றவாறு பக்கத்தை அமைத்தல்
st.set_page_config(page_title="Live Auto-Pivot Matrix", layout="centered")

st.title("🚀 Live Auto-Pivot Matrix Engine")
st.write("Fetches Data Directly from Web — No Typing Required")

# --- 1. சிம்பல் செலக்டர் இன்புட் (Top Control Panel) ---
ticker_options = {
    "Nifty 50": "^NSEI",
    "Bank Nifty": "^NSEBANK",
    "Reliance": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFC Bank": "HDFCBANK.NS"
}

selected_symbol_label = st.selectbox("🎯 Select Instrument / Stock:", list(ticker_options.keys()))
custom_ticker = st.text_input("✍️ Or Type Custom Yahoo Ticker (e.g., SBIN.NS, ^NSEI):", value=ticker_options[selected_symbol_label])

# --- 2. வெப்சைட்டில் இருந்து தரவுகளை எடுக்கும் இன்ஜின் ---
@st.cache_data(ttl=300)  # 5 நிமிடத்திற்கு ஒருமுறை டேட்டாவை புதுப்பிக்கும்
def fetch_ohlc_from_web(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    
    # வெவ்வேறு காலகட்டத்திற்கான ஹிஸ்டரி டேட்டா எடுத்தல்
    df_daily = ticker.history(period="5d", interval="1d")
    df_weekly = ticker.history(period="1mo", interval="1wk")
    df_monthly = ticker.history(period="6mo", interval="1mo")
    df_yearly = ticker.history(period="5y", interval="1y")
    
    # தற்போதைய லைவ் விலை (LTP)
    try:
        ltp = ticker.basic_info['lastPrice']
    except:
        ltp = df_daily['Close'].iloc[-1] if not df_daily.empty else 0.0

    ohlc_data = {}
    
    # A. Daily Data Processing
    if len(df_daily) >= 2:
        ohlc_data["Present Daily"] = {"H": df_daily['High'].iloc[-1], "L": df_daily['Low'].iloc[-1], "C": df_daily['Close'].iloc[-1]}
        ohlc_data["Previous Daily"] = {"H": df_daily['High'].iloc[-2], "L": df_daily['Low'].iloc[-2], "C": df_daily['Close'].iloc[-2]}
    else:
        ohlc_data["Present Daily"] = ohlc_data["Previous Daily"] = {"H": 0, "L": 0, "C": 0}

    # B. Weekly Data Processing
    if len(df_weekly) >= 2:
        ohlc_data["Present Weekly"] = {"H": df_weekly['High'].iloc[-1], "L": df_weekly['Low'].iloc[-1], "C": df_weekly['Close'].iloc[-1]}
        ohlc_data["Previous Weekly"] = {"H": df_weekly['High'].iloc[-2], "L": df_weekly['Low'].iloc[-2], "C": df_weekly['Close'].iloc[-2]}
    else:
        ohlc_data["Present Weekly"] = ohlc_data["Previous Weekly"] = {"H": 0, "L": 0, "C": 0}

    # C. Monthly Data Processing
    if not df_monthly.empty:
        ohlc_data["Present Monthly"] = {"H": df_monthly['High'].iloc[-1], "L": df_monthly['Low'].iloc[-1], "C": df_monthly['Close'].iloc[-1]}
    else:
        ohlc_data["Present Monthly"] = {"H": 0, "L": 0, "C": 0}

    # D. Yearly Data Processing
    if not df_yearly.empty:
        ohlc_data["Yearly"] = {"H": df_yearly['High'].iloc[-1], "L": df_yearly['Low'].iloc[-1], "C": df_yearly['Close'].iloc[-1]}
    else:
        ohlc_data["Yearly"] = {"H": 0, "L": 0, "C": 0}
        
    return ohlc_data, round(ltp, 2)

# --- 3. ஆட்டோமேட்டிக் லெவல் கால்குலேட்டர் ஃபங்ஷன் ---
def calculate_pivot_levels(high, low, close):
    cp = (high + low + close) / 3.0
    bc = (high + low) / 2.0
    tc = (cp - bc) + cp
    range_val = high - low
    h4 = close + (range_val * 1.1 / 2.0)
    h3 = close + (range_val * 1.1 / 4.0)
    l3 = close - (range_val * 1.1 / 4.0)
    l4 = close - (range_val * 1.1 / 2.0)
    return {"H4": round(h4,2), "H3": round(h3,2), "L3": round(l3,2), "L4": round(l4,2), "TC": round(tc,2), "CP": round(cp,2), "BC": round(bc,2)}

# வெப்சைட்டில் இருந்து டேட்டாவை எடுத்தல்
with st.spinner("Fetching live data from website..."):
    try:
        web_ohlc, market_close_price = fetch_ohlc_from_web(custom_ticker)
        st.success(f"Successfully loaded data for {custom_ticker}! LTP: {market_close_price}")
    except Exception as e:
        st.error("Error connecting to website. Please check the Ticker name.")
        st.stop()

# லெவல்களை கணக்கிட்டு அடுக்குதல்
view_order = ["Yearly", "Present Monthly", "Previous Weekly", "Present Weekly", "Previous Daily", "Present Daily"]
calculated_rows = []
for tf in view_order:
    vals = web_ohlc.get(tf, {"H": 0, "L": 0, "C": 0})
    pivots = calculate_pivot_levels(vals["H"], vals["L"], vals["C"])
    pivots["Level"] = tf
    calculated_rows.append(pivots)

df = pd.DataFrame(calculated_rows)[["Level", "H4", "H3", "L3", "L4", "TC", "CP", "BC"]]

# --- 4. 7 Types of Pivot Relationship இன்ஜின் ---
def detect_pivot_relationship(prev_tc, prev_bc, curr_tc, curr_bc):
    prev_high, prev_low = max(prev_tc, prev_bc), min(prev_tc, prev_bc)
    curr_high, curr_low = max(curr_tc, curr_bc), min(curr_bc, curr_tc)
    if curr_low > prev_high: return "🟢 Higher Value (Strongly Bullish)", "மார்க்கெட் நல்ல அப்-டிரெண்டில் மேலே செல்ல வாய்ப்பு அதிகம்."
    elif curr_high < prev_low: return "🔴 Lower Value (Strongly Bearish)", "மார்க்கெட் நல்ல டவுன்-டிரெண்டில் கீழே விழ வாய்ப்பு அதிகம்."
    elif curr_high < prev_high and curr_low > prev_low: return "🟣 Inside Value (Breakout Imminent)", "கடுமையான சுருக்கம்! பெரிய பிரேக்அவுட் மூவ்மெண்ட் இன்று நிகழும்."
    elif curr_high > prev_high and curr_low < prev_low: return "🔵 Outside Value (Sideways / Rangebound)", "சந்தை பெரிய டிரெண்ட் எடுக்காமல் இரண்டு பக்கமும் அலைபாயும்."
    elif curr_high > prev_high and curr_low >= prev_low: return "🟡 Overlapping Higher (Moderately Bullish)", "சந்தை லேசான பாசிட்டிவ் போக்கில் நகரக்கூடும்."
    elif curr_low < prev_low and curr_high <= prev_high: return "🟠 Overlapping Lower (Moderately Bearish)", "சந்தை லேசான நெகட்டிவ் போக்கில் நகரக்கூடும்."
    else: return "⚪ Unchanged Congestion", "மாற்றங்கள் இல்லை, முந்தைய ரேஞ்சிலேயே நீடிக்கிறது."

row_map = df.set_index("Level")
d_rel_title, d_rel_desc = detect_pivot_relationship(row_map.loc["Previous Daily", "TC"], row_map.loc["Previous Daily", "BC"], row_map.loc["Present Daily", "TC"], row_map.loc["Present Daily", "BC"])
w_rel_title, w_rel_desc = detect_pivot_relationship(row_map.loc["Previous Weekly", "TC"], row_map.loc["Previous Weekly", "BC"], row_map.loc["Present Weekly", "TC"], row_map.loc["Present Weekly", "BC"])

st.info(f"**📅 Intraday View (Prev Daily ➔ Pres Daily):** {d_rel_title}\n\n💡 *{d_rel_desc}*")
st.success(f"**⏳ Swing View (Prev Weekly ➔ Pres Weekly):** {w_rel_title}\n\n💡 *{w_rel_desc}*")

# --- 5. வியூ பெர்ஸ்பெக்டிவ் பட்டன்கள் ---
st.subheader("🎯 View Perspective")
selected_tab = st.radio("Select View Range:", ["Full Structure View", "Tactical Focus View (W & D)"], horizontal=True)
sub_df = df.copy() if selected_tab == "Full Structure View" else df[df["Level"].isin(["Previous Weekly", "Present Weekly", "Previous Daily", "Present Daily"])].reset_index(drop=True)

# --- 6. நிலையான Matplotlib சார்ட் என்ஜின் ---
def plot_mobile_engine(plot_df, ltp):
    fig, ax = plt.subplots(figsize=(10, 6.5))
    x_positions = range(len(plot_df))
    bar_width = 0.4
    all_prices = [ltp]

    for idx, row in plot_df.iterrows():
        x = x_positions[idx]
        all_prices.extend([row["H4"], row["H3"], row["L3"], row["L4"], row["TC"], row["CP"], row["BC"]])
        ax.hlines(y=row["H4"], xmin=x - bar_width, xmax=x + bar_width, colors="blue", linewidth=2.5)
        ax.text(x, row["H4"] + 12, f'{row["H4"]:.1f}', ha="center", va="bottom", fontsize=8, color="blue", weight="bold")
        ax.hlines(y=row["H3"], xmin=x - bar_width, xmax=x + bar_width, colors="orange", linewidth=2.5)
        ax.text(x, row["H3"] + 12, f'{row["H3"]:.1f}', ha="center", va="bottom", fontsize=8, color="red", weight="bold")
        ax.hlines(y=row["L3"], xmin=x - bar_width, xmax=x + bar_width, colors="orange", linestyles="--", linewidth=2)
        ax.text(x, row["L3"] - 12, f'{row["L3"]:.1f}', ha="center", va="top", fontsize=8, color="red", weight="bold")
        ax.hlines(y=row["L4"], xmin=x - bar_width, xmax=x + bar_width, colors="blue", linestyles="--", linewidth=2)
        ax.text(x, row["L4"] - 12, f'{row["L4"]:.1f}', ha="center", va="top", fontsize=8, color="blue", weight="bold")
        ax.hlines(y=row["TC"], xmin=x - bar_width, xmax=x + bar_width, colors="purple", linestyles=":", linewidth=1.5)
        ax.hlines(y=row["CP"], xmin=x - bar_width, xmax=x + bar_width, colors="purple", linestyles="-.", linewidth=2)
        ax.hlines(y=row["BC"], xmin=x - bar_width, xmax=x + bar_width, colors="purple", linestyles=":", linewidth=1.5)
        ax.text(x - bar_width, row["CP"], f' CP:{row["CP"]:.1f}', ha="left", va="center", fontsize=7.5, color="purple")
        ax.hlines(y=ltp, xmin=x - bar_width, xmax=x + bar_width, colors="crimson", linestyles="-", linewidth=1.2, alpha=0.7)
        ax.plot(x, ltp, marker="o", color="crimson", markersize=5)
        if idx == len(plot_df) - 1: ax.text(x + bar_width + 0.02, ltp, f'LTP:{ltp}', va="center", ha="left", color="crimson", weight="bold", fontsize=8.5)

    if "Present Weekly" in plot_df["Level"].values and "Present Daily" in plot_df["Level"].values:
        w_row = plot_df[plot_df["Level"] == "Present Weekly"].iloc[0]
        d_row = plot_df[plot_df["Level"] == "Present Daily"].iloc[0]
        all_keys = ["H4", "H3", "L3", "L4", "TC", "CP", "BC"]
        for wk in all_keys:
            for dk in all_keys:
                if abs(w_row[wk] - d_row[dk]) / w_row[wk] <= 0.0015:
                    y_min, y_max = min(w_row[wk], d_row[dk]), max(w_row[wk], d_row[dk])
                    ax.axhspan(y_min - 6, y_max + 6, xmin=0.2, xmax=0.9, color="#ff00ff", alpha=0.1)

    ax.set_xticks(x_positions)
    ax.set_xticklabels(plot_df["Level"], fontsize=9.5, weight="bold")
    ax.grid(True, linestyle=":", alpha=0.4)
    ax.set_xlim(-0.5, len(plot_df) - 0.5)
    min_p, max_p = min(all_prices), max(all_prices)
    padding = (max_p - min_p) * 0.08
    ax.set_ylim(min_p - padding, max_p + padding)
    plt.tight_layout()
    return fig

st.pyplot(plot_mobile_engine(sub_df, market_close_price))

# --- 7. ஆக்டிவ் டேட்டா டேபிள் மற்றும் PDF டவுன்லோடு ---
st.subheader("📋 Active Data Table")
st.dataframe(df.set_index("Level"), use_container_width=True)

st.subheader("📥 Download Analysis Report")
pdf_path = "Multi_Pivot_Analysis_Report.pdf"
with PdfPages(pdf_path) as pdf:
    for view_name, plot_data in [("Full View Structure", df), ("Tactical Focus (W and D)", df[df["Level"].isin(["Previous Weekly", "Present Weekly", "Previous Daily", "Present Daily"])])]:
        fig_pdf = plot_mobile_engine(plot_data.reset_index(drop=True), market_close_price)
        plt.title(f"Market Analysis - {view_name}", fontsize=11, weight="bold", pad=12)
        pdf.savefig(fig_pdf)
        plt.close()

with open(pdf_path, "rb") as pdf_file:
    st.download_button(label="Download PDF Matrix Report", data=pdf_file, file_name="Multi_Pivot_Matrix_Report.pdf", mime="application/pdf")
