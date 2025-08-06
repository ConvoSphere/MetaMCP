#!/bin/bash

# MetaMCP Log Viewer
# This script shows real-time logs from the running applications

echo "📋 MetaMCP Log Viewer"
echo "====================="
echo "Monitoring application logs..."
echo "Press Ctrl+C to stop"
echo

# Function to show recent logs
show_logs() {
    echo "🔄 Recent Application Activity:"
    echo "==============================="
    
    # Show recent process activity
    echo "📊 Process Status (last 10 seconds):"
    ps aux | grep -E "(metamcp|streamlit)" | grep -v grep | head -5
    
    echo
    
    # Show recent network connections
    echo "🌐 Network Connections:"
    ss -tlnp | grep -E "(8000|8501)" | head -5
    
    echo
    
    # Show recent file changes
    echo "📁 Recent File Changes:"
    find . -name "*.db" -o -name "*.log" -newermt "5 minutes ago" 2>/dev/null | head -5
    
    echo
    
    # Show system resources
    echo "💻 System Resources:"
    echo "   CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
    echo "   Memory: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
    echo "   Disk: $(df -h . | tail -1 | awk '{print $5}')"
    
    echo
    echo "⏰ Last updated: $(date)"
    echo "Press Ctrl+C to stop monitoring"
}

# Main log monitoring loop
while true; do
    clear
    show_logs
    sleep 3
done