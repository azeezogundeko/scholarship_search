---
title: Track AI/ML Conference Deadlines
description: Monitor upcoming AI and ML conferences with paper submission deadlines
recurring: daily
output_type: sqlite
db_table: conferences
max_results: 20
search_depth: 1
---

# Task: Track AI/ML Conference Deadlines

## Objective
Find and track upcoming AI, Machine Learning, and Computer Vision conferences with their paper submission deadlines.

## Search Strategy
1. Search for "AI conference deadlines 2025"
2. Search for "machine learning conference CFP 2025"
3. Check AI conference aggregator sites like WikiCFP, AI Deadlines
4. Look for NeurIPS, ICML, CVPR, ICCV, ACL, EMNLP, etc.

## Information to Extract
For each conference:
- **Conference Name**: Full name and acronym
- **Year**: Conference year
- **Submission Deadline**: Abstract/paper submission deadline
- **Notification Date**: When decisions are sent
- **Conference Dates**: When the conference takes place
- **Location**: City and country (or virtual)
- **Website**: Official conference website
- **Tier**: Tier A*/A/B (if applicable)
- **Topics**: Main topic areas

## Filter Criteria
- Only include conferences in: AI, ML, CV, NLP, Data Science
- Deadline not passed
- Reputable conferences (avoid predatory conferences)

## Output
Save to SQLite database for tracking and querying.
