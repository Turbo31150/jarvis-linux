---
name: auto-learn
description: "Use when the user provides preferences, facts, or workflow instructions that should be applied to future interactions."
---

# Auto-Learn Skill

This skill ensures that user preferences and important facts are preserved across sessions.

## Learning Workflow

When the user states a preference (e.g., "Always use TypeScript", "Prefer using tabs", "Speak to me in French") or teaches you a new fact about their environment:

1. **Extract the Core Fact**: Summarize the user's instruction into a concise, global preference.
2. **Save to Memory**: Immediately call the `save_memory` tool with this summarized fact.
3. **Acknowledge**: Briefly confirm to the user that you have learned and saved the preference for future sessions.
