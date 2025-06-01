# MCP-Hub – Remaining Work / Developer TODO
*Last updated: 2025-05-31*

---

## 1  GUI: full first-run wizard & settings panel
| Item | Where | Details / Notes | Done? |
|------|-------|-----------------|-------|
| 1.1 | **electron/src/pages/Wizard** | Add "🔧 LLM backend" step **after** dependency check.<br/>- Radio choices: **Claude (desktop)**, **OpenAI (api.openai.com)**, **OpenAI-compatible (custom URL)**.<br/>- If custom → text input for base URL and *optional* bearer token. | ❌ |
| 1.2 | same | Show *Test* button → calls `ipcRenderer.invoke('llmTest', cfg)`.<br/>Main process sends a 1-token completion request; wizard displays ✅/❌. | ❌ |
| 1.3 | **electron/src/pages/Settings.tsx** | Add "LLM & Tool Settings" tab:<br/>- Re-surface the above inputs<br/>- Button to **Re-test connection**<br/>- Button **"Re-generate OpenAPI bridge schema"** (calls `mcpctl regenerate-bridge`). | ❌ |
| 1.4 | **ipcMain ( electron/main.ts )** | Implement `llmTest` handler:<br/>✓ Claude: open `http://localhost:…/status` (desktop) <br/>✓ OpenAI: POST `/v1/chat/completions` model=`gpt-3.5-turbo`, messages=`[{"role":"user","content":"ping"}]` <br/>✓ Return duration ms and HTTP status. | ❌ |

---

## 2  CLI: new commands & wiring
| Command | File | Requirements | Done? |
|---------|------|--------------|-------|
| `mcpctl add` | `mcpctl/cli.py` | Uses `discover.py` → fetch image/tag → write `services/<name>.yml` → run `docker/vessel compose up -d <name>` → inject healthcheck. | ❌ |
| `mcpctl remove / swap` | same | Update compose, prune container(s), update images.lock. | ❌ |
| `mcpctl test <name>` | same | `docker/vessel exec <name> curl -fsSL http://localhost:8080/health` | ❌ |
| `mcpctl daemon` | same | Log-tail + auto-restart loop; used by launchd/Run key. | ❌ |
| `mcpctl regenerate-bridge` | same | Rebuild OpenAPI bridge spec based on current LLM config; restart `mcp-openapi` container. | ❌ |

---

## 3  Container-engine abstraction (Docker ⟷ Vessel)
### 3.1 Launcher detection
*In `compose_gen.py`*  
```python
def _engine():
    if shutil.which("docker"):
        return "docker"
    if shutil.which("vessel"):
        return "vessel"
    raise RuntimeError("Neither docker nor vessel found.")
```

### 3.2 Wrapper helpers
Create `mcpctl/container_engine.py`:
```python
ENGINE = _engine()

def run(cmd: list[str], **kw):
    full = [ENGINE] + cmd
    return subprocess.run(full, check=True, **kw)
```
Replace every `subprocess.run(["docker", …])` call with `container_engine.run([...])`.

### 3.3 macOS special-case
If `ENGINE == "vessel"` and user chose Docker workflow in wizard, start a compatibility daemon:
```python
container_engine.run(["compat"])
time.sleep(4)          # wait for dockerd to expose socket
```

### 3.4 Compose alternative
Short-term: invoke `vessel compose -f compose.yml ...` because Vessel vendors docker-compose v2.
Long-term: consider calling docker-compose binary inside the compat daemon.

**Status:** ❌ Not implemented

---

## 4  Dependency installer updates

| Dependency | macOS (brew) | Windows (winget) | Vessel flag |
|------------|--------------|------------------|-------------|
| Docker Desktop | `brew install --cask docker` | `Docker.DockerDesktop` | skip if Vessel chosen |
| Vessel | `brew install vessel` | TODO: add Chocolatey or MSI link | install if user ticks "Use Vessel" |
| Git | `brew install git` | `Git.Git` | — |
| Python 3.11 | `brew install python` | `Python.Python.3.11` | only if secrets backend = env |

Update `electron/src/deps.ts` to reflect table.

**Status:** ❌ Not implemented

---

## 5  Firecrawl & default services
Replace `services/firecrawl.yml` with:
```yaml
services:
  firecrawl:
    image: ghcr.io/mendableai/firecrawl-mcp-server:latest
    environment:
      - PORT=8080
    ports: ["8081:8080"]
    healthcheck:
      test: ["CMD","curl","-f","http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    restart: unless-stopped
```

**Status:** ❌ Not implemented

---

## 6  Image-digest locking
1. After every successful `publish-images`, gather digests:
```python
import docker, json, pathlib, subprocess, re
client = docker.from_env()
dig = {t: client.images.get(t).attrs['RepoDigests'][0]
       for t in tags}
pathlib.Path("images.lock.json").write_text(json.dumps(dig, indent=2))
```

2. `pull-images` reads the file and pulls by digest.

**Status:** ❌ Not implemented

---

## 7  Auto-start installation

| OS | Implementation |
|----|----------------|
| macOS | Write `~/Library/LaunchAgents/com.mcphub.daemon.plist` with ProgramArguments → `mcpctl daemon`. |
| Windows | `reg add "HKCU\...\Run" /v MCPHub /d "\"%LOCALAPPDATA%\\mcp-hub\\mcpctl.exe\" daemon"` |

Add these steps to `electron/builder.json` afterInstall hook.

**Status:** ❌ Not implemented

---

## 8  CI / nightly
`.github/workflows/build.yml`:
```yaml
name: Build & Publish
on:
  push: { branches: [main] }
  schedule: [ cron: "0 5 * * *" ]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: sudo apt-get update && sudo apt-get install -y docker.io
      - run: |
          pip install typer docker
          npm i --prefix electron
          pyinstaller mcpctl/cli.py -n mcpctl --onefile
          npm run build --prefix electron
          mcpctl publish-images --tag ${{ github.sha }}
      - uses: actions/upload-artifact@v4
        with: { path: "dist_installer/*" }
```

**Status:** ❌ Not implemented

---

## 9  Documentation updates
- `README.md` — add screenshots of wizard, explain Vessel option, add "Test LLM" how-to.
- `docs/ARCH.md` — new section on container-engine abstraction layer.

**Status:** ❌ Not implemented

---

## 10  Acceptance checklist (QA)
1. Fresh macOS with Vessel only → installer succeeds, fires up hub.
2. Fresh Windows with Docker Desktop → same workflow.
3. Change LLM backend in settings → Test passes, bridge regenerates, Claude & OpenAI calls work.
4. `mcpctl add instagram` adds fragment, runs container, shows healthy.
5. `mcpctl publish-images` writes digests; second laptop `pull-images` reproduces stack exactly.

**Status:** ❌ Not tested

---

## Implementation Priority

### Phase 1 (Core Functionality)
- [ ] 3.1-3.2: Container engine abstraction
- [ ] 2.1-2.3: Core CLI commands (`add`, `remove`, `test`)
- [ ] 5: Updated service definitions

### Phase 2 (User Experience)
- [ ] 1.1-1.4: GUI wizard improvements
- [ ] 4: Dependency installer updates
- [ ] 7: Auto-start installation

### Phase 3 (Production Ready)
- [ ] 6: Image digest locking
- [ ] 8: CI/CD pipeline
- [ ] 9: Documentation
- [ ] 10: QA testing

---

### Need code snippets for any bullet?
Ping with the bullet # (e.g., "3.1 Wrapper detection code") and specific code will be provided.

### Next Steps
1. Add this file to the repo as `docs/TODO.md`
2. Create GitHub issues per top-level section
3. Hand repo + doc to developer for feature-by-feature implementation
4. Tick checklist items as MVP features are completed
