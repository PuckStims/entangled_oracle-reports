import cors from "cors";
import dotenv from "dotenv";
import express from "express";

dotenv.config();

const app = express();
const port = Number(process.env.OPENROUTER_PROXY_PORT ?? 8787);

app.use(cors({ origin: true }));
app.use(express.json({ limit: "1mb" }));

app.get("/api/openrouter/status", (_req, res) => {
  res.json({
    status: process.env.OPENROUTER_API_KEY ? "available" : "disabled",
    model: process.env.OPENROUTER_MODEL ?? "openai/gpt-4o-mini"
  });
});

app.post("/api/openrouter/synthesis", async (req, res) => {
  const apiKey = process.env.OPENROUTER_API_KEY;
  const model = process.env.OPENROUTER_MODEL ?? "openai/gpt-4o-mini";

  if (!apiKey) {
    res.status(200).json({
      status: "disabled",
      model,
      errorMessage: "OPENROUTER_API_KEY is not configured."
    });
    return;
  }

  const prompt = typeof req.body?.prompt === "string" ? req.body.prompt : "";
  if (!prompt) {
    res.status(400).json({
      status: "error",
      model,
      errorMessage: "Missing prompt."
    });
    return;
  }

  try {
    const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
        "HTTP-Referer": process.env.OPENROUTER_SITE_URL ?? "http://localhost:5173",
        "X-Title": process.env.OPENROUTER_APP_NAME ?? "The Entangled Dashboard"
      },
      body: JSON.stringify({
        model,
        messages: [
          {
            role: "user",
            content: prompt
          }
        ],
        temperature: 0.8
      })
    });

    const bodyText = await response.text();
    let body: unknown;
    try {
      body = JSON.parse(bodyText);
    } catch {
      body = undefined;
    }

    if (!response.ok) {
      const quotaLike =
        response.status === 402 ||
        response.status === 429 ||
        bodyText.toLowerCase().includes("quota") ||
        bodyText.toLowerCase().includes("rate limit");

      res.status(response.status).json({
        status: quotaLike ? "quota_reached" : "error",
        model,
        errorMessage: bodyText
      });
      return;
    }

    const content =
      typeof body === "object" &&
      body !== null &&
      "choices" in body &&
      Array.isArray((body as { choices: unknown }).choices)
        ? ((body as { choices: Array<{ message?: { content?: string } }> }).choices[0]?.message?.content ?? "")
        : "";

    res.json({
      status: "available",
      model,
      content
    });
  } catch (error) {
    res.status(500).json({
      status: "error",
      model,
      errorMessage: error instanceof Error ? error.message : "Unknown OpenRouter proxy error."
    });
  }
});

app.listen(port, () => {
  console.log(`OpenRouter proxy listening on http://127.0.0.1:${port}`);
});
