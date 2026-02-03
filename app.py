import streamlit as st
from sentence_transformers import SentenceTransformer, util

# 1. Page Configuration (The "Look and Feel")
st.set_page_config(
    page_title="DPDP 2025 Auditor",
    page_icon="⚖️",
    layout="wide"
)

# 2. Load Model (Cached so it doesn't reload every time)
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

# 3. The Rules (Your "Gold Standard" from the 2025 Gazette)
DPDP_RULES = {
    "Rule 3 (Notice)": "The Data Fiduciary must provide a notice comprising an itemised description of personal data collected and the specified purpose for processing.",
    "Rule 7(1) (User Notification)": "On becoming aware of a breach, the Data Fiduciary shall intimate each affected Data Principal in a concise and clear manner without delay.",
    "Rule 7(2) (Board Notification)": "On becoming aware of a breach, the Data Fiduciary shall intimate the Data Protection Board within seventy-two hours of becoming aware of such breach.",
    "Rule 8 (Erasure)": "The Data Fiduciary shall erase personal data if the Data Principal does not approach the Fiduciary for the specified purpose for a defined period.",
    "Rule 9 (Contact Info)": "Every Data Fiduciary shall prominently publish the business contact information of the Data Protection Officer or a person able to answer processing questions.",
    "Rule 10 (Children's Consent)": "The Data Fiduciary shall adopt technical measures to ensure verifiable consent of the parent is obtained before processing any personal data of a child.",
    "Rule 14 (Rights)": "The Data Fiduciary shall publish details of the means using which a Data Principal may exercise their rights to access, correction, and grievance redressal.",
    "Rule 15 (Cross-Border Transfer)": "Personal data may be transferred outside India only if the Data Fiduciary meets requirements specified by the Central Government."
}

# 4. The UI Header
st.title("⚖️ Automated DPDP 2025 Compliance Auditor")
st.markdown("""
This tool uses an **AI Neural Network (MiniLM-L6)** to audit company privacy policies against the **Digital Personal Data Protection Rules, 2025**.
""")

# 5. Input Section
col1, col2 = st.columns(2)
with col1:
    st.subheader("📝 Input Policy Text")
    policy_text = st.text_area("Paste Privacy Policy Here:", height=400, placeholder="Paste the full text of the privacy policy here...")

with col2:
    st.subheader("⚙️ Audit Controls")
    threshold = st.slider("Sensitivity Threshold (Calibration)", 0.0, 1.0, 0.45, 0.01, help="Adjust strictness based on your calibration study.")
    st.info(f"**Current Status:** Ready to Audit\n\n**Strictness:** {int(threshold*100)}%")
    
    audit_button = st.button("🚀 Run Compliance Audit", type="primary")

# 6. Audit Logic & Results
if audit_button and policy_text:
    st.divider()
    st.subheader("📊 Compliance Report")
    
    # Split policy into sentences for granular matching
    policy_sentences = [s.strip() for s in policy_text.split('.') if len(s) > 20]
    
    # Progress Bar
    progress_bar = st.progress(0)
    
    # Metrics containers
    passed = 0
    failed = 0
    
    results_container = st.container()

    for idx, (rule_name, rule_text) in enumerate(DPDP_RULES.items()):
        # Vectorize
        rule_vec = model.encode(rule_text, convert_to_tensor=True)
        policy_vecs = model.encode(policy_sentences, convert_to_tensor=True)
        
        # Calculate Similarity
        scores = util.cos_sim(rule_vec, policy_vecs)[0]
        max_score = float(scores.max())
        best_match_idx = int(scores.argmax())
        best_match_text = policy_sentences[best_match_idx]
        
        # Display Result
        with results_container:
            with st.expander(f"{rule_name}", expanded=True):
                if max_score > threshold:
                    st.success(f"✅ COMPLIANT ({int(max_score*100)}% Match)")
                    st.markdown(f"**Matched Clause:** ...*{best_match_text}*...")
                    passed += 1
                else:
                    st.error(f"🔴 GAP DETECTED - HIGH RISK")
                    st.markdown("**Action Required:** Draft specific policy language for this rule.")
                    failed += 1
        
        progress_bar.progress((idx + 1) / len(DPDP_RULES))

    # Summary Scorecard
    st.sidebar.metric("Compliance Score", f"{int((passed/8)*100)}%", delta=f"{passed} Passed / {failed} Failed")

elif audit_button and not policy_text:
    st.warning("Please paste a privacy policy first.")