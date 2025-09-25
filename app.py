# app.py - polished, professional Streamlit UI for SynStyl
import streamlit as st
import pandas as pd
import altair as alt
import random
import time
from io import StringIO

# Defensive imports: try lower-case module names used earlier
try:
    from tokenizer import tokenize_dataset
except Exception as e:
    raise ImportError("tokenizer.py must define tokenize_dataset(df, salt=None). Error: " + str(e))

try:
    from Main import generate_synthetic_data
except Exception as e:
    raise ImportError("Main.py must define generate_synthetic_data(df, salt=None). Error: " + str(e))

# ---------- Page config ----------
st.set_page_config(page_title="SYNSTYL — Turning Patterns into Possibilities",
                   page_icon="🛡️",
                   layout="wide",
                   initial_sidebar_state="auto")

# ---------- Custom CSS & Fonts (Inter) ----------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css"]  {k
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg, #071427 0%, #0e2a3b 50%, #081522 100%);
        color: #dff6f6;
    }
    .card {
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 8px 30px rgba(2,10,20,0.6);
        border: 1px solid rgba(255,255,255,0.035);
    }
    .muted { color: #9fe6e6; }
    .accent { color: #00e6e6; font-weight:700; }
    .cta { background: linear-gradient(90deg,#00e6e6,#6ae3ff); color:#001; font-weight:700; border-radius:8px; padding:8px 12px; }
    .small { font-size:13px; color:#bfeff0; }
    .kpi { background: rgba(255,255,255,0.02); border-radius:8px; padding:10px; text-align:center; }
    .note { color:#9fe6e6; font-size:13px; }

    /* Make Streamlit buttons green */
    .stButton > button {
        background: linear-gradient(90deg, #00e676 60%, #1de9b6 100%) !important;
        color: #012 !important;
        font-weight: 700;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(0,230,118,0.10);
        transition: background 0.2s;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #1de9b6 60%, #00e676 100%) !important;
        color: #001 !important;
    }

    /* Make file uploader label white */
    span[data-testid="stFileUploaderLabel"] {
        color: #fff !important;
    }

    /* Make file uploader button green */
    div[data-testid="stFileUploader"] button {
        background: linear-gradient(90deg, #00e676 60%, #1de9b6 100%) !important;
        color: #012 !important;
        font-weight: 700;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(0,230,118,0.10);
        transition: background 0.2s;
    }
    div[data-testid="stFileUploader"] button:hover {
        background: linear-gradient(90deg, #1de9b6 60%, #00e676 100%) !important;
        color: #001 !important;
    }

    /* Green label for special texts */
    .label-green {
        color: #00e676 !important;
        font-weight: 600;
    }
    /* Make download buttons green */
    div[data-testid="stDownloadButton"] button {
        background: linear-gradient(90deg, #00e676 60%, #1de9b6 100%) !important;
        color: #012 !important;
        font-weight: 700;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(0,230,118,0.10);
        transition: background 0.2s;
    }
    div[data-testid="stDownloadButton"] button:hover {
        background: linear-gradient(90deg, #1de9b6 60%, #00e676 100%) !important;
        color: #001 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
header_col1, header_col2 = st.columns([3,1])
with header_col1:
    col_logo, col_text = st.columns([1, 3])
    with col_logo:
        st.image("data/logoSynStyl.png", width=400)
    with col_text:
        st.markdown('''
        <div style="display: flex; flex-direction: column; justify-content: center; height: 80px; margin-left: 10px;">
            <div style="font-size: 60px; font-weight: 1000; color: #4A90E2; letter-spacing: 2px; margin-bottom: -90px;">Synthetic Data Generator</div>
            
        </div>
        ''', unsafe_allow_html=True)
with header_col2:
    st.markdown("<div style='text-align:right'><span class='small muted'></span></div>", unsafe_allow_html=True)

st.markdown("---")

# ---------- Sidebar quick help ----------
with st.sidebar:
    st.markdown("## Quick guide")
    st.markdown("""
    1. Upload your `input_real.csv` (or click **Use sample data**).  
    2. Optionally enter a reproducible **salt** (leave blank for randomized output).  
    3. Click **Generate Synthetic Data** → preview tokenized and synthetic outputs.  
    4. Use **Regenerate** to get a new variation (different salt).
    """)
    st.markdown("---")
    st.markdown("⚠️ Note: This prototype demonstrates privacy-preserving transformations. Use secure key management for production.")
    st.markdown("---")

# ---------- Controls & Upload ----------
col_upload, col_controls = st.columns([2,1])
with col_upload:
    st.markdown("### Upload dataset (CSV)")
    st.markdown('<span class="label-green">Upload CSV with headers (e.g., input_real.csv)</span>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=["csv"])
    st.markdown('<div class="small muted">Fields like SenderName, SenderAadhar, SenderSSN, SenderCard, TransactionAmount help the demo.</div>', unsafe_allow_html=True)

    # sample generator button
    if st.button("Use sample dataset (100 rows)"):
        # generate a simple sample CSV client-side (no server write)
        from faker import Faker
        fake = Faker("en_IN")
        rows = []
        for i in range(1, 101):
            rows.append({
                "TransactionID": i,
                "SenderName": fake.first_name(),
                "SenderPhone": fake.msisdn(),
                "SenderAadhar": "".join([str(random.randint(0,9)) for _ in range(12)]),
                "SenderSSN": "".join([str(random.randint(0,9)) for _ in range(9)]),
                "SenderCard": "".join([str(random.randint(0,9)) for _ in range(16)]),
                "SenderAddress": fake.address().replace('\\n', ', '),
                "SenderIP": fake.ipv4(),
                "SenderISP": random.choice(["Jio", "Airtel", "BSNL", "Vodafone", "ACT", "Hathway", "Verizon", "T-Mobile", "AT&T", "Spectrum", "Comcast"]),
                "SenderBankBalance": round(random.uniform(1000,200000),2),
                "SenderAnnualIncome": round(random.uniform(200000,2000000),2),
                "SenderLoanStatus": random.choice(["Yes","No"]),
                "SenderPastFraud": random.choice(["Yes","No"]),
                "ReceiverName": fake.first_name(),
                "ReceiverPhone": fake.msisdn(),
                "ReceiverSSN": "".join([str(random.randint(0,9)) for _ in range(9)]),
                "ReceiverCard": "".join([str(random.randint(0,9)) for _ in range(16)]),
                "ReceiverAddress": fake.address().replace('\\n', ', '),
                "ReceiverIP": fake.ipv4(),
                "ReceiverISP": random.choice(["Jio", "Airtel", "BSNL", "Vodafone", "ACT", "Hathway", "Verizon", "T-Mobile", "AT&T", "Spectrum", "Comcast"]),
                "ReceiverBankBalance": round(random.uniform(1000,200000),2),
                "ReceiverAnnualIncome": round(random.uniform(200000,2000000),2),
                "TransactionAmount": round(random.uniform(100,10000),2),
                "TransactionTime": fake.time(),
                "TransactionLocation": fake.city(),
                "TransactionDate": fake.date_this_decade(),
                "ReceiverAccountCreationDate": fake.date_between(start_date='-10y', end_date='today'),
                "ReceiverRegisteredName": fake.first_name(),
                "Fraud": random.choice([0,1])
            })
        sample_df = pd.DataFrame(rows)
        # put into session_state as if uploaded
        st.session_state["_uploaded_sample"] = sample_df
        st.success("Sample dataset ready. Scroll down and click Generate Synthetic Data.")

with col_controls:
    st.markdown("### Controls")
    st.markdown('<span class="label-green">Optional run salt (leave blank for random)</span>', unsafe_allow_html=True)
    salt = st.text_input("", value="")
    generate_btn = st.button("Generate Synthetic Data", key="gen")
    regen_btn = st.button("Regenerate (new variation)", key="regen")

# ---------- Helper wrappers (handle function signatures with/without salt) ----------
def call_tokenize(df: pd.DataFrame, salt_arg):
    try:
        return tokenize_dataset(df.copy(), salt_arg)
    except TypeError:
        return tokenize_dataset(df.copy())

def call_generate(df: pd.DataFrame, salt_arg):
    try:
        return generate_synthetic_data(df.copy(), salt_arg)
    except TypeError:
        return generate_synthetic_data(df.copy())

# ---------- Main processing ----------
# decide source dataframe from upload or sample
src_df = None
if uploaded_file is not None:
    try:
        src_df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error("Could not read uploaded CSV: " + str(e))
elif "_uploaded_sample" in st.session_state:
    src_df = st.session_state["_uploaded_sample"]

if src_df is not None:
    st.markdown("---")
    st.subheader("Original dataset preview")
    st.dataframe(src_df.head(8), use_container_width=True)

    # decide salt: regen uses fresh random, else use input salt or None
    run_salt = None
    if regen_btn:
        run_salt = hex(random.getrandbits(64))
    else:
        run_salt = salt if salt.strip() != "" else None

    # If generate clicked: process
    if generate_btn or regen_btn:
        with st.spinner("Tokenizing sensitive fields..."):
            time.sleep(0.4)
            tokenized = call_tokenize(src_df, run_salt)
        with st.spinner("Generating synthetic dataset..."):
            time.sleep(0.6)
            synthetic = call_generate(tokenized, run_salt)

        # store
        st.session_state["tokenized_df"] = tokenized
        st.session_state["synthetic_df"] = synthetic
        st.session_state["run_salt"] = run_salt or "random"
        st.success("✅ Synthetic data generated")

    # if processed previously in session show outputs
    if "synthetic_df" in st.session_state:
        tokenized = st.session_state["tokenized_df"]
        synthetic = st.session_state["synthetic_df"]

        # top KPIs
        k1, k2, k3 = st.columns([1,1,1])
        with k1:
            st.markdown("<div class='kpi'><div style='font-weight:700'>Rows</div><div style='font-size:20px'>{}</div></div>".format(len(synthetic)), unsafe_allow_html=True)
        with k2:
            if "Fraud" in src_df.columns:
                st.markdown("<div class='kpi'><div style='font-weight:700'>Fraud (orig)</div><div style='font-size:20px'>{}</div></div>".format(int(src_df['Fraud'].sum())), unsafe_allow_html=True)
            else:
                st.markdown("<div class='kpi'><div style='font-weight:700'>Fraud (orig)</div><div style='font-size:20px'>N/A</div></div>", unsafe_allow_html=True)
        with k3:
            st.markdown("<div class='kpi'><div style='font-weight:700'>Run salt</div><div style='font-size:14px'>{}</div></div>".format(str(st.session_state.get("run_salt"))), unsafe_allow_html=True)

        st.markdown("---")

        # side-by-side tables & download
        tcol1, tcol2 = st.columns([1,1], gap="large")
        with tcol1:
            st.markdown("### 🔒 Tokenized sample")
            st.dataframe(tokenized.head(8), use_container_width=True)
            st.download_button("Download tokenized_output.csv", tokenized.to_csv(index=False).encode("utf-8"), file_name="tokenized_output.csv", mime="text/csv")
        with tcol2:
            st.markdown("### 🤖 Synthetic sample")
            st.dataframe(synthetic.head(8), use_container_width=True)
            st.download_button("Download synthetic_output.csv", synthetic.to_csv(index=False).encode("utf-8"), file_name="synthetic_output.csv", mime="text/csv")

        st.markdown("---")

        # ---------- Visualizations (fixed) ----------
        st.subheader("Quick Visualizations")
        viz_col1, viz_col2 = st.columns([1.2, 1], gap="large")

        # choose a numeric column intelligently
        numeric_cols = src_df.select_dtypes(include=["number"]).columns.tolist()
        prefer = ["TransactionAmount", "Amount", "SenderBankBalance", "ReceiverBankBalance", "SenderAnnualIncome", "ReceiverAnnualIncome"]
        chosen = None
        for p in prefer:
            if p in numeric_cols:
                chosen = p
                break
        if chosen is None and numeric_cols:
            chosen = numeric_cols[0]

        with viz_col1:
            if chosen:
                st.markdown(f"**Distribution overlay — {chosen}**")
                # Prepare histogram data with samples (avoid huge plot slowdowns)
                a = src_df[chosen].dropna().astype(float)
                b = synthetic[chosen].dropna().astype(float)
                # sample up to 1000 for plotting
                a_s = a.sample(min(len(a), 1000), replace=False, random_state=42).to_frame(name="value").assign(dataset="original")
                b_s = b.sample(min(len(b), 1000), replace=False, random_state=43).to_frame(name="value").assign(dataset="synthetic")
                plot_df = pd.concat([a_s, b_s], ignore_index=True)
                hist = alt.Chart(plot_df).mark_area(opacity=0.45).encode(
                    alt.X("value:Q", bin=alt.Bin(maxbins=40), title=chosen),
                    alt.Y('count()', stack=None, title='Count'),
                    alt.Color('dataset:N', scale=alt.Scale(range=['#2563eb','#00e6e6']))
                ).properties(width=700, height=420)
                st.altair_chart(hist, use_container_width=True)
            else:
                st.info("No numeric columns found to plot distributions.")

        with viz_col2:
            if chosen:
                st.markdown(f"**Row-wise comparison — {chosen}**")
                # build alignment for line chart (sample up to 200 points)
                or_val = src_df[chosen].dropna().astype(float).reset_index(drop=True)
                syn_val = synthetic[chosen].dropna().astype(float).reset_index(drop=True)
                # align length by padding/trimming
                n = max(len(or_val), len(syn_val))
                idx = list(range(n))
                or_plot = pd.DataFrame({'index': idx, 'value': list(or_val.sample(n, replace=True, random_state=1))[:n], 'series': 'original'}) if len(or_val)>0 else pd.DataFrame({'index':[], 'value':[], 'series':[]})
                syn_plot = pd.DataFrame({'index': idx, 'value': list(syn_val.sample(n, replace=True, random_state=2))[:n], 'series': 'synthetic'}) if len(syn_val)>0 else pd.DataFrame({'index':[], 'value':[], 'series':[]})
                line_df = pd.concat([or_plot, syn_plot], ignore_index=True)
                line = alt.Chart(line_df).mark_line(point=False).encode(
                    x='index:Q',
                    y='value:Q',
                    color=alt.Color('series:N', scale=alt.Scale(range=['#2563eb','#00e6e6'])),
                    tooltip=['index', 'value', 'series']
                ).properties(width=520, height=420)
                st.altair_chart(line, use_container_width=True)
            else:
                st.info("No numeric columns for row-wise comparison.")

        st.markdown("---")
        st.caption("Tip: Use the salt field to reproduce the same synthetic dataset. Click Regenerate for a fresh variation.")
    else:
        st.info("Click 'Generate Synthetic Data' to tokenize and create synthetic data output.")
else:
    st.markdown('<div class="card"><h3 style="color:#00e6e6;margin:0">Ready to demo?</h3><p class="muted">Upload your CSV or click <b>Use sample dataset</b> to try the prototype.</p></div>', unsafe_allow_html=True)

# ---------- footer ----------
st.markdown("<br><hr>", unsafe_allow_html=True)
