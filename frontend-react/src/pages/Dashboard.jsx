import { useState } from "react";
import UploadBox from "../components/UploadBox";
import ResultCard from "../components/ResultCard";

export default function Dashboard() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fastMode, setFastMode] = useState(false);

  const analyzeFile = async () => {
    if (!file) {
      setError("Please select a file first");
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const url = `http://127.0.0.1:8000/analyze${fastMode ? '?fast=true' : ''}`;
      const response = await fetch(url, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(`Analysis failed: ${err.message}`);
      console.error("Analysis error:", err);
    } finally {
      setLoading(false);
    }
  };

  const resetAnalysis = () => {
    setFile(null);
    setResult(null);
    setError(null);
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>DeepShield-X</h1>
        <p>Advanced AI-Powered Deepfake Detection</p>
      </header>

      <main className="dashboard-main">
        {!result ? (
          <div className="upload-section">
            <div className="upload-container">
              <h2>Upload Media for Analysis</h2>
              <p>Supported formats: Images (JPG, PNG), Videos (MP4, AVI), Audio (WAV, MP3), Documents (TXT, PDF, DOC, DOCX)</p>

              <UploadBox setFile={setFile} />

              {file && (
                <div className="file-info">
                  <p><strong>Selected file:</strong> {file.name}</p>
                  <p><strong>Size:</strong> {(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              )}

              {error && <div className="error-message">{error}</div>}

              <div className="action-buttons">
                <div className="analysis-options">
                  <label className="fast-mode-toggle">
                    <input
                      type="checkbox"
                      checked={fastMode}
                      onChange={(e) => setFastMode(e.target.checked)}
                    />
                    <span className="toggle-label">Fast Mode (Skip Grad-CAM)</span>
                  </label>
                  <p className="option-description">
                    {fastMode ? "Faster analysis without visual explanations" : "Full analysis with Grad-CAM visualizations"}
                  </p>
                </div>

                <button
                  onClick={analyzeFile}
                  disabled={!file || loading}
                  className="analyze-btn"
                >
                  {loading ? "Analyzing..." : "Analyze File"}
                </button>

                {file && (
                  <button onClick={resetAnalysis} className="reset-btn">
                    Clear
                  </button>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="results-section">
            <ResultCard data={result} />
            <button onClick={resetAnalysis} className="new-analysis-btn">
              Analyze Another File
            </button>
          </div>
        )}
      </main>

      <footer className="dashboard-footer">
        <p>&copy; 2026 DeepShield-X. Advanced deepfake detection powered by AI.</p>
      </footer>
    </div>
  );
}