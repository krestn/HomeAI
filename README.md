# HomeAI
HomeAI is an agentic assistant MVP built for homeowners. It blends retrieval-augmented generation (RAG), task memory, and property-aware context so each chat, email, or voice interaction can take action on the user’s behalf—whether that means reading an inspection PDF, finding local contractors, or closing the loop on reminders.

## Product Overview
- **Agentic conversation engine:** `run_home_agent` combines a purpose-built system prompt with guardrails for tone, empathy, and property safety checks. The LLM reasons over the latest user turn, the prior reply, and injected context to produce grounded responses rather than single-shot chat completion.

- **Property context resolution:** Every conversation is scoped to a specific home. We look up the user’s properties, auto-disambiguate free-form references, and inject the resolved address + metadata directly into the system prompt so downstream tool calls (e.g., Zillow Zestimate, Google Places) stay accurate.

- **Lightweight RAG pipeline:** PDF uploads flow through `DocumentStore`, which extracts page-level text via `pypdf`, caches full-text `.txt` renditions, and keeps an indexed preview. The agent exposes document tools (`list`, `summarize`, `search`) so each answer can retrieve the right passages before generating.

- **Task memory:** Follow-up actions live in `AgentMemory`, giving the assistant a short-term memory for reminders. The agent detects completion statements, confirms intent, and marks items done without user micromanagement.

- **Multi-tool orchestration:** We register every capability (home value lookup, local services, documents, reminders) as OpenAI function-calling schemas. The agent can chain multiple tools per turn, feeding JSON results back into the model until it has enough signal to reply.

## Architecture at a Glance
| Layer | Tech | Notes |
| --- | --- | --- |
| Frontend | Next.js (React) | Chat UI, document uploader, tasks dashboard. |
| Backend API | FastAPI + SQLAlchemy | Hosts agent endpoints, property context services, task memory, document store. |
| AI Stack | OpenAI GPT-3.5 Turbo | Custom prompts, function/tool calling, document-grounded responses. |
| Data Stores | PostgreSQL, local document cache | Relational data for properties/users, PDF+text storage under `storage/documents/<user_id>`. |

## Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL instance (local Docker container works)
- OpenAI, Google Maps/Places, and OpenWebNinja API keys

## Backend Setup
1. **Create a virtual environment (recommended).**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   ```
2. **Install dependencies.**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment variables.** Copy `.env.example` to `.env` (if provided) or create `.env` with:
   ```
   DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/homeai
   OPENAI_API_KEY=sk-...
   OPENWEBNINJA_API_KEY=...
   GOOGLE_API_KEY=...
   GOOGLE_MAP_API_KEY=...
   ```
4. **Run database migrations.**
   ```bash
   alembic upgrade head
   ```
5. **Seed development data (optional but recommended).**
   ```bash
   python -m app.scripts.seed_db
   ```
6. **Start the API.**
   ```bash
   uvicorn app.main:app --reload
   ```

## Frontend Setup
1. Install dependencies.
   ```bash
   cd frontend
   npm install
   ```
2. Run the dev server (defaults to http://localhost:3000 with proxying to the FastAPI backend).
   ```bash
   npm run dev
   ```

## Document Workflow & RAG
1. Users upload PDFs from the **Documents** tab. Files are stored at `storage/documents/<user_id>/<uuid>.pdf`.
2. `DocumentStore` extracts the full text, saves it as `<uuid>.txt`, and adds metadata (original name, preview, timestamp) to `index.json`.
3. During a chat turn, the agent decides whether to call `list_user_documents`, `summarize_user_document`, or `search_user_documents`. Each tool returns only the relevant excerpt/snippet, which is fed back into the LLM before it drafts the final reply.

## Prompting, Memory, and Tooling Highlights
- **Prompting:** Dedicated system prompts (`HOME_AGENT_SYSTEM_PROMPT`, `GENERAL_AGENT_SYSTEM_PROMPT`) enforce tone, safety, and property-awareness. We prepend resolved property summaries, active task lists, and prior assistant replies to keep the model on track.
- **Memory:** Tasks are persisted in `AgentMemory` so the agent can ask “Should I mark that done?” when the user implies completion. Memory state is injected into prompts and exposed to the UI.
- **Context windows:** The agent concatenates prior reply + new message + optional property clarification to maintain coherence without overloading tokens.
- **Multi-function calls:** We cap tool usage per turn and normalize arguments (e.g., auto-inject current address/city). After each tool response, we nudge the LLM on whether more calls are allowed to keep responses deterministic.

## Testing & Smoke Checks
1. Start backend (`uvicorn app.main:app --reload`) and frontend (`npm run dev`).
2. Upload a PDF and confirm it appears with a preview in the Documents tab.
3. Chat “Summarize the inspection report I uploaded” to watch the agent invoke document tools before responding.
4. Ask for local help (“Find roofers near my property”) to confirm the Places tool path.
5. Create a reminder (“Remind me to call the plumber tomorrow”) and then say “I called the plumber” to see the auto-completion flow in action.


Happy building! Contributions, bug reports, and feature ideas are welcome via pull requests or issues.
