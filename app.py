import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
from matplotlib.backends.backend_pdf import PdfPages

# மொபைலுக்கு ஏற்றவாறு பக்கத்தை அமைத்தல்
st.set_page_config(page_title="Advanced Multi-Pivot Matrix", layout="centered")

st.title("📊 Advanced Multi-Pivot & Breakout Screener")
st.write("Automatically Screens Nifty 50 Stocks for Narrow CPR Breakouts")

# --- Nifty 50 பங்குகள் பட்டியல் ---
NIFTY_50_STOCKS = {
    "Nifty 50 Index": "^NSEI", "Bank Nifty Index": "^NSEBANK", "Sensex Index": "^BSESN",
    "Reliance": "RELIANCE.NS", "TCS": "TCS.NS", "HDFC Bank": "HDFCBANK.NS", "ICICI Bank": "ICICIBANK.NS",
    "Infosys": "INFY.NS", "SBIN": "SBIN.NS", "Bharti Airtel": "BHARTIARTL.NS", "L&T": "LT.NS",
    "ITC": "ITC.NS", "Tata Motors": "TATAMOTORS.NS", "Axis Bank": "AXISBANK.NS", "Kotak Bank": "KOTAKBANK.NS",
    "M&M": "M&M.NS", "HUL": "HINDUNILVR.NS", "Maruti": "MARUTI.NS", "Sun Pharma": "SUNPHARMA.NS",
    "NTPC": "NTPC.NS", "Tata Steel": "TATASTEEL.NS", "Power Grid": "POWERGRID.NS", "Titan": "TITAN.NS"
}

# --- 1. ஆட்டோமேட்டிக் லெவல் கால்குலேட்டர் ஃபங்ஷன் ---
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

# --- 2. வெப்சைட்டில் இருந்து தரவுகளை எடுக்கும் இன்ஜின் ---
@st.cache_data(ttl=300)
def fetch_perfect_ohlc_matrix(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period="1y", interval="1d")
    if df.empty or len(df) < 10:
        return None, 0.0
    try:
        ltp = ticker.basic_info['lastPrice']
    except:
        ltp = df['Close'].iloc[-1]
    
    matrix_data = {}
    matrix_data["Present Daily"] = {"H": df['High'].iloc[-1], "L": df['Low'].iloc[-1], "C": df['Close'].iloc[-1]}
    matrix_data["Previous Daily"] = {"H": df['High'].iloc[-2], "L": df['Low'].iloc[-2], "C": df['Close'].iloc[-2]}
    
    df_weekly = df.resample('W-SUN').agg({'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()
    if len(df_weekly) >= 3:
        matrix_data["Previous Week"] = {"H": df_weekly['High'].iloc[-2], "L": df_weekly['Low'].iloc[-2], "C": df_weekly['Close'].iloc[-2]}
        matrix_data["2 Weeks Ago"] = {"H": df_weekly['High'].iloc[-3], "L": df_weekly['Low'].iloc[-3], "C": df_weekly['Close'].iloc[-3]}
        
    df_monthly = df.resample('ME').agg({'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()
    if len(df_monthly) >= 3:
        matrix_data["Previous Month"] = {"H": df_monthly['High'].iloc[-2], "L": df_monthly['Low'].iloc[-2], "C": df_monthly['Close'].iloc[-2]}
        matrix_data["2 Months Ago"] = {"H": df_monthly['High'].iloc[-3], "L": df_monthly['Low'].iloc[-3], "C": df_monthly['Close'].iloc[-3]}
        
    return matrix_data, round(ltp, 2)

# --- 3. தானியங்கி பிரேக்அவுட் ஸ்கேனர் பட்டன் ---
st.subheader("🎯 1-Click Breakout Radar (Narrow CPR Scanner)")
if st.button("🔍 Scan All Stocks for Breakout"):
    narrow_list = []
    progress_bar = st.progress(0)
    
    for idx, (name, ticker) in enumerate(NIFTY_50_STOCKS.items()):
        web_data, ltp = fetch_perfect_ohlc_matrix(ticker)
        if web_data and "Present Daily" in web_data:
            vals = web_data["Present Daily"]
            pivots = calculate_pivot_levels(vals["H"], vals["L"], vals["C"])
            width_pct = (abs(pivots["TC"] - pivots["BC"]) / ltp) * 100
            
            if width_pct <= 0.16:  # Narrow CPR லிமிட்
                narrow_list.append({"Stock": name, "Ticker": ticker, "LTP": ltp, "CPR Width %": round(width_pct, 2)})
        progress_bar.progress((idx + 1) / len(NIFTY_50_STOCKS))
        
    if narrow_list:
        st.success(f"Shortlisted {len(narrow_list)} Stocks with Narrow CPR for Tomorrow's Breakout!")
        st.dataframe(pd.DataFrame(narrow_list).sort_values(by="CPR Width %"), use_container_width=True)
    else:
        st.warning("No Narrow CPR stocks found today. All stocks are in rangebound structure.")

st.markdown("---")

# --- 4. சிம்பல் செலக்டர் இன்புட் (தனித்தனி அனாலிசிஸ்) ---
st.subheader("🕵️ Detailed Stock Analysis")
selected_symbol_label = st.selectbox("🎯 Choose Stock for Detailed Visuals:", list(NIFTY_50_STOCKS.keys()))
custom_ticker = NIFTY_50_STOCKS[selected_symbol_label]

with st.spinner("Loading Chart Matrix Data..."):
    web_data, market_close_price = fetch_perfect_ohlc_matrix(custom_ticker)

if not web_data:
    st.error("Error loading specific ticker data.")
    st.stop()

# லெவல்களை அடுக்குதல்
view_order = ["2 Months Ago", "Previous Month", "2 Weeks Ago", "Previous Week", "Previous Daily", "Present Daily"]
calculated_rows = []
for tf in view_order:
    vals = web_data.get(tf, {"H": 0, "L": 0, "C": 0})
    pivots = calculate_pivot_levels(vals["H"], vals["L"], vals["C"])
    pivots["Level"] = tf
    calculated_rows.append(pivots)

df = pd.DataFrame(calculated_rows)[["Level", "H4", "H3", "L3", "L4", "TC", "CP", "BC"]]
row_map = df.set_index("Level")

# CPR Width Matrix Analysis பாக்ஸ்
width = abs(row_map.loc["Present Daily", "TC"] - row_map.loc["Present Daily", "BC"])
width_pct = (width / market_close_price) * 100
if width_pct <= 0.15:
    st.error(f"⚡ **NARROW CPR DETECTED ({width_pct:.2f}%)** — Ready for high volume breakout play today!")
else:
    st.info(f"📐 **Average/Wide CPR Structure ({width_pct:.2f}%)** — Best suited for range bound plays.")

# --- 5. 4 விதமான சார்ட் வியூ பட்டன்கள் ---
selected_tab = st.radio("Select View Range:", ["Full Structure View", "Two Month Relationship", "Two Week Relationship", "Two Day & Weekly to Daily View"], horizontal=True)
sub_df = df.copy() if selected_tab == "Full Structure View" else df[df["Level"].isin(["2 Months Ago", "Previous Month"])] if selected_tab == "Two Month Relationship" else df[df["Level"].isin(["2 Weeks Ago", "Previous Week"])] if selected_tab == "Two Week Relationship" else df[df["Level"].isin(["Previous Week", "Previous Daily", "Present Daily"])].reset_index(drop=True)

# --- 6. Matplotlib சார்ட் என்ஜின் ---
def plot_mobile_engine(plot_df, ltp):
    fig, ax = plt.subplots(figsize=(10, 6.5))
    x_positions = range(len(plot_df))
    all_prices = [ltp]
    bar_width = 0.4

    for idx, row in plot_df.iterrows():
        x = x_positions[idx]
        all_prices.extend([row["H4"], row["H3"], row["L3"], row["L4"], row["TC"], row["CP"], row["BC"]])
        ax.hlines(y=row["H4"], xmin=x - bar_width, xmax=x + bar_width, colors="blue", linewidth=2.5)
        ax.text(x, row["H4"] + (ltp*0.0005), f'{row["H4"]:.1f}', ha="center", va="bottom", fontsize=8, color="blue", weight="bold")
        ax.hlines(y=row["H3"], xmin=x - bar_width, xmax=x + bar_width, colors="orange", linewidth=2.5)
        ax.text(x, row["H3"] + (ltp*0.0005), f'{row["H3"]:.1f}', ha="center", va="bottom", fontsize=8, color="red", weight="bold")
        ax.hlines(y=row["L3"], xmin=x - bar_width, xmax=x + bar_width, colors="orange", linestyles="--", linewidth=2)
        ax.text(x, row["L3"] - (ltp*0.0005), f'{row["L3"]:.1f}', ha="center", va="top", fontsize=8, color="red", weight="bold")
        ax.hlines(y=row["L4"], xmin=x - bar_width, xmax=x + bar_width, colors="blue", linestyles="--", linewidth=2)
        ax.text(x, row["L4"] - (ltp*0.0005), f'{row["L4"]:.1f}', ha="center", va="top", fontsize=8, color="blue", weight="bold")
        ax.hlines(y=row["TC"], xmin=x - bar_width, xmax=x + bar_width, colors="purple", linestyles=":", linewidth=1.5)
        ax.hlines(y=row["CP"], xmin=x - bar_width, xmax=x + bar_width, colors="purple", linestyles="-.", linewidth=2)
        ax.hlines(y=row["BC"], xmin=x - bar_width, xmax=x + bar_width, colors="purple", linestyles=":", linewidth=1.5)
        ax.text(x - bar_width, row["CP"], f' CP:{row["CP"]:.1f}', ha="left", va="center", fontsize=7.5, color="purple")
        ax.hlines(y=ltp, xmin=x - bar_width, xmax=x + bar_width, colors="crimson", linestyles="-", linewidth=1.2, alpha=0.7)
        ax.plot(x, ltp, marker="o", color="crimson", markersize=5)
        if idx == len(plot_df) - 1: ax.text(x + bar_width + 0.02, ltp, f'LTP:{ltp}', va="center", ha="left", color="crimson", weight="bold", fontsize=8.5)

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
pdf_path = "Advanced_Multi_Pivot_Report.pdf"
with PdfPages(pdf_path) as pdf:
    for view_name, plot_data in [
        ("Full View Structure", df), 
        ("Two Month Relationship", df[df["Level"].isin(["2 Months Ago", "Previous Month"])]),
        ("Two Week Relationship", df[df["Level"].isin(["2 Weeks Ago", "Previous Week"])]),
        ("Two Day and Weekly to Daily View", df[df["Level"].isin(["Previous Week", "Previous Daily", "Present Daily"])])
    ]:
        fig_pdf = plot_mobile_engine(plot_data.reset_index(drop=True), market_close_price)
        plt.title(f"Market Analysis - {view_name}", fontsize=11, weight="bold", pad=12)
        pdf.savefig(fig_pdf)
        plt.close()

with open(pdf_path, "rb") as pdf_file:
    st.download_button(label="Download Full PDF Matrix Report", data=pdf_file, file_name="Advanced_Multi_Pivot_Report.pdf", mime="application/pdf")
