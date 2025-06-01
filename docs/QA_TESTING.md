# MCP Hub - QA Testing & Acceptance Checklist

*Comprehensive testing scenarios for production readiness*

## 🧪 Test Categories

### 1. Platform Compatibility Tests

#### macOS with Vessel
- [ ] Fresh macOS installation with only Vessel
- [ ] Installer succeeds without Docker Desktop
- [ ] Setup wizard detects Vessel correctly
- [ ] Service startup uses Vessel commands
- [ ] Health checks work through Vessel
- [ ] Auto-start LaunchAgent installation

#### Windows with Docker Desktop  
- [ ] Fresh Windows installation with Docker Desktop
- [ ] winget dependency installation works
- [ ] Setup wizard completes successfully
- [ ] All CLI commands function correctly
- [ ] Registry Run key auto-start works
- [ ] Desktop app launches on startup

#### Linux with Docker CE
- [ ] Ubuntu/Debian with apt package manager
- [ ] CentOS/RHEL with yum package manager
- [ ] Docker CE detection and operation
- [ ] systemd integration (when implemented)

### 2. LLM Backend Integration Tests

#### Claude Desktop Integration
- [ ] Setup wizard detects Claude Desktop
- [ ] Connection test succeeds on multiple ports (52262-52264)
- [ ] Bridge configuration generates correctly
- [ ] API calls route through Claude Desktop
- [ ] Error handling for Claude Desktop not running

#### OpenAI API Integration
- [ ] API key validation works
- [ ] Connection test with valid/invalid keys
- [ ] Rate limiting handling
- [ ] Model selection and configuration
- [ ] Error handling for network issues

#### Custom LLM Endpoint
- [ ] Custom URL validation
- [ ] Bearer token authentication
- [ ] HTTP/HTTPS endpoint support
- [ ] Connection timeout handling
- [ ] Response parsing and error handling

### 3. Service Management Tests

#### Service Addition
- [ ] `mcpctl add instagram` adds service definition
- [ ] Service YAML generation is valid
- [ ] Container starts successfully
- [ ] Health check shows healthy status
- [ ] Service appears in `mcpctl status`

#### Service Removal
- [ ] `mcpctl remove service` stops container
- [ ] Service definition file is deleted
- [ ] Compose file regenerated correctly
- [ ] No orphaned containers remain
- [ ] Data volumes handled per user preference

#### Service Health Monitoring
- [ ] Health checks detect unhealthy services
- [ ] Auto-restart triggers on failure
- [ ] Daemon monitors service status
- [ ] Alert logging for persistent failures
- [ ] Manual health test command works

### 4. Production Deployment Tests

#### Image Digest Locking
- [ ] `mcpctl lock-images` captures current digests
- [ ] `images.lock.json` contains valid digest hashes
- [ ] `mcpctl pull-images` uses locked digests
- [ ] Second laptop reproduces stack exactly
- [ ] Digest verification prevents tampering

#### Registry Operations
- [ ] `mcpctl publish-images` pushes to GHCR
- [ ] Registry authentication works
- [ ] Multi-platform image support
- [ ] Offline tarball generation
- [ ] Image layer deduplication

#### CI/CD Integration
- [ ] GitHub Actions workflow succeeds
- [ ] Automated testing in CI environment
- [ ] Multi-platform builds complete
- [ ] Artifact publishing works
- [ ] Version tagging and releases

### 5. Security & Secrets Tests

#### Environment Backend
- [ ] Environment variables injected correctly
- [ ] No secrets persisted to disk
- [ ] Container environment isolation
- [ ] Secret rotation handling

#### LastPass Backend
- [ ] LastPass CLI authentication
- [ ] Secret retrieval from vault
- [ ] Team folder access permissions
- [ ] Error handling for offline vault

#### Auto-start Security
- [ ] LaunchAgent runs with correct permissions
- [ ] Registry keys don't expose secrets
- [ ] Daemon runs in user context
- [ ] No privilege escalation required

## 🎯 Acceptance Test Scenarios

### Scenario A: New Developer Onboarding

**Setup**: Fresh developer machine, no prior MCP tools
**Goal**: Get from zero to running MCP servers in <10 minutes

**Steps:**
1. Download MCP Hub installer
2. Launch setup wizard  
3. Select LLM backend (Claude Desktop)
4. Install missing dependencies automatically
5. Add first MCP service (`mcpctl add web-search`)
6. Verify service is healthy
7. Test LLM integration end-to-end

**Success Criteria:**
- [ ] Wizard completes without manual intervention
- [ ] All dependencies install correctly
- [ ] Service starts and passes health checks
- [ ] LLM can successfully call MCP service
- [ ] Total time under 10 minutes

### Scenario B: Production Deployment

**Setup**: Production server environment
**Goal**: Deploy reproducible, monitored MCP stack

**Steps:**
1. Clone repository to production server
2. Pull images using `images.lock.json`
3. Start services with locked images
4. Enable daemon monitoring
5. Verify all services healthy
6. Test failover and recovery
7. Check logs and monitoring data

**Success Criteria:**
- [ ] Exact image digests match development
- [ ] All services start successfully
- [ ] Health monitoring detects failures
- [ ] Auto-restart recovers from failures
- [ ] Logs contain structured monitoring data
- [ ] Zero manual intervention required

### Scenario C: Multi-Platform Team

**Setup**: Team with macOS (Vessel), Windows (Docker), Linux (Docker CE)
**Goal**: Consistent experience across all platforms

**Steps:**
1. Each team member runs setup wizard
2. Configure same LLM backend (OpenAI)
3. Deploy identical service stack
4. Lock images on one platform
5. Reproduce exact stack on other platforms
6. Verify cross-platform compatibility

**Success Criteria:**
- [ ] Setup wizard works on all platforms
- [ ] Same services run identically everywhere
- [ ] Image digests ensure reproducibility
- [ ] Cross-platform debugging tools work
- [ ] Team collaboration is seamless

## 🔧 Automated Testing

### Unit Tests

```bash
# CLI unit tests
cd mcpctl/
python -m pytest tests/

# Desktop app unit tests  
cd electron/
npm test

# Integration tests
./scripts/integration-test.sh
```

### End-to-End Tests

```bash
# Full workflow test
./scripts/e2e-test.sh

# Platform-specific tests
./scripts/test-macos-vessel.sh
./scripts/test-windows-docker.sh
./scripts/test-linux-docker.sh
```

### Performance Tests

```bash
# Service startup time
mcpctl benchmark startup

# Memory usage monitoring
mcpctl benchmark memory --duration 1h

# Container resource usage
mcpctl benchmark resources --services all
```

## 🐛 Known Issues & Workarounds

### Issue: Vessel Compatibility Daemon
**Symptom**: Docker commands fail on macOS with Vessel
**Workaround**: Ensure `vessel compat` is running
**Test**: `mcpctl test-engine vessel`

### Issue: Windows Path Handling  
**Symptom**: File paths with spaces cause CLI failures
**Workaround**: Use quoted paths in CLI commands
**Test**: Create service in path with spaces

### Issue: LLM Rate Limiting
**Symptom**: API calls fail during high usage
**Workaround**: Implement exponential backoff
**Test**: Simulate rate limit conditions

## 📊 Test Results Template

### Test Run: [Date]
**Platform**: [macOS/Windows/Linux]
**Engine**: [Docker/Vessel]  
**LLM Backend**: [Claude/OpenAI/Custom]

#### Results Summary
- ✅ **Platform Compatibility**: [Pass/Fail]
- ✅ **LLM Integration**: [Pass/Fail]  
- ✅ **Service Management**: [Pass/Fail]
- ✅ **Production Deployment**: [Pass/Fail]
- ✅ **Security & Secrets**: [Pass/Fail]

#### Performance Metrics
- **Setup Time**: [X minutes]
- **Service Startup**: [X seconds]
- **Memory Usage**: [X MB baseline]
- **Container Count**: [X services]

#### Issues Found
1. [Issue description]
   - **Severity**: [Low/Medium/High/Critical]
   - **Workaround**: [Description]
   - **Fix Required**: [Yes/No]

## 🎉 Production Readiness Checklist

**Core Functionality**
- [ ] All CLI commands work without errors
- [ ] Desktop app launches and functions correctly
- [ ] Services start, stop, and restart reliably
- [ ] Health monitoring detects and recovers from failures

**Cross-Platform Support**
- [ ] macOS with Docker and Vessel
- [ ] Windows with Docker Desktop  
- [ ] Linux with Docker CE
- [ ] Auto-start works on all platforms

**Production Features**
- [ ] Image digest locking ensures reproducibility
- [ ] Registry operations support enterprise workflows
- [ ] Secret management handles sensitive data securely
- [ ] Monitoring provides operational visibility

**Documentation & Support**
- [ ] README covers all major use cases
- [ ] Architecture documentation is complete
- [ ] Troubleshooting guide addresses common issues
- [ ] API documentation enables automation

**Quality Assurance**
- [ ] All acceptance scenarios pass
- [ ] Performance meets requirements
- [ ] Security review completed
- [ ] End-user testing successful

---

**When all items are checked**, MCP Hub is ready for production deployment! 🚀
