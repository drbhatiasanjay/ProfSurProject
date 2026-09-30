import re, sys

BANNED_WORDS = [
    "delve", "tapestry", "beacon", "testament to", "pivotal", "realm", "vibrant", 
    "crucial", "foster", "harness", "multifaceted", "game-changer", "seamless", 
    "bedrock", "plethora", "in today's dynamic", "in today's fast-paced", "it is worth noting"
]

def audit_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    
    findings = []
    for word in BANNED_WORDS:
        matches = list(re.finditer(rf"\b{re.escape(word)}\b", text, re.IGNORECASE))
        if matches:
            findings.append((word, len(matches)))
    
    return findings

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
        findings = audit_file(target)
        if findings:
            print(f"[FAIL] AI Slop Patterns detected in {target}:")
            for word, count in findings:
                print(f"  - '{word}': {count} instance(s)")
            sys.exit(1)
        else:
            print(f"[PASS] Clean academic prose in {target}.")
            sys.exit(0)
