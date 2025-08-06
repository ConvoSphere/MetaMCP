#!/bin/bash

# Quick Status Check for MetaMCP Applications

echo "🚀 MetaMCP Status Check"
echo "======================"
echo

# Check main server
if curl -s http://127.0.0.1:8000/health/ > /dev/null 2>&1; then
    echo "✅ API Server (8000): HEALTHY"
else
    echo "❌ API Server (8000): UNHEALTHY"
fi

# Check admin interface
if curl -s http://127.0.0.1:8501/ > /dev/null 2>&1; then
    echo "✅ Admin UI (8501): HEALTHY"
else
    echo "❌ Admin UI (8501): UNHEALTHY"
fi

echo
echo "📊 Process Status:"
if pgrep -f "python -m metamcp.main" > /dev/null; then
    echo "✅ Main Server: RUNNING"
else
    echo "❌ Main Server: STOPPED"
fi

if pgrep -f "streamlit.*streamlit_app.py" > /dev/null; then
    echo "✅ Admin Interface: RUNNING"
else
    echo "❌ Admin Interface: STOPPED"
fi

echo
echo "💾 Database:"
if [ -f "metamcp.db" ]; then
    echo "✅ SQLite database exists"
else
    echo "❌ SQLite database missing"
fi

echo
echo "🔗 Quick Links:"
echo "API Docs: http://127.0.0.1:8000/docs"
echo "Admin UI: http://127.0.0.1:8501"