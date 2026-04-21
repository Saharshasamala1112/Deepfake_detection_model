import numpy as np

def compute_threshold(scores):
    # Adaptive threshold based on distribution
    return np.mean(scores)
