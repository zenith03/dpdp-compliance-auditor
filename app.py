import streamlit as st
from ai_engine import ComplianceAuditor

# Page Config
st.set_page_config(page_title="DPDP 2025 Auditor", page_icon="⚖️", layout="wide")

st.title("🇮🇳 DPDP 2025 Compliance Auditor")
st.markdown("Upload a Privacy Policy to check compliance with the **Digital Personal Data Protection Rules 2025**.")

# Initialize AI Engine (Cached to prevent reloading)
@st.cache_resource
def load_auditor():
    return ComplianceAuditor()

try:
    auditor = load_auditor()
except Exception as e:
    st.error(f"Error loading AI Engine: {e}")
    st.stop()

# Sidebar for Input
with st.sidebar:
    st.header("Upload Policy")
    uploaded_file = st.file_uploader("Choose a text file", type="txt")
    
    # Optional: Paste Text directly
    text_input = st.text_area("Or paste policy text here:", height=200)

# Main Logic
policy_content = ""
if uploaded_file is not None:
    # Safely decode the file
    policy_content = uploaded_file.read().decode("utf-8")
elif text_input:
    policy_content = text_input

if st.button("🚀 Run Compliance Audit"):
    if not policy_content:
        st.warning("Please upload a file or paste text first.")
    else:
        with st.spinner("AI is analyzing legal clauses..."):
            # Run the audit
            results = auditor.audit_policy(policy_content)
        
        if not results:
            st.error("No rules found or policy text was empty.")
        else:
            # Calculate Score
            pass_count = sum(1 for r in results if r['status'] == 'PASS')
            total_rules = len(results)
            
            # Avoid division by zero if something goes wrong
            score = int((pass_count / total_rules) * 100) if total_rules > 0 else 0

            # Display Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Compliance Score", f"{score}%")
            col2.metric("Rules Passed", f"{pass_count} / {total_rules}")
            col3.metric("Critical Gaps", f"{total_rules - pass_count}")

            st.divider()

            # Display Detailed Report
            st.subheader("📝 Detailed Audit Report")
            
            for res in results:
                # Color code the expander based on status
                icon = '✅' if res['status'] == 'PASS' else '🔴'
                label = f"{icon} {res['rule_id']} (Match Confidence: {res['match_score']}%)"
                
                with st.expander(label):
                    st.markdown(f"**Legal Requirement:**\n{res['requirement']}")
                    st.divider()
                    if res['status'] == 'PASS':
                        st.success(f"**Company Policy Matches:** \n> \"{res['company_clause']}\"")
                    else:
                        st.error(f"**Gap Detected:** The policy does not adequately address this rule.")
                        st.markdown("*Recommendation: Add a specific clause addressing this requirement.*")
