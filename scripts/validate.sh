#!/bin/bash

# Quick Service Validation Wrapper
# This script provides a simple way to check if all services are ready

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "🔍 Checking Observability Services..."
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -q -r requirements.txt
fi

# Run validation script
python scripts/validate_services.py
VALIDATION_EXIT_CODE=$?

echo ""

# Handle exit code
case $VALIDATION_EXIT_CODE in
    0)
        echo -e "${GREEN}✅ All services are ready!${NC}"
        echo -e "${GREEN}You can start the agent with: ./start.sh${NC}"
        exit 0
        ;;
    1)
        echo -e "${RED}❌ Critical services are down. Cannot proceed.${NC}"
        echo -e "${YELLOW}Run 'python scripts/fix_connections.py' if services are in cluster${NC}"
        exit 1
        ;;
    2)
        echo -e "${YELLOW}⚠️  Some optional services are unavailable.${NC}"
        echo -e "${YELLOW}Agent can start but some features may not work.${NC}"
        exit 2
        ;;
    *)
        echo -e "${RED}❌ Validation failed with unknown error${NC}"
        exit 1
        ;;
esac
