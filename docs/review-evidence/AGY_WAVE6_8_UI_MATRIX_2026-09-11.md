# Wave 6-8 UI Matrix Validation

## Overview
This matrix validates the UI rendering, theme states, user context isolation, and page navigation for all 4 profiles.

## Execution Status
**Status:** BLOCKED
**Blocker:** The provided UI testing harness (`scratch/run_25_dual_matrix_8501.py`) only implements logic for 2 users (`drbhatia`, `profsurkumar`) and does not toggle or test theme selection logic (Light vs Dark). 

## Four-Profile Matrix

| Profile | Theme | Login | Root Render | Sidebar Nav | Active Panel Isolation | Cross-Bleed | Stale Rerun State |
|---------|-------|-------|-------------|-------------|------------------------|-------------|-------------------|
| profsurkumar | Light | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| profsurkumar | Dark | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| skumar | Light | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| skumar | Dark | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| drbhatia | Light | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| drbhatia | Dark | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| sbhatia | Light | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| sbhatia | Dark | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |

## UI Observations
- Missing automated harness capability for `skumar`, `sbhatia`, and Light/Dark toggling.
