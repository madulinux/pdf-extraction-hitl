#!/bin/bash

# Quick script to run API-based experiment
# Usage: ./run_experiment.sh [template_id] [batch_size] [additional_args...]
#
# Template ID mapping:
#   1 = form_template
#   2 = table_template
#   3 = letter_template
#   4 = mixed_template
#
# Example with debug:
#   ./run_experiment.sh 1 5 --debug

TEMPLATE_ID=${1:-1}
BATCH_SIZE=${2:-5}

# Shift first two arguments so $@ contains only additional arguments
shift 2

# Template name mapping
case $TEMPLATE_ID in
    1) TEMPLATE_NAME="form_template" ;;
    2) TEMPLATE_NAME="table_template" ;;
    3) TEMPLATE_NAME="letter_template" ;;
    4) TEMPLATE_NAME="mixed_template" ;;
    *)
        echo "❌ Invalid template ID: $TEMPLATE_ID"
        echo "Valid template IDs:"
        echo "  1 = form_template"
        echo "  2 = table_template"
        echo "  3 = letter_template"
        echo "  4 = mixed_template"
        exit 1
        ;;
esac

echo "🧪 Running API Experiment"
echo "=========================="
echo "Template ID: $TEMPLATE_ID ($TEMPLATE_NAME)"
echo "Batch Size: $BATCH_SIZE"
echo "PDF Directory: Auto-detected (experiments/generator/storage/output/$TEMPLATE_NAME)"
echo ""

# Check if server is running
echo "🔍 Checking if API server is running..."
if curl -s http://localhost:8000/api/v1/auth/login > /dev/null 2>&1; then
    echo "✅ Server is running"
else
    echo "❌ Server is not running!"
    echo "Please start the server first:"
    echo "  python manage.py runserver"
    exit 1
fi

echo ""
echo "🚀 Starting experiment..."
echo ""

# Run the experiment (PDF directory will be auto-detected)
# Pass all additional arguments to Python script
python experiments/run_api_experiment.py \
    --template-id $TEMPLATE_ID \
    --batch-size $BATCH_SIZE \
    "$@"

echo ""
echo "✅ Experiment completed!"
