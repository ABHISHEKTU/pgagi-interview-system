const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function startSession(resumeFile, role, candidateName = "") {
  const formData = new FormData();
  formData.append("resume", resumeFile);
  formData.append("role", role);
  if (candidateName) formData.append("candidate_name", candidateName);

  const res = await fetch(`${BASE_URL}/api/sessions/start`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to start session");
  }
  return res.json();
}

export async function submitAnswer(sessionId, questionId, answerText) {
  const res = await fetch(`${BASE_URL}/api/interview/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      question_id: questionId,
      answer_text: answerText,
    }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to submit answer");
  }
  return res.json();
}

export async function getSessionSummary(sessionId) {
  const res = await fetch(`${BASE_URL}/api/sessions/${sessionId}/summary`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to get summary");
  }
  return res.json();
}

export async function getSession(sessionId) {
  const res = await fetch(`${BASE_URL}/api/sessions/${sessionId}`);
  if (!res.ok) throw new Error("Session not found");
  return res.json();
}

export async function completeSession(sessionId) {
  const res = await fetch(`${BASE_URL}/api/interview/complete/${sessionId}`, {
    method: "POST",
  });
  return res.json();
}

export async function getIngestStatus() {
  const res = await fetch(`${BASE_URL}/api/ingest/status`);
  return res.json();
}