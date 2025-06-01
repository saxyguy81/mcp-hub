#!/bin/bash
# Manual Docker Container Publishing Script for MCP Hub
# Usage: ./scripts/publish-docker.sh [version] [options]

set -euo pipefail

# Configuration
REGISTRY="ghcr.io"
REPO_NAME="saxyguy81/mcp-hub"
IMAGE_NAME="$REGISTRY/$REPO_NAME/web"
DEFAULT_VERSION="v1.0.2"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Logging functions
log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✅${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}❌${NC} $1"; }
log_step() { echo -e "${BOLD}${BLUE}📋 $1${NC}"; }

# Parse arguments
VERSION="${1:-$DEFAULT_VERSION}"
PUSH_LATEST="${2:-true}"
DRY_RUN="${3:-false}"

# Validate version format
if [[ ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+.*$ ]]; then
    log_error "Invalid version format: $VERSION (expected: vX.Y.Z)"
    exit 1
fi

# Display configuration
echo -e "${BOLD}${BLUE}🐳 MCP Hub Docker Publishing${NC}"
echo -e "${BLUE}Registry: ${BOLD}$REGISTRY${NC}"
echo -e "${BLUE}Image: ${BOLD}$IMAGE_NAME${NC}"
echo -e "${BLUE}Version: ${BOLD}$VERSION${NC}"
echo -e "${BLUE}Push Latest: ${BOLD}$PUSH_LATEST${NC}"
echo -e "${BLUE}Dry Run: ${BOLD}$DRY_RUN${NC}"
echo

# Check prerequisites
log_step "Checking prerequisites..."
if ! command -v docker >/dev/null 2>&1; then
    log_error "Docker not found. Please install Docker."
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    log_error "Docker daemon not running. Please start Docker."
    exit 1
fi

log_success "Docker is available"

# Build the image
log_step "Building Docker image..."
BUILD_ARGS=(
    "build"
    "-f" "web/Dockerfile"
    "-t" "$IMAGE_NAME:$VERSION"
    "."
)

if [ "$PUSH_LATEST" = "true" ]; then
    BUILD_ARGS+=("-t" "$IMAGE_NAME:latest")
fi

if [ "$DRY_RUN" = "true" ]; then
    log_info "DRY RUN: docker ${BUILD_ARGS[*]}"
else
    docker "${BUILD_ARGS[@]}"
    log_success "Image built successfully"
fi

# Test the image
log_step "Testing the image..."
if [ "$DRY_RUN" = "false" ]; then
    if docker run --rm "$IMAGE_NAME:$VERSION" python -c "import server; print('✅ Container works!')"; then
        log_success "Image test passed"
    else
        log_error "Image test failed"
        exit 1
    fi
fi

# Login to registry (if not already logged in)
log_step "Logging in to $REGISTRY..."
if [ "$DRY_RUN" = "false" ]; then
    if ! docker login "$REGISTRY" 2>/dev/null; then
        log_warning "Not logged in to $REGISTRY"
        log_info "Please run: docker login $REGISTRY"
        log_info "Or set GITHUB_TOKEN environment variable"
        
        if [ -n "${GITHUB_TOKEN:-}" ]; then
            echo "$GITHUB_TOKEN" | docker login "$REGISTRY" -u "$GITHUB_ACTOR" --password-stdin
            log_success "Logged in using GITHUB_TOKEN"
        else
            exit 1
        fi
    else
        log_success "Already logged in to $REGISTRY"
    fi
fi

# Push the image(s)
log_step "Pushing Docker image(s)..."
if [ "$DRY_RUN" = "true" ]; then
    log_info "DRY RUN: docker push $IMAGE_NAME:$VERSION"
    if [ "$PUSH_LATEST" = "true" ]; then
        log_info "DRY RUN: docker push $IMAGE_NAME:latest"
    fi
else
    docker push "$IMAGE_NAME:$VERSION"
    log_success "Pushed $IMAGE_NAME:$VERSION"
    
    if [ "$PUSH_LATEST" = "true" ]; then
        docker push "$IMAGE_NAME:latest"
        log_success "Pushed $IMAGE_NAME:latest"
    fi
fi

# Summary
echo
echo -e "${BOLD}${GREEN}🎉 Docker publishing complete!${NC}"
echo -e "${GREEN}📦 Published images:${NC}"
echo -e "  • $IMAGE_NAME:$VERSION"
if [ "$PUSH_LATEST" = "true" ]; then
    echo -e "  • $IMAGE_NAME:latest"
fi
echo
echo -e "${BLUE}🚀 Usage:${NC}"
echo -e "  docker run -p 5000:5000 $IMAGE_NAME:$VERSION"
echo
