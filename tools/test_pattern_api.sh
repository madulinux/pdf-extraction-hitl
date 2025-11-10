#!/bin/bash

# Test Pattern Info API

BASE_URL="http://localhost:8000"

# Login
echo "🔐 Logging in..."
TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['data']['tokens']['access_token'])")

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed"
  exit 1
fi

echo "✅ Login successful"
echo ""

# Test 1: Get all patterns for template
echo "📊 Test 1: Get all patterns for template 1"
echo "=========================================="
curl -s "$BASE_URL/api/v1/patterns/template/1" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -100

echo ""
echo ""

# Test 2: Get specific field patterns
echo "📊 Test 2: Get patterns for field 'issue_place'"
echo "================================================"
curl -s "$BASE_URL/api/v1/patterns/field/1/issue_place" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -80

echo ""
echo ""

# Test 3: Get learning jobs
echo "📊 Test 3: Get learning job history"
echo "===================================="
curl -s "$BASE_URL/api/v1/patterns/learning-jobs/1" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -50

echo ""
echo "✅ All tests completed"
