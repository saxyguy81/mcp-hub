#!/bin/bash
# Standalone Platform Detection Script
# Used by both install.sh and tests to ensure consistency

detect_platform() {
    case "$(uname -s)" in
        Darwin*)
            case "$(uname -m)" in
                x86_64) echo "macos-amd64" ;;
                arm64) echo "macos-arm64" ;;
                *) echo "unsupported-macos-$(uname -m)" ;;
            esac ;;
        Linux*)
            case "$(uname -m)" in
                x86_64) echo "linux-amd64" ;;
                aarch64|arm64) echo "linux-arm64" ;;
                *) echo "unsupported-linux-$(uname -m)" ;;
            esac ;;
        CYGWIN*|MINGW*|MSYS*) echo "windows-amd64" ;;
        *) echo "unsupported-$(uname -s)" ;;
    esac
}

# If called directly, run the function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    detect_platform
fi
