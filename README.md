# LuxeCart Concierge

A personal-stylist assistant for independent luxury boutiques. A shopper describes what they need in plain words; the concierge suggests up to three pieces that are in stock, in their size and within their budget, with a short note on why each one works.

- **Live app:** (add your Streamlit URL here)
- **How it works:** three AI steps on Google Gemini (understand the request, choose from real candidates, write the note), with code checks around them. Prices, sizes and stock always come from `data/catalog.csv`, never from AI text.
- **Data:** 47-piece demo catalog and style vocabulary built from Assignment 3 public data (DummyJSON, a Hugging Face fashion dataset, fashion RSS feeds).
- **Error handling:** plain-English messages for missing or invalid input; retry with backoff and a fallback model when the AI service is busy (429/503) or a model is retired (404).

Course project for INFO 7375 Branding and AI, Northeastern University.
