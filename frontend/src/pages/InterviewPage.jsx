import { useState, useEffect, useRef } from "react";
import { submitAnswer } from "../services/api";

export default function InterviewPage({ sessionData, onComplete }) {
  const [currentQuestion, setCurrentQuestion] = useState(sessionData.first_question);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [questionNumber, setQuestionNumber] = useState(1);
  const [showFeedback, setShowFeedback] = useState(false);
  const textareaRef = useRef(null);

  const totalQuestions = sessionData.total_questions;
  const progress = (questionNumber / totalQuestions) * 100;

  useEffect(() => {
    if (textareaRef.current) textareaRef.current.focus();
  }, [currentQuestion]);

  const handleSubmit = async () => {
    if (!answer.trim()) return setError("Please write an answer before submitting.");
    if (answer.trim().length < 20) return setError("Please provide a more detailed answer.");

    setLoading(true);
    setError("");
    try {
      const result = await submitAnswer(
        sessionData.session_id,
        currentQuestion.id,
        answer.trim()
      );

      setFeedback(result);
      setShowFeedback(true);

      if (result.is_last_question) {
        setTimeout(() => onComplete(sessionData.session_id), 3000);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleNext = () => {
    if (!feedback?.next_question) return;
    setCurrentQuestion(feedback.next_question);
    setQuestionNumber(feedback.next_question.question_number);
    setAnswer("");
    setFeedback(null);
    setShowFeedback(false);
    setError("");
  };

  const difficultyColor = {
    easy: "#10b981",
    medium: "#f59e0b",
    hard: "#ef4444",
  };

  return (
    <div className="interview-page">
      <div className="interview-header">
        <div className="header-left">
          <span className="logo-small">PG-AGI</span>
          <span className="role-tag">{sessionData.role}</span>
        </div>
        <div className="header-right">
          {sessionData.candidate_name && (
            <span className="candidate-name">{sessionData.candidate_name}</span>
          )}
          <span className="q-counter">Question {questionNumber} of {totalQuestions}</span>
        </div>
      </div>

      <div className="progress-bar-bg">
        <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
      </div>

      <div className="interview-body">
        <div className="skills-panel">
          <h3>Your Profile</h3>
          <div className="skill-tags">
            {sessionData.extracted_skills?.slice(0, 12).map((s) => (
              <span key={s} className="skill-tag">{s}</span>
            ))}
          </div>
          {sessionData.domain_exposure?.length > 0 && (
            <>
              <h3 style={{ marginTop: "1.5rem" }}>Domains</h3>
              <div className="skill-tags">
                {sessionData.domain_exposure.map((d) => (
                  <span key={d} className="domain-tag">{d}</span>
                ))}
              </div>
            </>
          )}
        </div>

        <div className="question-panel">
          <div className="question-meta">
            <span className="topic-badge">{currentQuestion.topic}</span>
            <span
              className="difficulty-badge"
              style={{ background: difficultyColor[currentQuestion.difficulty] }}
            >
              {currentQuestion.difficulty}
            </span>
          </div>

          <div className="question-box">
            <span className="q-num">Q{questionNumber}.</span>
            <p className="question-text">{currentQuestion.question_text}</p>
          </div>

          {!showFeedback ? (
            <>
              <textarea
                ref={textareaRef}
                className="answer-textarea"
                placeholder="Type your answer here. Be as detailed as you can — explain your reasoning, not just the answer..."
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                rows={8}
              />
              <div className="answer-footer">
                <span className="char-count">{answer.length} characters</span>
                {error && <span className="error-inline">{error}</span>}
                <button
                  className="submit-btn"
                  onClick={handleSubmit}
                  disabled={loading || !answer.trim()}
                >
                  {loading ? "Evaluating..." : "Submit Answer →"}
                </button>
              </div>
            </>
          ) : (
            <div className="feedback-panel">
              <div className="feedback-header">
                <div className="score-circle" style={{
                  background: feedback.score >= 7 ? "#10b981" : feedback.score >= 4 ? "#f59e0b" : "#ef4444"
                }}>
                  {feedback.score}/10
                </div>
                <div className="feedback-text">
                  <h3>Feedback</h3>
                  <p>{feedback.feedback}</p>
                </div>
              </div>

              {feedback.is_last_question ? (
                <div className="last-q-note">
                  ✅ Interview complete! Generating your summary...
                </div>
              ) : (
                <button className="next-btn" onClick={handleNext}>
                  Next Question →
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}