import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
from matplotlib.backends.backend_pdf import PdfPages

# மொபைலுக்கு ஏற்றவாறு பக்கத்தை அமைத்தல்
st.set_page_config(page_title="Advanced Multi-Pivot Matrix", layout="centered")

st.title("📊 3-Week & 3-Month Real-Time Matrix Engine")
st.write("Live Data Screener & Structure Matrix — New Multi-Frame Forecast Layout")

# --- Nifty & Sensex பங்குகளின் பட்டியல் ---
NIFTY_AND_SENSEX_STOCKS = {
    "Nifty 50 Index": "^NSEI", "Bank Nifty Index": "^NSEBANK", "Sensex Index": "^BSESN",
    "Reliance Industries": "RELIANCE.NS", "TCS": "TCS.NS", "HDFC Bank": "HDFCBANK.NS"
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
    
    # B. WEEKLY (புதிய மாற்றுப் பெயர்களுடன்)
    df_weekly = df.resample('W-SUN').agg({'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()
    if len(df_weekly) >= 3:
        matrix_data["Forecast Week"] = {"H": df_weekly['High'].iloc[-1], "L": df_weekly['Low'].iloc[-1], "C": df_weekly['Close'].iloc[-1]}
        matrix_data["Current Week"] = {"H": df_weekly['High'].iloc[-2], "L": df_weekly['Low'].iloc[-2], "C": df_weekly['Close'].iloc[-2]}
        matrix_data["Previous Week"] = {"H": df_weekly['High'].iloc[-3], "L": df_weekly['Low'].iloc[-3], "C": df_weekly['Close'].iloc[-3]}
        
    # C. MONTHLY (புதிய மாற்றுப் பெயர்களுடன்)
    df_monthly = df.resample('ME').agg({'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()
    if len(df_monthly) >= 3:
        matrix_data["Forecast Month"] = {"H": df_monthly['High'].iloc[-1], "L": df_monthly['Low'].iloc[-1], "C": df_monthly['Close'].iloc[-1]}
        matrix_data["Current Month"] = {"H": df_monthly['High'].iloc[-2], "L": df_monthly['Low'].iloc[-2], "C": df_monthly['Close'].iloc[-2]}
        matrix_data["Previous Month"] = {"H": df_monthly['High'].iloc[-3], "L": df_monthly['Low'].iloc[-3], "C": df_monthly['Close'].iloc[-3]}
        
    return matrix_data, round(ltp, 2)

# --- Confluence Level Zone கண்டறியும் மேம்படுத்தப்பட்ட லாஜிக் (New Names Applied) ---
def get_confluence_zones(plot_df):
    confluences = []
    required_levels = ["Current Month", "Current Week", "Present Daily"]
    
    if all(lvl in plot_df["Level"].values for lvl in required_levels):
        m_row = plot_df[plot_df["Level"] == "Current Month"].iloc[0]
        w_row = plot_df[plot_df["Level"] == "Current Week"].iloc[0]
        d_row = plot_df[plot_df["Level"] == "Present Daily"].iloc[0]
        
        all_keys = ["H4", "H3", "L3", "L4", "TC", "CP", "BC"]
        
        for mk in all_keys:
            for wk in all_keys:
                if abs(m_row[mk] - w_row[wk]) / m_row[mk] <= 0.0015:
                    confluences.append(f"🔥 Confluence: Current Month {mk} ({m_row[mk]:.1f}) ≈ Current Week {wk} ({w_row[wk]:.1f})")
        for wk in all_keys:
            for dk in all_keys:
                if abs(w_row[wk] - d_row[dk]) / w_row[wk] <= 0.0015:
                    confluences.append(f"🔥 Confluence: Current Week {wk} ({w_row[wk]:.1f}) ≈ Pres Daily {dk} ({d_row[dk]:.1f})")
        for mk in all_keys:
            for dk in all_keys:
                if abs(m_row[mk] - d_row[dk]) / m_row[mk] <= 0.0015:
                    confluences.append(f"🔥 Confluence: Current Month {mk} ({m_row[mk]:.1f}) ≈ Pres Daily {dk} ({d_row[dk]:.1f})")
                    
    return list(set(confluences))

# --- 3. சிம்பல் செலக்டர் இன்புட் ---
st.subheader("🕵️ Detailed Stock Analysis")
selected_symbol_label = st.selectbox("🎯 Choose Stock for Detailed Visuals:", list(NIFTY_AND_SENSEX_STOCKS.keys()))
custom_ticker = NIFTY_AND_SENSEX_STOCKS[selected_symbol_label]

with st.spinner("Loading Chart Matrix Data..."):
    web_data, market_close_price = fetch_perfect_ohlc_matrix(custom_ticker)

if not web_data:
    st.error("Error loading specific ticker data.")
    st.stop()

# புதிய மாற்றுப் பெயர்களின்படி வரிசைப்படுத்துதல்
view_order = ["Previous Month", "Current Month", "Forecast Month", "Previous Week", "Current Week", "Forecast Week", "Previous Daily", "Present Daily"]
calculated_rows = []
for tf in view_order:
    vals = web_data.get(tf, {"H": 0, "L": 0, "C": 0})
    pivots = calculate_pivot_levels(vals["H"], vals["L"], vals["C"])
    pivots["Level"] = tf
    calculated_rows.append(pivots)

df = pd.DataFrame(calculated_rows)[["Level", "H4", "H3", "L3", "L4", "TC", "CP", "BC"]]

# --- 4. Matplotlib சார்ட் என்ஜின் ---
def plot_mobile_engine(plot_df, ltp):
    fig, ax = plt.subplots(figsize=(11, 6.5))
    x_positions = range(len(plot_df))
    all_prices = [ltp]
    bar_width = 0.4

    for idx, row in plot_df.iterrows():
        x = x_positions[idx]
        all_prices.extend([row["H4"], row["H3"], row["L3"], row["L4"], row["TC"], row["CP"], row["BC"]])
        
        ax.hlines(y=row["H4"], xmin=x - bar_width, xmax=x + bar_width, colors="blue", linewidth=2.5)
        ax.text(x, row["H4"] + (ltp*0.0005), f'{row["H4"]:.1f}', ha="center", va="bottom", fontsize=7.5, color="blue", weight="bold")
        ax.hlines(y=row["H3"], xmin=x - bar_width, xmax=x + bar_width, colors="orange", linewidth=2.5)
        ax.text(x, row["H3"] + (ltp*0.0005), f'{row["H3"]:.1f}', ha="center", va="bottom", fontsize=7.5, color="red", weight="bold")
        ax.hlines(y=row["L3"], xmin=x - bar_width, xmax=x + bar_width, colors="orange", linestyles="--", linewidth=2)
        ax.text(x, row["L3"] - (ltp*0.0005), f'{row["L3"]:.1f}', ha="center", va="top", fontsize=7.5, color="red", weight="bold")
        ax.hlines(y=row["L4"], xmin=x - bar_width, xmax=x + bar_width, colors="blue", linestyles="--", linewidth=2)
        ax.text(x, row["L4"] - (ltp*0.0005), f'{row["L4"]:.1f}', ha="center", va="top", fontsize=7.5, color="blue", weight="bold")
        
        ax.hlines(y=row["TC"], xmin=x - bar_width, xmax=x + bar_width, colors="purple", linestyles=":", linewidth=1.5)
        ax.hlines(y=row["CP"], xmin=x - bar_width, xmax=x + bar_width, colors="purple", linestyles="-.", linewidth=2)
        ax.hlines(y=row["BC"], xmin=x - bar_width, xmax=x + bar_width, colors="purple", linestyles=":", linewidth=1.5)
        ax.text(x - bar_width, row["CP"], f' CP:{row["CP"]:.1f}', ha="left", va="center", fontsize=7, color="purple")
        
        ax.hlines(y=ltp, xmin=x - bar_width, xmax=x + bar_width, colors="crimson", linestyles="-", linewidth=1.2, alpha=0.7)
        ax.plot(x, ltp, marker="o", color="crimson", markersize=5)

    ax.set_xticks(x_positions)
    ax.set_xticklabels(plot_df["Level"], fontsize=8.5, weight="bold", rotation=15)
    ax.grid(True, linestyle=":", alpha=0.4)
    ax.set_xlim(-0.5, len(plot_df) - 0.5)
    
    min_p, max_p = min(all_prices), max(all_prices)
    padding = (max_p - min_p) * 0.08
    ax.set_ylim(min_p - padding, max_p + padding)
    plt.tight_layout()
    return fig

st.pyplot(plot_mobile_engine(df, market_close_price))

# --- 5. ஆக்டிவ் டேட்டா டேபிள் UI ---
st.subheader("📋 Active Data Table")
st.dataframe(df.set_index("Level"), use_container_width=True)

active_confluences = get_confluence_zones(df)

# --- 6. திருத்தப்பட்ட மற்றும் மேம்படுத்தப்பட்ட PDF ஜெனரேட்டர் (No Font Error) ---
st.subheader("📥 Download Analysis Report")
pdf_path = "Advanced_3_Tier_Pivot_Report.pdf"
with PdfPages(pdf_path) as pdf:
    # PAGE 1: Full 8-Level View
    fig1 = plot_mobile_engine(df, market_close_price)
    plt.title("Market Analysis - Full Structure View", fontsize=11, weight="bold", pad=12)
    pdf.savefig(fig1)
    plt.close()
    
    # PAGE 2: Transposed Table (Bug Fixed)
    fig2, ax2 = plt.subplots(figsize=(11, 6.5))
    ax2.axis('off')
    df_transposed = df.set_index("Level").T.reset_index()
    df_transposed = df_transposed.rename(columns={'index': 'Pivot Level / Frame'})
    
    table = ax2.table(cellText=df_transposed.values, colLabels=df_transposed.columns, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    # Property assignment பக் இல்லாமல் செய்ய ஃபான்ட் அளவை லூப்பில் மாற்றுகிறோம்
    for cell in table.get_celld().values():
        cell.set_fontsize(7)
    table.scale(1.0, 1.8)
    
    pdf_conf_text = "🎯 Detected Confluence Levels (CM ➔ CW ➔ PD):\n" + ("\n".join(active_confluences) if active_confluences else "No confluences found.")
    plt.figtext(0.1, 0.04, pdf_conf_text, fontsize=8.5, color="purple", weight="bold")
    plt.title("Active Data Table (Transposed Layout)", fontsize=11, weight="bold", pad=12)
    pdf.savefig(fig2)
    plt.close()
    
    # PAGE 3: Special Request View (Current Month, Current Week, Present Daily)
    sp_df = df[df["Level"].isin(["Current Month", "Current Week", "Present Daily"])].reset_index(drop=True)
    fig3 = plot_mobile_engine(sp_df, market_close_price)
    plt.title("Market Analysis - Special Structural View (CM, CW, PD)", fontsize=11, weight="bold", pad=12)
    pdf.savefig(fig3)
    plt.close()

with open(pdf_path, "rb") as pdf_file:
    st.download_button(label="Download Advanced PDF Report", data=pdf_file, file_name="Advanced_Pivot_Report.pdf", mime="application/pdf")
