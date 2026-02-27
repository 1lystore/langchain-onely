#!/bin/bash
# Automated Verification Script for langchain-onely v0.1.1
# This script performs AUTOMATED checks only - does NOT test live API integration

set -e  # Exit on any error

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  langchain-onely v0.1.1${NC}"
echo -e "${BLUE}  Automated Verification${NC}"
echo -e "${BLUE}======================================${NC}\n"

echo -e "${YELLOW}NOTE: This script only runs AUTOMATED checks.${NC}"
echo -e "${YELLOW}Live API integration tests must be run separately.${NC}\n"

# Phase 1: Code Compilation
echo -e "${BLUE}Phase 1: Code Compilation & Syntax${NC}"
echo "-----------------------------------"

echo -n "Compiling source files... "
python3 -m py_compile langchain_onely/*.py 2>/dev/null
echo -e "${GREEN}✅ PASSED${NC}"

echo -n "Compiling example files... "
python3 -m py_compile examples/*.py 2>/dev/null
echo -e "${GREEN}✅ PASSED${NC}"

echo -n "Compiling test files... "
python3 -m py_compile tests/*.py 2>/dev/null
echo -e "${GREEN}✅ PASSED${NC}"

echo -n "Running linter (ruff)... "
if ruff check langchain_onely/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASSED${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
    echo -e "${YELLOW}Run 'ruff check langchain_onely/' to see errors${NC}"
    exit 1
fi

echo -n "Checking code formatting (black)... "
if black --check langchain_onely/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASSED${NC}"
else
    echo -e "${YELLOW}⚠️  NEEDS FORMATTING${NC}"
    echo -e "${YELLOW}Run 'black langchain_onely/' to fix${NC}"
fi

echo ""

# Phase 2: Unit Tests
echo -e "${BLUE}Phase 2: Unit Tests${NC}"
echo "-------------------"

echo -n "Running pytest... "
if pytest tests/ -q > /dev/null 2>&1; then
    TEST_COUNT=$(pytest tests/ --collect-only -q 2>/dev/null | grep "test session starts" -A 1 | tail -1 | awk '{print $1}')
    echo -e "${GREEN}✅ ALL $TEST_COUNT TESTS PASSED${NC}"
else
    echo -e "${RED}❌ TESTS FAILED${NC}"
    echo -e "${YELLOW}Run 'pytest tests/ -v' to see failures${NC}"
    exit 1
fi

echo ""

# Phase 3: Package Build
echo -e "${BLUE}Phase 3: Package Build${NC}"
echo "----------------------"

echo -n "Cleaning old build artifacts... "
rm -rf dist/ build/ *.egg-info 2>/dev/null
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo -e "${GREEN}✅ CLEANED${NC}"

echo -n "Building package... "
python3 -m build > /dev/null 2>&1
if [ -f "dist/langchain_onely-0.1.1-py3-none-any.whl" ]; then
    echo -e "${GREEN}✅ BUILT${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
    exit 1
fi

echo -n "Verifying package metadata... "
if twine check dist/* > /dev/null 2>&1; then
    echo -e "${GREEN}✅ VALID${NC}"
else
    echo -e "${RED}❌ INVALID${NC}"
    exit 1
fi

echo ""

# Phase 4: Installation Test
echo -e "${BLUE}Phase 4: Installation Test${NC}"
echo "--------------------------"

echo -n "Creating test environment... "
python3 -m venv test_env > /dev/null 2>&1
echo -e "${GREEN}✅ CREATED${NC}"

echo -n "Installing package from wheel... "
./test_env/bin/pip install -q dist/langchain_onely-0.1.1-py3-none-any.whl
echo -e "${GREEN}✅ INSTALLED${NC}"

echo -n "Testing import... "
./test_env/bin/python -c "from langchain_onely import OneLyToolkit" 2>/dev/null
echo -e "${GREEN}✅ PASSED${NC}"

echo -n "Testing version... "
VERSION=$(./test_env/bin/python -c "from langchain_onely import __version__; print(__version__)")
if [ "$VERSION" = "0.1.1" ]; then
    echo -e "${GREEN}✅ v0.1.1${NC}"
else
    echo -e "${RED}❌ Version mismatch: $VERSION${NC}"
    rm -rf test_env
    exit 1
fi

echo -n "Testing toolkit initialization... "
./test_env/bin/python -c "
from langchain_onely import OneLyToolkit
toolkit = OneLyToolkit()
tools = toolkit.get_tools()
assert len(tools) == 5, f'Expected 5 tools, got {len(tools)}'
" 2>/dev/null
echo -e "${GREEN}✅ 5 tools loaded${NC}"

echo -n "Cleaning up test environment... "
rm -rf test_env
echo -e "${GREEN}✅ REMOVED${NC}"

echo ""

# Phase 5: Security Check
echo -e "${BLUE}Phase 5: Security Verification${NC}"
echo "-------------------------------"

echo -n "Scanning for hardcoded secrets... "
if grep -r "sk-[a-zA-Z0-9]\{20\}" langchain_onely/ 2>/dev/null | grep -v test; then
    echo -e "${RED}❌ FOUND SECRETS${NC}"
    exit 1
else
    echo -e "${GREEN}✅ CLEAN${NC}"
fi

echo -n "Checking for private keys in source... "
if grep -r "0x[a-fA-F0-9]\{64\}" langchain_onely/ 2>/dev/null | grep -v "test\|example"; then
    echo -e "${RED}❌ FOUND KEYS${NC}"
    exit 1
else
    echo -e "${GREEN}✅ CLEAN${NC}"
fi

echo -n "Verifying .gitignore coverage... "
if grep -q "\\.env$" .gitignore && grep -q "__pycache__" .gitignore; then
    echo -e "${GREEN}✅ COMPLETE${NC}"
else
    echo -e "${RED}❌ INCOMPLETE${NC}"
    exit 1
fi

echo ""

# Phase 6: Documentation Check
echo -e "${BLUE}Phase 6: Documentation${NC}"
echo "----------------------"

echo -n "Checking README sections... "
MISSING_SECTIONS=""
grep -q "## Installation" README.md || MISSING_SECTIONS+="Installation "
grep -q "## Quick Start" README.md || MISSING_SECTIONS+="QuickStart "
grep -q "## Examples" README.md || MISSING_SECTIONS+="Examples "
grep -q "## Tools" README.md || MISSING_SECTIONS+="Tools "

if [ -z "$MISSING_SECTIONS" ]; then
    echo -e "${GREEN}✅ COMPLETE${NC}"
else
    echo -e "${RED}❌ Missing: $MISSING_SECTIONS${NC}"
fi

echo -n "Verifying examples documentation... "
if [ -f "examples/README.md" ]; then
    echo -e "${GREEN}✅ EXISTS${NC}"
else
    echo -e "${YELLOW}⚠️  MISSING${NC}"
fi

echo ""

# Phase 7: Version Consistency
echo -e "${BLUE}Phase 7: Version Consistency${NC}"
echo "----------------------------"

echo -n "Checking pyproject.toml... "
grep -q 'version = "0.1.1"' pyproject.toml && echo -e "${GREEN}✅ 0.1.1${NC}" || echo -e "${RED}❌ MISMATCH${NC}"

echo -n "Checking constants.py... "
grep -q 'PACKAGE_VERSION = "0.1.1"' langchain_onely/constants.py && echo -e "${GREEN}✅ 0.1.1${NC}" || echo -e "${RED}❌ MISMATCH${NC}"

echo -n "Checking __init__.py... "
python3 -c "from langchain_onely import __version__; assert __version__ == '0.1.1'" 2>/dev/null && echo -e "${GREEN}✅ 0.1.1${NC}" || echo -e "${RED}❌ MISMATCH${NC}"

echo ""

# Phase 8: Package Contents
echo -e "${BLUE}Phase 8: Package Contents${NC}"
echo "-------------------------"

SOURCE_COUNT=$(find langchain_onely -name "*.py" | wc -l | xargs)
TEST_COUNT=$(find tests -name "*.py" | wc -l | xargs)
EXAMPLE_COUNT=$(find examples -name "*.py" | wc -l | xargs)

echo "Source files: ${SOURCE_COUNT}"
echo "Test files: ${TEST_COUNT}"
echo "Example files: ${EXAMPLE_COUNT}"
echo "Total Python files: $((SOURCE_COUNT + TEST_COUNT + EXAMPLE_COUNT))"

echo ""

# Final Summary
echo -e "${BLUE}======================================${NC}"
echo -e "${GREEN}   ✅ ALL AUTOMATED CHECKS PASSED!${NC}"
echo -e "${BLUE}======================================${NC}\n"

echo -e "${YELLOW}⚠️  IMPORTANT: Automated checks only verify code quality.${NC}"
echo -e "${YELLOW}⚠️  Live API integration tests are REQUIRED before publishing.${NC}\n"

echo -e "${GREEN}Automated verification complete! ✅${NC}\n"

echo "Next steps:"
echo "1. ${YELLOW}Run live integration tests:${NC} python test_live_integration.py"
echo "2. ${YELLOW}Review results in:${NC} VERIFICATION_REPORT.md"
echo "3. If live tests pass, then:"
echo "   - Push to GitHub: git push origin main"
echo "   - Tag release: git tag -a v0.1.1 -m 'Release v0.1.1'"
echo "   - Publish to PyPI: twine upload dist/*"

echo ""
echo -e "${BLUE}Built packages ready in dist/:${NC}"
ls -lh dist/

echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  ⚠️  DO NOT PUBLISH TO PYPI YET!${NC}"
echo -e "${YELLOW}  Run test_live_integration.py first${NC}"
echo -e "${YELLOW}========================================${NC}"
