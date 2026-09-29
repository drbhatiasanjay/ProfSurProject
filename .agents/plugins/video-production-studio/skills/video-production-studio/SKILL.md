---
name: video-production-studio
description: Enterprise automated video walkthrough production, dynamic Playwright screen-recording, neural TTS voiceover, word-aligned subtitle burning, and automated Red Team visual QA.
---

# Video Production Studio Skill

## Purpose
Automates end-to-end broadcast-grade video walkthrough generation for web platforms, ensuring 100% dynamic screen execution (live typing, submit triggers, and focal scrolling) locked to neural audio and subtitles.

## Core Capabilities
1. **Dynamic Screen Run-Up Engine:** Simulates human-like character typing into input fields (`delay=15ms`), triggers submit events, waits for real-time model streaming, and immediately resets scroll coordinates to `y=0`.
2. **Paced Focal Scrolling:** Smoothly navigates the viewport to anchor specific DOM elements in direct lockstep with sentence-level audio cues.
3. **Audio-Video Lockstep:** Generates studio neural voiceover via `edge-tts` or ElevenLabs, calculates exact word-boundary timestamps, and muxes them without audio-visual drift.
4. **Non-Obstructive Caption Burning:** Renders broadcast-standard lower-third outline subtitles (`BorderStyle=1`, `FontSize=11`, `MarginV=12`) with zero background occlusion.
5. **Automated Red Team Verification:** Extracts milestone keyframes at predetermined timestamps and certifies compliance against the 10-point rubric.

## Command Line Usage
```bash
# Produce full walkthrough with live dynamic screen execution
py -3.12 scripts/produce_ai_chatbot_demo_recordly.py

# Run Red Team 10/10 certification and keyframe extraction
py -3.12 scratch/redteam_review_recordly.py
```
