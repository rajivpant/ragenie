#!/bin/bash

# RaGenie Setup Verification Script
# This script checks if all services are running correctly

echo "🔍 RaGenie - Setup Verification"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    local endpoint=${3:-"/health"}

    echo -n "Checking $service_name... "

    if docker-compose ps | grep -q "$service_name.*Up"; then
        if [ -n "$port" ]; then
            if curl -s -f "http://localhost:$port$endpoint" > /dev/null 2>&1; then
                echo -e "${GREEN}✓ Running${NC}"
                return 0
            else
                echo -e "${YELLOW}⚠ Container up but endpoint not responding${NC}"
                return 1
            fi
        else
            echo -e "${GREEN}✓ Running${NC}"
            return 0
        fi
    else
        echo -e "${RED}✗ Not running${NC}"
        return 1
    fi
}

# Check if Docker is running
echo -n "Checking Docker... "
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Docker is not running${NC}"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

echo ""
echo "📦 Infrastructure Services:"
echo "-------------------------"
check_service "postgres" "5432"
check_service "redis" "6379"
check_service "minio" "9000" "/minio/health/live"

echo ""
echo "🔐 Backend Services:"
echo "-------------------"
check_service "auth-service" "8001" "/health"
check_service "user-service" "8002" "/health"
check_service "document-service" "8003" "/health"
check_service "conversation-service" "8004" "/health"
check_service "llm-gateway-service" "8005" "/health"

echo ""
echo "🌐 Frontend & Gateway:"
echo "---------------------"
check_service "nginx" "80" "/health"
check_service "frontend" "3000"

echo ""
echo "📊 Monitoring:"
echo "-------------"
check_service "prometheus" "9090"
check_service "grafana" "3001"

echo ""
echo "🔍 Database Check:"
echo "-----------------"
echo -n "Checking database connection... "
if docker-compose exec -T postgres pg_isready -U ragenie > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Connected${NC}"
else
    echo -e "${RED}✗ Cannot connect${NC}"
fi

echo ""
echo "📝 Environment Check:"
echo "--------------------"
echo -n "Checking .env file... "
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ Found${NC}"

    # Check for required API keys
    echo -n "Checking API keys... "
    api_keys_found=0

    if grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
        ((api_keys_found++))
    fi

    if grep -q "ANTHROPIC_API_KEY=sk-ant-" .env 2>/dev/null; then
        ((api_keys_found++))
    fi

    if grep -q "GEMINI_API_KEY=" .env 2>/dev/null && ! grep -q "GEMINI_API_KEY=$" .env; then
        ((api_keys_found++))
    fi

    if [ $api_keys_found -gt 0 ]; then
        echo -e "${GREEN}✓ Found $api_keys_found API key(s)${NC}"
    else
        echo -e "${YELLOW}⚠ No API keys configured${NC}"
        echo "  Please add at least one API key to .env file"
    fi
else
    echo -e "${RED}✗ Not found${NC}"
    echo "  Run: cp .env.example .env"
fi

echo ""
echo "🔗 Service URLs:"
echo "---------------"
echo "Frontend:        http://localhost:3000"
echo "API Gateway:     http://localhost"
echo "Auth Service:    http://localhost:8001/docs"
echo "User Service:    http://localhost:8002/docs"
echo "Document Service: http://localhost:8003/docs"
echo "Conversation:    http://localhost:8004/docs"
echo "LLM Gateway:     http://localhost:8005/docs"
echo "Grafana:         http://localhost:3001 (admin/admin)"
echo "Prometheus:      http://localhost:9090"
echo "MinIO Console:   http://localhost:9001 (minioadmin/minioadmin123)"

echo ""
echo "📋 Quick Commands:"
echo "-----------------"
echo "View logs:       docker-compose logs -f [service-name]"
echo "Restart service: docker-compose restart [service-name]"
echo "Stop all:        docker-compose down"
echo "Rebuild:         docker-compose up --build"
echo ""

# Count running services
total_services=11
running_services=$(docker-compose ps | grep "Up" | wc -l)

echo "=================================="
if [ "$running_services" -eq "$total_services" ]; then
    echo -e "${GREEN}✓ All services are running! ($running_services/$total_services)${NC}"
    echo ""
    echo "🎉 You're ready to use RaGenie!"
    echo "   Visit http://localhost:3000 to get started."
    exit 0
elif [ "$running_services" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Some services are not running ($running_services/$total_services)${NC}"
    echo ""
    echo "Try running: docker-compose up -d"
    exit 1
else
    echo -e "${RED}✗ No services are running${NC}"
    echo ""
    echo "Run: docker-compose up -d"
    exit 1
fi
