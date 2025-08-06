#!/bin/bash

# MetaMCP Application Monitor
# This script monitors the running MetaMCP applications

echo "🔍 MetaMCP Application Monitor"
echo "=============================="
echo

# Check if applications are running
echo "📊 Application Status:"
echo "----------------------"

# Check main server
if pgrep -f "python -m metamcp.main" > /dev/null; then
    echo "✅ MetaMCP Main Server: RUNNING"
    MAIN_PID=$(pgrep -f "python -m metamcp.main")
    echo "   PID: $MAIN_PID"
    echo "   Port: 8000"
else
    echo "❌ MetaMCP Main Server: NOT RUNNING"
fi

# Check admin interface
if pgrep -f "streamlit.*streamlit_app.py" > /dev/null; then
    echo "✅ MetaMCP Admin Interface: RUNNING"
    ADMIN_PID=$(pgrep -f "streamlit.*streamlit_app.py")
    echo "   PID: $ADMIN_PID"
    echo "   Port: 8501"
else
    echo "❌ MetaMCP Admin Interface: NOT RUNNING"
fi

echo
echo "🌐 Service URLs:"
echo "----------------"
echo "📡 API Server: http://127.0.0.1:8000"
echo "📖 API Docs:   http://127.0.0.1:8000/docs"
echo "🔧 Admin UI:   http://127.0.0.1:8501"
echo

# Check database
if [ -f "metamcp.db" ]; then
    echo "💾 Database: SQLite database exists (metamcp.db)"
    DB_SIZE=$(du -h metamcp.db | cut -f1)
    echo "   Size: $DB_SIZE"
else
    echo "❌ Database: SQLite database not found"
fi

echo
echo "📈 System Resources:"
echo "-------------------"
echo "CPU Usage:"
ps aux | grep -E "(metamcp|streamlit)" | grep -v grep | awk '{print "   " $11 ": " $3 "% CPU, " $4 "% MEM"}'

echo
echo "🔍 Recent Log Activity:"
echo "----------------------"
echo "Press Ctrl+C to stop monitoring"
echo

# Monitor logs in real-time
tail -f logs/*.log 2>/dev/null || echo "No log files found in logs/ directory"