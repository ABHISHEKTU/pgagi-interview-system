import { useState } from "react";
import UploadPage from "./pages/UploadPage";
import InterviewPage from "./pages/InterviewPage";
import SummaryPage from "./pages/SummaryPage";
import "./App.css";

export default function App() {
  const [stage, setStage] = useState("upload");
  const [sessionData, setSessionData] = useState(null);
  const [completedSessionId, setCompletedSessionId] = useState(null);

  const handleSessionStart = (data) => {
    setSessionData(data);
    setStage("interview");
  };

  const handleInterviewComplete = (sessionId) => {
    setCompletedSessionId(sessionId);
    setStage("summary");
  };

  const handleRestart = () => {
    setSessionData(null);
    setCompletedSessionId(null);
    setStage("upload");
  };

  return (
    <div className="app">
      {stage === "upload" && (
        <UploadPage onSessionStart={handleSessionStart} />
      )}
      {stage === "interview" && sessionData && (
        <InterviewPage
          sessionData={sessionData}
          onComplete={handleInterviewComplete}
        />
      )}
      {stage === "summary" && completedSessionId && (
        <SummaryPage
          sessionId={completedSessionId}
          onRestart={handleRestart}
        />
      )}
    </div>
  );
}