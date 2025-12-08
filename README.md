# 🛰️ J.U.N.O.

### **J**ira **U**nderstanding of **N**uance & **O**bjectives

> **"Objectives are binary. Nuance is human. J.U.N.O. bridges the gap."**

**J.U.N.O.** is an AI-powered observation engine for Technical Program Managers. Just as the NASA Juno probe peers through Jupiter's turbulent clouds to see the planet's true structure, this tool peers through the "clouds" of Jira comments to reveal the true health of your program.

It combines **Generative AI Inference** (to detect Nuance) with **Strict Velocity Math** (to track Objectives) to answer the ultimate question: *Are we going to hit the date?*

-----

## 🔭 The J.U.N.O. Methodology

J.U.N.O. orbits your Jira hierarchy and performs a two-layer scan:

### 1\. The Nuance Layer (Sentiment Inference)

Standard reports ignore text. J.U.N.O. reads it.

  * **The Problem:** A ticket can be marked `Green` while the comments are full of "blockers," "latency," and "risk."
  * **The Solution:** J.U.N.O. ingests Descriptions and Comment Histories, calculating a weighted "Vibe Score" ($-1$ to $+1$). It gives higher weight to:
      * **Priority:** Critical/Blocker issues ($3\times$ Multiplier).
      * **Recency:** The latest comments matter most.

### 2\. The Objectives Layer (Delivery Math)

Standard reports rely on hopeful target dates. J.U.N.O. relies on physics.

  * **The Problem:** Manual "Target End Dates" are often optimistic guesses.
  * **The Solution:** J.U.N.O. ignores the guess. It calculates the *actual* delivery date based on historical velocity:
      * If you have 20 children and close 2 per week, you *will* finish in 10 weeks, regardless of what the target date says.

-----

## 🧮 The Logic Core

J.U.N.O. operates on transparent, TPM-verified formulas:

### Sentiment (The Nuance Score)

$$\text{Overall Score} = \frac{\sum (\text{Text Sentiment} \times \text{Priority Multiplier} \times \text{Status Contribution})}{\sum (\text{Priority Multiplier} \times \text{Status Contribution})}$$

### Delivery Prediction (The Objective Reality)

$$\text{Est. Date} = \left( \frac{\text{Open Children}}{\text{Verified Velocity}} \right) + \text{Today} + 10\% \text{ Buffer}$$

### Health Status Triangulation

The final R/Y/G status is a composite of Nuance and Objectives:

  * 🟢 **Green:** Positive Sentiment + `Computed Date` $\le$ `Target Date`.
  * 🟡 **Yellow:** Neutral Sentiment OR `Computed Date` slips 1-3 weeks.
  * 🔴 **Red:** Negative Sentiment OR `Computed Date` slips \>3 weeks.

-----

## 🛠️ Installation & Setup

### Prerequisites

  * Python 3.9+
  * Jira API Token
  * LLM Provider (OpenAI/Azure) for the inference layer.

### Environment Variables

Configure your `.env` file to establish the uplink:

```bash
JIRA_BASE_URL="https://issues.redhat.com"
JIRA_API_TOKEN="your_token"
LLM_API_KEY="your_key"
```

### Mission Control (Usage)

Launch the probe against a specific Initiative or Epic:

```bash
python juno_probe.py --issue PROJECT-8842
```

-----

## 📄 The Mission Report

J.U.N.O. returns a structured **Markdown Assessment** containing:

1.  **Executive Summary:** A narrative synthesis of the risk.
2.  **Nuance Analysis:** "Why is the sentiment negative?" (e.g., *frequency of the word 'refactor' in comments*).
3.  **Objective Reality:** A side-by-side comparison of `Target Date` vs. `Computed Date`.
4.  **Anomaly Detection:** Specific child tickets that are dragging down the average velocity.

-----
