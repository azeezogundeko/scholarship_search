---
title: Find Fully Funded AI Scholarships
description: Search for fully funded PhD/Masters scholarships in AI matching my research profile
recurring: weekly
output_type: google_sheets
sheet_name: AI_Scholarships
max_results: 30
search_depth: 2
attachments:
  - attachments/sample_cv.txt
---

# Task: Find Fully Funded AI Scholarships

## Objective
Find fully funded scholarships for PhD or Masters programs in Artificial Intelligence, Machine Learning, and related fields that match my research interests and qualifications.

## Requirements

1. **Search Strategy**
   - Search for "fully funded AI PhD scholarships 2025"
   - Search for "machine learning masters scholarships"
   - Search for "computer vision PhD funding"
   - Check university scholarship pages
   - Look for research fellowship programs

2. **Eligibility Criteria**
   - Must be fully funded (tuition + stipend)
   - Related to: AI, Machine Learning, Computer Vision, NLP, or Deep Learning
   - Open to international students or my nationality
   - Application deadline not passed

3. **Information to Extract**
   For each scholarship found, extract:
   - **Title**: Scholarship/program name
   - **University/Institution**: Where it's offered
   - **Deadline**: Application deadline date
   - **Link**: URL to scholarship page or application
   - **Funding**: What's covered (tuition, stipend, travel, etc.)
   - **Eligibility**: Key eligibility requirements
   - **Research Areas**: Specific AI/ML topics covered
   - **Country**: Location of the program

4. **Relevance Ranking**
   - Read my CV/research interests from the attachment
   - Rank scholarships by how well they match my profile
   - Add a "relevance_score" field (1-10) and "match_reason"

5. **Output Format**
   Save results to Google Sheets with columns:
   - Title
   - University
   - Country
   - Deadline
   - Link
   - Funding Details
   - Research Areas
   - Eligibility
   - Relevance Score
   - Match Reason
   - Date Found

## Execution Notes
- Follow links to scholarship pages to get complete information
- Check multiple sources (university websites, scholarship databases, etc.)
- Filter out expired deadlines
- Prioritize recent postings
- Include both PhD and Masters opportunities
