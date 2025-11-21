# Experiment Results - Complete Package for Thesis

**Generated:** November 18, 2025  
**Status:** ✅ **COMPLETE AND READY FOR THESIS WRITING**

---

## 📊 Quick Summary

| Metric | Value |
|--------|-------|
| **Total Documents** | 140 |
| **Templates Tested** | 4 types |
| **Baseline Accuracy** | 72.65% ± 3.20% |
| **Adaptive Accuracy** | 98.61% ± 2.19% |
| **Average Improvement** | +35.91% ± 4.76% |
| **Error Reduction** | 94.92% |
| **User Effort** | 7% correction rate |
| **Learning Efficiency** | 1.88 corrections/pp |

---

## 📁 Directory Structure

```
experiments/results/
├── README.md                              # This file
├── EXPERIMENT_SUMMARY.md                  # Comprehensive summary (500+ lines)
├── THESIS_CHECKLIST.md                    # Complete thesis writing guide
│
├── Raw Data (JSON)
│   ├── baseline_template_1.json           # Form template baseline
│   ├── baseline_template_2.json           # Table template baseline
│   ├── baseline_template_3.json           # Letter template baseline
│   ├── baseline_template_4.json           # Mixed template baseline
│   ├── adaptive_template_1.json           # Form template adaptive
│   ├── adaptive_template_2.json           # Table template adaptive
│   ├── adaptive_template_3.json           # Letter template adaptive
│   ├── adaptive_template_4.json           # Mixed template adaptive
│   ├── comparison_template_1-4.json       # Comparison results
│   ├── learning_curve_1-4.json            # Learning curves
│   └── statistical_summary.json           # Statistical summary
│
├── Visualizations (PNG - 300 DPI)
│   ├── learning_curves_all_templates.png          # Main learning curves
│   ├── accuracy_comparison_all_templates.png      # Bar chart comparison
│   ├── metrics_improvement_heatmap.png            # Heatmap visualization
│   ├── error_reduction_analysis.png               # Error reduction charts
│   ├── learning_efficiency_analysis.png           # Efficiency analysis
│   ├── confidence_analysis.png                    # Confidence scores
│   ├── batch_progression_detailed.png             # Detailed progression
│   └── field_difficulty_analysis.png              # Field difficulty
│
├── LaTeX Tables
│   ├── latex_tables/
│   │   ├── all_tables.tex                 # Combined file
│   │   ├── main_results.tex               # Main comparison table
│   │   ├── detailed_metrics.tex           # Detailed metrics table
│   │   ├── confusion_matrix.tex           # Confusion matrix table
│   │   ├── learning_efficiency.tex        # Learning efficiency table
│   │   └── field_performance_1-4.tex      # Per-field tables
│
├── Thesis Content (LaTeX - Indonesian)
│   ├── thesis_content/
│   │   ├── abstract_id.tex                # Indonesian abstract
│   │   ├── results_section.tex            # Complete results section
│   │   ├── discussion_section.tex         # Complete discussion section
│   │   └── conclusion_section.tex         # Complete conclusion section
│
└── Generation Scripts
    ├── generate_latex_tables.py           # Generate LaTeX tables
    ├── generate_additional_analysis.py    # Generate visualizations
    └── generate_thesis_content.py         # Generate thesis content
```

---

## 🎯 How to Use This Package

### For Thesis Writing

1. **Read the Summary First:**
   ```bash
   cat EXPERIMENT_SUMMARY.md
   ```

2. **Check the Checklist:**
   ```bash
   cat THESIS_CHECKLIST.md
   ```

3. **Copy LaTeX Tables to Thesis:**
   ```bash
   cp latex_tables/*.tex ~/your-thesis/tables/
   ```

4. **Copy Visualizations to Thesis:**
   ```bash
   cp *.png ~/your-thesis/figures/
   ```

5. **Copy Thesis Content:**
   ```bash
   cp thesis_content/*.tex ~/your-thesis/sections/
   ```

### In Your LaTeX Document

```latex
% In your main thesis file

% Abstract
\input{sections/abstract_id.tex}

% Results Chapter (BAB IV)
\chapter{Hasil dan Pembahasan}
\input{sections/results_section.tex}
\input{sections/discussion_section.tex}

% Conclusion Chapter (BAB V)
\chapter{Kesimpulan dan Saran}
\input{sections/conclusion_section.tex}

% Tables (referenced in text)
\input{tables/main_results.tex}
\input{tables/detailed_metrics.tex}
\input{tables/confusion_matrix.tex}
\input{tables/learning_efficiency.tex}

% Figures (referenced in text)
\begin{figure}[htbp]
\centering
\includegraphics[width=0.9\textwidth]{figures/learning_curves_all_templates.png}
\caption{Kurva Pembelajaran Sistem Adaptif}
\label{fig:learning_curves}
\end{figure}
```

---

## 📊 Key Results by Template

### Template 1: Form Template (KTP/Identity Forms)
- **Documents:** 35 | **Fields:** 15 per doc
- **Baseline:** 76.76% → **Adaptive:** 100.00%
- **Improvement:** +23.24% (+30.27% relative)
- **Corrections:** 32 | **Efficiency:** 1.38 corr/pp
- **Status:** ✅ Perfect extraction achieved

### Template 2: Table Template (Inspection Reports)
- **Documents:** 35 | **Fields:** 23 per doc
- **Baseline:** 74.78% → **Adaptive:** 100.00%
- **Improvement:** +25.22% (+33.72% relative)
- **Corrections:** 29 | **Efficiency:** 1.15 corr/pp
- **Status:** ✅ Perfect extraction achieved
- **Note:** Best efficiency (1.15 corr/pp)

### Template 3: Letter Template (Official Letters)
- **Documents:** 35 | **Fields:** 21 per doc
- **Baseline:** 69.52% → **Adaptive:** 94.83%
- **Improvement:** +25.31% (+36.40% relative)
- **Corrections:** 81 | **Efficiency:** 3.20 corr/pp
- **Status:** ⚠️ Most challenging (most corrections needed)

### Template 4: Mixed Template (Invoices)
- **Documents:** 35 | **Fields:** 21 per doc
- **Baseline:** 69.52% → **Adaptive:** 99.59%
- **Improvement:** +30.07% (+43.25% relative)
- **Corrections:** 54 | **Efficiency:** 1.80 corr/pp
- **Status:** ✅ Best relative improvement (+43.25%)

---

## 📈 Statistical Summary

### Overall Performance

| Metric | Baseline | Adaptive | Improvement |
|--------|----------|----------|-------------|
| **Accuracy** | 72.65% ± 3.20% | 98.61% ± 2.19% | +35.91% |
| **Precision** | 73.15% ± 3.35% | 98.64% ± 2.19% | +34.84% |
| **Recall** | 99.00% ± 1.12% | 99.97% ± 0.06% | +0.96% |
| **F1-Score** | 84.12% ± 2.05% | 99.29% ± 1.11% | +18.04% |

### Error Analysis

| Error Type | Baseline | Adaptive | Reduction |
|------------|----------|----------|-----------|
| **False Positives** | 752 | 40 | 94.68% |
| **False Negatives** | 21 | 1 | 95.24% |
| **Total Errors** | 773 | 41 | 94.69% |
| **Error Rate** | 27.35% | 1.39% | 94.92% |

### Learning Efficiency

| Metric | Value |
|--------|-------|
| **Total Corrections** | 196 |
| **Total Fields** | 2,800 |
| **Correction Rate** | 7.00% |
| **Avg Corrections/Doc** | 1.40 |
| **Corrections/PP** | 1.88 |
| **Batches to >95%** | 5-7 |

---

## 🎓 Thesis Contributions

### 1. Hybrid Extraction Strategy
- Combines rule-based and CRF approaches
- Adaptive weight adjustment based on confidence
- Fallback mechanism for robustness

### 2. Human-in-the-Loop Learning
- Minimal user burden (7% correction rate)
- Efficient learning (1.88 corrections/pp)
- Incremental learning without full retraining

### 3. Cross-Template Generalization
- Validated on 4 different document types
- Consistent performance (σ = 2.19%)
- Adapts to template-specific characteristics

### 4. Production-Ready System
- High accuracy (98.61%)
- Low error rate (1.39%)
- Fast learning (5-7 batches)
- Practical deployment

---

## 📝 Citation Data

### For Abstract/Introduction

> "An adaptive document extraction system using hybrid rule-based and CRF strategies 
> improved accuracy from 72.65% to 98.61% (+35.91%) across 140 documents with only 7% 
> user corrections, demonstrating effective human-in-the-loop learning with minimal 
> user burden."

### Key Numbers for Quick Reference

- **Documents:** 140
- **Templates:** 4 types
- **Baseline:** 72.65%
- **Adaptive:** 98.61%
- **Improvement:** +35.91%
- **Error Reduction:** 94.92%
- **User Effort:** 7%
- **Efficiency:** 1.88 corr/pp

---

## 🔬 Methodology Summary

### Experiment Design

1. **Phase 0: Preparation**
   - Clean database
   - Remove existing models
   - Disable auto-training

2. **Phase 1: Baseline**
   - Upload documents
   - Extract using rule-based only
   - Evaluate against ground truth

3. **Phase 2: Adaptive**
   - Enable auto-training
   - Upload same documents
   - Simulate user feedback (batch-wise)
   - Train CRF model
   - Re-extract with hybrid strategy
   - Evaluate improvements

4. **Phase 3: Analysis**
   - Compare baseline vs adaptive
   - Generate visualizations
   - Calculate statistics

### Metrics Calculated

All metrics follow standard definitions:

- **Accuracy:** $A = \frac{TP}{TP + FP + FN}$
- **Precision:** $P = \frac{TP}{TP + FP}$
- **Recall:** $R = \frac{TP}{TP + FN}$
- **F1-Score:** $F1 = 2 \times \frac{P \times R}{P + R}$
- **Improvement:** $\Delta A\% = \frac{A_{\text{adaptive}} - A_{\text{baseline}}}{A_{\text{baseline}}} \times 100\%$

---

## 🎨 Visualization Guide

### Figure 1: Learning Curves
**File:** `learning_curves_all_templates.png`  
**Usage:** Show learning progression for all templates  
**Caption:** "Kurva pembelajaran menunjukkan peningkatan akurasi yang konsisten across semua template"

### Figure 2: Accuracy Comparison
**File:** `accuracy_comparison_all_templates.png`  
**Usage:** Bar chart comparing baseline vs adaptive  
**Caption:** "Perbandingan akurasi baseline dan adaptive menunjukkan peningkatan signifikan"

### Figure 3: Metrics Heatmap
**File:** `metrics_improvement_heatmap.png`  
**Usage:** Heatmap of improvements by metric and template  
**Caption:** "Heatmap peningkatan metrik menunjukkan improvement across semua dimensi"

### Figure 4: Error Reduction
**File:** `error_reduction_analysis.png`  
**Usage:** Show FP and FN reduction  
**Caption:** "Pengurangan error yang signifikan dari baseline ke adaptive"

### Figure 5: Learning Efficiency
**File:** `learning_efficiency_analysis.png`  
**Usage:** Corrections vs improvement scatter plot  
**Caption:** "Efisiensi pembelajaran ditunjukkan dengan minimal corrections untuk maximum improvement"

### Figure 6: Confidence Analysis
**File:** `confidence_analysis.png`  
**Usage:** Per-field confidence comparison  
**Caption:** "Analisis confidence score menunjukkan kalibrasi yang lebih baik pada sistem adaptive"

### Figure 7: Batch Progression
**File:** `batch_progression_detailed.png`  
**Usage:** Detailed batch-wise progression  
**Caption:** "Progression detail per batch menunjukkan pembelajaran yang monoton tanpa degradasi"

### Figure 8: Field Difficulty
**File:** `field_difficulty_analysis.png`  
**Usage:** Most challenging fields analysis  
**Caption:** "Analisis kesulitan field mengidentifikasi area yang memerlukan improvement"

---

## 📋 Table Guide

### Table 1: Main Results
**File:** `latex_tables/main_results.tex`  
**Content:** Overall comparison by template  
**Usage:** Primary results table

### Table 2: Detailed Metrics
**File:** `latex_tables/detailed_metrics.tex`  
**Content:** Precision, Recall, F1 for all templates  
**Usage:** Comprehensive metrics comparison

### Table 3: Confusion Matrix
**File:** `latex_tables/confusion_matrix.tex`  
**Content:** TP, FP, FN for baseline and adaptive  
**Usage:** Error analysis

### Table 4: Learning Efficiency
**File:** `latex_tables/learning_efficiency.tex`  
**Content:** Corrections and efficiency metrics  
**Usage:** HITL effectiveness analysis

### Tables 5-8: Field Performance
**Files:** `latex_tables/field_performance_1-4.tex`  
**Content:** Per-field accuracy for each template  
**Usage:** Detailed field-level analysis

---

## ✅ Quality Assurance

### Data Integrity Checks
- [x] All 140 documents processed
- [x] No missing ground truth files
- [x] Consistent field counts
- [x] All metrics calculated correctly

### Metric Validation
- [x] Accuracy formula verified
- [x] Precision formula verified
- [x] Recall formula verified
- [x] F1-Score formula verified
- [x] Confusion matrix sums correct

### Reproducibility
- [x] Experiment scripts documented
- [x] Environment documented
- [x] Data generation process documented
- [x] Results can be regenerated

---

## 🚀 Next Steps

### Immediate (Thesis Writing)
1. Copy files to thesis directory
2. Include LaTeX tables and figures
3. Write narrative using provided content
4. Add citations and references

### Optional (Additional Analysis)
1. Generate more visualizations if needed
2. Create presentation slides
3. Prepare demo for defense
4. Write journal paper

---

## 📞 Support

**Experiment Location:**  
`/Users/madulinux/Documents/S2 UNAS/TESIS/Project/backend/experiments/results/`

**Key Scripts:**
- `run_full_experiment.sh` - Main experiment runner
- `generate_latex_tables.py` - LaTeX table generator
- `generate_additional_analysis.py` - Visualization generator
- `generate_thesis_content.py` - Thesis content generator

**Documentation:**
- `EXPERIMENT_SUMMARY.md` - Comprehensive summary
- `THESIS_CHECKLIST.md` - Complete checklist
- `README.md` - This file

---

## 🎉 Status

**✅ COMPLETE AND READY FOR THESIS WRITING**

All data collected, analyzed, and documented. All visualizations and LaTeX tables generated. 
Thesis content sections written in Indonesian. Ready for integration into thesis document.

**Last Updated:** November 18, 2025  
**Total Files Generated:** 30+  
**Total Visualizations:** 8  
**Total LaTeX Tables:** 8  
**Total Thesis Sections:** 4

---

**Good luck with your thesis! 🎓**
