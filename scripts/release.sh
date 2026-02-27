#!/usr/bin/env bash
set -euo pipefail

# dopeTask Automated Release Script
# Usage: ./scripts/release.sh <version>
# Example: ./scripts/release.sh 0.1.3

if [ $# -ne 1 ]; then
    echo "❌ Usage: $0 <version>"
    echo "Example: $0 0.1.3"
    exit 1
fi

VERSION="$1"
TAG="v$VERSION"

# Validate version format
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$ ]]; then
    echo "❌ Invalid version format: $VERSION"
    echo "Version must be semver (X.Y.Z[-modifier][+build])"
    exit 1
fi

# Check if tag already exists
if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "❌ Tag $TAG already exists"
    exit 1
fi

# Update version in pyproject.toml
echo "📝 Updating pyproject.toml version to $VERSION..."
sed -i "" "s/^version = \".*\"$/version = \"$VERSION\"/" pyproject.toml

# Update version in src/dopetask/__init__.py
echo "📝 Updating src/dopetask/__init__.py version to $VERSION..."
sed -i "" "s/^__version__ = \".*\"$/__version__ = \"$VERSION\"/" src/dopetask/__init__.py

# Commit version updates
echo "💾 Committing version updates..."
git add pyproject.toml src/dopetask/__init__.py
git commit -m "chore(release): bump version to $VERSION"

# Create annotated tag
echo "🏷️  Creating tag $TAG..."
git tag -a "$TAG" -m "Release v$VERSION"

# Push changes and tag
echo "🔄 Pushing to origin..."
git push origin main
git push origin "$TAG"

echo "🎉 Release process complete!"
echo ""
echo "📦 Automated workflow will now:"
echo "   1. Run CI tests"
echo "   2. Build distribution packages"
echo "   3. Publish to PyPI"
echo "   4. Create GitHub Release"
echo ""
echo "🔗 Monitor progress at:"
echo "   https://github.com/DDD-Enterprises/dopeTask/actions"
