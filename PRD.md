# PRD — AI GitHub Repo Digest

## 1. Product Overview

**AI GitHub Repo Digest** is a web application that automatically converts interesting GitHub repositories into structured blog articles.

Instead of manually writing summaries, an admin only needs to paste **text from social media** (for example a tweet, LinkedIn post, or Reddit comment).  
The system will then:

1. Extract the **GitHub repository URL**
2. Analyze the repository
3. Generate a **structured blog post**
4. Allow the admin to review and publish the article

The website acts like an **online tech magazine** that curates useful frameworks and libraries from GitHub.

---

# 2. Goals

Primary goals:

- Quickly convert interesting GitHub repositories into readable articles
- Build a searchable library of frameworks and developer tools
- Reduce time spent browsing social media for useful repos

Secondary goals:

- Allow readers to **like, bookmark, and comment**
- Organize articles with **AI-generated tags**

---

# 3. Scope (Phase 1)

## Included Features

- Admin pastes text containing a GitHub repo mention
- AI extracts the GitHub repository URL
- AI analyzes the repository
- AI generates a blog article (Vietnamese and English)
- Language toggle button on article page
- Admin review and publish
- Online magazine-style article pages
- AI-generated tags
- Keyword search
- User login
- Like articles
- Save favorite articles
- Comment system
- Admin comment moderation

---

## Excluded Features (Future Phases)

- Chrome extension for saving posts
- Trending algorithm
- GitHub automatic re-sync
- Newsletter generation
- Collections
- Semantic/vector search

---

# 4. System Architecture

## Backend

FastAPI will handle:

- REST API
- AI processing pipeline
- Authentication integration
- Content management

Recommended stack:
FastAPI
Python
OpenAI / LLM API


---

## Frontend

The frontend can follow a **traditional MVC structure**.

React frontend
FastAPI backend API

---

## Database

Only one database will be used: Supabase (PostgreSQL) - using supabase free tierservice so will need to integrate key


Database features used:

- relational tables
- basic full-text search (optional)

Not used:

- vector databases
- embedding search
- heavy AI indexing

This keeps the system lightweight enough to run on a **mini PC server**.

---

# 5. Database Schema

## 5.1 Users

| field | type |
|------|------|
| id | uuid |
| email | text |
| username | text |
| avatar_url | text |
| created_at | timestamp |
| role | enum (admin, user) |

---

## 5.2 GitHub Repositories

Only minimal repository information is stored.

| field | type |
|------|------|
| id | uuid |
| repo_name | text |
| github_url | text |
| created_at | timestamp |

---

## 5.3 Posts

Main blog articles.

| field | type |
|------|------|
| id | uuid |
| title_vi | text |
| title_en | text |
| slug | text |
| summary_vi | text |
| summary_en | text |
| content_markdown_vi | text |
| content_markdown_en | text |
| cover_image | text |
| repo_id | uuid |
| status | enum (draft, published) |
| created_at | timestamp |
| published_at | timestamp |
| views | integer |

---

## 5.4 Tags

| field | type |
|------|------|
| id | uuid |
| name | text |
| slug | text |

---

## 5.5 Post Tags (Many-to-Many)

| field | type |
|------|------|
| post_id | uuid |
| tag_id | uuid |

---

## 5.6 Likes

| field | type |
|------|------|
| id | uuid |
| user_id | uuid |
| post_id | uuid |
| created_at | timestamp |

---

## 5.7 Saved Posts

Bookmarks for users.

| field | type |
|------|------|
| id | uuid |
| user_id | uuid |
| post_id | uuid |
| created_at | timestamp |

---

## 5.8 Comments

| field | type |
|------|------|
| id | uuid |
| post_id | uuid |
| user_id | uuid |
| content | text |
| created_at | timestamp |
| status | enum (visible, deleted) |

Admins have permission to **delete comments if necessary**.

---

# 6. AI Processing Pipeline

## Input

Admin pastes text copied from a social network.

Example:
Just discovered an amazing AI agent framework.

https://github.com/crewAIInc/crewAI


---

## Step 1 — Extract GitHub URL

AI parses the text and extracts the GitHub repository URL.

Example result:
https://github.com/crewAIInc/crewAI


---

## Step 2 — Fetch Repository Information

The system retrieves basic repository information such as:

- README
- documentation
- examples
- repository description

---

## Step 3 — AI Analysis

The AI analyzes the repository to understand:

- what problem the project solves
- key features
- architecture
- example usage

---

## Step 4 — Generate Blog Article

The AI generates a structured article with the following format (create both Vietnamese and English versions):
Title

Introduction

What problem this project solves

Key features

How it works

Example usage

Why this project is interesting

GitHub repository link


---

## Step 5 — Generate Tags

The AI automatically generates tags.

Example:
AI
Agents
Python
Automation
LLM Tools


---

## Step 6 — Save Draft

The generated article is saved as a **draft**.

Admin can:

- review
- edit
- publish

---

# 7. Website Features

## 7.1 Homepage

The homepage displays:

- latest articles
- featured article
- tag sidebar

Example layout:
Featured Article

Latest Articles List

Tag Sidebar


---

## 7.2 Article Page

Each article page includes:

- title
- summary
- GitHub repository link
- tags
- article content
- like button
- save button
- comments

---

## 7.3 Tag Page

Example:
/tag/ai-agents


Displays:

- all articles associated with that tag

---

## 7.4 Search

Search is implemented as **simple keyword search**.

Search fields:

- title
- summary
- tags

Example SQL:
ILIKE %keyword%

## 7.5 User Accounts

Users can:

- register
- log in
- like articles
- save articles
- comment

Authentication can use: Supabase Auth


---

## 7.6 Favorite Articles

Users can view their bookmarked articles.

Example page:
/favorites


Displays:

- saved articles list

---

## 7.7 Admin Panel

Admin capabilities include:

- submit new text input
- review generated articles
- edit articles
- publish articles
- delete comments

---

# 8. User Flows

---

## Flow 1 — Submit Content
Admin pastes text
↓
AI extracts GitHub URL
↓
System fetches repository
↓
AI generates article
↓
Draft saved
↓
Admin edits
↓
Publish


---

## Flow 2 — Reader
User opens homepage
↓
User clicks article
↓
User reads article
↓
User likes or saves article


---

## Flow 3 — Comment
User opens article
↓
User writes comment
↓
Comment posted
↓
Admin can delete comment if needed


---

## Flow 4 — Search
User enters keyword
↓
System searches title + summary + tags
↓
Matching articles displayed





