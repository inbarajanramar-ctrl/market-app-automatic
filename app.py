import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
from matplotlib.backends.backend_pdf import PdfPages

# மொபைலுக்கு ஏற்றவாறு பக்கத்தை அமைத்தல்
st.set_page_config(page_title="Advanced Multi-Pivot Matrix", layout="centered")

st.title("📊 Advanced Multi-Pivot Structure Matrix")
st.write("Using Completed Previous Frames with Automatic CPR Width Analysis")

# --- 1. சிம்பல் செலக்டர் இன்புட் ---
ticker_options = {
    "Nifty 50": "^NSEI",
    "Bank Nifty": "^NSEBANK",
    "Sensex": "^BSESN",
    "Reliance": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFC Bank": "HDFCBANK.NS"
}

selected_symbol_label = st.selectbox("🎯 Select Instrument / Stock:", list(ticker_options.keys()))
custom_ticker = st.text_input("✍️ Or Type Custom Yahoo Ticker:", value=ticker_options[selected_symbol_label])

# --- 2. வெப்சைட்டில் இருந்து தரவுகளை எடுக்கும் இன்ஜின் ---
@st.cache_data(ttl=60)
def fetch_perfect_ohlc_matrix(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period="2y", interval="1d")
    
    if df.empty or len(df) < 60:
        st.error("No sufficient data found.")
        st.stop()
        
    try:
        ltp = ticker.basic_info['lastPrice']
    except:
        ltp = df['Close'].iloc[-1]

    matrix_data = {}
    
    # A. Daily
    matrix_data["Present Daily"] = {"H": df['High'].iloc[-1], "L": df['Low'].iloc[-1], "C": df['Close'].iloc[-1]}
    matrix_data["Previous Daily"] = {"H": df['High'].iloc[-2], "L": df['Low'].iloc[-2], "C": df['Close'].iloc[-2]}
    
    # B. Weekly
    df_weekly = df.resample('W-SUN').agg({'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()
    matrix_data["Previous Week"] = {"H": df_weekly['High'].iloc[-2], "L": df_weekly['Low'].iloc[-2], "C": df_weekly['Close'].iloc[-2]}
    matrix_data["2 Weeks Ago"] = {"H": df_weekly['High'].iloc[-3], "L": df_weekly['Low'].iloc[-3], "C": df_weekly['Close'].iloc[-3]}
    
    # C. Monthly
    df_monthly = df.resample('ME').agg({'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()
    matrix_data["Previous Month"] = {"H": df_monthly['High'].iloc[-2], "L": df_monthly['Low'].iloc[-2], "C": df_monthly['Close'].iloc[-2]}
    matrix_data["2 Months Ago"] = {"H": df_monthly['High'].iloc[-3], "L": df_monthly['Low'].iloc[-3], "C": df_monthly['Close'].iloc[-3]}
    
    return matrix_data, round(ltp, 2)

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

with st.spinner("Fetching data from website..."):
    try:
        web_data, market_close_price = fetch_perfect_ohlc_matrix(custom_ticker)
        st.success(f"Loaded Data for {custom_ticker}! LTP: {market_close_price}")
    except Exception as e:
        st.error("Connection error. Please verify the Ticker name.")
        st.stop()

# லெவல்களை கணக்கிட்டு வரிசைப்படுத்துதல்
view_order = ["2 Months Ago", "Previous Month", "2 Weeks Ago", "Previous Week", "Previous Daily", "Present Daily"]
calculated_rows = []
for tf in view_order:
    vals = web_data.get(tf, {"H": 0, "L": 0, "C": 0})
    pivots = calculate_pivot_levels(vals["H"], vals["L"], vals["C"])
    pivots["Level"] = tf
    calculated_rows.append(pivots)

df = pd.DataFrame(calculated_rows)[["Level", "H4", "H3", "L3", "L4", "TC", "CP", "BC"]]

# --- 4. நீங்கள் கேட்ட புதிய PIVOT WIDTH ANALYSIS இன்ஜின் ---
def analyze_pivot_width(tc, bc, ltp):
    width = abs(tc - bc)
    width_pct = (width / ltp) * 100
    
    if width_pct <= 0.15:
        return f"⚡ Narrow Width ({width_pct:.2f}%)", "🎯 BREAKOUT IMMINENT! சந்தை இன்று கடுமையான ஒரு பக்க நகர்வை (Trending Move) எடுக்கப் போகிறது. ஆப்ஷன் பையர்களுக்கு சாதகமான நாள்."
    elif width_pct >= 0.50:
        return f"🪵 Wide Width ({width_pct:.2f}%)", "🧱 RANGEBOUND / SIDEWAYS! சந்தை பெரிய டிரெண்ட் எடுக்காமல் ஒரு குறிப்பிட்ட எல்லைக்குள்ளேயே சுற்றப் போகிறது. ஆப்ஷன் செல்லர்களுக்கு சாதகமான நாள்."
    else:
        return f"📐 Average Width ({width_pct:.2f}%)", "⚖️ மிதமான நகர்வு. முந்தைய நாளின் முக்கிய சப்போர்ட் மற்றும் ரெசிஸ்டன்ஸ் லெவல்களைப் பொறுத்து மார்க்கெட் நகரும்."

row_map = df.set_index("Level")

# தனித்தனி காலக்கட்டங்களின் பிவட் அகலத்தைக் கணக்கிடுதல்
d_width_title, d_width_desc = analyze_pivot_width(row_map.loc["Present Daily", "TC"], row_map.loc["Present Daily", "BC"], market_close_price)
w_width_title, w_width_desc = analyze_pivot_width(row_map.loc["Previous Week", "TC"], row_map.loc["Previous Week", "BC"], market_close_price)

# --- 5. 7 Types of Pivot Relationship இன்ஜின் ---
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

m_title, m_desc = detect_pivot_relationship(row_map.loc["2 Months Ago", "TC"], row_map.loc["2 Months Ago", "BC"], row_map.loc["Previous Month", "TC"], row_map.loc["Previous Month", "BC"])
w_title, w_desc = detect_pivot_relationship(row_map.loc["2 Weeks Ago", "TC"], row_map.loc["2 Weeks Ago", "BC"], row_map.loc["Previous Week", "TC"], row_map.loc["Previous Week", "BC"])
d_title, d_desc = detect_pivot_relationship(row_map.loc["Previous Daily", "TC"], row_map.loc["Previous Daily", "BC"], row_map.loc["Present Daily", "TC"], row_map.loc["Present Daily", "BC"])

# --- 🔍 திரையில் அனாலிசிஸ் ரிப்போர்ட்டைக் காட்டுதல் ---
st.subheader("🔍 CPR Structural & Width Analysis")

col1, col2 = st.columns(2)
with col1:
    st.info(f"**📅 Intraday CPR Width (Today):**\n\n**{d_width_title}**\n\n*{d_width_desc}*")
with col2:
    st.success(f"**⏳ Weekly CPR Width (Prev Week):**\n\n**{w_width_title}**\n\n*{w_width_desc}*")

st.markdown("---")
st.warning(f"**🦅 Month-on-Month Trend:** {m_title} | *{m_desc}*")
st.info(f"**⏳ Week-on-Week Trend:** {w_title} | *{w_desc}*")
st.error(f"**📅 Day-on-Day Trend:** {d_title} | *{d_desc}*")

# --- 6. 4 விதமான சார்ட் வியூ பட்டன்கள் ---
st.subheader("🎯 View Perspective")
selected_tab = st.radio("Select View Range:", [
    "Full Structure View", 
    "Two Month Relationship", 
    "Two Week Relationship", 
    "Two Day & Weekly to Daily View"
], horizontal=True)

if selected_tab == "Full Structure View":
    sub_df = df.copy()
elif selected_tab == "Two Month Relationship":
    sub_df = df[df["Level"].isin(["2 Months Ago", "Previous Month"])].reset_index(drop=True)
elif selected_tab == "Two Week Relationship":
    sub_df = df[df["Level"].isin(["2 Weeks Ago", "Previous Week"])].reset_index(drop=True)
else:
    sub_df = df[df["Level"].isin(["Previous Week", "Previous Daily", "Present Daily"])].reset_index(drop=True)

# --- 7. நிலையான Matplotlib சார்ட் என்ஜின் ---
def plot_mobile_engine(plot_df, ltp):
    fig, ax = plt.subplots(figsize=(10, 6.5))
    x_positions = range(len(plot_df))
    bar_width = 0.4
    all_prices = [ltp]

    for idx, row in plot_df.iterrows():
        x = x_positions[idx]
        all_prices.extend([row["H4"], row["H3"], row["L3"], row["L4"], row["TC"], row["CP"], row["BC"]])
        
        # Camarilla
        ax.hlines(y=row["H4"], xmin=x - bar_width, xmax=x + bar_width, colors="blue", linewidth=2.5)
        ax.text(x, row["H4"] + (ltp*0.0005), f'{row["H4"]:.1f}', ha="center", va="bottom", fontsize=8, color="blue", weight="bold")
        ax.hlines(y=row["H3"], xmin=x - bar_width, xmax=x + bar_width, colors="orange", linewidth=2.5)
        ax.text(x, row["H3"] + (ltp*0.0005), f'{row["H3"]:.1f}', ha="center", va="bottom", fontsize=8, color="red", weight="bold")
        ax.hlines(y=row["L3"], xmin=x - bar_width, xmax=x + bar_width, colors="orange", linestyles="--", linewidth=2)
        ax.text(x, row["L3"] - (ltp*0.0005), f'{row["L3"]:.1f}', ha="center", va="top", fontsize=8, color="red", weight="bold")
        ax.hlines(y=row["L4"], xmin=x - bar_width, xmax=x + bar_width, colors="blue", linestyles="--", linewidth=2)
        ax.text(x, row["L4"] - (ltp*0.0005), f'{row["L4"]:.1f}', ha="center", va="top", fontsize=8, color="blue", weight="bold")
        
        # CPR
        ax.hlines(y=row["TC"], xmin=x - bar_width, xmax=x + bar_width, colors="purple", linestyles=":", linewidth=1.5)
        ax.hlines(y=row["CP"], xmin=x - bar_width, xmax=x + bar_width, colors="purple", linestyles="-.", linewidth=2)
        ax.hlines(y=row["BC"], xmin=x - bar_width, xmax=x + bar_width, colors="purple", linestyles=":", linewidth=1.5)
        ax.text(x - bar_width, row["CP"], f' CP:{row["CP"]:.1f}', ha="left", va="center", fontsize=7.5, color="purple")
        
        # LTP
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

# --- 8. ஆக்டிவ் டேட்டா டேபிள் மற்றும் PDF டவுன்লোடு ---
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
