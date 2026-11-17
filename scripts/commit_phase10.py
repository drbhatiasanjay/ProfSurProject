import subprocess
import sys

def run(cmd):
    print(f"Running: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if res.stdout:
        print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)
    return res.returncode

def main():
    # Add target files
    files = [
        "frontend/src/types/terminal.ts",
        "frontend/src/services/dataService.ts",
        "frontend/src/components/CompactCockpitHUD.tsx",
        "frontend/src/components/LintelTowers.tsx",
        "frontend/src/components/StatutoryOfferHero.tsx",
        "frontend/src/components/vaults/ProvenanceLedgerVault.tsx",
        "models/pre_ipo_capability_gate.py",
        "api/server.py",
        "tests/test_assert_capability_allowed.py",
        "tests/test_api_capability_gate.py",
        "progress.md",
        "scripts/commit_phase10.py"
    ]
    for f in files:
        run(["git", "add", f])
        
    # Check staged status
    run(["git", "--no-pager", "diff", "--staged", "--stat"])
    
    # Commit
    msg = "feat(pre-ipo): refactor DealPricingState, SEBI Capability Gate, and ProvenanceField into discriminated unions"
    code = run(["git", "commit", "-m", msg])
    if code == 0:
        print("Commit successful!")
        run(["git", "--no-pager", "log", "-n", "3", "--oneline"])
    else:
        print(f"Commit exited with code {code}")

if __name__ == "__main__":
    main()
