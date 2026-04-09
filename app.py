import streamlit as st
import numpy as np
import plotly.graph_objects as go
from google import genai
import os
from google.genai.errors import ClientError

# ====================== PASSWORD GATE ======================
st.set_page_config(page_title="Scripbox PMS Pathfinder", page_icon="🛡️", layout="centered")

st.title("🛡️ Scripbox PMS Pathfinder")

# Change this password to anything you like
PASSWORD = "hackathon2026"   # ← CHANGE THIS IF YOU WANT

if "password_correct" not in st.session_state:
    st.session_state.password_correct = False

if not st.session_state.password_correct:
    st.markdown("### 🔐 Enter password to access PMS Pathfinder")
    entered_password = st.text_input("Password", type="password")
    if st.button("Unlock"):
        if entered_password == PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("❌ Wrong password")
    st.stop()
# ===========================================================

os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
client = genai.Client()

st.markdown("**Helping HNI clients decide if PMS makes sense for their goals** — 100% private, behavioural + financial comparison.")

# ================== GOAL INPUT ==================
st.header("1️⃣ Your Goal")
goal_desc = st.text_input("Describe your goal in plain English", value="Rs 5 Crore for retirement in 8 years")

col_unit, col_val = st.columns([1, 3])
with col_unit:
    unit = st.selectbox("Target unit", options=["Crores", "Lakhs"], index=0)
with col_val:
    if unit == "Crores":
        target_value = st.number_input("Target amount", value=5.0, min_value=0.1, step=0.1, format="%.1f")
        target_amount = int(target_value * 10_000_000)
    else:
        target_value = st.number_input("Target amount", value=500.0, min_value=1.0, step=1.0, format="%.0f")
        target_amount = int(target_value * 100_000)

st.success(f"**Target: ₹{target_amount:,.0f}**")

years = st.number_input("Time horizon (years)", value=8, min_value=1, max_value=30)
monthly_sip = st.number_input("Planned monthly SIP / additional investment (₹)", value=150000, min_value=1000, step=1000)

# ================== CURRENT INVESTABLE CORPUS (Key for PMS) ==================
st.subheader("💼 Current Investable Corpus")
col_pms_unit, col_pms_val = st.columns([1, 3])
with col_pms_unit:
    pms_unit = st.selectbox("Corpus unit", options=["Crores", "Lakhs"], index=0)
with col_pms_val:
    if pms_unit == "Crores":
        pms_value = st.number_input("Current investable corpus", value=0.75, min_value=0.0, step=0.1, format="%.1f")
        current_corpus = int(pms_value * 10_000_000)
    else:
        pms_value = st.number_input("Current investable corpus", value=75.0, min_value=0.0, step=1.0, format="%.0f")
        current_corpus = int(pms_value * 100_000)

st.success(f"**Current investable corpus: ₹{current_corpus:,.0f}**")

if current_corpus >= 5000000:
    st.success("✅ You qualify for PMS (₹50 lakh+ threshold)")
else:
    st.warning("Note: PMS typically requires ₹50 lakh+ investable corpus")
# =====================================================================

# Behaviour quiz
st.header("2️⃣ Your Behaviour Profile (8 quick questions)")
st.caption("Be honest — this is what makes the magic happen!")

q1 = st.slider("During market crashes (like 2020), how often did you pause or reduce your SIP?", 1, 5, 3)
q2 = st.slider("If markets fall 15% tomorrow, how likely are you to stop your SIP?", 1, 5, 3)
q3 = st.slider("Do you ever buy a fund just because everyone on social media is talking about it?", 1, 5, 2)
q4 = st.slider("Would you rather lock in a small gain than risk it for a bigger upside?", 1, 5, 3)
q5 = st.slider("How much do recent market news affect your investment decisions?", 1, 5, 3)
q6 = st.slider("How often do you skip SIPs when cash feels tight?", 1, 5, 2)
q7 = st.slider("Have you ever sold a fund early because of fear of further loss?", 1, 5, 2)
q8 = st.slider("Do you check your portfolio daily/weekly during volatile times?", 1, 5, 4)

answers = np.array([q1, q2, q3, q4, q5, q6, q7, q8])
discipline_score = int(100 - (answers.mean() - 1) * 12.5)
discipline_score = max(0, min(100, discipline_score))

if st.button("🚀 Analyse PMS Suitability", type="primary"):
    with st.spinner("Running MF vs PMS Monte Carlo simulation..."):
        n_sim = 5000
        mf_return = 0.12
        pms_return = 0.145          # realistic PMS gross return
        vol = 0.18
        behavioural_drag = (100 - discipline_score) / 100 * 0.035
        pms_fees = 0.018            # ~1.8% total fees

        mf_corpus = np.zeros(n_sim)
        pms_corpus = np.zeros(n_sim)
        for i in range(n_sim):
            r_mf = np.random.normal(mf_return, vol, years)
            r_pms = np.random.normal(pms_return - pms_fees, vol * 1.1, years)
            
            mf_val = float(current_corpus)
            pms_val = float(current_corpus)
            for yr in range(years):
                mf_val = (mf_val + monthly_sip * 12) * (1 + r_mf[yr])
                pms_val = (pms_val + monthly_sip * 12) * (1 + r_pms[yr])
            mf_corpus[i] = mf_val
            pms_corpus[i] = pms_val
        
        mf_prob = np.mean(mf_corpus >= target_amount) * 100
        pms_prob = np.mean(pms_corpus >= target_amount) * 100
        
        crisis_harm = int((100 - discipline_score) * 0.65)
        
        # PMS Suitability Score
        pms_suitability = int((discipline_score * 0.5) + (min(current_corpus / 5000000, 1) * 30) + (pms_prob - mf_prob))
        pms_suitability = max(0, min(100, pms_suitability))
        
        # AI Coach (strict prompt)
                # === AI CALL WITH ERROR HANDLING ===
                # === AI CALL WITH ERROR HANDLING (PMS Pathfinder) ===
        try:
            prompt = f"""
            You are a friendly behavioural finance coach for high-net-worth clients.
            Goal: {goal_desc}
            Current corpus: ₹{current_corpus:,.0f}
            Discipline score: {discipline_score}/100
            MF probability: {mf_prob:.0f}%
            PMS probability: {pms_prob:.0f}%
            PMS Suitability Score: {pms_suitability}/100
            Give a warm, encouraging explanation of their biases and with actionable suggestions. Focus  on general behaviour, emotions and mindset as well corrective actions they can take. Never mention specific app features. Use simple, friendly language and structure the feedback in an effective easy to read manner. Avoid big chunky paragraphs. Use bullet points where relevant.
            """
            ai_response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=prompt).text
        except ClientError as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower():
                ai_response = "⚠️ Gemini API quota limit reached for today (free tier). Please try again tomorrow or create a new API key from a new Google Cloud project."
            else:
                ai_response = f"⚠️ AI coach temporarily unavailable: {str(e)[:100]}..."
        except Exception as e:
            ai_response = "⚠️ The AI coach is temporarily unavailable. However, your probabilities and chart are still shown above."
        # =====================================
        
        # Results
        st.success("✅ Your PMS Pathfinder Report")
        st.metric("Your Discipline Score", f"{discipline_score}/100")
        st.metric("PMS Suitability Score", f"{pms_suitability}/100", help="Higher score = better fit for PMS")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Regular MF Path Probability", f"{mf_prob:.0f}%")
        with col2:
            delta = f"{pms_prob - mf_prob:+.0f}%"
            st.metric("PMS Path Probability", f"{pms_prob:.0f}%", delta)
        
        st.metric("Crisis Harm Likelihood", f"{crisis_harm}% chance")
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=["MF Path", "PMS Path"], y=[mf_prob, pms_prob], text=[f"{mf_prob:.0f}%", f"{pms_prob:.0f}%"], textposition="auto"))
        fig.update_layout(title="Goal Achievement Probability: MF vs PMS", yaxis_title="Probability (%)", yaxis_range=[0,100])
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("🧠 Your Personalised Coach Advice")
        st.write(ai_response)
        
        total_contrib = monthly_sip * 12 * years
        st.caption(f"Total future contributions planned: ₹{total_contrib:,.0f} | This is a prototype for Scripbox PMS acquisition. Not financial advice. Built with ❤️ using Gemini AI + Monte Carlo.")
