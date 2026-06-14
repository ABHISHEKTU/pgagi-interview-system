import { useState } from "react";
import { startSession } from "../services/api";

const ROLES = [
  "AI/ML Engineer",
  "Backend Engineer",
  "Data Scientist",
  "Full Stack Engineer",
];

export default function UploadPage({ onSessionStart }) {
  const [resume, setResume] = useState(null);
  const [role, setRole] = useState("AI/ML Engineer");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);

  const handleFile = (file) => {
    if (!file) return;
    if (!file.name.endsWith(".pdf") && !file.name.endsWith(".txt")) {
      setError("Only PDF or TXT files accepted.");
      return;
    }
    setResume(file);
    setError("");
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const handleSubmit = async () => {
    if (!resume) return setError("Please upload your resume.");
    setLoading(true);
    setError("");
    try {
      const data = await startSession(resume, role, name);
      onSessionStart(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-page">
      <div className="upload-card">
        <div className="upload-header">
          <div className="logo-badge">PG-AGI</div>
          <h1>AI Interview System</h1>
          <p>Upload your resume and select a role to begin your technical interview.</p>
        </div>

        <div className="form-group">
          <label>Your Name (optional)</label>
          <input
            type="text"
            placeholder="e.g. Abhishek T U"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>Target Role</label>
          <div className="role-grid">
            {ROLES.map((r) => (
              <button
                key={r}
                className={`role-btn ${role === r ? "active" : ""}`}
                onClick={() => setRole(r)}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        <div className="form-group">
          <label>Resume</label>
          <div
            className={`drop-zone ${dragOver ? "drag-over" : ""} ${resume ? "has-file" : ""}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => document.getElementById("file-input").click()}
          >
            <input
              id="file-input"
              type="file"
              accept=".pdf,.txt"
              style={{ display: "none" }}
              onChange={(e) => handleFile(e.target.files[0])}
            />
            {resume ? (
              <div className="file-info">
                <span className="file-icon">📄</span>
                <span className="file-name">{resume.name}</span>
                <span className="file-size">{(resume.size / 1024).toFixed(1)} KB</span>
              </div>
            ) : (
              <div className="drop-hint">
                <span className="drop-icon">⬆</span>
                <span>Drop your PDF here or click to browse</span>
              </div>
            )}
          </div>
        </div>

        {error && <div className="error-msg">{error}</div>}

        <button
          className="start-btn"
          onClick={handleSubmit}
          disabled={loading || !resume}
        >
          {loading ? (
            <span className="loading-row">
              <span className="spinner" /> Analyzing Resume...
            </span>
          ) : (
            "Start Interview →"
          )}
        </button>

        {loading && (
          <p className="loading-note">
            Parsing your resume and generating your first question. This may take 15–30 seconds.
          </p>
        )}
      </div>
    </div>
  );
}