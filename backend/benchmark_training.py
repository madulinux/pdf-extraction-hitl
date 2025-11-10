#!/usr/bin/env python3
"""
Benchmark CRF training performance
"""

import time
import pdfplumber
from database.db_manager import DatabaseManager
from core.learning.learner import AdaptiveLearner
from sklearn_crfsuite import CRF
from database.repositories.document_repository import DocumentRepository
from database.repositories.feedback_repository import FeedbackRepository


def benchmark_training(template_id: int):
    """Benchmark CRF training time"""

    print(f"\n{'='*60}")
    print(f"🔍 BENCHMARK CRF TRAINING PERFORMANCE")
    print(f"{'='*60}\n")

    # Get feedback
    db = DatabaseManager()
    feedback_repo = FeedbackRepository(db)
    feedback_list = feedback_repo.find_for_training(template_id, unused_only=False)

    print(f"📊 Training data:")
    print(f"   - Total feedback: {len(feedback_list)} records")

    # Group by document
    feedback_by_doc = {}
    for feedback in feedback_list:
        doc_id = feedback["document_id"]
        if doc_id not in feedback_by_doc:
            feedback_by_doc[doc_id] = []
        feedback_by_doc[doc_id].append(feedback)

    print(f"   - Unique documents: {len(feedback_by_doc)}")
    print()

    # Prepare training data
    print(f"⏱️  Preparing training data...")
    start_prep = time.time()

    X_train = []
    y_train = []
    learner = AdaptiveLearner()
    document_repo = DocumentRepository(db)

    for doc_id, doc_feedbacks in feedback_by_doc.items():
        document = document_repo.find_by_id(doc_id)
        if not document:
            continue

        with pdfplumber.open(document.file_path) as pdf:
            words = []
            for page in pdf.pages:
                page_words = page.extract_words(x_tolerance=3, y_tolerance=3)
                words.extend(page_words)

        features, labels = learner._create_bio_sequence_multi(doc_feedbacks, words)

        if features and labels:
            X_train.append(features)
            y_train.append(labels)

    prep_time = time.time() - start_prep
    print(f"✅ Data preparation: {prep_time:.3f} seconds")
    print(f"   - Training samples: {len(X_train)}")
    print()

    # Train model
    print(f"⏱️  Training CRF model...")
    start_train = time.time()

    crf = CRF(
        algorithm="lbfgs",
        max_iterations=100,
        all_possible_transitions=True,
        verbose=False,
    )

    crf.fit(X_train, y_train)

    train_time = time.time() - start_train
    print(f"✅ Model training: {train_time:.3f} seconds")
    print()

    # Total time
    total_time = prep_time + train_time
    print(f"{'='*60}")
    print(f"📊 BENCHMARK RESULTS")
    print(f"{'='*60}\n")
    print(f"Data preparation: {prep_time:.3f}s ({prep_time/total_time*100:.1f}%)")
    print(f"Model training:   {train_time:.3f}s ({train_time/total_time*100:.1f}%)")
    print(f"{'─'*60}")
    print(f"Total time:       {total_time:.3f}s")
    print()

    # Performance assessment
    if total_time < 1.0:
        status = "⚡ EXCELLENT"
        comment = "Extremely fast, no performance concern"
    elif total_time < 3.0:
        status = "✅ GOOD"
        comment = "Fast enough for real-time learning"
    elif total_time < 10.0:
        status = "⚠️  ACCEPTABLE"
        comment = "Acceptable, but consider optimization"
    else:
        status = "❌ SLOW"
        comment = "May need optimization or incremental approach"

    print(f"Performance: {status}")
    print(f"Assessment: {comment}")
    print()

    # Scalability projection
    print(f"{'='*60}")
    print(f"📈 SCALABILITY PROJECTION")
    print(f"{'='*60}\n")

    samples_per_sec = len(X_train) / total_time if total_time > 0 else 0

    projections = [
        (50, "Small dataset"),
        (100, "Medium dataset"),
        (500, "Large dataset"),
        (1000, "Very large dataset"),
    ]

    for n_samples, desc in projections:
        projected_time = n_samples / samples_per_sec if samples_per_sec > 0 else 0
        print(f"{n_samples:4d} samples ({desc:20s}): ~{projected_time:.2f}s")

    print()

    # Memory usage (approximate)
    import sys

    model_size = sys.getsizeof(crf) / 1024  # KB
    print(f"Model memory: ~{model_size:.1f} KB")
    print()

    return {
        "prep_time": prep_time,
        "train_time": train_time,
        "total_time": total_time,
        "samples": len(X_train),
        "status": status,
    }


if __name__ == "__main__":
    import sys

    template_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    # Run benchmark multiple times for average
    print("Running benchmark (3 iterations)...\n")

    results = []
    for i in range(3):
        print(f"Iteration {i+1}/3:")
        result = benchmark_training(template_id)
        results.append(result)
        time.sleep(0.5)

    # Average results
    avg_total = sum(r["total_time"] for r in results) / len(results)
    avg_train = sum(r["train_time"] for r in results) / len(results)

    print(f"\n{'='*60}")
    print(f"📊 AVERAGE RESULTS (3 iterations)")
    print(f"{'='*60}\n")
    print(f"Average total time: {avg_total:.3f}s")
    print(f"Average train time: {avg_train:.3f}s")
    print()
