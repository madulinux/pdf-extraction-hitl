#!/bin/bash


set -e  # Exit on error

TEMPLATE_ID=$1
TEMPLATE_NAME=$2
LIMIT_DOCUMENTS=$3

if [ -z "$TEMPLATE_ID" ] || [ -z "$TEMPLATE_NAME" ]; then
    echo "Usage: ./run_full_baseline.sh <template_id> <template_name>"
    echo "Example: ./run_full_baseline.sh 1 form_template"
    echo "Limit Documents: $LIMIT_DOCUMENTS"
    exit 1
fi

echo "======================================================================"
echo "🧪 FULL BASELINE WORKFLOW"
echo "======================================================================"
echo "Template ID: $TEMPLATE_ID"
echo "Template Name: $TEMPLATE_NAME"
echo ""


# ============================================================================
# FASE 1: BASELINE EXPERIMENT
# ============================================================================
echo "======================================================================"
echo "📊 FASE 1: BASELINE EXPERIMENT"
echo "======================================================================"

# Step 1.1: Upload dokumen baseline
echo ""
echo "Step 1.1: Upload dokumen baseline..."
python experiments/upload_documents.py \
    --template-id $TEMPLATE_ID \
    --folder experiments/generator/storage/output/$TEMPLATE_NAME \
    --experiment-phase baseline \
    --limit $LIMIT_DOCUMENTS

# Step 1.2: Map ground truth
echo ""
echo "Step 1.2: Map ground truth to document IDs..."
python experiments/map_ground_truth.py \
    --template-id $TEMPLATE_ID \
    --experiment-phase baseline

# Step 1.3: Evaluasi baseline
echo ""
echo "Step 1.3: Evaluate baseline performance..."
python experiments/run_baseline.py --template-id $TEMPLATE_ID

echo ""
echo "✅ FASE 1 SELESAI"
echo ""