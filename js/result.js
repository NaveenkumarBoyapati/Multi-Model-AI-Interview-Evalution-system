// =========================================
// AI INTERVIEW - RESULT PAGE CONTROLLER
// =========================================

// =========================================
// GET DOM ELEMENTS
// =========================================

const interviewIdElement = document.getElementById("interviewId");
const roleName = document.getElementById("roleName");
const totalQuestions = document.getElementById("totalQuestions");
const questionsAttemptedElement = document.getElementById("questionsAttempted") || totalQuestions;
const questionsAnsweredElement = document.getElementById("questionsAnswered");
const questionsUnansweredElement = document.getElementById("questionsUnanswered");
const interviewDateElement = document.getElementById("interviewDate");
const interviewTimeElement = document.getElementById("interviewTime");
const recordingStatus = document.getElementById("recordingStatus");
const recordingMessage = document.getElementById("recordingMessage");

const resultStatusCard = document.getElementById("resultStatusCard");
const resultStatusIcon = document.getElementById("resultStatusIcon");
const resultStatusHeading = document.getElementById("resultStatusHeading");
const resultStatusSubheading = document.getElementById("resultStatusSubheading");
const resultStatusBadge = document.getElementById("resultStatusBadge");
const terminationBanner = document.getElementById("terminationBanner");

const interviewStatusElement = document.getElementById("interviewStatus");
const terminationReasonElement = document.getElementById("terminationReason");
const securityViolationElement = document.getElementById("securityViolation");
const tabSwitchCountElement = document.getElementById("tabSwitchCount");

const bannerTermReason = document.getElementById("bannerTermReason");
const bannerSecViolation = document.getElementById("bannerSecViolation");
const bannerTabSwitchCount = document.getElementById("bannerTabSwitchCount");

const transcriptSection = document.getElementById("transcriptSection");
const transcriptText = document.getElementById("transcriptText");
const transcriptWordCount = document.getElementById("transcriptWordCount");

const overallScore = document.getElementById("overallScore");
const performanceText = document.getElementById("performanceText");
const scoreDescription = document.getElementById("scoreDescription") || document.querySelector(".score-description");

const technicalScore = document.getElementById("technicalScore");
const relevanceScore = document.getElementById("relevanceScore");
const conceptCoverageScore = document.getElementById("conceptCoverageScore");
const completenessScore = document.getElementById("completenessScore");
const communicationScore = document.getElementById("communicationScore");
const confidenceScore = document.getElementById("confidenceScore");
const problemScore = document.getElementById("problemScore");

const technicalBar = document.getElementById("technicalBar");
const relevanceBar = document.getElementById("relevanceBar");
const conceptCoverageBar = document.getElementById("conceptCoverageBar");
const completenessBar = document.getElementById("completenessBar");
const communicationBar = document.getElementById("communicationBar");
const confidenceBar = document.getElementById("confidenceBar");
const problemBar = document.getElementById("problemBar");

const questionEvaluationContainer = document.getElementById("questionEvaluationContainer");

const communicationFeedbackText = document.getElementById("communicationFeedbackText");
const technicalFeedbackText = document.getElementById("technicalFeedbackText");
const confidenceFeedbackText = document.getElementById("confidenceFeedbackText");
const practiceFeedbackText = document.getElementById("practiceFeedbackText");


// =========================================
// HELPER: ESCAPE HTML
// =========================================

function escapeHTML(str) {
    const div = document.createElement("div");
    div.textContent = String(str ?? "");
    return div.innerHTML;
}


// =========================================
// SHOW RESULT NOT FOUND STATE
// =========================================

function showResultNotFound() {
    console.warn("[Result] Interview result not found in sessionStorage or localStorage.");

    if (interviewIdElement) interviewIdElement.textContent = "--";
    if (roleName) roleName.textContent = localStorage.getItem("selectedRole") || "--";
    if (totalQuestions) totalQuestions.textContent = "--";
    if (questionsAttemptedElement) questionsAttemptedElement.textContent = "--";
    if (questionsAnsweredElement) questionsAnsweredElement.textContent = "--";
    if (questionsUnansweredElement) questionsUnansweredElement.textContent = "--";
    if (interviewDateElement) interviewDateElement.textContent = new Date().toLocaleDateString();
    if (interviewStatusElement) interviewStatusElement.textContent = "--";
    if (terminationReasonElement) terminationReasonElement.textContent = "--";
    if (securityViolationElement) securityViolationElement.textContent = "--";
    if (tabSwitchCountElement) tabSwitchCountElement.textContent = "--";
    if (terminationBanner) terminationBanner.style.display = "none";
    if (recordingStatus) recordingStatus.textContent = "Unavailable";
    if (transcriptText) transcriptText.innerHTML = "<em>No interview transcript available in current session.</em>";
    if (transcriptWordCount) transcriptWordCount.textContent = "0 words";

    if (overallScore) overallScore.textContent = "--";
    if (technicalScore) technicalScore.textContent = "--";
    if (relevanceScore) relevanceScore.textContent = "--";
    if (conceptCoverageScore) conceptCoverageScore.textContent = "--";
    if (completenessScore) completenessScore.textContent = "--";
    if (communicationScore) communicationScore.textContent = "--";
    if (confidenceScore) confidenceScore.textContent = "--";
    if (problemScore) problemScore.textContent = "--";

    if (performanceText) performanceText.textContent = "Result Not Found";

    if (scoreDescription) {
        scoreDescription.textContent = "No evaluation data found in session. Please complete an interview to view AI evaluation.";
    }

    if (questionEvaluationContainer) {
        questionEvaluationContainer.innerHTML = `
            <div class="evaluation-loading" style="background:#fff; border:1px solid #fed7aa; border-radius:14px; padding:32px 20px; text-align:center;">
                <i class="fa-solid fa-triangle-exclamation" style="font-size:32px; color:#f97316; margin-bottom:12px;"></i>
                <h3 style="font-size:16px; font-weight:600; color:#9a3412; margin-bottom:6px;">Interview Result Not Found</h3>
                <p style="font-size:13px; color:#64748b; max-width:440px; margin:0 auto 16px;">
                    No interview evaluation data was found in your browser session. Please start and finish an interview recording to view your detailed AI evaluation.
                </p>
                <button onclick="window.location.href='role.html'" style="background:#2563eb; color:white; border:none; padding:9px 20px; border-radius:8px; font-size:13px; font-weight:500; cursor:pointer;">
                    <i class="fa-solid fa-play" style="margin-right:6px;"></i> Start Interview
                </button>
            </div>
        `;
    }
}


// =========================================
// RENDER QUESTION-WISE EVALUATION CARDS
// =========================================

function renderQuestionWiseEvaluation(questions) {
    if (!questionEvaluationContainer) return;

    if (!questions || !Array.isArray(questions) || questions.length === 0) {
        questionEvaluationContainer.innerHTML = `
            <div class="evaluation-loading" style="background:#fff; border:1px solid #e2e8f0; border-radius:14px; padding:28px 20px; text-align:center;">
                <i class="fa-solid fa-circle-info" style="font-size:28px; color:#64748b; margin-bottom:10px;"></i>
                <p style="font-size:14px; color:#475569; font-weight:500;">No question-wise evaluation data is available.</p>
                <span style="font-size:12px; color:#94a3b8;">Question analysis will appear once interview responses are processed.</span>
            </div>
        `;
        return;
    }

    questionEvaluationContainer.innerHTML = "";

    questions.forEach((item, index) => {
        const qNum = item.question_number || (index + 1);
        const questionText = item.question || `Question ${qNum}`;
        const rawAnswer = item.candidate_answer;
        const candidateAnswer = (rawAnswer && typeof rawAnswer === "string")
            ? rawAnswer.trim()
            : (rawAnswer ? String(rawAnswer).trim() : "");

        // A question is answered if candidate_answer contains non-empty text after trimming whitespace and is_answered is not false
        const isAnswered = candidateAnswer.length > 0 && item.is_answered !== false;
        const isUnanswered = !isAnswered;

        let expectedConcepts = Array.isArray(item.expected_concepts) ? item.expected_concepts : [];
        const rawMatched = isUnanswered ? [] : (Array.isArray(item.matched_concepts) ? item.matched_concepts : []);
        const rawMissing = isUnanswered ? [] : (Array.isArray(item.missing_concepts) ? item.missing_concepts : []);

        // Reconstruct consistent expected concepts if missing on item but present in matched or missing
        if (expectedConcepts.length === 0 && (rawMatched.length > 0 || rawMissing.length > 0)) {
            expectedConcepts = Array.from(new Set([...rawMatched, ...rawMissing]));
        }

        const matchedConcepts = isUnanswered ? [] : rawMatched;

        // Scores: unanswered questions display scores as 0; answered questions preserve existing evaluation scores
        const techScoreText = isUnanswered
            ? "0%"
            : ((item.technical_score !== undefined && item.technical_score !== null)
                ? `${Math.round(Number(item.technical_score))}%`
                : `${item.technical_score || 0}%`);

        const relScoreText = isUnanswered
            ? "0%"
            : ((item.relevance_score !== undefined && item.relevance_score !== null)
                ? `${Math.round(Number(item.relevance_score))}%`
                : `${item.relevance_score || 0}%`);

        // Concept score determination:
        // - Unanswered question: strictly 0%
        // - Answered question with valid concept score: display rounded percentage
        // - Answered question with expected concepts: compute percentage from matched / expected
        // - Answered question where expected concepts are not defined: display "Not Available" (prevents misleading 0%)
        let conceptScoreText = "0%";
        const rawConceptScore = (item.concept_score !== undefined && item.concept_score !== null)
            ? item.concept_score
            : item.concept_coverage_score;

        if (isUnanswered) {
            conceptScoreText = "0%";
        } else if (rawConceptScore !== undefined && rawConceptScore !== null && rawConceptScore !== "N/A" && rawConceptScore !== "Not Available") {
            conceptScoreText = `${Math.round(Number(rawConceptScore))}%`;
        } else if (expectedConcepts.length > 0) {
            conceptScoreText = `${Math.round((matchedConcepts.length / expectedConcepts.length) * 100)}%`;
        } else {
            conceptScoreText = "Not Available";
        }

        const compScoreText = isUnanswered
            ? "0%"
            : ((item.completeness_score !== undefined && item.completeness_score !== null)
                ? `${Math.round(Number(item.completeness_score))}%`
                : `${item.completeness_score || 0}%`);

        const commScoreText = isUnanswered
            ? "0%"
            : ((item.communication_score !== undefined && item.communication_score !== null)
                ? `${Math.round(Number(item.communication_score))}%`
                : `${item.communication_score || 0}%`);

        const confScoreText = isUnanswered
            ? "0%"
            : ((item.confidence_score !== undefined && item.confidence_score !== null)
                ? `${Math.round(Number(item.confidence_score))}%`
                : `${item.confidence_score || 0}%`);

        let probScoreText = "0%";
        if (isUnanswered) {
            probScoreText = "0%";
        } else if (item.problem_solving_score === null || item.problem_solving_score === "N/A" || item.problem_solving_score === "Not Available") {
            probScoreText = "Not Available";
        } else if (item.problem_solving_score !== undefined && item.problem_solving_score !== null) {
            probScoreText = `${Math.round(Number(item.problem_solving_score))}%`;
        } else {
            probScoreText = "0%";
        }

        const qOverallVal = isUnanswered
            ? 0
            : ((item.overall_score !== undefined && item.overall_score !== null)
                ? Math.round(Number(item.overall_score))
                : (item.overall_score || 0));

        const qOverallText = `${qOverallVal}%`;

        // Missing concepts
        const missingConcepts = isUnanswered
            ? expectedConcepts
            : (rawMissing.length > 0
                ? rawMissing
                : expectedConcepts.filter(c => !matchedConcepts.includes(c)));

        // Strengths & Improvements with safe fallback
        const strengthsList = isUnanswered
            ? ["No spoken or written answer was provided to evaluate candidate strengths for this question."]
            : ((Array.isArray(item.strengths) && item.strengths.length > 0)
                ? item.strengths
                : (item.strengths || ["Answer demonstrated effort and domain awareness."]));

        const improvementsList = isUnanswered
            ? ["Question was not answered. Attempt every question to demonstrate your technical depth, problem-solving skills, and communication clarity."]
            : ((Array.isArray(item.improvements) && item.improvements.length > 0)
                ? item.improvements
                : (item.improvements || ["Elaborate on core concepts and practical examples for a more complete response."]));

        // Format Expected Concepts
        let expectedConceptsHTML = "";
        if (expectedConcepts.length > 0) {
            expectedConceptsHTML = expectedConcepts.map(c => `
                <span class="concept-tag expected-tag">
                    <i class="fa-solid fa-lightbulb" style="font-size:9px; margin-right:5px; opacity:0.7;"></i>
                    ${escapeHTML(c)}
                </span>
            `).join("");
        } else {
            expectedConceptsHTML = `<span class="concept-empty">No expected concepts defined for this question.</span>`;
        }

        // Format Matched Concepts
        let matchedConceptsHTML = "";
        if (isUnanswered) {
            matchedConceptsHTML = `
                <span class="concept-empty" style="color:#dc2626; display:inline-flex; align-items:center; gap:5px;">
                    <i class="fa-solid fa-circle-xmark"></i>
                    Not Answered &mdash; No concepts matched
                </span>
            `;
        } else if (matchedConcepts.length > 0) {
            matchedConceptsHTML = matchedConcepts.map(c => `
                <span class="concept-tag matched-tag">
                    <i class="fa-solid fa-check" style="margin-right:5px; font-weight:700;"></i>
                    ${escapeHTML(c)}
                </span>
            `).join("");
        } else {
            matchedConceptsHTML = `
                <span class="concept-empty" style="color:#d97706; display:inline-flex; align-items:center; gap:5px;">
                    <i class="fa-solid fa-circle-exclamation"></i>
                    No key concepts matched in the candidate's answer
                </span>
            `;
        }

        // Format Missing Concepts
        let missingConceptsHTML = "";
        if (isUnanswered) {
            if (expectedConcepts.length > 0) {
                missingConceptsHTML = expectedConcepts.map(c => `
                    <span class="concept-tag" style="background:#fee2e2; color:#991b1b; border-color:#fca5a5;">
                        <i class="fa-solid fa-xmark" style="margin-right:5px; font-weight:700;"></i>
                        ${escapeHTML(c)}
                    </span>
                `).join("");
            } else {
                missingConceptsHTML = `<span class="concept-empty" style="color:#dc2626;">Not Answered</span>`;
            }
        } else if (missingConcepts.length > 0) {
            missingConceptsHTML = missingConcepts.map(c => `
                <span class="concept-tag" style="background:#fee2e2; color:#991b1b; border-color:#fca5a5;">
                    <i class="fa-solid fa-xmark" style="margin-right:5px; font-weight:700;"></i>
                    ${escapeHTML(c)}
                </span>
            `).join("");
        } else if (expectedConcepts.length > 0 && matchedConcepts.length > 0) {
            missingConceptsHTML = `
                <span class="concept-empty" style="color:#16a34a; display:inline-flex; align-items:center; gap:5px;">
                    <i class="fa-solid fa-circle-check"></i>
                    All expected key concepts were covered
                </span>
            `;
        } else {
            missingConceptsHTML = `<span class="concept-empty">None</span>`;
        }

        // Format Strengths & Improvements lists
        const strengthsHTML = strengthsList.map(s => `<li>${escapeHTML(s)}</li>`).join("");
        const improvementsHTML = improvementsList.map(imp => `<li>${escapeHTML(imp)}</li>`).join("");

        // Build Question Card Element
        const card = document.createElement("div");
        card.className = `question-evaluation-card ${isUnanswered ? 'question-card-unanswered' : ''}`;

        card.innerHTML = `
            <div class="evaluation-card-header">
                <div>
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px; flex-wrap:wrap;">
                        <span class="question-number-badge">
                            Question ${qNum}
                        </span>
                        ${isUnanswered ? `
                            <span class="question-status-badge not-answered" style="background:#fef2f2; color:#dc2626; border:1px solid #fecaca; font-size:11px; font-weight:600; padding:3px 10px; border-radius:20px; display:inline-flex; align-items:center; gap:5px;">
                                <i class="fa-solid fa-circle-xmark"></i> Not Answered
                            </span>
                        ` : `
                            <span class="question-status-badge answered" style="background:#ecfdf5; color:#16a34a; border:1px solid #bbf7d0; font-size:11px; font-weight:600; padding:3px 10px; border-radius:20px; display:inline-flex; align-items:center; gap:5px;">
                                <i class="fa-solid fa-circle-check"></i> Answered
                            </span>
                        `}
                    </div>
                    <h3>${escapeHTML(questionText)}</h3>
                </div>

                <div class="question-score ${isUnanswered ? 'not-answered-score' : ''}" ${isUnanswered ? 'style="background:#fef2f2;"' : ''}>
                    <strong ${isUnanswered ? 'style="color:#dc2626;"' : ''}>${qOverallVal}</strong>
                    <span>/ 100</span>
                    ${isUnanswered ? `<span style="display:block; font-size:9px; color:#dc2626; font-weight:700; text-transform:uppercase; margin-top:2px;">Not Answered</span>` : ''}
                </div>
            </div>

            <!-- Candidate Answer Block -->
            <div class="answer-block ${isUnanswered ? 'not-answered-block' : ''}" ${isUnanswered ? 'style="border-left:4px solid #dc2626; background:#fffafa;"' : ''}>
                <h4>
                    <i class="fa-solid fa-user" ${isUnanswered ? 'style="color:#dc2626;"' : ''}></i>
                    Candidate Answer
                    ${isUnanswered ? `
                        <span style="background:#fee2e2; color:#dc2626; font-size:10px; padding:2px 8px; border-radius:10px; margin-left:6px; font-weight:600; display:inline-flex; align-items:center; gap:4px;">
                            <i class="fa-solid fa-ban"></i> Not Answered
                        </span>
                    ` : ''}
                </h4>
                <p>
                    ${isUnanswered
                        ? '<span style="color:#dc2626; font-weight:600;"><i class="fa-solid fa-circle-xmark" style="margin-right:6px;"></i>Not Answered</span> &mdash; <em style="color:#64748b;">No spoken or written answer was detected for this question.</em>'
                        : escapeHTML(candidateAnswer)}
                </p>
            </div>

            <!-- Expected Concepts Block -->
            <div class="concept-block">
                <h4>
                    <i class="fa-solid fa-lightbulb"></i>
                    Expected Concepts
                </h4>
                <div class="concept-list">
                    ${expectedConceptsHTML}
                </div>
            </div>

            <!-- Matched Concepts Block -->
            <div class="concept-block matched-block">
                <h4>
                    <i class="fa-solid fa-check-double"></i>
                    Matched Concepts
                </h4>
                <div class="concept-list">
                    ${matchedConceptsHTML}
                </div>
            </div>

            <!-- Missing Concepts Block -->
            <div class="concept-block" style="margin-top: 14px;">
                <h4 style="color: #dc2626;">
                    <i class="fa-solid fa-circle-xmark" style="color: #dc2626;"></i>
                    Missing Concepts
                </h4>
                <div class="concept-list">
                    ${missingConceptsHTML}
                </div>
            </div>

            <!-- Score Grid: Technical, Relevance, Concept Coverage, Completeness, Communication, Confidence, Problem Solving, Overall -->
            <div class="question-score-grid">
                <div class="mini-score">
                    <span>Technical</span>
                    <strong ${isUnanswered ? 'style="color:#dc2626;"' : ''}>${techScoreText}</strong>
                </div>
                <div class="mini-score">
                    <span>Relevance</span>
                    <strong ${isUnanswered ? 'style="color:#dc2626;"' : ''}>${relScoreText}</strong>
                </div>
                <div class="mini-score">
                    <span>Concepts</span>
                    <strong ${isUnanswered ? 'style="color:#dc2626;"' : (conceptScoreText === 'Not Available' ? 'style="font-size:11px; white-space:nowrap; color:#64748b;"' : '')}>${conceptScoreText}</strong>
                </div>
                <div class="mini-score">
                    <span>Completeness</span>
                    <strong ${isUnanswered ? 'style="color:#dc2626;"' : ''}>${compScoreText}</strong>
                </div>
                <div class="mini-score">
                    <span>Communication</span>
                    <strong ${isUnanswered ? 'style="color:#dc2626;"' : ''}>${commScoreText}</strong>
                </div>
                <div class="mini-score">
                    <span>Confidence</span>
                    <strong ${isUnanswered ? 'style="color:#dc2626;"' : ''}>${confScoreText}</strong>
                </div>
                <div class="mini-score">
                    <span>Problem Solving</span>
                    <strong ${isUnanswered ? 'style="color:#dc2626;"' : (probScoreText === 'Not Available' ? 'style="font-size:11px; white-space:nowrap; color:#64748b;"' : '')}>${probScoreText}</strong>
                </div>
                <div class="mini-score mini-score-overall" ${isUnanswered ? 'style="border-color:#fca5a5; background:#fef2f2;"' : ''}>
                    <span>Overall</span>
                    <strong ${isUnanswered ? 'style="color:#dc2626;"' : ''}>${qOverallText}</strong>
                </div>
            </div>

            <!-- Strengths and Areas for Improvement -->
            <div class="question-feedback">
                <div class="feedback-column strengths">
                    <h4>
                        <i class="fa-solid fa-circle-check"></i>
                        Strengths
                    </h4>
                    <ul>
                        ${strengthsHTML}
                    </ul>
                </div>

                <div class="feedback-column improvements">
                    <h4>
                        <i class="fa-solid fa-arrow-up"></i>
                        Areas for Improvement
                    </h4>
                    <ul>
                        ${improvementsHTML}
                    </ul>
                </div>
            </div>
        `;

        questionEvaluationContainer.appendChild(card);
    });
}


// =========================================
// NAVIGATION ACTIONS
// =========================================

function setupNavigationButtons(data) {
    const dashboardBtn = document.getElementById("dashboardBtn");
    if (dashboardBtn) {
        dashboardBtn.addEventListener("click", () => {
            window.location.href = "dashboard.html";
        });
    }

    const dashboardActionBtn = document.getElementById("dashboardActionBtn");
    if (dashboardActionBtn) {
        dashboardActionBtn.addEventListener("click", () => {
            window.location.href = "dashboard.html";
        });
    }

    const downloadReportBtn = document.getElementById("downloadReportBtn");
    if (downloadReportBtn) {
        downloadReportBtn.onclick = async () => {
            if (downloadReportBtn.disabled) return;

            const urlParams = new URLSearchParams(window.location.search);
            const currentInterviewId =
                (data && (data.interview_id || data.id)) ||
                urlParams.get("id") ||
                sessionStorage.getItem("interviewId") ||
                localStorage.getItem("interviewId");

            if (!currentInterviewId) {
                alert("Unable to locate interview session ID. Please try again from the dashboard or history page.");
                return;
            }

            const originalBtnHtml = downloadReportBtn.innerHTML;
            downloadReportBtn.disabled = true;
            downloadReportBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin" style="color: #ef4444;"></i> Generating Report...`;

            try {
                const token = localStorage.getItem("sessionToken");
                const headers = {};
                if (token) {
                    headers["Authorization"] = `Bearer ${token}`;
                }

                const endpointUrl = `/api/interview/${currentInterviewId}/report/pdf` +
                    (token ? `?token=${encodeURIComponent(token)}` : "");

                const response = await fetch(endpointUrl, {
                    method: "GET",
                    headers: headers
                });

                if (!response.ok) {
                    let errMsg = "Unable to generate the interview report. Please try again.";
                    try {
                        const errBody = await response.json();
                        if (errBody && errBody.detail) {
                            errMsg = errBody.detail;
                        }
                    } catch (_) {}
                    throw new Error(errMsg);
                }

                const blob = await response.blob();
                const blobUrl = window.URL.createObjectURL(blob);
                const downloadLink = document.createElement("a");
                downloadLink.style.display = "none";
                downloadLink.href = blobUrl;
                downloadLink.download = `AI_Interview_Report_${currentInterviewId}.pdf`;
                document.body.appendChild(downloadLink);
                downloadLink.click();

                setTimeout(() => {
                    window.URL.revokeObjectURL(blobUrl);
                    if (downloadLink.parentNode) {
                        downloadLink.parentNode.removeChild(downloadLink);
                    }
                }, 1000);
            } catch (error) {
                console.error("[Interview Report Download Error]", error);
                alert(error.message || "Unable to generate the interview report. Please try again.");
            } finally {
                downloadReportBtn.disabled = false;
                downloadReportBtn.innerHTML = originalBtnHtml;
            }
        };
    }

    const retryBtn = document.getElementById("retryBtn");
    if (retryBtn) {
        retryBtn.addEventListener("click", () => {
            window.location.href = "role.html";
        });
    }

    const historyBtn = document.getElementById("historyBtn");
    if (historyBtn) {
        historyBtn.addEventListener("click", () => {
            window.location.href = "history.html";
        });
    }

    const viewRecordingBtn = document.getElementById("viewRecordingBtn");
    if (viewRecordingBtn) {
        viewRecordingBtn.addEventListener("click", () => {
            const hasRec = Boolean(data && (data.recording_available || data.recording_url || data.recording_path || data.recordingURL || data.filename));
            let recUrl = (data && data.recording_url) ? data.recording_url : null;
            if (!recUrl && data && data.interview_id) {
                recUrl = `/interview/${data.interview_id}/recording`;
            } else if (!recUrl && data && data.filename) {
                recUrl = `/uploads/${data.filename}`;
            } else if (!recUrl && data && data.recordingURL) {
                recUrl = data.recordingURL;
            }

            if (!hasRec || !recUrl) {
                alert("Recording unavailable");
                return;
            }

            const modal = document.getElementById("videoModal");
            const player = document.getElementById("interviewVideoPlayer");
            const info = document.getElementById("videoModalInfo");
            const dlLink = document.getElementById("downloadVideoLink");

            if (modal && player) {
                player.src = recUrl;
                if (info) {
                    const intId = data.interview_id || data.id || "";
                    info.textContent = `Interview #${intId} (${data.role || "Session"})`;
                }
                if (dlLink) {
                    dlLink.href = recUrl;
                    dlLink.download = `interview_${data.interview_id || "recording"}.webm`;
                }
                modal.style.display = "flex";
                player.play().catch(e => console.log("Auto-play note:", e));
            } else {
                window.open(recUrl, "_blank");
            }
        });
    }

    const closeBtn = document.getElementById("closeVideoModalBtn");
    if (closeBtn) {
        closeBtn.addEventListener("click", () => {
            const modal = document.getElementById("videoModal");
            const player = document.getElementById("interviewVideoPlayer");
            if (player) {
                player.pause();
                player.src = "";
            }
            if (modal) modal.style.display = "none";
        });
    }

    const videoModal = document.getElementById("videoModal");
    if (videoModal) {
        videoModal.addEventListener("click", (e) => {
            if (e.target === videoModal) {
                const player = document.getElementById("interviewVideoPlayer");
                if (player) {
                    player.pause();
                    player.src = "";
                }
                videoModal.style.display = "none";
            }
        });
    }
}


// =========================================
// MAIN CONTROLLER INITIALIZATION
// =========================================

async function loadResult() {
    console.log("=================================");
    console.log("RESULT PAGE: LOADING INTERVIEW DATA");
    console.log("Session interviewResult:", sessionStorage.getItem("interviewResult") ? "Found" : "None");
    console.log("Local interviewResult:", localStorage.getItem("interviewResult") ? "Found" : "None");
    console.log("Session interviewId:", sessionStorage.getItem("interviewId"));
    console.log("Session transcript:", sessionStorage.getItem("transcript") ? "Found" : "None");
    console.log("=================================");

    const urlParams = new URLSearchParams(window.location.search);
    const paramId = urlParams.get("id") || urlParams.get("interview_id");
    const sessionInterviewId = sessionStorage.getItem("interviewId") || localStorage.getItem("interviewId");
    const targetInterviewId = paramId || sessionInterviewId;

    let data = null;

    // 1. If an interview ID is available, try fetching fresh and authoritative data from backend SQL Server
    if (targetInterviewId && targetInterviewId !== "null" && targetInterviewId !== "undefined") {
        try {
            const resp = await fetch(`/interview/${targetInterviewId.trim()}`);
            if (resp.ok) {
                const json = await resp.json();
                if (json && json.interview) {
                    const intRow = json.interview;
                    const ansRows = json.answers || [];
                    const evalRow = json.evaluation || {};
                    const fbRow = json.feedback || {};
                    const isTerm = String(intRow.status || "").toLowerCase() === "terminated";

                    const parsedQuestions = ansRows.map(a => {
                        const hasAns = Boolean(a.answer_text && a.answer_text.trim().length > 0);
                        let matched = [];
                        let missing = [];
                        let expected = [];
                        let strengths = [];
                        let improvements = [];
                        try { matched = typeof a.matched_concepts === "string" ? JSON.parse(a.matched_concepts || "[]") : (a.matched_concepts || []); } catch (e) {}
                        try { missing = typeof a.missing_concepts === "string" ? JSON.parse(a.missing_concepts || "[]") : (a.missing_concepts || []); } catch (e) {}
                        try { strengths = typeof a.strengths === "string" ? JSON.parse(a.strengths || "[]") : (a.strengths || []); } catch (e) {}
                        try { improvements = typeof a.weaknesses === "string" ? JSON.parse(a.weaknesses || "[]") : (a.weaknesses || []); } catch (e) {}

                        if (Array.isArray(a.expected_concepts) && a.expected_concepts.length > 0) {
                            expected = a.expected_concepts;
                        } else if (matched.length > 0 || missing.length > 0) {
                            expected = Array.from(new Set([...matched, ...missing]));
                        }

                        let cScore = null;
                        if (!hasAns || isTerm) {
                            cScore = isTerm ? null : 0;
                        } else if (a.concept_score !== undefined && a.concept_score !== null && a.concept_score !== "N/A" && a.concept_score !== "Not Available") {
                            cScore = Number(a.concept_score);
                        } else if (expected.length > 0) {
                            cScore = Math.round((matched.length / expected.length) * 100);
                        } else {
                            cScore = null;
                        }

                        return {
                            question_number: a.question_number,
                            question: a.question_text,
                            candidate_answer: a.answer_text || "",
                            is_answered: hasAns,
                            status: hasAns ? "answered" : "not_answered",
                            technical_score: isTerm ? null : a.technical_score,
                            communication_score: isTerm ? null : a.communication_score,
                            confidence_score: isTerm ? null : a.confidence_score,
                            problem_solving_score: isTerm ? null : a.problem_solving_score,
                            relevance_score: isTerm ? null : a.relevance_score,
                            completeness_score: isTerm ? null : a.completeness_score,
                            overall_score: isTerm ? null : a.overall_answer_score,
                            expected_concepts: expected,
                            concept_score: cScore,
                            concept_coverage_score: cScore,
                            matched_concepts: matched,
                            missing_concepts: missing,
                            strengths: strengths,
                            improvements: improvements,
                            feedback: isTerm ? "AI evaluation was not generated because this interview was terminated due to a security violation." : (a.feedback || "")
                        };
                    });

                    let globalStrengths = [];
                    let globalImprovements = [];
                    try { globalStrengths = JSON.parse(fbRow.strengths || "[]"); } catch (e) {}
                    try { globalImprovements = JSON.parse(fbRow.improvements || "[]"); } catch (e) {}

                    data = {
                        ...json,
                        ...intRow,
                        status: intRow.status || (isTerm ? "Terminated" : "COMPLETED"),
                        interview_status: intRow.status || (isTerm ? "Terminated" : "COMPLETED"),
                        termination_type: intRow.termination_type || (isTerm ? "TAB_SWITCH" : ""),
                        terminated_reason: intRow.terminated_reason || (isTerm ? "Tab Switch Detected" : ""),
                        termination_reason: intRow.terminated_reason || (isTerm ? "Tab Switch Detected" : ""),
                        security_violation: Boolean(intRow.security_violation || isTerm),
                        tab_switch_count: Number(intRow.tab_switch_count || (isTerm ? 1 : 0)),
                        terminated_at: intRow.terminated_at,
                        recording_path: intRow.recording_path || "",
                        recording_filename: intRow.recording_filename || "",
                        recording_available: Boolean(json.recording_available ?? intRow.recording_available ?? (intRow.recording_path || intRow.recording_filename)),
                        recording_url: json.recording_url || intRow.recording_url || (intRow.id ? `/interview/${intRow.id}/recording` : null),
                        interview_id: intRow.id,
                        role: intRow.role,
                        total_questions: intRow.total_questions,
                        duration_seconds: intRow.duration_seconds,
                        transcript: isTerm ? "" : (intRow.transcript || ""),
                        created_at: intRow.created_at,
                        evaluation: isTerm ? null : {
                            overall_score: intRow.overall_score ?? evalRow.overall_score,
                            technical_score: intRow.technical_score ?? evalRow.technical_score,
                            communication_score: intRow.communication_score ?? evalRow.communication_score,
                            confidence_score: intRow.confidence_score ?? evalRow.confidence_score,
                            problem_solving_score: intRow.problem_solving_score ?? evalRow.problem_solving_score,
                            relevance_score: intRow.relevance_score ?? evalRow.relevance_score,
                            completeness_score: evalRow.completeness_score ?? intRow.relevance_score,
                            concept_score: evalRow.concept_score ?? intRow.technical_score,
                            strengths: globalStrengths,
                            improvements: globalImprovements
                        },
                        question_answers: parsedQuestions
                    };
                }
            }
        } catch (fetchErr) {
            console.warn("[Result] Backend fetch failed, falling back to local storage:", fetchErr);
        }
    }

    // 2. Try reading complete interviewResult JSON from sessionStorage or localStorage if not fetched from backend
    if (!data) {
        let rawResult = sessionStorage.getItem("interviewResult") || localStorage.getItem("interviewResult");
        if (rawResult) {
            try {
                data = JSON.parse(rawResult);
            } catch (error) {
                console.error("Invalid interviewResult JSON:", error);
                data = null;
            }
        }
    }

    // 3. Fallback to individual keys
    if (!data) {
        const interviewId = sessionStorage.getItem("interviewId");
        const transcript = sessionStorage.getItem("transcript");
        const selectedRole = sessionStorage.getItem("selectedRole") || localStorage.getItem("selectedRole");
        const storedTotalQuestions = sessionStorage.getItem("totalQuestions");
        const recordingAvailable = sessionStorage.getItem("recordingAvailable");
        const interviewDate = sessionStorage.getItem("interviewDate");
        const recordingURL = sessionStorage.getItem("recordingURL");

        if (interviewId || transcript || selectedRole) {
            data = {
                status: sessionStorage.getItem("interviewStatus") || "COMPLETED",
                interview_status: sessionStorage.getItem("interviewStatus") || "COMPLETED",
                interview_id: interviewId || "1",
                role: selectedRole || "Developer",
                total_questions: Number(storedTotalQuestions) || 0,
                transcript: transcript || "",
                recording_available: recordingAvailable === "true",
                interviewDate: interviewDate || new Date().toLocaleString(),
                recording_url: recordingURL || "",
                evaluation: null,
                question_answers: []
            };
        }
    }

    // If neither source has any data, show not found state
    if (!data) {
        showResultNotFound();
        return;
    }

    console.log("INTERVIEW DATA LOADED:", data);

    // 4. Populate Interview ID, Role, Total Questions, Date, Duration
    const actualId = data.interview_id || data.id || sessionStorage.getItem("interviewId") || "1";
    if (interviewIdElement) {
        interviewIdElement.textContent = `#${actualId}`;
    }

    const actualRole = data.role || sessionStorage.getItem("selectedRole") || localStorage.getItem("selectedRole") || "--";
    if (roleName) {
        roleName.textContent = actualRole;
    }

    const actualDate = data.interviewDate || data.created_at || sessionStorage.getItem("interviewDate") || new Date().toLocaleDateString();
    if (interviewDateElement) {
        interviewDateElement.textContent = actualDate;
    }

    if (interviewTimeElement) {
        const durSec = Number(data.duration_seconds || sessionStorage.getItem("interviewDuration") || 0);
        if (durSec > 0) {
            if (durSec < 60) {
                interviewTimeElement.textContent = `${Math.round(durSec)} Seconds`;
            } else {
                const mins = Math.floor(durSec / 60);
                const secs = Math.round(durSec % 60);
                interviewTimeElement.textContent = secs > 0 ? `${mins} min ${secs} sec` : `${mins} Minutes`;
            }
        } else {
            interviewTimeElement.textContent = "--";
        }
    }

    // =========================================
    // STRICT TAB SWITCH & TERMINATION DISPLAY
    // =========================================
    const backendInterview = (data && data.interview) ? data.interview : (data || {});
    const rawStatus = String(backendInterview.status || data.interview_status || data.status || sessionStorage.getItem("interviewStatus") || "").trim();
    const rawTabSwitchCount = backendInterview.tab_switch_count ?? data.tab_switch_count ?? sessionStorage.getItem("tabSwitchCount");
    const parsedTabCount = Number(rawTabSwitchCount) || 0;
    const rawTermReason = String(backendInterview.terminated_reason || data.terminated_reason || data.termination_reason || sessionStorage.getItem("terminatedReason") || "").trim();
    const rawTermType = String(backendInterview.termination_type || data.termination_type || sessionStorage.getItem("terminationType") || "").trim();
    const rawSecViolation = backendInterview.security_violation ?? data.security_violation ?? (sessionStorage.getItem("securityViolation") === "true");

    const isTerminated = rawStatus.toLowerCase() === "terminated" || 
                         rawTermType.toUpperCase() === "TAB_SWITCH" || 
                         parsedTabCount > 0 || 
                         rawTermReason.toLowerCase().includes("tab switch") ||
                         rawSecViolation === true;

    const breakdownCard = document.querySelector(".breakdown-card");
    const feedbackSection = document.querySelector(".feedback-section");
    const scoreCircle = document.querySelector(".score-circle");

    if (isTerminated) {
        // --- 1. Info Cards: Terminated State ---
        if (interviewStatusElement) {
            interviewStatusElement.textContent = "Terminated";
            interviewStatusElement.style.color = "#dc2626";
        }
        if (terminationReasonElement) {
            terminationReasonElement.textContent = "Tab Switch Detected";
            terminationReasonElement.style.color = "#dc2626";
        }
        if (securityViolationElement) {
            securityViolationElement.textContent = "Yes";
            securityViolationElement.style.color = "#dc2626";
        }
        if (tabSwitchCountElement) {
            tabSwitchCountElement.textContent = "1";
            tabSwitchCountElement.style.color = "#dc2626";
        }

        const statusIconEl = document.getElementById("statusInfoIcon");
        if (statusIconEl) {
            statusIconEl.style.background = "#fee2e2";
            statusIconEl.style.color = "#dc2626";
            statusIconEl.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';
        }
        const reasonIconEl = document.getElementById("reasonInfoIcon");
        if (reasonIconEl) {
            reasonIconEl.style.background = "#fee2e2";
            reasonIconEl.style.color = "#dc2626";
        }
        const secIconEl = document.getElementById("securityInfoIcon");
        if (secIconEl) {
            secIconEl.style.background = "#fee2e2";
            secIconEl.style.color = "#dc2626";
            secIconEl.innerHTML = '<i class="fa-solid fa-shield-virus"></i>';
        }
        const tabIconEl = document.getElementById("tabSwitchInfoIcon");
        if (tabIconEl) {
            tabIconEl.style.background = "#fee2e2";
            tabIconEl.style.color = "#dc2626";
        }

        // --- 2. Termination Banner ---
        if (terminationBanner) {
            terminationBanner.style.display = "block";
        }
        if (bannerTermReason) bannerTermReason.textContent = "Tab Switch Detected";
        if (bannerSecViolation) bannerSecViolation.textContent = "Yes";
        if (bannerTabSwitchCount) bannerTabSwitchCount.textContent = "1";

        // --- 3. Status Card (Header message) ---
        if (resultStatusCard) {
            resultStatusCard.style.borderColor = "#fecaca";
            resultStatusCard.style.background = "#fffbfb";
        }
        if (resultStatusIcon) {
            resultStatusIcon.style.background = "#fee2e2";
            resultStatusIcon.style.color = "#dc2626";
            resultStatusIcon.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';
        }
        if (resultStatusHeading) {
            resultStatusHeading.textContent = "⚠️ Interview Terminated";
            resultStatusHeading.style.color = "#991b1b";
        }
        if (resultStatusSubheading) {
            resultStatusSubheading.textContent = "Your interview was automatically terminated because you left the interview window.";
            resultStatusSubheading.style.color = "#7f1d1d";
        }
        if (resultStatusBadge) {
            resultStatusBadge.style.background = "#fef2f2";
            resultStatusBadge.style.color = "#dc2626";
            resultStatusBadge.style.border = "1px solid #fecaca";
            resultStatusBadge.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Terminated';
        }

        // --- 4. Hide AI Score Breakdown Card ---
        if (breakdownCard) {
            breakdownCard.style.display = "none";
        }

        // --- 5. Overall Score Card: Terminated Display ---
        if (overallScore) {
            overallScore.textContent = "Not Available";
            overallScore.style.fontSize = "22px";
            overallScore.style.color = "#64748b";
        }
        const scoreInner = document.querySelector(".score-inner");
        if (scoreInner) {
            const spanUnit = scoreInner.querySelector("span");
            if (spanUnit) spanUnit.style.display = "none";
        }
        if (scoreCircle) {
            scoreCircle.style.background = "#e2e8f0";
        }
        if (performanceText) {
            performanceText.textContent = "Evaluation: Not Generated";
            performanceText.style.color = "#991b1b";
        }
        if (scoreDescription) {
            scoreDescription.textContent = "AI evaluation was not generated because this interview was automatically terminated due to a security violation.";
            scoreDescription.style.color = "#7f1d1d";
        }

        // --- 6. Question-wise AI Evaluation Section: Terminated Notice ---
        if (questionEvaluationContainer) {
            questionEvaluationContainer.innerHTML = `
                <div style="background:#fff5f5; border:1.5px solid #fecaca; border-radius:14px; padding:28px 24px; text-align:center;">
                    <div style="width:52px; height:52px; border-radius:50%; background:#fee2e2; color:#dc2626; display:flex; align-items:center; justify-content:center; font-size:24px; margin:0 auto 12px;">
                        <i class="fa-solid fa-triangle-exclamation"></i>
                    </div>
                    <h3 style="font-size:18px; font-weight:700; color:#991b1b; margin-bottom:8px;">AI Evaluation Not Generated</h3>
                    <p style="font-size:14px; color:#7f1d1d; max-width:540px; margin:0 auto 12px; line-height:1.6;">
                        AI evaluation was not generated because this interview was automatically terminated due to a security violation.
                    </p>
                </div>
            `;
        }

        // --- 7. Hide AI Feedback Section ---
        if (feedbackSection) {
            feedbackSection.style.display = "none";
        }

        // --- 8. Hide or note Speech-to-Text Transcript Section ---
        if (transcriptSection) {
            transcriptSection.style.display = "none";
        }

    } else {
        // --- Normal Completed Interview ---
        if (interviewStatusElement) {
            interviewStatusElement.textContent = "Completed";
            interviewStatusElement.style.color = "#16a34a";
        }
        if (terminationReasonElement) {
            terminationReasonElement.textContent = "None";
            terminationReasonElement.style.color = "#64748b";
        }
        if (securityViolationElement) {
            securityViolationElement.textContent = "No";
            securityViolationElement.style.color = "#16a34a";
        }
        if (tabSwitchCountElement) {
            tabSwitchCountElement.textContent = "0";
            tabSwitchCountElement.style.color = "#1e293b";
        }
        if (terminationBanner) {
            terminationBanner.style.display = "none";
        }
        if (breakdownCard) {
            breakdownCard.style.display = "block";
        }
        if (feedbackSection) {
            feedbackSection.style.display = "block";
        }
        if (transcriptSection) {
            transcriptSection.style.display = "block";
        }
    }

    const evaluation = data.evaluation || null;

    // Use data.question_answers to calculate:
    // - Questions Attempted = number of questions actually displayed during the interview.
    // - Questions Answered = questions whose candidate_answer contains non-empty text after trimming whitespace.
    // - Questions Unanswered = Questions Attempted minus Questions Answered.
    let questionsList = [];
    if (Array.isArray(data.question_answers) && data.question_answers.length > 0) {
        questionsList = data.question_answers;
    } else if (evaluation && Array.isArray(evaluation.questions) && evaluation.questions.length > 0) {
        questionsList = evaluation.questions;
    } else {
        try {
            const storedSubmitted = sessionStorage.getItem("submittedQuestions");
            if (storedSubmitted) {
                const parsed = JSON.parse(storedSubmitted);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    questionsList = parsed;
                }
            }
        } catch (e) {
            console.warn("[Result] Could not parse submittedQuestions:", e);
        }
    }

    if (!data.question_answers || !Array.isArray(data.question_answers)) {
        data.question_answers = questionsList;
    }
    const questions = questionsList;

    // Questions Attempted
    let attemptedCount = questionsList.length;
    if (attemptedCount === 0) {
        if (data.attempted_questions !== undefined && data.attempted_questions !== null) {
            attemptedCount = Number(data.attempted_questions) || 0;
        } else if (data.total_questions !== undefined && data.total_questions !== null) {
            attemptedCount = Number(data.total_questions) || 0;
        } else {
            const storedTotal = sessionStorage.getItem("totalQuestions") || sessionStorage.getItem("attemptedQuestions");
            attemptedCount = Number(storedTotal) || 0;
        }
    }

    // Questions Answered
    let answeredCount = 0;
    if (questionsList.length > 0) {
        answeredCount = questionsList.filter(item => {
            if (!item) return false;
            if (item.is_answered === false) return false;
            const ans = item.candidate_answer;
            if (typeof ans === "string") {
                return ans.trim().length > 0;
            }
            return Boolean(ans && String(ans).trim().length > 0);
        }).length;
    } else if (data.answered_questions !== undefined && data.answered_questions !== null) {
        answeredCount = Number(data.answered_questions) || 0;
    } else if (evaluation && evaluation.answered_questions !== undefined && evaluation.answered_questions !== null) {
        answeredCount = Number(evaluation.answered_questions) || 0;
    } else if (sessionStorage.getItem("answeredQuestions")) {
        answeredCount = Number(sessionStorage.getItem("answeredQuestions")) || 0;
    }

    // Questions Unanswered
    let unansweredCount = Math.max(0, attemptedCount - answeredCount);
    if (questionsList.length === 0 && data.unanswered_questions !== undefined && data.unanswered_questions !== null) {
        unansweredCount = Number(data.unanswered_questions) || 0;
    } else if (questionsList.length === 0 && evaluation && evaluation.unanswered_questions !== undefined && evaluation.unanswered_questions !== null) {
        unansweredCount = Number(evaluation.unanswered_questions) || 0;
    } else if (questionsList.length === 0 && sessionStorage.getItem("unansweredQuestions")) {
        unansweredCount = Number(sessionStorage.getItem("unansweredQuestions")) || 0;
    }

    if (totalQuestions) {
        totalQuestions.textContent = String(attemptedCount);
    }
    if (questionsAttemptedElement) {
        questionsAttemptedElement.textContent = String(attemptedCount);
    }
    if (questionsAnsweredElement) {
        questionsAnsweredElement.textContent = String(answeredCount);
    }
    if (questionsUnansweredElement) {
        questionsUnansweredElement.textContent = String(unansweredCount);
    }

    // 5. Populate Speech-to-Text Transcript (Whisper) for normal interviews
    if (!isTerminated) {
        const transcript = (data.transcript || sessionStorage.getItem("transcript") || "").trim();
        if (transcriptText) {
            if (transcript) {
                transcriptText.textContent = transcript;
            } else {
                transcriptText.innerHTML = "<em>No speech was detected in this interview recording.</em>";
            }
        }

        if (transcriptWordCount) {
            const words = transcript ? transcript.split(/\s+/).filter(Boolean).length : 0;
            transcriptWordCount.textContent = `${words} word${words === 1 ? "" : "s"}`;
        }

        // 6. Display Scores for Normal Interviews
        const rawOverall = evaluation ? evaluation.overall_score : null;
        const rawTech = evaluation ? evaluation.technical_score : null;
        const rawRel = evaluation ? evaluation.relevance_score : null;
        const rawConcept = evaluation ? ((evaluation.concept_score !== undefined && evaluation.concept_score !== null) ? evaluation.concept_score : evaluation.concept_coverage_score) : null;
        const rawComp = evaluation ? evaluation.completeness_score : null;
        const rawComm = evaluation ? evaluation.communication_score : null;
        const rawConf = evaluation ? evaluation.confidence_score : null;
        const rawProb = evaluation ? evaluation.problem_solving_score : null;

        const hasEvaluation = evaluation !== null && rawOverall !== null && rawOverall !== undefined;

        const overallVal = hasEvaluation ? Math.round(Number(rawOverall)) : "--";
        const techVal = hasEvaluation ? Math.round(Number(rawTech)) : "--";
        const relVal = hasEvaluation ? Math.round(Number(rawRel)) : "--";
        const conceptVal = (hasEvaluation && rawConcept !== null && rawConcept !== undefined) ? Math.round(Number(rawConcept)) : (hasEvaluation ? "N/A" : "--");
        const compVal = hasEvaluation ? Math.round(Number(rawComp)) : "--";
        const commVal = hasEvaluation ? Math.round(Number(rawComm)) : "--";
        const confVal = hasEvaluation ? Math.round(Number(rawConf)) : "--";
        const probVal = (hasEvaluation && rawProb !== null && rawProb !== undefined) ? Math.round(Number(rawProb)) : (hasEvaluation ? "N/A" : "--");

        if (overallScore) {
            overallScore.textContent = overallVal;
            overallScore.style.fontSize = "";
            overallScore.style.color = "";
        }
        const scoreInner = document.querySelector(".score-inner");
        if (scoreInner) {
            const spanUnit = scoreInner.querySelector("span");
            if (spanUnit) spanUnit.style.display = "";
        }

        if (technicalScore) technicalScore.textContent = techVal;
        if (relevanceScore) relevanceScore.textContent = relVal;
        if (conceptCoverageScore) conceptCoverageScore.textContent = conceptVal;
        if (completenessScore) completenessScore.textContent = compVal;
        if (communicationScore) communicationScore.textContent = commVal;
        if (confidenceScore) confidenceScore.textContent = confVal;
        if (problemScore) problemScore.textContent = probVal;

        // Animate category progress bars
        setTimeout(() => {
            if (technicalBar && typeof techVal === "number") {
                technicalBar.style.width = `${Math.min(100, Math.max(0, techVal))}%`;
            }
            if (relevanceBar && typeof relVal === "number") {
                relevanceBar.style.width = `${Math.min(100, Math.max(0, relVal))}%`;
            }
            if (conceptCoverageBar && typeof conceptVal === "number") {
                conceptCoverageBar.style.width = `${Math.min(100, Math.max(0, conceptVal))}%`;
            }
            if (completenessBar && typeof compVal === "number") {
                completenessBar.style.width = `${Math.min(100, Math.max(0, compVal))}%`;
            }
            if (communicationBar && typeof commVal === "number") {
                communicationBar.style.width = `${Math.min(100, Math.max(0, commVal))}%`;
            }
            if (confidenceBar && typeof confVal === "number") {
                confidenceBar.style.width = `${Math.min(100, Math.max(0, confVal))}%`;
            }
            if (problemBar && typeof probVal === "number") {
                problemBar.style.width = `${Math.min(100, Math.max(0, probVal))}%`;
            }
        }, 300);

        // Overall Circular Score progress
        if (scoreCircle && typeof overallVal === "number") {
            setTimeout(() => {
                const degree = Math.min(360, overallVal * 3.6);
                scoreCircle.style.background = `conic-gradient(
                    #2563eb 0deg,
                    #2563eb ${degree}deg,
                    #e9eef6 ${degree}deg,
                    #e9eef6 360deg
                )`;
            }, 300);
        }

        // Dynamic evaluation narrative & feedback
        if (scoreDescription) {
            scoreDescription.textContent = hasEvaluation
                ? "AI evaluation generated from your interview responses."
                : "Interview recording and Faster-Whisper transcription completed successfully.";
            scoreDescription.style.color = "";
        }

        if (performanceText) {
            performanceText.style.color = "";
            if (!hasEvaluation) {
                performanceText.textContent = "Interview Completed";
            } else if (overallVal >= 90) {
                performanceText.textContent = "Outstanding Performance";
            } else if (overallVal >= 80) {
                performanceText.textContent = "Very Good Performance";
            } else if (overallVal >= 70) {
                performanceText.textContent = "Good Performance";
            } else if (overallVal >= 60) {
                performanceText.textContent = "Average Performance";
            } else {
                performanceText.textContent = "Needs Improvement";
            }
        }

        // Feedback Cards
        if (evaluation) {
            const globalStrengths = Array.isArray(evaluation.strengths) ? evaluation.strengths : [];
            const globalImprovements = Array.isArray(evaluation.improvements) ? evaluation.improvements : [];

            if (technicalFeedbackText) {
                technicalFeedbackText.textContent =
                    (typeof techVal === "number" && techVal >= 75)
                        ? (globalStrengths[0] || "Demonstrated solid technical understanding and concept coverage.")
                        : (globalImprovements[0] || "Focus on elaborating key technical principles and terminology.");
            }

            if (communicationFeedbackText) {
                communicationFeedbackText.textContent =
                    (typeof commVal === "number" && commVal >= 75)
                        ? "Your answers were well-structured, articulate, and easy to understand."
                        : "Work on structuring your responses with clear beginnings and specific examples.";
            }

            if (confidenceFeedbackText) {
                confidenceFeedbackText.textContent =
                    (typeof confVal === "number" && confVal >= 75)
                        ? "Demonstrated high confidence and conviction during responses."
                        : "Practice speaking decisively and maintaining steady delivery.";
            }

            if (practiceFeedbackText) {
                practiceFeedbackText.textContent =
                    typeof overallVal === "number"
                        ? `Overall Score: ${overallVal}/100. Practice routinely to build consistency.`
                        : "Complete mock sessions to refine your interview skills.";
            }
        }

        // Render question-wise evaluation for normal interviews
        if (questions && questions.length > 0) {
            renderQuestionWiseEvaluation(questions);
        }
    }

    // 8. Recording status indicator (based on genuine recording existence)
    const isRecordingAvailable = Boolean(
        data && (data.recording_available === true ||
                 (data.recording_url && !String(data.recording_url).includes("null")) ||
                 (data.recording_path && data.recording_path.length > 0))
    );

    if (isRecordingAvailable) {
        if (recordingStatus) {
            recordingStatus.textContent = "Available";
            recordingStatus.style.color = "#16a34a";
        }
        if (recordingMessage) {
            recordingMessage.textContent = isTerminated
                ? "Your interview recording was captured before termination and is available for review."
                : "Your interview recording was processed and verified successfully.";
        }
    } else {
        if (recordingStatus) {
            recordingStatus.textContent = "Unavailable";
            recordingStatus.style.color = "#dc2626";
        }
        if (recordingMessage) {
            recordingMessage.textContent = "Recording unavailable for this interview session.";
        }
    }

    // 9. Setup action buttons
    setupNavigationButtons(data);
}

// Compatibility alias
const initResultPage = loadResult;


// =========================================
// RUN CONTROLLER ON LOAD
// =========================================

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadResult);
} else {
    loadResult();
}