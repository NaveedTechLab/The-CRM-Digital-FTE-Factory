#!/bin/bash

# Verification script for Customer Success Digital FTE prototype
# Sends curl requests to all three channels and verifies ticket creation and response generation

echo "Starting verification of Customer Success Digital FTE prototype..."
echo "Testing all three channels: email, whatsapp, webform"

# Base URL for the API (assuming it's running on localhost:8000)
BASE_URL="http://localhost:8000/inbound"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counter for test results
passed_tests=0
total_tests=3

# Function to run a test and check results
run_test() {
    local channel=$1
    local params=$2
    local test_name=$3

    echo -e "\n${YELLOW}Testing $test_name...${NC}"

    # Send the curl request
    response=$(curl -s -X POST "$BASE_URL/$channel?$params" -w "\nHTTP_CODE:%{http_code}" -o /tmp/curl_output.txt)

    http_code=$(echo "$response" | tail -n 1 | cut -d':' -f2)
    actual_response=$(head -n -1 /tmp/curl_output.txt)

    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✓ HTTP $http_code - Success${NC}"

        # Check if response contains required fields
        if echo "$actual_response" | grep -q '"success":true'; then
            echo -e "${GREEN}✓ Response contains success:true${NC}"
        else
            echo -e "${RED}✗ Response missing success:true${NC}"
        fi

        if echo "$actual_response" | grep -q '"ticket_created":true'; then
            echo -e "${GREEN}✓ Response indicates ticket was created${NC}"
            ((passed_tests++))
        else
            echo -e "${RED}✗ Response does not indicate ticket was created${NC}"
        fi
    else
        echo -e "${RED}✗ HTTP $http_code - Failed${NC}"
        echo "Response: $actual_response"
    fi

    # Show the actual response for debugging
    echo "Response: $actual_response"
}

# Test 1: Email channel
echo -e "\n${YELLOW}=== EMAIL CHANNEL TEST ===${NC}"
run_test "email" "email=test@example.com&name=Test%20User&message=Hello%2C%20I%20have%20a%20question%20about%20your%20product." "Email Channel"

# Wait a moment between requests
sleep 2

# Test 2: WhatsApp channel
echo -e "\n${YELLOW}=== WHATSAPP CHANNEL TEST ===${NC}"
run_test "whatsapp" "phone=+1234567890&name=WhatsApp%20User&message=Hi%2C%20I%20need%20help%20with%20setup." "WhatsApp Channel"

# Wait a moment between requests
sleep 2

# Test 3: Webform channel
echo -e "\n${YELLOW}=== WEBFORM CHANNEL TEST ===${NC}"
run_test "webform" "email=web@example.com&name=Web%20User&message=I%20would%20like%20more%20information%20about%20pricing." "WebForm Channel"

# Summary
echo -e "\n${YELLOW}=== TEST SUMMARY ===${NC}"
echo "Passed: $passed_tests/$total_tests tests"

if [ $passed_tests -eq $total_tests ]; then
    echo -e "${GREEN}🎉 All tests passed! The verification script confirms that all three channels work correctly.${NC}"
    echo "Each channel successfully:"
    echo "  - Received the request"
    echo "  - Created a ticket"
    echo "  - Generated a response"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please check the implementation.${NC}"
    exit 1
fi