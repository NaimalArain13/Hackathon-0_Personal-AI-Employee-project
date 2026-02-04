# Personal AI Employee Hackathon 0: Building Autonomous FTEs (Summary)

## Overview
- **Goal**: Build a "Digital FTE" (Full-Time Equivalent) - an AI agent that works like a human employee
- **Concept**: A "Smart Consultant" that proactively manages personal and business affairs 24/7
- **Focus**: High-level reasoning, autonomy, and flexibility
- **Tech Stack**: Claude Code as reasoning engine, Obsidian as management dashboard

## Architecture Components
- **The Brain**: Claude Code as reasoning engine with Ralph Wiggum Stop hook
- **The Memory/GUI**: Obsidian (local Markdown) as dashboard
- **The Senses (Watchers)**: Python scripts monitoring Gmail, WhatsApp, filesystems
- **The Hands (MCP)**: Model Context Protocol servers for external actions

## Digital FTE vs Human FTE Comparison
- **Availability**: 168 hours/week (24/7) vs 40 hours/week
- **Cost**: $500-$2,000 monthly vs $4,000-$8,000
- **Ramp-up Time**: Instant vs 3-6 months
- **Consistency**: 99%+ vs 85-95%
- **Annual Hours**: ~8,760 vs ~2,000

## Four Achievement Tiers

### Bronze Tier: Foundation (8-12 hours)
- Obsidian vault with Dashboard.md and Company_Handbook.md
- One working Watcher script (Gmail OR file system monitoring)
- Claude Code reading from and writing to vault
- Basic folder structure: /Inbox, /Needs_Action, /Done
- All AI functionality as Agent Skills

### Silver Tier: Functional Assistant (20-30 hours)
- All Bronze requirements plus:
- Two or more Watcher scripts (Gmail + WhatsApp + LinkedIn)
- Automatic LinkedIn posting
- Claude reasoning loop creating Plan.md files
- One working MCP server for external action
- Human-in-the-loop approval workflow
- Basic scheduling

### Gold Tier: Autonomous Employee (40+ hours)
- All Silver requirements plus:
- Full cross-domain integration
- Odoo Community accounting system integration
- Facebook, Instagram, and Twitter integration
- Weekly Business and Accounting Audit
- Error recovery and audit logging
- Ralph Wiggum loop for autonomous completion

### Platinum Tier: Always-On Cloud + Local Executive (60+ hours)
- All Gold requirements plus:
- 24/7 Cloud deployment (Oracle/AWS VM)
- Work-zone specialization (Cloud for triage, Local for approvals)
- Vault synchronization between Cloud and Local
- Production-level deployment

## Core Architecture Pattern
- **Perception**: Watcher scripts detect changes and create action files
- **Reasoning**: Claude Code processes files and creates plans
- **Action**: MCP servers execute external actions
- **Persistence**: Ralph Wiggum loop for continuous operation

## Key Features
- **Business Handover**: Autonomous weekly business auditing
- **Human-in-the-Loop**: Approval system for sensitive actions
- **Local-First**: Privacy-focused architecture using Obsidian
- **Continuous Operations**: Watcher scripts run indefinitely

## Security & Privacy Measures
- Credential management using environment variables
- Sandboxing and isolation for development
- Audit logging for all actions
- Permission boundaries for automated vs manual approval

## Technology Requirements
- Claude Code (Pro subscription)
- Obsidian v1.10.6+
- Python 3.13+
- Node.js v24+ LTS
- GitHub Desktop
- Hardware: Minimum 8GB RAM, 4-core CPU

## Error Handling & Recovery
- Transient error retries with exponential backoff
- Authentication failure alerts
- Graceful degradation when components fail
- Watchdog processes to restart failed services