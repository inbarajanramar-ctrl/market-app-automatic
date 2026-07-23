import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
from matplotlib.backends.backend_pdf import PdfPages

# மொபைலுக்கு ஏற்றவாறு பக்கத்தை அமைத்தல்
st.set_page_config(page_title="Advanced Multi-Pivot Matrix", layout="centered")

st.title("📊 3-Week & 3-Month Real-Time Matrix Engine")
st.write("Live Data Screener & Structure Matrix — New Multi-Frame Forecast Layout")

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

# --- 2. வெப்சைட்டில் இருந்து புதிய பெயரிடலில் தரவுகளை எடுக்கும் இன்ஜின் ---
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
    
    # B. WEEKLY
    df_weekly = df.resample('W-SUN').agg({'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()
    if len(df_weekly) >= 3:
        matrix_data["Forecast Week"] = {"H": df_weekly['High'].iloc[-1], "L": df_weekly['Low'].iloc[-1], "C": df_weekly['Close'].iloc[-1]}
        matrix_data["Current Week"] = {"H": df_weekly['High'].iloc[-2], "L": df_weekly['Low'].iloc[-2], "C": df_weekly['Close'].iloc[-2]}
        matrix_data["Previous Week"] = {"H": df_weekly['High'].iloc[-3], "L": df_weekly['Low'].iloc[-3], "C": df_weekly['Close'].iloc[-3]}
        
    # C. MONTHLY
    df_monthly = df.resample('ME').agg({'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()
    if len(df_monthly) >= 3:
        matrix_data["Forecast Month"] = {"H": df_monthly['High'].iloc[-1], "L": df_monthly['Low'].iloc[-1], "C": df_monthly['Close'].iloc[-1]}
        matrix_data["Current Month"] = {"H": df_monthly['High'].iloc[-2], "L": df_monthly['Low'].iloc[-2], "C": df_monthly['Close'].iloc[-2]}
        matrix_data["Previous Month"] = {"H": df_monthly['High'].iloc[-3], "L": df_monthly['Low'].iloc[-3], "C": df_monthly['Close'].iloc[-3]}
        
    return matrix_data, round(ltp, 2)

# --- Confluence Level Zone (Support: L3, CP | Resistance: H3, CP) ---
def get_confluence_zones(plot_df):
    confluences = []
    required_levels = ["Current Month", "Current Week", "Present Daily"]
    
    if all(lvl in plot_df["Level"].values for lvl in required_levels):
        m_row = plot_df[plot_df["Level"] == "Current Month"].iloc[0]
        w_row = plot_df[plot_df["Level"] == "Current Week"].iloc[0]
        d_row = plot_df[plot_df["Level"] == "Present Daily"].iloc[0]
        
        support_keys = ["L3", "CP"]
        resistance_keys = ["H3", "CP"]
        
        # --- SUPPORT CONFLUENCE (L3 & CP) ---
        for mk in support_keys:
            for wk in support_keys:
                if abs(m_row[mk] - w_row[wk]) / m_row[mk] <= 0.0010:
                    confluences.append(f"🟢 Support Confluence: Current Month {mk} ({m_row[mk]:.1f}) ≈ Current Week {wk} ({w_row[wk]:.1f})")
                    
        for wk in support_keys:
            for dk in support_keys:
                if abs(w_row[wk] - d_row[dk]) / w_row[wk] <= 0.0010:
                    confluences.append(f"🟢 Support Confluence: Current Week {wk} ({w_row[wk]:.1f}) ≈ Pres Daily {dk} ({d_row[dk]:.1f})")
                    
        for mk in support_keys:
            for dk in support_keys:
                if abs(m_row[mk] - d_row[dk]) / m_row[mk] <= 0.0010:
                    confluences.append(f"🟢 Support Confluence: Current Month {mk} ({m_row[mk]:.1f}) ≈ Pres Daily {dk} ({d_row[dk]:.1f})")

        # --- RESISTANCE CONFLUENCE (H3 & CP) ---
        for mk in resistance_keys:
            for wk in resistance_keys:
                if abs(m_row[mk] - w_row[wk]) / m_row[mk] <= 0.0010:
                    confluences.append(f"🔴 Resistance Confluence: Current Month {mk} ({m_row[mk]:.1f}) ≈ Current Week {wk} ({w_row[wk]:.1f})")
                    
        for wk in resistance_keys:
            for dk in resistance_keys:
                if abs(w_row[wk] - d_row[dk]) / w_row[wk] <= 0.0010:
                    confluences.append(f"🔴 Resistance Confluence: Current Week {wk} ({w_row[wk]:.1f}) ≈ Pres Daily {dk} ({d_row[dk]:.1f})")
                    
        for mk in resistance_keys:
            for dk in resistance_keys:
                if abs(m_row[mk] - d_row[dk]) / m_row[mk] <= 0.0010:
                    confluences.append(f"🔴 Resistance Confluence: Current Month {mk} ({m_row[mk]:.1f}) ≈ Pres Daily {dk} ({d_row[dk]:.1f})")
                    
    return list(set(confluences))

# --- 🔔 AUTOMATED NIFTY 50 CPR ALERT (<= 0.005%) ---
nifty_data, nifty_ltp = fetch_perfect_ohlc_matrix("^NSEI")
if nifty_data and "Present Daily" in nifty_data:
    p_vals = nifty_data["Present Daily"]
    p_pivots = calculate_pivot_levels(p_vals["H"], p_vals["L"], p_vals["C"])
    nifty_cpr_width = (abs(p_pivots["TC"] - p_pivots["BC"]) / nifty_ltp) * 100

    if nifty_cpr_width <= 0.005:
        st.error(
            f"🚨 **NIFTY 50 NARROW CPR ALERT:** The Nifty Index CPR width is **{nifty_cpr_width:.4f}%** "
            f"(<= 0.005%). High probability of a sharp, trending breakout move!"
        )
    elif nifty_cpr_width <= 0.05:
        st.warning(
            f"⚠️ **NIFTY NARROW CPR:** Nifty 50 Index CPR width is currently **{nifty_cpr_width:.3f}%**."
        )

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
                narrow_list.append({"Stock": name, "Ticker": ticker, "LTP": ltp, "CPR Width %": round(width_pct, 4)})
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

# லெவல்களை அடுக்குதல்
view_order = ["Previous Month", "Current Month", "Forecast Month", "Previous Week", "Current Week", "Forecast Week", "Previous Daily", "Present Daily"]
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

m_rel1 = detect_pivot_relationship(row_map.loc["Previous Month", "TC"], row_map.loc["Previous Month", "BC"], row_map.loc["Current Month", "TC"], row_map.loc["Current Month", "BC"])
m_rel2 = detect_pivot_relationship(row_map.loc["Current Month", "TC"], row_map.loc["Current Month", "BC"], row_map.loc["Forecast Month", "TC"], row_map.loc["Forecast Month", "BC"])

w_rel1 = detect_pivot_relationship(row_map.loc["Previous Week", "TC"], row_map.loc["Previous Week", "BC"], row_map.loc["Current Week", "TC"], row_map.loc["Current Week", "BC"])
w_rel2 = detect_pivot_relationship(row_map.loc["Current Week", "TC"], row_map.loc["Current Week", "BC"], row_map.loc["Forecast Week", "TC"], row_map.loc["Forecast Week", "BC"])

st.subheader("🔍 3-Tier Multi-Timeframe Analysis")
st.warning(f"**🦅 3 Months Matrix Trend:** {m_rel1} ➔ Then {m_rel2}")
st.success(f"**⏳ 3 Weeks Matrix Trend:** {w_rel1} ➔ Then {w_rel2}")
st.info(f"**📅 Day-on-Day Trend:** {detect_pivot_relationship(row_map.loc['Previous Daily', 'TC'], row_map.loc['Previous Daily', 'BC'], row_map.loc['Present Daily', 'TC'], row_map.loc['Present Daily', 'BC'])}")

# --- 6. 5 விதமான மாஸ் சார்ட் வியூ பட்டன்கள் ---
st.subheader("🎯 View Perspective")
selected_tab = st.radio("Select View Range:", [
    "Full 8-Level View", 
    "Special Request View (CM, CW, PD)", 
    "3 Month Structural View", 
    "3 Week Structural View", 
    "Tactical Weekly to Daily View"
], horizontal=True)

if selected_tab == "Full 8-Level View":
    sub_df = df.copy()
elif selected_tab == "Special Request View (CM, CW, PD)":
    sub_df = df[df["Level"].isin(["Current Month", "Current Week", "Present Daily"])].reset_index(drop=True)
elif selected_tab == "3 Month Structural View":
    sub_df = df[df["Level"].isin(["Previous Month", "Current Month", "Forecast Month"])].reset_index(drop=True)
elif selected_tab == "3 Week Structural View":
    sub_df = df[df["Level"].isin(["Previous Week", "Current Week", "Forecast Week"])].reset_index(drop=True)
else:
    sub_df = df[df["Level"].isin(["Forecast Week", "Previous Daily", "Present Daily"])].reset_index(drop=True)

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

    # CM, CW, PD Target Confluence Shading (Support: Green | Resistance: Red)
    levels_in_plot = plot_df["Level"].values
    if "Current Month" in levels_in_plot and "Current Week" in levels_in_plot and "Present Daily" in levels_in_plot:
        m_row = plot_df[plot_df["Level"] == "Current Month"].iloc[0]
        w_row = plot_df[plot_df["Level"] == "Current Week"].iloc[0]
        d_row = plot_df[plot_df["Level"] == "Present Daily"].iloc[0]
        
        support_keys = ["L3", "CP"]
        resistance_keys = ["H3", "CP"]
        
        # Support Shading (Green)
        for mk in support_keys:
            for wk in support_keys:
                for dk in support_keys:
                    if abs(m_row[mk] - w_row[wk]) / m_row[mk] <= 0.0010 and abs(w_row[wk] - d_row[dk]) / w_row[wk] <= 0.0010:
                        y_min = min(m_row[mk], w_row[wk], d_row[dk])
                        y_max = max(m_row[mk], w_row[wk], d_row[dk])
                        ax.axhspan(y_min - (ltp*0.0002), y_max + (ltp*0.0002), color="#00ff00", alpha=0.2)

        # Resistance Shading (Red)
        for mk in resistance_keys:
            for wk in resistance_keys:
                for dk in resistance_keys:
                    if abs(m_row[mk] - w_row[wk]) / m_row[mk] <= 0.0010 and abs(w_row[wk] - d_row[dk]) / w_row[wk] <= 0.0010:
                        y_min = min(m_row[mk], w_row[wk], d_row[dk])
                        y_max = max(m_row[mk], w_row[wk], d_row[dk])
                        ax.axhspan(y_min - (ltp*0.0002), y_max + (ltp*0.0002), color="#ff0000", alpha=0.2)

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

# --- 8. ஆக்டிவ் டேட்டா டேபிள் UI & கன்ஃப்ளூயன்ஸ் காட்சி ---
st.subheader("📋 Active Data Table")
st.dataframe(df.set_index("Level"), use_container_width=True)

st.subheader("🎯 Targeted Support (L3, CP) & Resistance (H3, CP) Confluence Zones")
active_confluences = get_confluence_zones(df)
if active_confluences:
    for conf in active_confluences:
        st.write(conf)
else:
    st.write("No strong confluences detected for Support (L3, CP) or Resistance (H3, CP) within 0.1% threshold.")

# --- 9. மேம்படுத்தப்பட்ட PDF ஜெனரேட்டர் ---
st.subheader("📥 Download Analysis Report")
pdf_path = "Advanced_3_Tier_Pivot_Report.pdf"
with PdfPages(pdf_path) as pdf:
    # --- PAGE 1: Full 8-Level Structure View ---
    fig1 = plot_mobile_engine(df, market_close_price)
    plt.title("Market Analysis - Full 8-Level Structure View", fontsize=11, weight="bold", pad=12)
    pdf.savefig(fig1)
    plt.close()
    
    # --- PAGE 2: Transposed Active Data Table Only ---
    fig2, ax2 = plt.subplots(figsize=(11, 6.5))
    ax2.axis('off')
    
    df_transposed = df.set_index("Level").T.reset_index()
    df_transposed = df_transposed.rename(columns={'index': 'Pivot Level / Frame'})
    
    table = ax2.table(cellText=df_transposed.values, colLabels=df_transposed.columns, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    for cell in table.get_celld().values():
        cell.set_fontsize(7)
    table.scale(1.0, 1.8)
    
    plt.title("Active Data Table (Transposed Matrix Layout)", fontsize=11, weight="bold", pad=12)
    pdf.savefig(fig2)
    plt.close()

    # --- PAGE 3: Detected Confluence Zones Page ---
    fig_conf, ax_conf = plt.subplots(figsize=(11, 6.5))
    ax_conf.axis('off')
    pdf_conf_text = "🎯 Support (L3, CP) & Resistance (H3, CP) Confluences:\n\n" + ("\n\n".join(active_confluences) if active_confluences else "No confluences found within 0.1% threshold.")
    plt.figtext(0.1, 0.5, pdf_conf_text, fontsize=9.5, color="purple", weight="bold", va="center")
    plt.title("Detected Confluence Zones", fontsize=11, weight="bold", pad=12)
    pdf.savefig(fig_conf)
    plt.close()
    
    # --- PAGE 4: Special Request View ---
    sp_df = df[df["Level"].isin(["Current Month", "Current Week", "Present Daily"])].reset_index(drop=True)
    fig3 = plot_mobile_engine(sp_df, market_close_price)
    plt.title("Market Analysis - Special Structural View (CM, CW, PD)", fontsize=11, weight="bold", pad=12)
    pdf.savefig(fig3)
    plt.close()
    
    # --- PAGE 5: 3 Month Structural View ---
    m_df = df[df["Level"].isin(["Previous Month", "Current Month", "Forecast Month"])].reset_index(drop=True)
    fig4 = plot_mobile_engine(m_df, market_close_price)
    plt.title("Market Analysis - 3 Month Structural View", fontsize=11, weight="bold", pad=12)
    pdf.savefig(fig4)
    plt.close()
    
    # --- PAGE 6: 3 Week Structural View ---
    w_df = df[df["Level"].isin(["Previous Week", "Current Week", "Forecast Week"])].reset_index(drop=True)
    fig5 = plot_mobile_engine(w_df, market_close_price)
    plt.title("Market Analysis - 3 Week Structural View", fontsize=11, weight="bold", pad=12)
    pdf.savefig(fig5)
    plt.close()
    
    # --- PAGE 7: Tactical Weekly to Daily View ---
    d_df = df[df["Level"].isin(["Forecast Week", "Previous Daily", "Present Daily"])].reset_index(drop=True)
    fig6 = plot_mobile_engine(d_df, market_close_price)
    plt.title("Market Analysis - Tactical Weekly to Daily View", fontsize=11, weight="bold", pad=12)
    pdf.savefig(fig6)
    plt.close()

with open(pdf_path, "rb") as pdf_file:
    st.download_button(label="Download Full 3-Tier PDF Report", data=pdf_file, file_name="Advanced_3_Tier_Pivot_Report.pdf", mime="application/pdf")
