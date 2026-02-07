import streamlit as st
import warnings
warnings.filterwarnings("ignore")
from sentence_transformers import SentenceTransformer, util

# --- BACKEND CLASS (AI ENGINE) ---
class ComplianceAuditor:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        # Using st.cache_resource inside the class isn't ideal, 
        # so we load the model once in the main app logic below.
        self.model = SentenceTransformer(model_name)
        self.rules = self._load_rules()
        self.rule_texts = [r['text'] for r in self.rules]
        self.rule_embeddings = self.model.encode(self.rule_texts, convert_to_tensor=True)

    def _load_rules(self, filename='dpdp_rules.txt'):
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
            st.error("❌ ERROR: 'dpdp_rules.txt' not found!")
            return []

    def audit_policy(self, policy_text):
        if not policy_text or not self.rules:
            return []
        
        policy_chunks = [p.strip() for p in policy_text.split('\n') if len(p) > 20]
        policy_embeddings = self.model.encode(policy_chunks, convert_to_tensor=True)
        audit_results = []

        for i, rule in enumerate(self.rules):
            scores = util.cos_sim(self.rule_embeddings[i], policy_embeddings)[0]
            best_match_idx = scores.argmax().item()
            score = scores[best_match_idx].item()
            matched_text = policy_chunks[best_match_idx]
            
            is_compliant = score > 0.45 
            
            audit_results.append({
                'rule_id': rule['id'],
                'requirement': rule['text'],
                'match_score': round(score * 100, 1),
                'status': 'PASS' if is_compliant else 'FAIL',
                'company_clause': matched_text if is_compliant else "No matching clause found."
            })
        return audit_results

# --- FRONTEND (STREAMLIT) ---
st.set_page_config(page_title="DPDP 2025 Auditor", page_icon="⚖️", layout="wide")

st.title("🇮🇳 DPDP 2025 Compliance Auditor")
st.markdown("Upload a Privacy Policy to check compliance with the **Digital Personal Data Protection Rules 2025**.")

@st.cache_resource
def load_auditor():
    return ComplianceAuditor()

try:
    auditor = load_auditor()
except Exception as e:
    st.error(f"Error loading AI Engine: {e}")
    st.stop()

# Sidebar
with st.sidebar:
    st.header("Upload Policy")
    uploaded_file = st.file_uploader("Choose a text file", type="txt")
    text_input = st.text_area("Or paste policy text here:", height=200)

# Main Logic
policy_content = ""
if uploaded_file is not None:
    policy_content = uploaded_file.read().decode("utf-8")
elif text_input:
    policy_content = text_input

if st.button("🚀 Run Compliance Audit"):
    if not policy_content:
        st.warning("Please upload a file or paste text first.")
    else:
        with st.spinner("AI is analyzing legal clauses..."):
            results = auditor.audit_policy(policy_content)
        
        if not results:
            st.error("No rules found or policy text was empty.")
        else:
            pass_count = sum(1 for r in results if r['status'] == 'PASS')
            total_rules = len(results)
            score = int((pass_count / total_rules) * 100) if total_rules > 0 else 0

            col1, col2, col3 = st.columns(3)
            col1.metric("Compliance Score", f"{score}%")
            col2.metric("Rules Passed", f"{pass_count} / {total_rules}")
            col3.metric("Critical Gaps", f"{total_rules - pass_count}")
            st.divider()
            
            st.subheader("📝 Detailed Audit Report")
            for res in results:
                icon = '✅' if res['status'] == 'PASS' else '🔴'
                label = f"{icon} {res['rule_id']} (Match Confidence: {res['match_score']}%)"
                with st.expander(label):
                    st.markdown(f"**Legal Requirement:**\n{res['requirement']}")
                    st.divider()
                    if res['status'] == 'PASS':
                        st.success(f"**Company Policy Matches:** \n> \"{res['company_clause']}\"")
                    else:
                        st.error(f"**Gap Detected:** The policy does not adequately address this rule.")


