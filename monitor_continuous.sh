#!/bin/bash

# Continuous MetaMCP Application Monitor
# This script continuously monitors the running MetaMCP applications

echo "🔍 MetaMCP Continuous Monitor"
echo "============================="
echo "Press Ctrl+C to stop monitoring"
echo

# Function to display status
show_status() {
    clear
    echo "🔍 MetaMCP Continuous Monitor - $(date)"
    echo "=========================================="
    echo
    
    # Check main server
    if pgrep -f "python -m metamcp.main" > /dev/null; then
        echo "✅ MetaMCP Main Server: RUNNING"
        MAIN_PID=$(pgrep -f "python -m metamcp.main")
        echo "   PID: $MAIN_PID"
        echo "   Port: 8000"
        
        # Check health endpoint
        if curl -s http://127.0.0.1:8000/health/ > /dev/null 2>&1; then
            HEALTH=$(curl -s http://127.0.0.1:8000/health/ | grep -o '"uptime_formatted":"[^"]*"' | cut -d'"' -f4)
            echo "   Health: ✅ HEALTHY (uptime: $HEALTH)"
        else
            echo "   Health: ❌ UNHEALTHY"
        fi
    else
        echo "❌ MetaMCP Main Server: NOT RUNNING"
    fi
    
    echo
    
    # Check admin interface
    if pgrep -f "streamlit.*streamlit_app.py" > /dev/null; then
        echo "✅ MetaMCP Admin Interface: RUNNING"
        ADMIN_PID=$(pgrep -f "streamlit.*streamlit_app.py")
        echo "   PID: $ADMIN_PID"
        echo "   Port: 8501"
        
        # Check if admin interface is responding
        if curl -s http://127.0.0.1:8501/ > /dev/null 2>&1; then
            echo "   Status: ✅ RESPONDING"
        else
            echo "   Status: ⚠️  NOT RESPONDING"
        fi
    else
        echo "❌ MetaMCP Admin Interface: NOT RUNNING"
    fi
    
    echo
    
    # System resources
    echo "💻 System Resources:"
    echo "   CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
    echo "   Memory Usage: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
    echo "   Disk Usage: $(df -h . | tail -1 | awk '{print $5}')"
    
    echo
    
    # Database status
    if [ -f "metamcp.db" ]; then
        DB_SIZE=$(ls -lh metamcp.db | awk '{print $5}')
        echo "💾 Database: SQLite (metamcp.db) - $DB_SIZE"
    else
        echo "💾 Database: ❌ NOT FOUND"
    fi
    
    echo
    
    # Quick links
    echo "🔗 Quick Links:"
    echo "   API Docs: http://127.0.0.1:8000/docs"
    echo "   Admin UI: http://127.0.0.1:8501"
    echo "   Health: http://127.0.0.1:8000/health/"
    
    echo
    echo "⏰ Last updated: $(date)"
    echo "Press Ctrl+C to stop monitoring"
}

# Main monitoring loop
while true; do
    show_status
    sleep 5
done