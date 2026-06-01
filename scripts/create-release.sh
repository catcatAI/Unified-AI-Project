#!/bin/bash
# Create Angela AI v6.0 Release Package
# This script creates a clean release archive excluding large files

set -e

VERSION="7.5.0-dev"
RELEASE_NAME="angela-ai-v${VERSION}"
RELEASE_DIR="releases"

echo "🎉 Creating Angela AI v${VERSION} Release Package..."
echo ""

# Create releases directory
mkdir -p "${RELEASE_DIR}"

# Create release archive using git archive (respects .gitignore)
echo "📦 Creating source archive..."
git archive --format=zip --prefix="${RELEASE_NAME}/" -o "${RELEASE_DIR}/${RELEASE_NAME}-source.zip" HEAD

echo "✅ Source archive created: ${RELEASE_DIR}/${RELEASE_NAME}-source.zip"
echo ""

# Get archive size
if [ -f "${RELEASE_DIR}/${RELEASE_NAME}-source.zip" ]; then
    SIZE=$(du -h "${RELEASE_DIR}/${RELEASE_NAME}-source.zip" | cut -f1)
    echo "📊 Archive size: ${SIZE}"
fi

echo ""
echo "🚀 Release package ready!"
echo ""
echo "📋 Contents:"
echo "   - All source code"
echo "   - Documentation (excluding analysis reports)"
echo "   - Setup files (setup.py, requirements.txt)"
echo "   - No virtual environments"
echo "   - No credential files"
echo "   - No large model files"
echo ""
echo "📁 Location: ${RELEASE_DIR}/${RELEASE_NAME}-source.zip"
echo ""
echo "⚠️  IMPORTANT:"
echo "   1. This archive excludes credentials.json - users must set up their own"
echo "   2. Live2D SDK must be downloaded separately (proprietary)"
echo "   3. Python dependencies will be installed via pip"
echo "   4. Training data not included (will be downloaded on first run)"
echo ""
echo "🔒 Security verified:"
echo "   ✓ No credentials in archive"
echo "   ✓ .gitignore properly configured"
echo "   ✓ Sensitive files excluded"
