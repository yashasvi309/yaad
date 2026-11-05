# 🌼 Yaad: 6-Day Memory Continuity & Wellness Companion

> *An open-source, multimodal AI companion powered by Gemma and Graphify that preserves family memories and supports elder cognitive wellness.*

## 📖 The Problem & Solution
Standard AI chatbots treat every day like a blank slate, forgetting yesterday's conversations. For aging elders living independently, this lack of daily continuity accelerates short-term episodic memory fade and isolation, while leaving busy families in the dark.

**Yaad** (*meaning "Remembrance"*) replaces AI amnesia with a **Rolling 6-Day Episodic Memory Vault**. During daily voice, text, or photo check-ins, Yaad responds warmly and naturally weaves in **one gentle recall question** from the past week (e.g., *"How are the marigold saplings you planted with Rohan on Tuesday?"*)—exercising short-term memory with dignity while sending instant wellness summaries to the family's **Telegram** group.

---

## ✨ Key Features
* **🧠 6-Day Episodic Memory Vault:** Maintains a rolling 6-day window of verified daily routines, visitors, and health moments (`yaad_6day_memory_vault.json`).
* **🤖 2-Call Gemma Multimodal Engine:** Powered by open-weight `gemma-3-27b-it` for empathetic conversation, photo inspection (prescriptions, meals, plants), and deterministic JSON cognitive auditing.
* **🗺️ Graphify Anti-Hallucination Grounding:** Ingests `graph.json` schema constraints so the AI strictly cites verified vault entries and never invents false medical facts or visitors.
* **🔊 Zero-Cost Voice & Vision UI:** Responsive Marigold & Obsidian web dashboard featuring native browser Speech-to-Text dictation and Text-to-Speech voice synthesis.
* **📱 Telegram Family Briefings:** Dispatches instant, non-diagnostic mood and memory continuity summaries to family group chats via REST webhook.
* **🛡️ Production Hardened:** Built with OWASP security headers, sliding-window IP rate limiting, Pydantic v2 validation (4MB MIME allowlists), atomic file writes (`os.replace`), and a `/healthz` readiness probe.

---

## 📂 Repository Structure
```text
yaad/
├── main.py                      # FastAPI server, OWASP middleware, rate limiter & routes
├── memory_agents.py             # 2-call Gemma pipeline, Graphify grounding & atomic vault I/O
├── templates/
│   └── index.html               # Voice-enabled Marigold & Obsidian web companion UI
├── requirements.txt             # Lean production dependencies
└── .env.example                 # Environment configuration template
```

---

## 🚀 Quickstart

**1. Clone & Install**
```bash
git clone [https://github.com/yashasvi309/yaad.git](https://github.com/yashasvi309/yaad.git)
cd yaad
pip install -r requirements.txt
```

**2. Configure Environment**
```bash
cp .env.example .env
```
Add your keys to `.env`:
```env
GEMINI_API_KEY=your_google_ai_studio_key
TELEGRAM_BOT_TOKEN=optional_telegram_bot_token
TELEGRAM_CHAT_ID=optional_family_chat_id
PORT=8000
```

**3. Run the Server**
```bash
python main.py
```
Open **`http://localhost:8000`** in your browser to start a check-in, or verify health status at **`http://localhost:8000/healthz`**.

---

## 🔌 API Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Renders the interactive Yaad Web Companion dashboard |
| `GET` | `/api/vault` | Returns the current 6-day episodic memory vault & Graphify telemetry |
| `POST` | `/api/checkin` | Executes the multimodal Gemma check-in, vault update & Telegram alert |
| `POST` | `/api/device/checkin` | Headless REST webhook for single-button IoT bedside devices |
| `POST` | `/api/vault/reset` | Resets the 6-day memory vault to baseline demo state |
| `GET` | `/healthz` | Production readiness and liveness probe |

---

## 🏆 Built With
* **AI Model:** Open-Weight Google **Gemma** (`gemma-3-27b-it`)
* **Knowledge Grounding:** **Graphify** (`graph.json` AST & schema constraints)
* **Backend & Security:** Python, FastAPI, Pydantic v2, Uvicorn
* **Notifications:** Telegram Bot REST API
