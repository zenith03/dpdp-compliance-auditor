import streamlit as st
import pandas as pd
import plotly.express as px
from ai_engine import ComplianceAuditor

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="DPDP 2025 Auditor",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR BETTER UI ---
st.markdown("""
    <style>
    .main {
        background-color: #f9f9f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
    }
    div[data-testid="stExpander"] {
        border: none;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
        background-color: white;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- TITLE HEADER ---
col1, col2 = st.columns([1, 5])
with col1:
    st.markdown("## ⚖️")
with col2:
    st.title("DPDP Act 2025 Compliance Auditor")
    st.markdown("Automated legal gap analysis for Indian Data Protection Standards.")

st.divider()

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("⚙️ Audit Configuration")
    
    # 1. Slider
    threshold = st.slider("Strictness Level (Threshold)", 0.30, 0.80, 0.50, 0.05)
    st.caption("Lower = More lenient (fewer gaps). Higher = Stricter (more gaps).")
    
    st.divider()
    
    # 2. Upload
    st.header("📄 Document Input")
    uploaded_file = st.file_uploader("Upload Policy (TXT)", type="txt")
    text_input = st.text_area("Or paste text directly:", height=150)
    
    st.info("💡 **Tip:** Ensure the policy contains the full text including 'Contact Us' and 'Grievance Officer' sections.")

# --- INITIALIZE AI ENGINE ---
@st.cache_resource
def load_auditor():
    return ComplianceAuditor()

try:
    auditor = load_auditor()
except Exception as e:
    st.error(f"❌ Critical Error: Could not load AI Engine. {e}")
    st.stop()

# --- MAIN APP LOGIC ---
policy_content = ""
if uploaded_file:
    policy_content = uploaded_file.read().decode("utf-8")
elif text_input:
    policy_content = text_input

# Run Audit Button
if st.button("🚀 Run Compliance Audit", type="primary", use_container_width=True):
    if not policy_content:
        st.warning("⚠️ Please upload a document or paste text to begin.")
    else:
        with st.spinner("🤖 AI is analyzing legal clauses against 2025 Rules..."):
            results = auditor.audit_policy(policy_content, threshold=threshold)
        
        if not results:
            st.error("❌ No results generated. Check if 'dpdp_rules.txt' is loaded correctly.")
        else:
            # --- CALCULATE METRICS ---
            pass_count = sum(1 for r in results if r['status'] == 'PASS')
            total_rules = len(results)
            score = int((pass_count / total_rules) * 100) if total_rules > 0 else 0
            
            # --- DISPLAY DASHBOARD ---
            st.subheader("📊 Audit Dashboard")
            
            # 1. Key Metrics Row
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Compliance Score", f"{score}%", delta_color="normal")
            m2.metric("Rules Analyzed", total_rules)
            m3.metric("Passed Clauses", pass_count, delta="Safe")
            m4.metric("Critical Gaps", total_rules - pass_count, delta="-High Risk", delta_color="inverse")
            
            st.divider()

            # 2. Visualization Row
            c1, c2 = st.columns([1, 2])
            
            with c1:
                # Donut Chart
                chart_data = pd.DataFrame({
                    "Status": ["Compliant", "Gaps"],
                    "Count": [pass_count, total_rules - pass_count]
                })
                fig = px.pie(chart_data, values='Count', names='Status', hole=0.5,
                             color='Status', color_discrete_map={'Compliant':'#00CC96', 'Gaps':'#EF553B'})
                fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=200)
                st.plotly_chart(fig, use_container_width=True)
            
            with c2:
                # Progress Bar Context
                st.markdown("#### Risk Assessment")
                if score > 80:
                    st.success("This policy is largely compliant. Review minor gaps.")
                elif score > 50:
                    st.warning("Moderate Risk. Significant updates required for 2025 compliance.")
                else:
                    st.error("High Risk. Policy likely predates the 2025 Act.")
            
            # --- DETAILED REPORT TABS ---
            st.subheader("📝 Detailed Findings")
            
            tab1, tab2 = st.tabs(["🔴 Gaps & Violations", "✅ Compliant Clauses"])
            
            with tab1:
                gaps = [r for r in results if r['status'] == 'FAIL']
                if not gaps:
                    st.info("No gaps detected! 🎉")
                for res in gaps:
                    with st.expander(f"🔴 {res['rule_id']} (Confidence: {res['match_score']}%)"):
                        st.markdown(f"**Missing Requirement:**")
                        st.code(res['requirement'], language="text")
                        st.markdown("**Recommendation:** *Add a specific clause addressing this requirement.*")

            with tab2:
                passes = [r for r in results if r['status'] == 'PASS']
                if not passes:
                    st.info("No compliant clauses found.")
                for res in passes:
                    with st.expander(f"✅ {res['rule_id']} (Confidence: {res['match_score']}%)"):
                        st.markdown(f"**Requirement:** {res['requirement']}")
                        st.success(f"**Found in Policy:**\n> \"{res['company_clause']}\"")
            
            # --- DOWNLOAD BUTTON ---
            st.divider()
            df = pd.DataFrame(results)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Full Audit Report (CSV)",
                data=csv,
                file_name='dpdp_audit_report.csv',
                mime='text/csv',
            )
