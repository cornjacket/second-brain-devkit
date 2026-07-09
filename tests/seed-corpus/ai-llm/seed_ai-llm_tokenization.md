---
tags: [seed, ai-llm]
---

# Tokenization

Language models operate on tokens, not raw characters or words — a tokenizer maps the input string to integer ids drawn from a fixed vocabulary, and the embedding layer looks up a vector for each id. Subword schemes dominate: byte-pair encoding starts from bytes and greedily merges the most frequent adjacent pairs into a learned merge table, while WordPiece and SentencePiece unigram models optimize related objectives, so rare or novel words still decompose into known subword pieces rather than becoming out-of-vocabulary. This is why a single uncommon word may span several tokens and why leading whitespace, casing, and punctuation each carry token boundaries that shift the count. Token count directly drives inference cost and consumes the context-window budget, so prompt formatting, indentation, and delimiter choices measurably change sequence length. Non-Latin scripts and code often tokenize less densely, inflating their token footprint, and the decoder detokenizes generated ids back into text at the end.
