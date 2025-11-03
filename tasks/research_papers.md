---
title: Find Recent Papers on Computer Vision
description: Search for and index recent research papers on computer vision topics
output_type: faiss
max_results: 50
search_depth: 1
---

# Task: Find Recent Computer Vision Papers

## Objective
Find recent (2024-2025) research papers on computer vision, image segmentation, and medical imaging, and index them in FAISS for semantic search.

## Search Strategy
1. Search for "computer vision papers 2025 image segmentation"
2. Search for "medical image analysis deep learning 2025"
3. Search for "semantic segmentation transformers"
4. Check arXiv, Papers with Code, Google Scholar

## Information to Extract
For each paper:
- **Title**: Paper title
- **Authors**: Author list
- **Abstract**: Paper abstract (full text for FAISS indexing)
- **Published Date**: Publication or upload date
- **Venue**: Conference/journal or arXiv
- **Link**: URL to paper PDF or page
- **Code**: Link to code repository if available
- **Categories**: arXiv categories or keywords

## FAISS Indexing
- Index the abstract text for semantic search
- Store metadata (title, authors, link, date) alongside vectors
- This enables semantic search like "papers about transformer-based segmentation"

## Filter Criteria
- Only papers from 2024 onwards
- Must be related to computer vision, medical imaging, or deep learning
- Prefer papers with available code
