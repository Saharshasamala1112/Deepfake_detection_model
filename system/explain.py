def explain(result: dict) -> str:
    """Produce a detailed human-readable explanation for a detection result.

    Provides comprehensive analysis based on multiple factors including
    CNN confidence, reconstruction error, and final combined score.
    """
    # Check if there's an error
    if result.get("error"):
        return f"Analysis failed: {result['error']}"

    # Get all relevant scores
    final_score = result.get("final_score", 0)
    cnn_score = result.get("cnn_score", 0)
    recon_error = result.get("reconstruction_error", 0)
    recon_error_norm = result.get("reconstruction_error_norm", 0)
    threshold = result.get("threshold", 0.5)

    prediction = result.get("prediction", "UNKNOWN")

    # Build detailed explanation
    explanations = []

    # Primary prediction statement
    if prediction == "FAKE":
        if final_score > 0.8:
            explanations.append("High confidence deepfake detected with strong evidence of manipulation.")
        elif final_score > 0.6:
            explanations.append("Moderate to high likelihood of deepfake content detected.")
        else:
            explanations.append("Potential deepfake content identified, though confidence is moderate.")
    elif prediction == "REAL":
        if final_score < 0.2:
            explanations.append("High confidence that this appears to be authentic content.")
        elif final_score < 0.4:
            explanations.append("Content appears authentic with good confidence.")
        else:
            explanations.append("Content likely authentic, though some minor anomalies detected.")
    else:
        explanations.append("Unable to determine authenticity with current analysis.")

    # CNN analysis details
    if cnn_score > 0.7:
        explanations.append(f"Neural network analysis shows strong indicators of manipulation (CNN score: {cnn_score:.3f}).")
    elif cnn_score > 0.5:
        explanations.append(f"Neural network detected some suspicious patterns (CNN score: {cnn_score:.3f}).")
    elif cnn_score < 0.3:
        explanations.append(f"Neural network analysis suggests authentic content (CNN score: {cnn_score:.3f}).")
    else:
        explanations.append(f"Neural network analysis is inconclusive (CNN score: {cnn_score:.3f}).")

    # Reconstruction error analysis
    if recon_error_norm > 0.6:
        explanations.append(f"Significant reconstruction anomalies detected (normalized error: {recon_error_norm:.3f}), indicating potential manipulation.")
    elif recon_error_norm > 0.3:
        explanations.append(f"Moderate reconstruction inconsistencies found (normalized error: {recon_error_norm:.3f}).")
    elif recon_error_norm < 0.2:
        explanations.append(f"Low reconstruction error suggests natural image characteristics (normalized error: {recon_error_norm:.3f}).")

    # Combined score analysis
    explanations.append(f"Final combined score: {final_score:.3f} (threshold: {threshold:.3f}).")

    # Technical details for advanced users
    if recon_error > 0:
        explanations.append(f"Raw reconstruction error: {recon_error:.6f}.")

    return " ".join(explanations)