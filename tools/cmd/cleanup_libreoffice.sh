#!/bin/bash
# Script untuk cleanup LibreOffice processes yang masih berjalan

echo "=========================================="
echo "LibreOffice Process Cleanup"
echo "=========================================="

# Check for running LibreOffice processes
PROCESSES=$(ps aux | grep -i "soffice" | grep -v grep)

if [ -z "$PROCESSES" ]; then
    echo "✅ No LibreOffice processes found"
else
    echo "📋 Found LibreOffice processes:"
    echo "$PROCESSES"
    echo ""
    echo "🔄 Killing LibreOffice processes..."
    
    # Kill all soffice processes
    pkill -9 soffice
    
    # Wait a moment
    sleep 1
    
    # Check again
    REMAINING=$(ps aux | grep -i "soffice" | grep -v grep)
    if [ -z "$REMAINING" ]; then
        echo "✅ All LibreOffice processes cleaned up"
    else
        echo "⚠️  Some processes still running:"
        echo "$REMAINING"
    fi
fi

echo "=========================================="
