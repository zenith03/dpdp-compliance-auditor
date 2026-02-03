import warnings
warnings.filterwarnings("ignore")

from sentence_transformers import SentenceTransformer, util

print("--- 🕵️ AUTOMATED COMPLIANCE AUDIT INITIATED ---")

# 1. LOAD THE AI MODEL
print("[+] Loading Legal AI Model (MiniLM-L6)...")
model = SentenceTransformer('all-MiniLM-L6-v2')

def read_file(filename):
    """Reads a text file and cleans it up."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            text = f.read()
            # Split by lines and remove empty ones
            return [line.strip() for line in text.split('\n') if len(line) > 10]
    except FileNotFoundError:
        print(f"❌ ERROR: Could not find '{filename}'. Make sure it's in the same folder!")
        return []

# 2. INGEST DATA
print("\n[+] Reading Policy Documents...")
rules = read_file('dpdp_rules.txt')
policies = read_file('company_policy.txt')

if not rules or not policies:
    print("⚠️ STOPPING: Missing data files.")
else:
    # 3. VECTORIZE (Convert Text to Numbers)
    print(f"[+] Analyzing {len(rules)} Regulatory Rules against {len(policies)} Company Policies...")
    rule_embeddings = model.encode(rules, convert_to_tensor=True)
    policy_embeddings = model.encode(policies, convert_to_tensor=True)

    # 4. GENERATE REPORT
    print("\n" + "="*60)
    print(f"{'RISK GOVERNANCE REPORT':^60}")
    print("="*60 + "\n")

    for i, rule in enumerate(rules):
        # Clean up rule text for display (take first 60 chars)
        rule_short = rule[:60] + "..." if len(rule) > 60 else rule
        print(f"RULE {i+1}: {rule_short}")
        
        # FIND BEST MATCH
        scores = util.cos_sim(rule_embeddings[i], policy_embeddings)[0]
        best_match_idx = scores.argmax().item()
        score = scores[best_match_idx].item()
        matched_policy = policies[best_match_idx]
        
        # DECISION THRESHOLD (0.45 is a good balance)
        if score > 0.45:
            confidence = int(score * 100)
            print(f"  ✅ COMPLIANT ({confidence}% Confidence)")
            print(f"     Mapped to: \"{matched_policy[:80]}...\"")
        else:
            print(f"  🔴 GAP DETECTED - HIGH RISK")
            print(f"     Action Required: Draft policy for this rule.")
        
        print("-" * 60)

    print("\n[+] Audit Complete.")