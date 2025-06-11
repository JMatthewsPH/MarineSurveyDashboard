#!/bin/bash
# Deployment optimization script for Marine Conservation Platform

echo "Optimizing for deployment..."

# Clean UV cache selectively (keep essential files)
if [ -d ".cache/uv" ]; then
    echo "Cleaning UV cache..."
    find .cache/uv -name "*.tar.gz" -delete 2>/dev/null || true
    find .cache/uv -name "*.whl" -delete 2>/dev/null || true
    find .cache/uv -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
fi

# Remove Python cache files
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

# Clean matplotlib cache
if [ -d ".cache/matplotlib" ]; then
    rm -rf .cache/matplotlib/* 2>/dev/null || true
fi

# Clean fontconfig cache
if [ -d ".cache/fontconfig" ]; then
    rm -rf .cache/fontconfig/* 2>/dev/null || true
fi

echo "Optimization complete. Ready for deployment."