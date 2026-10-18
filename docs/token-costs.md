# Technical note: why images consume tokens fast

How chat models price a picture, with the per-provider math behind the
README's claim that a screenshot costs 15–50× more than the text it carries.

**TL;DR** — Vision chat models convert an image into a grid of tiles and bill
each tile as a fixed number of tokens. Cost therefore scales with the image's
*resolution*, not its *content*: a full-screen capture with one dialog in the
corner is billed like a dense page. The image is re-sent on every turn of the
conversation, and the model's own OCR of your screenshot is error-prone enough
to trigger correction rounds. Pasting the text avoids all three.

## 1. What text costs

Tokenizers chunk English at roughly **4 characters ≈ 1 token** (≈1.3 tokens
per word):

- a 50-word paragraph ≈ **65 tokens**
- one error line like `Error 0x80070005: Access denied` ≈ **10 tokens**

## 2. What images cost

Before the model "sees" anything, a vision encoder slices the image into
tiles; each tile becomes a fixed token count. The schemes (as documented in
October 2026 — they do change):

### OpenAI (GPT-4o / GPT-4.1 class)

- *low detail*: flat **85 tokens**, image heavily downscaled first
- *high detail*: `85 + 170 × tiles`, where `tiles = ceil(w/512) × ceil(h/512)`
  after the image is scaled to fit 2048×2048
- example: 1920×1080 → `4 × 3 = 12` tiles → **~2,125 tokens**

### Anthropic (Claude)

- `tokens ≈ (width × height) / 750`, after scaling the long edge to ≤1568 px
- example: 1920×1080 → resized to 1568×882 → **~1,850 tokens**

### Google (Gemini)

- **~258 tokens per 768×768 tile** of the resized image (small images: flat 258)
- example: 1920×1080 → resized to ~1536×864 → 4 tiles → **~1,030 tokens**

## 3. The multiplier, worked

Same 50-word paragraph (~65 tokens of text), delivered as a 1920×1080
screenshot:

| Delivery | Tokens | Multiplier |
|---|---|---|
| Pasted text | ~65 | 1× |
| Screenshot — OpenAI high detail | ~2,125 | ~33× |
| Screenshot — Anthropic | ~1,850 | ~28× |
| Screenshot — Gemini | ~1,030 | ~16× |

Cropping to the content helps — an 800×600 capture is ~640–765 tokens on
these schemes — but the text still wins by an order of magnitude, and users
rarely crop.

## 4. You pay again every turn

Chat is stateless: the whole conversation — image included — is re-sent with
each follow-up. Prompt caching softens this (providers discount *cached*
input, commonly 50–90% off, when the prefix is unchanged), but the first send
always pays full price and any context change re-bills. A ten-message
discussion around one screenshot can cost more input tokens than a hundred
messages around its pasted text.

## 5. The quality tax

Reading text out of pixels is genuinely hard for vision encoders: small font
sizes, anti-aliasing, subpixel rendering and stylized UI fonts cause misreads
— and occasionally hallucinated glyphs that were never on screen. Each
"no, it says 0x80070005, not 0x8OO7OOO5" correction round re-sends the image
*and* adds tokens. Most chat UIs never show token counts, so none of this
cost is visible until a quota or bill is hit.

## 6. Second-order costs

- **Bandwidth/latency**: a PNG is megabytes; text is bytes. On mobile links
  the upload alone can dominate.
- **Quotas**: free tiers and rate limits are usually denominated in tokens
  per day — a screenshot habit consumes in three messages what a week of
  pasted text would use.
- **Compatibility**: terminals, API integrations and text-only clients reject
  images outright.

## 7. Measure it yourself

Every API returns the input token count. Send the same question twice — once
with a base64 screenshot attached, once with the extracted text pasted — and
compare `usage.prompt_tokens`:

```python
# with any provider SDK:
#   r1 = client.chat(model=..., messages=[{role: user, content: [image, "what does this say?"}]}])
#   r2 = client.chat(model=..., messages=[{role: user, content: "what does this say? <pasted text>"}])
# print(r1.usage.prompt_tokens, r2.usage.prompt_tokens)
```

## 8. What snaptext does about it

snaptext performs the OCR *locally* (RapidOCR on ONNX Runtime) and hands you
exact text — ~60 tokens for the example above instead of thousands, no image
ever entering context, and ` [?]` markers flagging the passages a human
should verify before trusting them in a prompt.

## References

- OpenAI, *Vision — calculating costs*: <https://platform.openai.com/docs/guides/vision>
- Anthropic, *Vision (image tokenization)*: <https://docs.anthropic.com/en/docs/build-with-claude/vision>
- Google, *Gemini API — image understanding*: <https://ai.google.dev/gemini-api/docs/vision>

*Figures reflect provider documentation as of October 2026; tiling schemes
and prices change, so treat the numbers as illustrative and re-verify with
the method in §7.*
