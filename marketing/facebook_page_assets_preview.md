# Entangled Oracle — Facebook Page Assets

## Bio (72 / 101 characters)
> Precision-cast astrological reports. Ancient sky wisdom, modern clarity.

## About / Description
Entangled Oracle is a divination-focused software platform built for readers who want their astrology precise, not generic. Every Astrological Report is calculated locally with Swiss Ephemeris precision, using the Tropical zodiac and Whole Sign house system, then layered with our own proprietary interpretive indexes to surface patterns a standard chart alone won't show. The result is a personalized, in-depth reading of your placements, aspects, and the year ahead, written in clear, grounded language: symbolic and interpretive, never a guessing game and never a horoscope-column generality. Astrological Reports are our flagship offering today, with new divination tools currently in development. Order your report and see what your sky has been trying to tell you.

## Page Category
- **Primary:** Astrologer
- **Alternatives:** Software Company · Product/Service · Spirituality
- **API note:** Graph API uses `category` (single primary) plus optional `category_list` (secondary categories, by ID — see setup notes below).

## FAQs

**Q1: What do I need to provide to get my Astrological Report?**
Your full birth date, birth location, and birth time if you know it. Location is required even if you don't know your exact time, since it's needed to calculate your chart correctly. If your birth time is approximate or unknown, time-sensitive details (like house placements) are automatically softened or withheld rather than presented as if they were exact.

**Q2: How is my report calculated, and how accurate is it?**
Every chart is calculated with Swiss Ephemeris precision, using the Tropical zodiac and Whole Sign house system — the same rigorous foundation used across serious astrological practice. On top of that, we layer Entangled Oracle's own proprietary interpretive indexes to add depth a standard report doesn't offer. Your report is symbolic and interpretive: built to describe real themes, patterns, and timing windows for reflection, not to promise a single fixed outcome.

**Q3: How long does it take, and what will I actually receive?**
Reports are generated locally, then delivered to you as a complete, beautifully formatted personal document you can read on any device or print for reference. Because everything is calculated on request rather than pulled from a generic template, please allow a short turnaround — we'll confirm your delivery window when you order.

## Initial Launch Posts

### Post 1 — Introduction
Welcome to Entangled Oracle.

We build divination tools for people who want more than a horoscope-column generality — tools rooted in real calculation, not guesswork. Every report we produce starts with an actual chart: your exact planetary positions, houses, and aspects at the moment you were born, computed with the same precision serious astrologers rely on. From there, we add an interpretive layer built to notice what a standard chart alone tends to miss.

The sky doesn't need to be reduced to a single line to be useful. It can be read closely, carefully, and still make sense to the person living it. That's the work.

Glad you're here.

### Post 2 — Spotlight on Astrological Reports
What makes an Entangled Oracle report different?

Every chart is calculated with Swiss Ephemeris precision using the Tropical zodiac and Whole Sign house system, then layered with our proprietary interpretive indexes — additional lenses that extend the standard chart rather than replace it.

We also track what most reports skip entirely: retrograde clusters (stretches where multiple planets turn retrograde at once) and void-of-course Moon windows (the pauses before the Moon changes sign). Your chart wheel even rings your natal placements in orange and your current transiting retrogrades in cyan, so you can see your permanent shape and the weather passing over it, in the same picture.

That's the difference between a generic reading and an actual report.

### Post 3 — Call to Action
Curious what your chart is actually saying, beyond the sun-sign version?

Your first Astrological Report is ready when you are — just your birth date, time (if you know it), and location. No account, no app to download, just a real, personal reading delivered directly to you.

Request your report today and find out what the sky's been trying to tell you all along.

---

## Facebook API Setup Notes (for non-coders)

You don't need to write code to use this file — here's the manual path and the automated path:

**Manual (fastest, no API):**
1. Meta Business Suite → your Page → **Edit Page Info** — paste `bio` into the Page's short description, `about_description` into "About," and set `page_category` under Categories (type "Astrologer" and pick from the dropdown).
2. Post the three `initial_posts` directly through Meta Business Suite's composer — copy/paste each `text` value as-is (blank lines are intentional paragraph breaks).

**Automated (Graph API / automation tools like Zapier or Make):**
- This JSON is already shaped for that: each top-level key maps to a Page field (`about`, `category`, etc.) or, for `initial_posts`, to repeated calls against the Page's `/feed` endpoint (one POST per post, `message` = the post's `text`).
- You'll need a **Page Access Token** (generated once in Meta Business Suite → System Users, or via the Graph API Explorer) — treat it like a password, never share it publicly.
- `category` in the Graph API expects a category **ID**, not free text; look it up once via `GET /search?type=adcategory&q=Astrologer` or just set it manually in Business Suite (simplest option, one-time setup).
