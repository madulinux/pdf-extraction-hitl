#!/bin/bash

# Full Experiment Workflow Script
# Usage: ./run_full_experiment.sh <template_id> <template_name>
# Example: ./run_full_experiment.sh 1 form_template

set -e  # Exit on error

TEMPLATE_ID=$1
TEMPLATE_NAME=$2
LIMIT_DOCUMENTS=$3

if [ -z "$TEMPLATE_ID" ] || [ -z "$TEMPLATE_NAME" ] || [ -z "$LIMIT_DOCUMENTS" ]; then
    echo "Available templates:"
    echo "[1] form_template"
    echo "[2] table_template"
    echo "[3] letter_template"
    echo "[4] mixed_template"
    echo "======================================================================"
    echo "Usage: ./run_full_experiment.sh <template_id> <template_name> <limit_documents>"
    echo "Example: ./run_full_experiment.sh 1 form_template 100"
    exit 1
fi

# get this file directory
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BACKEND_DIR=$(cd "$SCRIPT_DIR/.." && pwd)

# Change to backend directory
cd "$BACKEND_DIR"

if [ ! -d "$SCRIPT_DIR/generator/storage/output/$TEMPLATE_NAME" ]; then
    echo "Error: Output folder not found for template $TEMPLATE_NAME"
    exit 1
fi

echo "======================================================================"
echo "🧪 FULL EXPERIMENT WORKFLOW"
echo "======================================================================"
echo "Template ID: $TEMPLATE_ID"
echo "Template Name: $TEMPLATE_NAME"
echo "Limit Documents: $LIMIT_DOCUMENTS"
echo ""

# ============================================================================
# FASE 0: PERSIAPAN
# ============================================================================
echo "======================================================================"
echo "📋 FASE 0: PERSIAPAN"
echo "======================================================================"

# Set AUTO_TRAINING=False untuk baseline
echo "AUTO_TRAINING=False" > .env
echo "✅ Set AUTO_TRAINING=False"

# Hapus model CRF (jika ada)
rm -f models/template_${TEMPLATE_ID}_model.joblib
echo "✅ Removed CRF model (if exists)"

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

if [ $? -ne 0 ]; then
    echo "❌ Error uploading baseline documents"
    exit 1
fi

# Step 1.2: Map ground truth
echo ""
echo "Step 1.2: Map ground truth to document IDs..."
python experiments/map_ground_truth.py \
    --template-id $TEMPLATE_ID \
    --experiment-phase baseline

if [ $? -ne 0 ]; then
    echo "❌ Error mapping ground truth"
    exit 1
fi

# Step 1.3: Evaluasi baseline
echo ""
echo "Step 1.3: Evaluate baseline performance..."
python experiments/run_baseline.py --template-id $TEMPLATE_ID

if [ $? -ne 0 ]; then
    echo "❌ Error running baseline evaluation"
    exit 1
fi

echo ""
echo "✅ FASE 1 SELESAI"
echo ""

# ============================================================================
# FASE 2: ADAPTIVE LEARNING EXPERIMENT
# ============================================================================
echo "======================================================================"
echo "🎓 FASE 2: ADAPTIVE LEARNING EXPERIMENT"
echo "======================================================================"

# Step 2.1: Enable AUTO_TRAINING
echo "AUTO_TRAINING=True" > .env
echo "✅ Set AUTO_TRAINING=True"

# Step 2.2: Upload dokumen adaptive
echo ""
echo "Step 2.2: Upload dokumen adaptive..."
python experiments/upload_documents.py \
    --template-id $TEMPLATE_ID \
    --folder experiments/generator/storage/output/$TEMPLATE_NAME \
    --experiment-phase adaptive \
    --limit $LIMIT_DOCUMENTS

if [ $? -ne 0 ]; then
    echo "❌ Error uploading adaptive documents"
    exit 1
fi

# Step 2.3: Map ground truth untuk adaptive
echo ""
echo "Step 2.3: Map ground truth for adaptive documents..."
python experiments/map_ground_truth.py \
    --template-id $TEMPLATE_ID \
    --experiment-phase adaptive

if [ $? -ne 0 ]; then
    echo "❌ Error mapping ground truth for adaptive"
    exit 1
fi

# Step 2.4: Run adaptive learning
echo ""
echo "Step 2.4: Run adaptive learning experiment..."
python experiments/run_adaptive.py \
    --template-id $TEMPLATE_ID \
    --batch-size 5

if [ $? -ne 0 ]; then
    echo "❌ Error running adaptive experiment"
    exit 1
fi

echo ""
echo "✅ FASE 2 SELESAI"
echo ""

# ============================================================================
# FASE 3: ANALISIS DAN PERBANDINGAN
# ============================================================================
echo "======================================================================"
echo "📈 FASE 3: ANALISIS DAN PERBANDINGAN"
echo "======================================================================"

python experiments/compare_experiments.py --template-id $TEMPLATE_ID

if [ $? -ne 0 ]; then
    echo "❌ Error comparing experiments"
    exit 1
fi

echo ""
echo "✅ FASE 3 SELESAI"
echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "======================================================================"
echo "🎉 EXPERIMENT COMPLETED!"
echo "======================================================================"
echo "Template ID: $TEMPLATE_ID"
echo "Template Name: $TEMPLATE_NAME"
echo ""
echo "📁 Results saved in: experiments/results/"
echo "   - baseline_template_${TEMPLATE_ID}.json"
echo "   - adaptive_template_${TEMPLATE_ID}.json"
echo "   - learning_curve_${TEMPLATE_ID}.json"
echo "   - comparison_template_${TEMPLATE_ID}.json"
echo "   - visualization_data_${TEMPLATE_ID}.json"
echo ""
echo "======================================================================"
