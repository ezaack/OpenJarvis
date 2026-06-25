# OpenJarvis — Project Overview (for Java/Spring Boot Developers)

## What is it?

OpenJarvis is a **local-first AI agent framework** — a modular, self-hosted AI backend. Think of it as Spring Boot for AI agents, designed to run on your own hardware by default.

---

## Architecture Analogy

| Spring Boot Concept | OpenJarvis Equivalent |
|---|---|
| `@SpringBootApplication` / Application context | `cli` (Click-based CLI entry point) + `server/app.py` (FastAPI app factory) |
| `application.yml` / `application-{profile}.yml` | `configs/openjarvis/config.toml` (TOML-based, single file) |
| Maven/Gradle modules (multi-module project) | Python package `src/openjarvis/` with sub-packages |
| `pom.xml` / `build.gradle` | `pyproject.toml` — dependencies, build system, optional "extras" |
| `mvnw` / `gradlew` | `uv` (Astral's Python package manager) |
| Spring Boot Actuator | `jarvis doctor` — health check + diagnostics |

---

## Module Map

### `core/` — The Framework Foundation
Like the shared library your Spring Boot apps depend on.

- **`types.py`** — Domain model (`Message`, `Conversation`, `ToolCall`, `ToolResult`, `Role`, `ModelSpec`)
- **`config.py`** — Configuration loader (reads `config.toml`, like `@ConfigurationProperties`)
- **`registry.py`** — Registries (`AgentRegistry`, `EngineRegistry`, `ToolRegistry`, `ModelRegistry`, `MemoryRegistry`) — like `@Service` auto-discovery
- **`events.py`** — Event bus (pub/sub, like `ApplicationEventPublisher`)
- **`paths.py`** / **`credentials.py`** — Data directories, OAuth credential stores

### `agents/` — Controller / Service Layer
Each agent is a `@Service` for a specific use case:

- `simple.py` — stateless chat
- `operative.py` — tool-using agent (the main, powerful agent)
- `deep_research.py` — multi-hop research (like a batch job)
- `morning_digest.py` — scheduled digest (like `@Scheduled`)
- `orchestrator.py` — routes queries to sub-agents (like a `@RequestMapping` dispatcher)
- `manager.py` — agent lifecycle manager (like `@PostConstruct` / `@PreDestroy`)
- `native_react.py`, `claude_code.py`, `openhands.py` — adapters for other frameworks

### `engine/` — LLM / AI Provider Layer (Data Access / Repository)
Plugs into LLMs. Each implements the `Engine` interface in `_base.py`:

- `ollama.py` — local models via Ollama (like an embedded database)
- `openai_compat_engines.py` — OpenAI-compatible APIs
- `cloud.py` — cloud inference providers
- `multi.py` — multi-provider routing (like load-balanced `@Bean`)
- `litellm.py` — LiteLLM (one API for many providers)

### `server/` — REST API Layer (FastAPI)
Spring Web MVC / `@RestController` layer:

- **`app.py`** — `FastAPI()` app factory (like `@SpringBootApplication`)
- **`routes.py`** — OpenAI-compatible `/v1/chat/completions` endpoint
- **`models.py`** — Pydantic models (like request/response DTOs)
- **`api_routes.py`** — additional REST endpoints
- **`agent_manager_routes.py`** — CRUD for agents (like `@RestController` + `@Service`)
- **`auth_middleware.py`** — auth filter (like `OncePerRequestFilter`)
- **`ws_bridge.py`** / **`stream_bridge.py`** — WebSocket / SSE (like `WebSocketHandler`)
- **`channel_bridge.py`** — multi-channel routing (SMS, Telegram, etc.)
- **`upload_router.py`** — file upload (like `MultipartFile` controller)

### `cli/` — Command-Line Interface (Click)
Like Spring Shell. Each file is a command group:

- `chat` → `jarvis chat`
- `serve` → `jarvis serve` (starts the FastAPI server)
- `agent` → `jarvis agent`
- `skill` → `jarvis skill`
- `config` → `jarvis config`
- `digest` → `jarvis digest`

### Other Packages

| Package | Spring Boot Analogy |
|---|---|
| `intelligence/` | Model catalog / model selection (like a routing datasource) |
| `memory/` | RAG / vector store (like caching layer + full-text search) |
| `tools/` | Tool definitions the agent can call (like `@Bean` utility services) |
| `mcp/` | Model Context Protocol (external tool integration, like Feign clients) |
| `workflow/` | DAG-based agent workflows (like `@Configuration` + `@Bean` wiring) |
| `scheduler/` | Task scheduling (like `@Scheduled` / Quartz) |
| `channels/` | Delivery channels — Telegram, SMS, Email (like Spring Integration) |
| `sandbox/` | Code execution sandbox (like Docker containers for tests) |
| `security/` | Auth / approval workflows (like Spring Security `@PreAuthorize`) |
| `telemetry/` | Usage tracking (like Micrometer / Prometheus) |
| `learning/` | Offline RL / training from agent traces (like A/B testing) |
| `rust/` | Rust native extensions via PyO3 (like JNI — performance-critical code) |

---

## Key Differences vs. Spring Boot

1. **No DI container.** No `@Autowired`. Objects are created manually or via factory functions. `registry.py` is the closest thing to `ApplicationContext.getBean()`.

2. **No ORM / JPA.** Data lives in JSON files, TOML config files, or vector databases (FAISS). No `@Entity` / `JPARepository` — direct file I/O or API calls.

3. **FastAPI, not Spring MVC.** FastAPI uses Pydantic for validation (like `@Valid` DTOs) and Python type hints. It's async-first (`async def` instead of `CompletableFuture`).

4. **Async everywhere.** Python `asyncio` — the whole server runs on an event loop. `@Async` / `@EventListener` → `async def` / `await`.

5. **`pyproject.toml`** = both `pom.xml` and dependency management. It declares Python version range, dependencies, and optional "extras" (like Maven profiles).

6. **Configuration is TOML, not YAML.** Similar structure, different syntax (`key = "value"` instead of `key: value`).

---

## Quick Start

```bash
cd src
.venv\Scripts\jarvis serve        # Start the FastAPI server (like mvnw spring-boot:run)
.venv\Scripts\jarvis chat          # CLI chat session
.venv\Scripts\jarvis doctor        # Health check
```

The HTTP server runs on port **9090** (default) with an OpenAI-compatible API at `/v1/chat/completions`.
