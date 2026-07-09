---
tags: [seed, ai-llm]
---

# Tokenization

Language models operate on tokens, not raw characters — subword schemes like byte-pair encoding split text into common fragments so rare words still decompose into known pieces. Token count drives both cost and the context-window budget. Whitespace and punctuation are tokens too, which is why prompt formatting affects length.
