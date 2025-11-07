"""
Training Utilities
Proper ML workflow with train/test split and cross-validation
"""

from typing import List, Tuple, Dict, Any
import random
from sklearn.model_selection import train_test_split as sklearn_split
import logging

logger = logging.getLogger(__name__)


def split_training_data(
    X: List[List[Dict]], 
    y: List[List[str]], 
    test_size: float = 0.2,
    random_state: int = 42,
    stratify_by_template: bool = False
) -> Tuple[List, List, List, List]:
    """
    Split training data into train and test sets
    
    Args:
        X: Feature sequences
        y: Label sequences
        test_size: Proportion of test set (default: 0.2 = 20%)
        random_state: Random seed for reproducibility
        stratify_by_template: Whether to stratify by template (if multiple templates)
        
    Returns:
        X_train, X_test, y_train, y_test
    """
    if len(X) != len(y):
        raise ValueError(f"X and y must have same length. Got {len(X)} and {len(y)}")
    
    if len(X) < 10:
        logger.warning(f"⚠️  Very small dataset ({len(X)} samples). Consider collecting more data.")
        logger.warning(f"    Minimum recommended: 50 samples for reliable evaluation")
    
    # Use sklearn's train_test_split
    X_train, X_test, y_train, y_test = sklearn_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        shuffle=True
    )
    
    logger.info(f"📊 Data split:")
    logger.info(f"   Total samples: {len(X)}")
    logger.info(f"   Training: {len(X_train)} ({len(X_train)/len(X)*100:.1f}%)")
    logger.info(f"   Testing: {len(X_test)} ({len(X_test)/len(X)*100:.1f}%)")
    
    return X_train, X_test, y_train, y_test


def k_fold_split(
    X: List[List[Dict]], 
    y: List[List[str]], 
    n_folds: int = 5,
    random_state: int = 42
) -> List[Tuple[List, List, List, List]]:
    """
    Create K-fold cross-validation splits
    
    Args:
        X: Feature sequences
        y: Label sequences
        n_folds: Number of folds (default: 5)
        random_state: Random seed
        
    Returns:
        List of (X_train, X_test, y_train, y_test) tuples for each fold
    """
    if len(X) < n_folds:
        raise ValueError(f"Not enough samples ({len(X)}) for {n_folds}-fold CV")
    
    # Shuffle data
    random.seed(random_state)
    indices = list(range(len(X)))
    random.shuffle(indices)
    
    # Create folds
    fold_size = len(X) // n_folds
    folds = []
    
    for i in range(n_folds):
        # Test indices for this fold
        test_start = i * fold_size
        test_end = test_start + fold_size if i < n_folds - 1 else len(X)
        test_indices = indices[test_start:test_end]
        
        # Train indices (everything else)
        train_indices = [idx for idx in indices if idx not in test_indices]
        
        # Split data
        X_train = [X[idx] for idx in train_indices]
        X_test = [X[idx] for idx in test_indices]
        y_train = [y[idx] for idx in train_indices]
        y_test = [y[idx] for idx in test_indices]
        
        folds.append((X_train, X_test, y_train, y_test))
    
    logger.info(f"📊 Created {n_folds}-fold cross-validation:")
    for i, (X_tr, X_te, _, _) in enumerate(folds, 1):
        logger.info(f"   Fold {i}: train={len(X_tr)}, test={len(X_te)}")
    
    return folds


def detect_data_leakage(
    X_train: List[List[Dict]], 
    X_test: List[List[Dict]],
    similarity_threshold: float = 0.95,
    sample_size: int = 10
) -> Dict[str, Any]:
    """
    Detect potential data leakage between train and test sets
    
    Uses sampling for efficiency with large datasets.
    
    Args:
        X_train: Training features
        X_test: Test features
        similarity_threshold: Threshold for considering samples as duplicates
        sample_size: Number of samples to check (for efficiency)
        
    Returns:
        Leakage detection results
    """
    import random
    from difflib import SequenceMatcher
    
    # ✅ OPTIMIZATION: Sample for large datasets
    if len(X_test) > sample_size:
        logger.info(f"   Sampling {sample_size} test samples for efficiency...")
        test_indices = random.sample(range(len(X_test)), sample_size)
        test_samples = [X_test[i] for i in test_indices]
    else:
        test_samples = X_test
        test_indices = list(range(len(X_test)))
    
    leakage_detected = []
    
    # ✅ OPTIMIZATION: Use hash-based quick check first
    train_hashes = [hash(str(sample)) for sample in X_train]
    
    for i, test_sample in enumerate(test_samples):
        test_hash = hash(str(test_sample))
        
        # Quick check: exact hash match (O(1))
        if test_hash in train_hashes:
            leakage_detected.append({
                'test_idx': test_indices[i],
                'train_idx': train_hashes.index(test_hash),
                'similarity': 1.0,
                'type': 'exact_duplicate'
            })
            continue
        
        # ✅ OPTIMIZATION: Only check similarity for non-exact matches
        # And only check first 20 training samples (for speed)
        test_str = str(test_sample)
        max_train_check = min(20, len(X_train))
        
        for j in range(max_train_check):
            train_str = str(X_train[j])
            
            # Quick length check first
            if abs(len(test_str) - len(train_str)) / max(len(test_str), len(train_str)) > 0.1:
                continue  # Too different in length
            
            # Calculate similarity
            similarity = SequenceMatcher(None, test_str, train_str).ratio()
            
            if similarity >= similarity_threshold:
                leakage_detected.append({
                    'test_idx': test_indices[i],
                    'train_idx': j,
                    'similarity': similarity,
                    'type': 'high_similarity'
                })
                break  # Found one, move to next test sample
    
    if leakage_detected:
        logger.warning(f"⚠️  Potential data leakage detected!")
        logger.warning(f"    Found {len(leakage_detected)} highly similar samples")
        logger.warning(f"    (checked {len(test_samples)} test samples)")
    else:
        logger.info(f"   ✅ No obvious data leakage detected")
        logger.info(f"      (checked {len(test_samples)} test samples)")
    
    return {
        'leakage_detected': len(leakage_detected) > 0,
        'num_leaks': len(leakage_detected),
        'samples_checked': len(test_samples),
        'details': leakage_detected[:5]  # Show first 5
    }


def validate_training_data_diversity(
    X: List[List[Dict]], 
    y: List[List[str]]
) -> Dict[str, Any]:
    """
    Validate diversity of training data
    
    Args:
        X: Feature sequences
        y: Label sequences
        
    Returns:
        Diversity metrics
    """
    # Count unique label sequences
    unique_sequences = set()
    label_distribution = {}
    
    for labels in y:
        # Convert to tuple for hashing
        seq = tuple(labels)
        unique_sequences.add(seq)
        
        # Count individual labels
        for label in labels:
            if label != 'O':
                label_distribution[label] = label_distribution.get(label, 0) + 1
    
    # Calculate diversity score
    diversity_score = len(unique_sequences) / len(y) if y else 0
    
    logger.info(f"📊 Training data diversity:")
    logger.info(f"   Total samples: {len(y)}")
    logger.info(f"   Unique sequences: {len(unique_sequences)}")
    logger.info(f"   Diversity score: {diversity_score:.2%}")
    logger.info(f"   Label distribution: {label_distribution}")
    
    # Warning if diversity is too low
    if diversity_score < 0.5:
        logger.warning(f"⚠️  Low diversity detected ({diversity_score:.2%})")
        logger.warning(f"    Your training data may be too similar!")
        logger.warning(f"    Consider adding more varied examples.")
    
    return {
        'total_samples': len(y),
        'unique_sequences': len(unique_sequences),
        'diversity_score': diversity_score,
        'label_distribution': label_distribution,
        'is_diverse': diversity_score >= 0.5
    }


def get_training_recommendations(
    num_samples: int,
    diversity_score: float,
    has_leakage: bool
) -> List[str]:
    """
    Get recommendations for improving training
    
    Args:
        num_samples: Number of training samples
        diversity_score: Diversity score (0-1)
        has_leakage: Whether data leakage detected
        
    Returns:
        List of recommendations
    """
    recommendations = []
    
    # Sample size recommendations
    if num_samples < 20:
        recommendations.append("❌ CRITICAL: Very small dataset (<20). Collect at least 50 samples.")
    elif num_samples < 50:
        recommendations.append("⚠️  Small dataset (<50). Consider collecting more data for better generalization.")
    elif num_samples < 100:
        recommendations.append("✅ Adequate dataset size, but more data would improve robustness.")
    else:
        recommendations.append("✅ Good dataset size.")
    
    # Diversity recommendations
    if diversity_score < 0.3:
        recommendations.append("❌ CRITICAL: Very low diversity. Data is too similar - high overfitting risk!")
    elif diversity_score < 0.5:
        recommendations.append("⚠️  Low diversity. Add more varied examples to improve generalization.")
    elif diversity_score < 0.7:
        recommendations.append("✅ Moderate diversity. System should generalize reasonably well.")
    else:
        recommendations.append("✅ Good diversity. Training data is varied.")
    
    # Leakage recommendations
    if has_leakage:
        recommendations.append("❌ CRITICAL: Data leakage detected! Metrics are inflated. Re-split your data.")
    else:
        recommendations.append("✅ No data leakage detected.")
    
    # General recommendations
    if num_samples >= 50 and diversity_score >= 0.5 and not has_leakage:
        recommendations.append("✅ Training setup looks good! Proceed with confidence.")
    else:
        recommendations.append("⚠️  Training setup needs improvement. Address issues above.")
    
    return recommendations
