import { useState } from "react";

export default function Login({ setAuth }) {
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setCredentials(prev => ({
      ...prev,
      [name]: value
    }));
    setError(""); // Clear error when user starts typing
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    // Simple demo authentication - in production, this should be server-side
    setTimeout(() => {
      if (credentials.username === "admin" && credentials.password === "1234") {
        setAuth(true);
      } else {
        setError("Invalid username or password");
      }
      setLoading(false);
    }, 1000); // Simulate network delay
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <div className="logo-section">
            <div className="logo">🛡️</div>
            <h1>DeepShield-X</h1>
          </div>
          <p className="tagline">Advanced AI-Powered Deepfake Detection Platform</p>
        </div>

        <form onSubmit={handleLogin} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="username"
              value={credentials.username}
              onChange={handleInputChange}
              placeholder="Enter your username"
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={credentials.password}
              onChange={handleInputChange}
              placeholder="Enter your password"
              required
              disabled={loading}
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button
            type="submit"
            className="login-btn"
            disabled={loading || !credentials.username || !credentials.password}
          >
            {loading ? "Signing In..." : "Sign In"}
          </button>
        </form>

        <div className="login-footer">
          <p>Demo credentials: admin / 1234</p>
          <p className="security-note">
            🔒 Secure authentication system powered by enterprise-grade security
          </p>
        </div>
      </div>

      <div className="features-preview">
        <div className="feature">
          <div className="feature-icon">🎯</div>
          <h3>High Accuracy</h3>
          <p>State-of-the-art AI models for precise deepfake detection</p>
        </div>
        <div className="feature">
          <div className="feature-icon">⚡</div>
          <h3>Real-time Analysis</h3>
          <p>Fast processing with instant results and detailed explanations</p>
        </div>
        <div className="feature">
          <div className="feature-icon">🔍</div>
          <h3>Visual Insights</h3>
          <p>Grad-CAM visualizations showing exactly where manipulations were detected</p>
        </div>
      </div>
    </div>
  );
}