const startBtn = document.getElementById("startBtn");

startBtn.addEventListener("click", () => {
    sessionStorage.removeItem("interviewId");
    localStorage.removeItem("interviewId");
    sessionStorage.removeItem("interviewResult");
    localStorage.removeItem("interviewResult");
    sessionStorage.removeItem("recordingURL");
    localStorage.removeItem("recordingURL");
    sessionStorage.removeItem("transcript");
    localStorage.removeItem("transcript");
    sessionStorage.removeItem("interviewStatus");
    localStorage.removeItem("interviewStatus");
    sessionStorage.removeItem("terminationType");
    localStorage.removeItem("terminationType");
    sessionStorage.removeItem("terminatedReason");
    localStorage.removeItem("terminatedReason");
    sessionStorage.removeItem("securityViolation");
    localStorage.removeItem("securityViolation");
    sessionStorage.removeItem("terminatedAt");
    localStorage.removeItem("terminatedAt");
    sessionStorage.removeItem("tabSwitchCount");
    localStorage.removeItem("tabSwitchCount");
    sessionStorage.removeItem("clientSessionId");
    localStorage.removeItem("clientSessionId");
    window.location.href = "interview.html";
});