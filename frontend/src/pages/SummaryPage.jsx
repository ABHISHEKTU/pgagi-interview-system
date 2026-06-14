import { useState, useEffect } from "react";
import { getSessionSummary } from "../services/api";

export default function SummaryPage({ sessionId, onRestart }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchSummary() {
      try {
        const data = await getSessionSummary(sessionId);
        setSummary(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchSummary();
  }, [sessionId]);

  if (loading) return (
    <div className="summary-loading">
      <div className="spinner large" />
      <p>Generating your interview report...</p>
    </div>
  );

  if (error) return (
    <div className="summary-error">
      <p>{error}</p>
      <button onClick={onRestart}>Try Again</button>
    </div>
  );

  const scoreColor = (s) => s >= 7 ? "#10b981" : s >= 4 ? "#f59e0b" : "#ef4444";
  const avgScore = summary.average_score;

  return (
    <div className="summary-page">
      <div className="summary-container">
        <div className="summary-header">
          <div className="logo-badge">PG-AGI</div>
          <h1>Interview Complete</h1>
          {summary.candidate_name && <p className="cand-name">{summary.candidate_name}</p>}
          <p className="role-label">{summary.role}</p>
        </div>

        <div className="score-card">
          <div className="big-score" style={{ color: scoreColor(avgScore) }}>
            {avgScore?.toFixed(1) ?? "—"}<span>/10</span>
          </div>
          <div className="score-stats">
            <div className="stat">
              <span className="stat-val">{summary.total_questions}</span>
              <span className="stat-label">Questions</span>
            </div>
            <div className="stat">
              <span className="stat-val">{summary.skills_evaluated?.length}</span>
              <span className="stat-label">Skills Covered</span>
            </div>
          </div>
        </div>

        <div className="overall-feedback">
          <h2>Overall Assessment</h2>
          <p>{summary.overall_feedback}</p>
        </div>

        <div className="qa-breakdown">
          <h2>Question Breakdown</h2>
          {summary.qa_pairs.map((qa, i) => (
            <div key={i} className="qa-card">
              <div className="qa-header">
                <span className="qa-num">Q{qa.question_number}</span>
                <span className="qa-topic">{qa.topic}</span>
                <span className="qa-diff">{qa.difficulty}</span>
                <span className="qa-score" style={{ color: scoreColor(qa.score) }}>
                  {qa.score ?? "—"}/10
                </span>
              </div>
              <p className="qa-question"><strong>Q:</strong> {qa.question_text}</p>
              <p className="qa-answer"><strong>A:</strong> {qa.answer_text}</p>
              {qa.ai_feedback && (
                <div className="qa-feedback">
                  <strong>Feedback:</strong> {qa.ai_feedback}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="skills-section">
          <h2>Skills Evaluated</h2>
          <div className="skill-tags">
            {summary.skills_evaluated?.map((s) => (
              <span key={s} className="skill-tag">{s}</span>
            ))}
          </div>
        </div>

        <button className="restart-btn" onClick={onRestart}>
          Start New Interview
        </button>
      </div>
    </div>
  );
}