import streamlit as st
import pandas as pd
import plotly.express as px
import warnings
warnings.filterwarnings("ignore")
from sentence_transformers import SentenceTransformer, util

# ==========================================
# 🧠 PART 1: THE AI ENGINE (Backend Logic)
# ==========================================
class ComplianceAuditor:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        # Load the model only once
        self.model = SentenceTransformer(model_name)
        self.rules = self._load_rules()
        
        # Pre-compute embeddings for speed
        if self.rules:
            self.rule_texts = [r['text'] for r in self.rules]
            self.rule_embeddings = self.model.encode(self.rule_texts, convert_to_tensor=True)
        else:
            self.rule_embeddings = None

    def _load_rules(self, filename='dpdp_rules.txt'):
        """Parses the rule file (Format: Rule ID: Rule Text)"""
        parsed_rules = []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    if ':' in line:
                        rule_id, rule_text = line.split(':', 1)
                        parsed_rules.append({
                            'id': rule_id.strip(),
                            'text': rule_text.strip()
                        })
            return parsed_rules
        except FileNotFoundError:
            return []

    def audit_policy(self, policy_text, threshold=0.50):
        if not policy_text or not self.rules:
            return []
        
        # Split policy into meaningful chunks
        policy_chunks = [p.strip() for p in policy_text.split('\n') if len(p) > 20]
        
        if not policy_chunks:
            return []

        # Vectorize the policy text
        policy_embeddings = self.model.encode(policy_chunks, convert_to_tensor=True)
        
        audit_results = []

        for i, rule in enumerate(self.rules):
            scores = util.cos_sim(self.rule_embeddings[i], policy_embeddings)[0]
            best_match_idx = scores.argmax().item()
            score = scores[best_match_idx].item()
            matched_text = policy_chunks[best_match_idx]
            
            is_compliant = score > threshold 
            
            audit_results.append({
                'rule_id': rule['id'],
                'requirement': rule['text'],
                'match_score': round(score * 100, 1),
                'status': 'PASS' if is_compliant else 'FAIL',
                'company_clause': matched_text if is_compliant else "No matching clause found."
            })
            
        return audit_results

# ==========================================
# 🎨 PART 2: THE APP UI (Frontend)
# ==========================================
st.set_page_config(
    page_title="DPDP 2025 Auditor",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0px 2px 5px rgba(0,0,0,0.05); }
    div[data-testid="stExpander"] { border: none; box-shadow: 0px 2px 5px rgba(0,0,0,0.05); background-color: white; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Header
col1, col2 = st.columns([1, 5])
with col1:
    st.markdown("## ⚖️")
with col2:
    st.title("DPDP Act 2025 Compliance Auditor")
    st.markdown("Automated legal gap analysis for Indian Data Protection Standards.")

st.divider()

# Sidebar
with st.sidebar:
    st.header("⚙️ Audit Configuration")
    threshold = st.slider("Strictness Level (Threshold)", 0.30, 0.80, 0.50, 0.05)
    st.caption("Lower = More lenient. Higher = Stricter.")
    st.divider()
    st.header("📄 Document Input")
    uploaded_file = st.file_uploader("Upload Policy (TXT)", type="txt")
    text_input = st.text_area("Or paste text directly:", height=150)
    st.info("💡 **Tip:** Ensure the policy contains the full text including 'Contact Us' sections.")

# Initialize AI Engine
@st.cache_resource
def load_auditor():
    return ComplianceAuditor()

try:
    auditor = load_auditor()
except Exception as e:
    st.error(f"❌ Critical Error: Could not load AI Engine. {e}")
    st.stop()

# Main Logic
policy_content = ""
if uploaded_file:
    policy_content = uploaded_file.read().decode("utf-8")
elif text_input:
    policy_content = text_input

if st.button("🚀 Run Compliance Audit", type="primary", use_container_width=True):
    if not policy_content:
        st.warning("⚠️ Please upload a document or paste text to begin.")
    else:
        with st.spinner("🤖 AI is analyzing legal clauses against 2025 Rules..."):
            results = auditor.audit_policy(policy_content, threshold=threshold)
        
        if not results:
            st.error("❌ No results generated. Check if 'dpdp_rules.txt' is loaded correctly.")
        else:
            # Metrics
            pass_count = sum(1 for r in results if r['status'] == 'PASS')
            total_rules = len(results)
            score = int((pass_count / total_rules) * 100) if total_rules > 0 else 0
            
            st.subheader("📊 Audit Dashboard")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Compliance Score", f"{score}%")
            m2.metric("Rules Analyzed", total_rules)
            m3.metric("Passed Clauses", pass_count, delta="Safe")
            m4.metric("Critical Gaps", total_rules - pass_count, delta="-High Risk", delta_color="inverse")
            
            st.divider()

            # Visualization
            c1, c2 = st.columns([1, 2])
            with c1:
                chart_data = pd.DataFrame({
                    "Status": ["Compliant", "Gaps"],
                    "Count": [pass_count, total_rules - pass_count]
                })
                fig = px.pie(chart_data, values='Count', names='Status', hole=0.5,
                             color='Status', color_discrete_map={'Compliant':'#00CC96', 'Gaps':'#EF553B'})
                fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=200)
                st.plotly_chart(fig, use_container_width=True)
            
            with c2:
                st.markdown("#### Risk Assessment")
                if score > 80: st.success("This policy is largely compliant. Review minor gaps.")
                elif score > 50: st.warning("Moderate Risk. Significant updates required for 2025 compliance.")
                else: st.error("High Risk. Policy likely predates the 2025 Act.")
            
            # Detailed Report
            st.subheader("📝 Detailed Findings")
            tab1, tab2 = st.tabs(["🔴 Gaps & Violations", "✅ Compliant Clauses"])
            
            with tab1:
                gaps = [r for r in results if r['status'] == 'FAIL']
                if not gaps: st.info("No gaps detected! 🎉")
                for res in gaps:
                    with st.expander(f"🔴 {res['rule_id']} (Confidence: {res['match_score']}%)"):
                        st.markdown(f"**Missing Requirement:**")
                        st.code(res['requirement'], language="text")
                        st.markdown("**Recommendation:** *Add a specific clause addressing this requirement.*")

            with tab2:
                passes = [r for r in results if r['status'] == 'PASS']
                if not passes: st.info("No compliant clauses found.")
                for res in passes:
                    with st.expander(f"✅ {res['rule_id']} (Confidence: {res['match_score']}%)"):
                        st.markdown(f"**Requirement:** {res['requirement']}")
                        st.success(f"**Found in Policy:**\n> \"{res['company_clause']}\"")
            
            # Download
            st.divider()
            df = pd.DataFrame(results)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Full Audit Report (CSV)", csv, 'dpdp_audit_report.csv', 'text/csv')
