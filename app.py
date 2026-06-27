import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
from matplotlib.backends.backend_pdf import PdfPages

# மொபைலுக்கு ஏற்றவாறு பக்கத்தை அமைத்தல்
st.set_page_config(page_title="Advanced Multi-Pivot Matrix", layout="centered")

st.title("📊 3-Week & 3-Month Real-Time Matrix Engine")
st.write("Live Data Screener & Structure Matrix — No Waiting for Weekend/Month-End")

# --- Nifty & Sensex பங்குகளின் முழுமையான பட்டியல் ---
NIFTY_AND_SENSEX_STOCKS = {
    "Nifty 50 Index": "^NSEI", "Bank Nifty Index": "^NSEBANK", "Sensex Index": "^BSESN",
    "Reliance Industries": "RELIANCE.NS", "TCS": "TCS.NS", "HDFC Bank": "HDFCBANK.NS", 
    "ICICI Bank": "ICICIBANK.NS", "Infosys": "INFY.NS", "SBI": "SBIN.NS", 
    "Bharti Airtel": "BHARTIARTL.NS", "L&T": "LT.NS", "ITC": "ITC.NS", 
    "Tata Motors": "TATAMOTORS.NS", "Axis Bank": "AXISBANK.NS", "Kotak Mahindra Bank": "KOTAKBANK.NS",
    "M&M": "M&M.NS", "Hindustan Unilever": "HINDUNILVR.NS", "Maruti Suzuki": "MARUTI.NS", 
    "Sun Pharma": "SUNPHARMA.NS", "NTPC": "NTPC.NS", "Tata Steel": "TATASTEEL.NS", 
    "Power Grid": "POWERGRID.NS", "Titan Company": "TITAN.NS", "HCL Tech": "HCLTECH.NS",
    "Adani Ports": "ADANIPORTS.NS", "Adani Enterprises": "ADANIENT.NS", "Asian Paints": "ASIANPAINT.NS",
    "Bajaj Auto": "BAJAJ-AUTO.NS", "Bajaj Finance": "BAJFINANCE.NS", "Bajaj Finserv": "BAJAJFINSV.NS",
    "BPCL": "BPCL.NS", "Cipla": "CIPLA.NS", "Coal India": "COALINDIA.NS", 
    "Divi's Lab": "DIVISLAB.NS", "Dr. Reddy's": "DRREDDY.NS", "Eicher Motors": "EICHERMOT.NS",
    "Grasim Industries": "GRASIM.NS", "Hindalco": "HINDALCO.NS", "JSW Steel": "JSWSTEEL.NS",
    "LTIMindtree": "LTIM.NS", "Nestle India": "NESTLEIND.NS", "ONGC": "ONGC.NS",
    "Apollo Hospitals": "APOLLOHOSP.NS", "Britannia": "BRITANNIA.NS", "IndusInd Bank": "INDUSINDBK.NS",
    "Shriram Finance": "SHRIRAMFIN.NS", "Trent": "TRENT.NS", "UltraTech Cement": "ULTRACEMCO.NS",
    "Wipro": "WIPRO.NS", "Tata Consumer Products": "TATACONSUM.NS", "Jio Financial Services": "JIOFIN.NS"
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

# --- 2. வெப்சைட்டில் இருந்து 3 வார மற்றும் 3 மாத தரவுகளை எடுக்கும் புதிய இன்ஜின் ---
@st.cache_data(ttl=120)
def fetch_perfect_ohlc_matrix(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period="2y", interval="1d")
    if df.empty or len(df) < 60:
        return None, 0.0
    try:
        ltp = ticker.basic_info['lastPrice']
    except:
        ltp = df['Close'].iloc[-1]
    
    matrix_data = {}
    
    # A. DAILY
    matrix_data["Present Daily"] = {"H": df['High'].iloc[-1], "L": df['Low'].iloc[-1], "C": df['Close'].iloc[-1]}
    matrix_data["Previous Daily"] = {"H": df['High'].iloc[-2], "L": df['Low'].iloc[-2], "C": df['Close'].iloc[-2]}
    
    # B. WEEKLY (நடப்பு வாரம் உட்பட மொத்தம் 3 வாரங்கள்)
    df_weekly = df.resample('W-SUN').agg({'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()
    if len(df_weekly) >= 3:
        matrix_data["Present Weekly"] = {"H": df_weekly['High'].iloc[-1], "L": df_weekly['Low'].iloc[-1], "C": df_weekly['Close'].iloc[-1]}
        matrix_data["Previous Week"] = {"H": df_weekly['High'].iloc[-2], "L": df_weekly['Low'].iloc[-2], "C": df_weekly['Close'].iloc[-2]}
        matrix_data["2 Weeks Ago"] = {"H": df_weekly['High'].iloc[-3], "L": df_weekly['Low'].iloc[-3], "C": df_weekly['Close'].iloc[-3]}
        
    # C. MONTHLY (நடப்பு மாதம் உட்பட மொத்தம் 3 மாதங்கள்)
    df_monthly = df.resample('ME').agg({'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()
    if len(df_monthly) >= 3:
        matrix_data["Present Monthly"] = {"H": df_monthly['High'].iloc[-1], "L": df_monthly['Low'].iloc[-1], "C": df_monthly['Close'].iloc[-1]}
        matrix_data["Previous Month"] = {"H": df_monthly['High'].iloc[-2], "L": df_monthly['Low'].iloc[-2], "C": df_monthly['Close'].iloc[-2]}
        matrix_data["2 Months Ago"] = {"H": df_monthly['High'].iloc[-3], "L": df_monthly['Low'].iloc[-3], "C": df_monthly['Close'].iloc[-3]}
        
    return matrix_data, round(ltp, 2)

# --- 3. தானியங்கி பிரேக்அவுட் ஸ்கேனர் பட்டன் ---
st.subheader("🎯 1-Click Breakout Radar (ALL Nifty & Sensex Stocks)")
if st.button("🔍 Scan All Stocks for Breakout"):
    narrow_list = []
    progress_bar = st.progress(0)
    
    for idx, (name, ticker) in enumerate(NIFTY_AND_SENSEX_STOCKS.items()):
        web_data, ltp = fetch_perfect_ohlc_matrix(ticker)
        if web_data and "Present Daily" in web_data:
            vals = web_data["Present Daily"]
            pivots = calculate_pivot_levels(vals["H"], vals["L"], vals["C"])
            width_pct = (abs(pivots["TC"] - pivots["BC"]) / ltp) * 100
            
            if width_pct <= 0.16:
                narrow_list.append({"Stock": name, "Ticker": ticker, "LTP": ltp, "CPR Width %": round(width_pct, 2)})
        progress_bar.progress((idx + 1) / len(NIFTY_AND_SENSEX_STOCKS))
        
    if narrow_list:
        st.success(f"Shortlisted {len(narrow_list)} Stocks with Narrow CPR for Tomorrow's Breakout!")
        st.dataframe(pd.DataFrame(narrow_list).sort_values(by="CPR Width %"), use_container_width=True)
    else:
        st.warning("No Narrow CPR stocks found today.")

st.markdown("---")

# --- 4. சிம்பல் செலக்டர் இன்புட் ---
st.subheader("🕵️ Detailed Stock Analysis")
selected_symbol_label = st.selectbox("🎯 Choose Stock for Detailed Visuals:", list(NIFTY_AND_SENSEX_STOCKS.keys()))
custom_ticker = NIFTY_AND_SENSEX_STOCKS[selected_symbol_label]

with st.spinner("Loading Chart Matrix Data..."):
    web_data, market_close_price = fetch_perfect_ohlc_matrix(custom_ticker)

if not web_data:
    st.error("Error loading specific ticker data.")
    st.stop()

# லெவல்களை அடுக்குதல் (3 வாரங்கள் மற்றும் 3 மாதங்கள் முழுமையாக அடுக்கப்பட்டுள்ளது)
view_order = ["2 Months Ago", "Previous Month", "Present Monthly", "2 Weeks Ago", "Previous Week", "Present Weekly", "Previous Daily", "Present Daily"]
calculated_rows = []
for tf in view_order:
    vals = web_data.get(tf, {"H": 0, "L": 0, "C": 0})
    pivots = calculate_pivot_levels(vals["H"], vals["L"], vals["C"])
    pivots["Level"] = tf
    calculated_rows.append(pivots)

df = pd.DataFrame(calculated_rows)[["Level", "H4", "H3", "L3", "L4", "TC", "CP", "BC"]]
row_map = df.set_index("Level")

# --- 5. 3-வாரம் மற்றும் 3-மாத விரிவான டிரெண்ட் அனாலிசிஸ் ---
def detect_pivot_relationship(prev_tc, prev_bc, curr_tc, curr_bc):
    prev_high, prev_low = max(prev_tc, prev_bc), min(prev_tc, prev_bc)
    curr_high, curr_low = max(curr_tc, curr_bc), min(curr_bc, curr_tc)
    if curr_low > prev_high: return "🟢 Higher Value (Strongly Bullish)"
    elif curr_high < prev_low: return "🔴 Lower Value (Strongly Bearish)"
    elif curr_high < prev_high and curr_low > prev_low: return "🟣 Inside Value (Breakout Imminent)"
    elif curr_high > prev_high and curr_low < prev_low: return "🔵 Outside Value (Sideways)"
    elif curr_high > prev_high and curr_low >= prev_low: return "🟡 Overlapping Higher (Bullish)"
    elif curr_low < prev_low and curr_high <= prev_high: return "🟠 Overlapping Lower (Bearish)"
    else: return "⚪ Unchanged"

# 3 Months Relationship Analysis (2 Months Ago -> Prev Month -> Pres Monthly)
m_rel1 = detect_pivot_relationship(row_map.loc["2 Months Ago", "TC"], row_map.loc["2 Months Ago", "BC"], row_map.loc["Previous Month", "TC"], row_map.loc["Previous Month", "BC"])
m_rel2 = detect_pivot_relationship(row_map.loc["Previous Month", "TC"], row_map.loc["Previous Month", "BC"], row_map.loc["Present Monthly", "TC"], row_map.loc["Present Monthly", "BC"])

# 3 Weeks Relationship Analysis (2 Weeks Ago -> Prev Week -> Pres Weekly)
w_rel1 = detect_pivot_relationship(row_map.loc["2 Weeks Ago", "TC"], row_map.loc["2 Weeks Ago", "BC"], row_map.loc["Previous Week", "TC"], row_map.loc["Previous Week", "BC"])
w_rel2 = detect_pivot_relationship(row_map.loc["Previous Week", "TC"], row_map.loc["Previous Week", "BC"], row_map.loc["Present Weekly", "TC"], row_map.loc["Present Weekly", "BC"])

st.subheader("🔍 3-Tier Multi-Timeframe Analysis")
st.warning(f"**🦅 3 Months Matrix Trend:** {m_rel1} ➔ Then {m_rel2}")
st.success(f"**⏳ 3 Weeks Matrix Trend:** {w_rel1} ➔ Then {w_rel2}")
st.info(f"**📅 Day-on-Day Trend:** {detect_pivot_relationship(row_map.loc["Previous Daily", "TC"], row_map.loc["Previous Daily", "BC"], row_map.loc["Present Daily", "TC"], row_map.loc["Present Daily", "BC"])}")

# --- 6. 4 விதமான மாஸ் சார்ட் வியூ பட்டன்கள் ---
st.subheader("🎯 View Perspective")
selected_tab = st.radio("Select View Range:", ["Full 8-Level View", "3 Month Structural View", "3 Week Structural View", "Tactical Weekly to Daily View"], horizontal=True)

if selected_tab == "Full 8-Level View":
    sub_df = df.copy()
elif selected_tab == "3 Month Structural View":
    sub_df = df[df["Level"].isin(["2 Months Ago", "Previous Month", "Present Monthly"])].reset_index(drop=True)
elif selected_tab == "3 Week Structural View":
    sub_df = df[df["Level"].isin(["2 Weeks Ago", "Previous Week", "Present Weekly"])].reset_index(drop=True)
else:
    sub_df = df[df["Level"].isin(["Present Weekly", "Previous Daily", "Present Daily"])].reset_index(drop=True)

# --- 7. Matplotlib சார்ட் என்ஜின் ---
def plot_mobile_engine(plot_df, ltp):
    fig, ax = plt.subplots(figsize=(11, 6.5))
    x_positions = range(len(plot_df))
    all_prices = [ltp]
    bar_width = 0.4

    for idx, row in plot_df.iterrows():
        x = x_positions[idx]
        all_prices.extend([row["H4"], row["H3"], row["L3"], row["L4"], row["TC"], row["CP"], row["BC"]])
        
        # Camarilla Lines
        ax.hlines(y=row["H4"], xmin=x - bar_width, xmax=x + bar_width, colors="blue", linewidth=2.5)
        ax.text(x, row["H4"] + (ltp*0.0005), f'{row["H4"]:.1f}', ha="center", va="bottom", fontsize=7.5, color="blue", weight="bold")
        ax.hlines(y=row["H3"], xmin=x - bar_width, xmax=x + bar_width, colors="orange", linewidth=2.5)
        ax.text(x, row["H3"] + (ltp*0.0005), f'{row["H3"]:.1f}', ha="center", va="bottom", fontsize=7.5, color="red", weight="bold")
        ax.hlines(y=row["L3"], xmin=x - bar_width, xmax=x + bar_width, colors="orange", linestyles="--", linewidth=2)
        ax.text(x, row["L3"] - (ltp*0.0005), f'{row["L3"]:.1f}', ha="center", va="top", fontsize=7.5, color="red", weight="bold")
        ax.hlines(y=row["L4"], xmin=x - bar_width, xmax=x + bar_width, colors="blue", linestyles="--", linewidth=2)
        ax.text(x, row["L4"] - (ltp*0.0005), f'{row["L4"]:.1f}', ha="center", va="top", fontsize=7.5, color="blue", weight="bold")
        
        # CPR Lines
        ax.hlines(y=row["TC"], xmin=x - bar_width, xmax=x + bar_width, colors="purple", linestyles=":", linewidth=1.5)
        ax.hlines(y=row["CP"], xmin=x - bar_width, xmax=x + bar_width, colors="purple", linestyles="-.", linewidth=2)
        ax.hlines(y=row["BC"], xmin=x - bar_width, xmax=x + bar_width, colors="purple", linestyles=":", linewidth=1.5)
        ax.text(x - bar_width, row["CP"], f' CP:{row["CP"]:.1f}', ha="left", va="center", fontsize=7, color="purple")
        
        # LTP Line
        ax.hlines(y=ltp, xmin=x - bar_width, xmax=x + bar_width, colors="crimson", linestyles="-", linewidth=1.2, alpha=0.7)
        ax.plot(x, ltp, marker="o", color="crimson", markersize=5)
        if idx == len(plot_df) - 1: 
            ax.text(x + bar_width + 0.02, ltp, f'LTP:{ltp}', va="center", ha="left", color="crimson", weight="bold", fontsize=8.5)

    ax.set_xticks(x_positions)
    ax.set_xticklabels(plot_df["Level"], fontsize=8.5, weight="bold", rotation=15)
    ax.grid(True, linestyle=":", alpha=0.4)
    ax.set_xlim(-0.5, len(plot_df) - 0.5)
    
    min_p, max_p = min(all_prices), max(all_prices)
    padding = (max_p - min_p) * 0.08
    ax.set_ylim(min_p - padding, max_p + padding)
    plt.tight_layout()
    return fig

st.pyplot(plot_mobile_engine(sub_df, market_close_price))

# --- 8. ஆக்டிவ் டேட்டா டேபிள் மற்றும் PDF டவுன்லோடு ---
st.subheader("📋 Active Data Table")
st.dataframe(df.set_index("Level"), use_container_width=True)

st.subheader("📥 Download Analysis Report")
pdf_path = "Advanced_3_Tier_Pivot_Report.pdf"
with PdfPages(pdf_path) as pdf:
    for view_name, plot_data in [
        ("Full 8-Level Structure View", df), 
        ("3 Month Structural View", df[df["Level"].isin(["2 Months Ago", "Previous Month", "Present Monthly"])]),
        ("3 Week Structural View", df[df["Level"].isin(["2 Weeks Ago", "Previous Week", "Present Weekly"])]),
        ("Tactical Weekly to Daily View", df[df["Level"].isin(["Present Weekly", "Previous Daily", "Present Daily"])])
    ]:
        fig_pdf = plot_mobile_engine(plot_data.reset_index(drop=True), market_close_price)
        plt.title(f"Market Analysis - {view_name}", fontsize=11, weight="bold", pad=12)
        pdf.savefig(fig_pdf)
        plt.close()

with open(pdf_path, "rb") as pdf_file:
    st.download_button(label="Download Full 3-Tier PDF Report", data=pdf_file, file_name="Advanced_3_Tier_Pivot_Report.pdf", mime="application/pdf")
