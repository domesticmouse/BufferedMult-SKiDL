# LinkedIn Posts & Short-Form Social

Brett's LinkedIn posts are concise, authentic, and completely free of typical "LinkedIn bro-etry" (no single-sentence line-break spam, no engagement-bait questions like *"Agree? 👇"*, no heavy emoji bullet lists, and no hashtag stuffing).

They generally fall into four patterns:

---

## 1. The Industry Observation / Cultural Case Study (1–2 Paragraphs)

Starts with a bold thesis anchored in a specific, unexpected niche example (like a cheap hardware synth), details what the community is doing with it, and pivots (`"But the real thing here is..."`) to the broader business or software engineering implication.

**Structure**:
1. **Hook**: Connect a big industry theme (like the future of AI software development) to a concrete, slightly quirky object.
2. **Colourful Evidence**: Mention real prices (`AU$75`), community nicknames (`"Temu DX7"`), hardware details (`"cute OLED display"`), and wild community creations.
3. **Strategic Takeaway**: Pivot to what this means for product design, sales, or PMF.

**Example**:
> *"If you want to see the future of software development with AI, look at how the synth scene is adopting the M Vave FM-1. Yes, it is a AU$75 Synth. It has even been called the Temu DX7. But, the real eye opener is that the entire synth world is going mad for this device because everyone is figuring out how to use AI to build custom firmwares for this lil synth. The fact that the MCU is probably over powered for this class of device, and there is a cute OLED display totally helps. It comes out of the box with a polyphonic FM synth, but I've seen drone synths and drum machines, I'm seeing analog style synths, I'm even seeing people one-shotting "hardcore metal synths".*
>
> *But the real thing here is that allowing your customers to re-design your product using AI is actually becoming a massive positive for sales. I'm actually wondering how long before the M Vave FM-1 becomes a MBA case study for engaging communities and finding PMF after shipping a device. This is totally not how music hardware sales used to work."*

---

## 2. The Article Share / Thesis Teaser (2 Sentences)

When sharing a new Medium post or technical article, avoid "I'm excited to announce my new blog post!" Instead, state the ongoing industry debate in one sentence, and offer your distilled hypothesis in the second:

**Example**:
> *"There has been an ongoing conversation about whether Model Context Protocol (MCPs) or Command Line Apps (CLIs) are the better interface for LLMs to interact with the world. I'm starting to think the answer may actually be a domain specific API library in a programming language that the LLMs are competent at writing."*

---

## 3. The Tool / Release Reshare with Wry Speaker Humour (2 Sentences)

When resharing product updates or release notes, acknowledge the momentum, add a relatable behind-the-scenes observation (like live-demo anxiety), and close warmly with a classic text smiley `=)`.

**Example**:
> *"The Antigravity app keeps shipping new capabilities. Slightly concerning seeing an update just before stepping on stage to demonstrate how to use the tool, but always fun to have new toys to play with =)"*

---

## 4. The Event & Peer Shout-Out (1–2 Sentences)

Warm, collegial, and direct endorsements of peers' talks or event turnouts:

**Examples**:
> *"I can vouch that Katie’s talk is indeed a fun and insightful talk that is totally worth seeing live and in person. So much AI, so little time."*

> *"Brisbane delivered on the amazing attendees front!"*

---

## Frontmatter Convention in This Repository

LinkedIn posts stored in `linkedin-posts/` use the following YAML frontmatter:

```yaml
---
date: YYYY-MM-DDTHH:MM:SS.sssZ
url: https://www.linkedin.com/posts/...
reshared_author: "Optional Author Name"
reshared_author_url: https://www.linkedin.com/in/...
shared_title: "Optional Shared Article Title"
shared_url: https://...
---
```
