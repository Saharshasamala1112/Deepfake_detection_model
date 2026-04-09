import { useState } from "react";

export default function ResultCard({ data }) {
  const [showDetails, setShowDetails] = useState(false);

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return "#dc3545";
    if (confidence >= 0.6) return "#fd7e14";
    if (confidence >= 0.4) return "#ffc107";
    return "#28a745";
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 0.8) return "High Confidence Fake";
    if (confidence >= 0.6) return "Moderate Fake Detection";
    if (confidence >= 0.4) return "Uncertain";
    return "Likely Authentic";
  };

  const formatConfidence = (confidence) => {
    return (confidence * 100).toFixed(1) + "%";
  };

  // Error handling
  if (data.error) {
    return (
      <div className="result-card error-card">
        <div className="result-header">
          <h2>Analysis Error</h2>
          <div className="prediction-badge error-badge">ERROR</div>
        </div>
        <div className="error-message">
          <p><strong>Error:</strong> {data.error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="result-card">

      {/* HEADER */}
      <div className="result-header">
        <h2>Analysis Results</h2>
        <div className={`prediction-badge ${data.prediction === 'FAKE' ? 'fake-badge' : 'real-badge'}`}>
          {data.prediction}
        </div>
      </div>

      {/* SUMMARY */}
      <div className="result-summary">
        <div className="metric">
          <span className="metric-label">Prediction:</span>
          <span className="metric-value">{data.prediction}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Confidence Score:</span>
          <span className="metric-value">{formatConfidence(data.confidence)}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Assessment:</span>
          <span className="metric-value">{getConfidenceLabel(data.confidence)}</span>
        </div>
      </div>

      {/* EXPLANATION */}
      <div className="explanation-section">
        <h3>Analysis Explanation</h3>
        <p className="explanation-text">{data.explanation}</p>
      </div>

      {/* ================= VIDEO SECTION ================= */}
      {data.type === 'video' && (
        <>
          {/* Video Info */}
          <div className="media-info-section">
            <h3>Video Information</h3>
            <div className="info-grid">
              {data.duration && (
                <div className="info-item">
                  <span className="info-label">Duration:</span>
                  <span className="info-value">{data.duration.toFixed(1)}s</span>
                </div>
              )}
              {data.frames_processed && (
                <div className="info-item">
                  <span className="info-label">Frames Analyzed:</span>
                  <span className="info-value">{data.frames_processed}</span>
                </div>
              )}
              {data.fps && (
                <div className="info-item">
                  <span className="info-label">FPS:</span>
                  <span className="info-value">{data.fps.toFixed(1)}</span>
                </div>
              )}
            </div>
          </div>

          {/* Extracted Frames */}
          {data.extracted_frames_dir && (
            <div className="frames-section">
              <h3>Extracted Frames</h3>
              <p className="frames-description">
                Frames extracted for analysis
              </p>
              <p>{data.extracted_frames_dir}</p>
            </div>
          )}

          {/* Fake Frames */}
          {Array.isArray(data.fake_frames) && data.fake_frames.length > 0 && (
            <div className="fake-frames-section">
              <h3>Fake Frame Detection</h3>

              <div className="fake-frames-list">
                {data.fake_frames.slice(0, 10).map((frame, index) => (
                  <div key={index} className="fake-frame-item">
                    <span>{frame.timestamp.toFixed(1)}s</span>
                    <span>{(frame.score * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>

              {data.fake_frames.length > 10 && (
                <p>+ {data.fake_frames.length - 10} more frames</p>
              )}
            </div>
          )}
        </>
      )}

      {/* ================= AUDIO SECTION ================= */}
      {data.type === 'audio' && (
        <div className="media-info-section">
          <h3>Audio Information</h3>
          <div className="info-grid">
            {data.duration && (
              <div className="info-item">
                <span>Duration:</span>
                <span>{data.duration.toFixed(1)}s</span>
              </div>
            )}
            {data.sample_rate && (
              <div className="info-item">
                <span>Sample Rate:</span>
                <span>{data.sample_rate} Hz</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ================= DOCUMENT SECTION ================= */}
      {data.type === 'document' && (
        <div className="media-info-section">
          <h3>Document Info</h3>
          <div className="info-grid">
            {data.word_count && (
              <div className="info-item">
                <span>Word Count:</span>
                <span>{data.word_count}</span>
              </div>
            )}
            {data.method && (
              <div className="info-item">
                <span>Method:</span>
                <span>{data.method}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ================= GRADCAM ================= */}
      {data.gradcam && (
        <div className="visualization-section">
          <h3>Grad-CAM</h3>
          <img
            src={`http://127.0.0.1:8000/${data.gradcam}`}
            alt="GradCAM"
            className="gradcam-image"
          />
        </div>
      )}

      {/* ================= RECONSTRUCTION ================= */}
      {data.reconstructed && (
        <div className="reconstruction-section">
          <h3>Reconstruction</h3>

          <img
            src={`http://127.0.0.1:8000/${data.reconstructed}`}
            alt="Reconstructed"
            className="reconstructed-image"
          />

          <a
            href={`http://127.0.0.1:8000/${data.reconstructed}`}
            download
            className="download-btn"
          >
            Download
          </a>
        </div>
      )}

      {/* ================= DETAILS ================= */}
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="details-btn"
      >
        {showDetails ? "Hide" : "Show"} Details
      </button>

      {showDetails && (
        <div className="technical-details">
          {data.cnn_score !== undefined && <p>CNN: {data.cnn_score}</p>}
          {data.reconstruction_error !== undefined && <p>Recon Error: {data.reconstruction_error}</p>}
          {data.final_score !== undefined && <p>Final Score: {data.final_score}</p>}
          {data.threshold !== undefined && <p>Threshold: {data.threshold}</p>}
        </div>
      )}

    </div>
  );
}