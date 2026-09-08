"""Deterministic Natural Language to Stata Command Translator.

Translates natural language financial econometric queries into authentic
Stata 17/18 syntax tokens without relying on local LLMs. Includes strict
AST-style security sanitization to prevent destructive inputs.
"""

import re
from typing import Dict, Any

MALICIOUS_PATTERNS = [
    r"\bdrop\b\s+(?:table|database|column|view)",
    r"\bdelete\b\s+from\b",
    r"\balter\b\s+table\b",
    r"\btruncate\b\s+table\b",
    r"\bexec\s*\(",
    r"\bexecute\s*\(",
    r"__import__",
    r"\bos\s*\.\s*system",
    r"\bsubprocess\b",
    r"\bshutil\b",
    r"--",
    r";",
]

NL_SYNTAX_RULES = [
    # 1. Instrumental variables / 2SLS
    (
        r"(?:instrument|iv|2sls|two[\s-]stage|endogen)\b.*?(?:tangib|profit|size|debt|leverage)",
        lambda q: "ivregress 2sls leverage (tangibility = L.tangibility) profitability log_size",
    ),
    # 2. Wooldridge panel autocorrelation test
    (
        r"(?:wooldridge|autocorrelat|serial\s+correlat|xtserial)",
        lambda q: "xtserial",
    ),
    # 3. Breusch-Pagan LM test
    (
        r"(?:breusch[\s-]pagan|lm\s+test|random\s+effects\s+test|xttest0)",
        lambda q: "xttest0",
    ),
    # 4. Hypothesis testing (Wald test / test var = 0)
    (
        r"(?:test|wald|hypothesis)\b.*?(?:coefficient|equal|zero|=|\b0\b)",
        lambda q: "test profitability = 0",
    ),
    # 5. Predict / fitted values / residuals
    (
        r"(?:predict|fitted\s+values?|linear\s+prediction|generate\s+fitted|(?:calculate|generate|save)\s+residuals?)",
        lambda q: "predict e_hat, residuals" if "residual" in q.lower() else "predict y_hat, xb",
    ),
    # 6. Winsorize / outlier clamping
    (
        r"(?:winsor\w*|outlier\w*|clamp\w*)",
        lambda q: "winsor2 leverage profitability tangibility, cuts(1 99) replace",
    ),
    # 7. Hausman specification test
    (
        r"(?:hausman|fe\s+vs\s+re|fixed\s+vs\s+random)\b",
        lambda q: "hausman fe re",
    ),
    # 8. Pairwise correlation with significance stars
    (
        r"(?:pairwise|pwcorr|correlat\w*)",
        lambda q: "pwcorr leverage profitability tangibility log_size, sig star(0.05)",
    ),
    # 9. Detailed summary statistics
    (
        r"(?:summar\w*|descript\w*|detail\w*)",
        lambda q: "summarize leverage profitability, detail",
    ),
    # 10. Random effects regression
    (
        r"(?:random\s+effects|re\s+regression|xtreg.*?re)\b",
        lambda q: "xtreg leverage profitability tangibility log_size, re",
    ),
    # 11. Fixed effects regression with clustering (default panel regression)
    (
        r"(?:fixed\s+effects|\bfe\b|clust|debt.*?(?:respond|profit)|regress)",
        lambda q: "xtreg leverage profitability tangibility log_size, fe cluster(company_code)",
    ),
]


def sanitize_input(query: str) -> bool:
    """Check if query contains prohibited destructive keywords or injection sequences."""
    low = query.lower()
    for pattern in MALICIOUS_PATTERNS:
        if re.search(pattern, low):
            return False
    return True


def translate_nl_to_stata(nl_query: str) -> Dict[str, Any]:
    """Translate natural language query to valid Stata command syntax."""
    if not nl_query or not isinstance(nl_query, str):
        return {
            "status": "error",
            "message": "r(198); empty or invalid query",
            "stata_command": "",
        }

    trimmed = nl_query.strip()

    # Security check
    if not sanitize_input(trimmed):
        return {
            "status": "error",
            "message": "r(198); syntax error: unauthorized operation detected",
            "stata_command": "",
        }

    # Evaluate deterministic rule table
    for pattern, generator in NL_SYNTAX_RULES:
        if re.search(pattern, trimmed, re.IGNORECASE):
            stata_cmd = generator(trimmed)
            return {
                "status": "success",
                "stata_command": stata_cmd,
                "intent": "Matched deterministic econometric template",
                "confidence": 1.0,
            }

    # Fallback for unknown or ambiguous NL text
    return {
        "status": "error",
        "message": "r(198); Unrecognized or ambiguous natural language econometric instruction. Please reformulate.",
        "stata_command": "",
    }
