import warnings
warnings.filterwarnings("ignore")
from sentence_transformers import SentenceTransformer, util

class ComplianceAuditor:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        print("[+] Loading Legal AI Model...")
        self.model = SentenceTransformer(model_name)
        self.rules = self._load_rules()
        # Pre-compute rule embeddings for speed
        self.rule_texts = [r['text'] for r in self.rules]
        self.rule_embeddings = self.model.encode(self.rule_texts, convert_to_tensor=True)

    def _load_rules(self, filename='dpdp_rules.txt'):
        """Parses the structured rule file."""
        parsed_rules = []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    if ':' in line:
                        # Split at the first colon only
                        rule_id, rule_text = line.split(':', 1)
                        parsed_rules.append({
                            'id': rule_id.strip(),
                            'text': rule_text.strip()
                        })
            print(f"[+] Loaded {len(parsed_rules)} DPDP 2025 Rules.")
            return parsed_rules
        except FileNotFoundError:
            print("❌ ERROR: 'dpdp_rules.txt' not found!")
            return []

    def audit_policy(self, policy_text):
        """Compares a privacy policy against the DPDP rules."""
        if not policy_text or not self.rules:
            return []

        # Split policy into chunks (paragraphs) for better matching
        policy_chunks = [p.strip() for p in policy_text.split('\n') if len(p) > 20]
        policy_embeddings = self.model.encode(policy_chunks, convert_to_tensor=True)

        audit_results = []

        print(f"[+] Auditing {len(policy_chunks)} policy segments against {len(self.rules)} rules...")

        for i, rule in enumerate(self.rules):
            # Find the best matching paragraph in the policy
            scores = util.cos_sim(self.rule_embeddings[i], policy_embeddings)[0]
            best_match_idx = scores.argmax().item()
            score = scores[best_match_idx].item()
            matched_text = policy_chunks[best_match_idx]

            # Strict Threshold for Legal Compliance
            is_compliant = score > 0.45 

            audit_results.append({
                'rule_id': rule['id'],
                'requirement': rule['text'],
                'match_score': round(score * 100, 1),
                'status': 'PASS' if is_compliant else 'FAIL',
                'company_clause': matched_text if is_compliant else "No matching clause found."
            })

        return audit_results
