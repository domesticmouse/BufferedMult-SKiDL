# Medium Posts & Long-Form Articles

Brett's Medium posts generally fall into four archetypes:
1. **The Exploration / Project Narrative** (e.g., *Agent Skills vs MCPs vs LLMs Writing Code*, *Reverse Engineering a this.is.NOISE Gamma synth*)
2. **The Conversational AI / Code Walkthrough** (e.g., *Making sense of a VCV patch with Antigravity*, *Adding testing to a Flutter app*, *Sydney Flutter Jam*)
3. **The Opinionated Craft & Tooling Guide** (e.g., *Supporting six platforms with two keyboards*, *Writing a good code sample*)
4. **The Big-Picture / Economic & Tech Essay** (e.g., *Societal structure change*, *San Francisco's Solar & the House of Saud*)

---

## 1. Opening Hooks

Start immediately with a relatable human entry point—never a dry textbook definition:

- **The Self-Deprecating Confession**:
  > *"I made a horrible mistake. I liked a synth I found online so much, I wound up buying it twice."*
  > *"I recently live coded a Flutter app live on stage, without any preparation."*
  > *"I should know better than to predict what an event is going to look like in advance. But, it is alway helpful to have a plan. This is that plan."*
- **The New Hobby / Learning Angle**:
  > *"I am exploring a new hobby — designing electronics. One of the fun parts of a new hobby is coming to terms with the tools."*
  > *"When you are starting out in a new hobby, there is always a time where you are lost for words when looking at something, trying to understand how it works."*
- **The Sharp Dichotomy / Clarified Thesis**:
  > *"The joy of Flutter is the ease of developing applications for six platforms. The pain is verifying your application on six platforms."*
  > *"Authoring a good code sample is hard. Let me clarify that, putting together a sample that demonstrates the usage of an API, or shows off a UI idiom, can be quick and easy. The difficulty comes from..."*

---

## 2. Explaining Domain Concepts

When introducing niche domains (like Eurorack, OpAmps, Daisy Seed, or Flutter internals), define them with accessible, tactile analogies before diving into the mechanics:

- **Use grounded metaphors**:
  > *"What is VCV Rack, and what is a patch? VCV Rack is a virtual Eurorack modular synthesizer. It's a program for making bleep-bloop music, amongst other things... Think of it as expensive lego with patch cables and lots of blinking LEDs."*
- **Contextualize the "Why" succinctly**:
  > *"For context, in Eurorack, a Buffered Mult is a utility module that takes in a voltage signal, and sends out multiple copies of that signal... The OpAmps prevent the voltage sagging, which is important in Eurorack, because the voltage level is used to signalling things like the musical note that should be played, via the so-called 1 Volt per Octave standard."*

---

## 3. Structuring Technical Walkthroughs

- **Chronological / Git-Commit Narrative**:
  - Structure debugging or refactoring stories in the order the work actually happened, including where assumptions failed:
    > *"The reason my test failed is interesting. I assumed that the mini FABs that are shown by clicking on the main FAB aren't in the widget tree when they are hidden. Not true, they were present, just that they are exceedingly small."*
- **Prompt-and-Screenshot Loops (for AI / Antigravity Tutorials)**:
  - Introduce the goal of the step in 1–3 conversational sentences.
  - Show the exact prompt given to the agent as a markdown blockquote (`> Please run ruff over this python file`).
  - Follow with an image and an italicized caption (`*Using ruff to lint and format the Python code*`).
  - Reflect on what the agent did, especially when it did something unexpected that revealed a missing requirement:
    > *"Antigravity wrote more Python code. So there is functionality missing from the skill. Time to iterate."*
- **Dense, Evidence-Rich Hyperlinking**:
  - Instead of dumping huge walls of code inline, weave links to specific GitHub commits, directories, skills (`SKILL.md`), scripts, and header files directly into the prose.

---

## 4. Subheadings (When Used)

Shorter narrative essays (700–1,000 words) often flow without subheadings at all, relying on transitional openers (*"Now the Agent Skill..."*, *"However, if you look..."*, *"Which leads me to an interesting realisation."*).

When subheadings (`###` or `####`) are used in multi-step tutorials, make them playful and conversational:
- `### Getting Started, for the third time`
- `### Dialing up a Recipe, JSON style`
- `### Adding cheese on top, and putting it in the oven`
- `#### Getting serious, adding lint checks`
- `#### Breaking down a wall, one BLoC at a time`

---

## 5. Endings & Sign-Offs

Never end with a formal `"## Conclusion"` header. Wrap up in 1–2 short paragraphs that either:
- **Zoom out to a broader architectural or personal takeaway**:
  > *"I think it is exciting that Antigravity makes it possible to explore areas that traditionally required years of training to get started in... Having Antigravity give me timely warnings of things I might be getting wrong has given me the confidence to try new things. It's liberating!"*
- **Deliver a punchy, practical blessing**:
  > *"Your sanity will thank you. ... Your compile times will thank you."*
- **Invite the reader to play and explore**:
  > *"The world is yours to explore!"*
  > *"How about we add a colour that traces out a rainbow effect while painting? Sure!"*

---

## 6. Frontmatter Convention in This Repository

Medium posts stored in `medium-posts/` use the following YAML frontmatter:

```yaml
---
title: "Post Title"
date: YYYY-MM-DD
published_at: YYYY-MM-DDTHH:MM:SSZ
author: "Brett Morgan"
canonical_url: "https://medium.com/..."
tags:
  - tag-one
  - tag-two
---
```
