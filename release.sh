#!/usr/bin/env bash
# release.sh — Create a clean release archive without development artifacts.
# Usage: ./release.sh [version]
# Output: reframe-v<version>.tar.gz (or reframe-latest.tar.gz if no version)

set -euo pipefail

VERSION="${1:-latest}"
ARCHIVE="reframe-${VERSION}.tar.gz"
INCLUDE_FILES=(
    main.py config.py database.py handlers.py admin_handlers.py
    media_processor.py scanner.py locales.py utils.py
    requirements.txt Dockerfile .env.example
    README.md README.fa.md LICENSE .gitignore
)

echo "Creating release archive: ${ARCHIVE}"

# Clean any previous build artifacts
rm -f "${ARCHIVE}"

# Create archive with only the specified files
tar czf "${ARCHIVE}" "${INCLUDE_FILES[@]}"

echo "Done. Archive size: $(du -h "${ARCHIVE}" | cut -f1)"
echo "Contents:"
tar tzf "${ARCHIVE}" | sort
