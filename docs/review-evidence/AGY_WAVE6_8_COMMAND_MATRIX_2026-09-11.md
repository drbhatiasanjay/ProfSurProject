# Wave 6-8 Command Matrix Validation

## Overview
This matrix validates the execution of 25 canonical commands through both the raw Stata Studio interface and the natural-language AI Chatbot.

## Execution Status
**Status:** FAIL (Harness Error)
**Blocker:** Test script `scratch/run_25_dual_matrix_8501.py` crashed during the AI Chatbot phase with `TypeError: Page.wait_for_function() takes 2 positional arguments but 3 positional arguments were given`.

## Command List

| Command | Expected Result | Actual Result | Status | Error Code | Graph Relevant? | Graph Rendered? | Text/Reasoning Correct? | Evidence |
|---------|----------------|---------------|--------|------------|----------------|-----------------|-------------------------|----------|
| 1. regress leverage prof profit_margin | OLS Table | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 2. xtreg leverage prof, fe | FE Table | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 3. ivregress 2sls leverage (prof = ) size | IV Table | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 4. hdfe leverage prof, absorb(non_existent_var) | Typed Error | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 5. gmm leverage prof tang, lags(1 30) | GMM Table/Unsupported | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 6. didregress leverage prof | DiD Table/Unsupported | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 7. summarize company_name, detail | Summary Stats | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 8. tabstat leverage, by(prof) | Tabstat Table | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 9. tabulate prof | Tabulate Table | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 10. pwcorr prof, star(0.05) | Correlation Matrix | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 11. hausman fe re | Hausman Test | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 12. estat vif | VIF Table | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 13. estimates store m1 | Success Msg | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 14. esttab m1 m2 | Esttab Table | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 15. xttest0 | BP Test | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 16. xtserial | Serial Cor Test | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 17. test prof = size | Wald Test | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 18. predict res, resid | Residuals saved | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 19. scatter leverage prof tang size | Scatter Matrix | N/A | FAIL | N/A | Yes | N/A | N/A | Script Crash |
| 20. histogram company_code | Histogram | N/A | FAIL | N/A | Yes | N/A | N/A | Script Crash |
| 21. graph box leverage, over(prof) | Box Plot | N/A | FAIL | N/A | Yes | N/A | N/A | Script Crash |
| 22. coefplot | Coef Plot | N/A | FAIL | N/A | Yes | N/A | N/A | Script Crash |
| 23. margins | Margins Table | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 24. predict_ml leverage prof | ML Pred/Unsupported| N/A | FAIL | N/A | No | N/A | N/A | Script Crash |
| 25. scenario leverage prof interventions... | Scenario Table | N/A | FAIL | N/A | No | N/A | N/A | Script Crash |

## AI Chat Parity Notes
- Script crashed immediately when interacting with the AI Chatbot interface.
