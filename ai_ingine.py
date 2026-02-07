import warnings
warnings.filterwarnings("ignore")
from sentence_transformers import SentenceTransformer, util
import torch

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
        """
        Audits the policy text against loaded rules.
        Args:
            policy_text (str): The full text of the privacy policy.
            threshold (float): Score cutoff for 'PASS' (0.0 to 1.0).
        """
        if not policy_text or not self.rules:
            return []
        
        # Split policy into meaningful chunks (paragraphs)
        policy_chunks = [p.strip() for p in policy_text.split('\n') if len(p) > 20]
        
        if not policy_chunks:
            return []

        # Vectorize the policy text
        policy_embeddings = self.model.encode(policy_chunks, convert_to_tensor=True)
        
        audit_results = []

        for i, rule in enumerate(self.rules):
            # Find the single best matching paragraph for this rule
            scores = util.cos_sim(self.rule_embeddings[i], policy_embeddings)[0]
            best_match_idx = scores.argmax().item()
            score = scores[best_match_idx].item()
            matched_text = policy_chunks[best_match_idx]
            
            # Compliance Decision
            is_compliant = score > threshold 
            
            audit_results.append({
                'rule_id': rule['id'],
                'requirement': rule['text'],
                'match_score': round(score * 100, 1),
                'status': 'PASS' if is_compliant else 'FAIL',
                'company_clause': matched_text if is_compliant else "No matching clause found."
            })
            
        return audit_results
