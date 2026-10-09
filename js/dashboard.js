// =========================================
// AI Interview Evaluation System - Candidate Progress Dashboard
// =========================================

let progressChartInstance = null;
let currentSummaryData = null;

function checkCandidateAuth() {
    const token = localStorage.getItem("sessionToken") || sessionStorage.getItem("sessionToken");
    if (!token) {
        window.location.replace("login.html?auth_msg=login_required");
        return false;
    }

    // Role check: Administrator must NEVER land on candidate dashboard
    const isAdmin = localStorage.getItem("isAdmin") === "true" ||
                    sessionStorage.getItem("isAdmin") === "true" ||
                    localStorage.getItem("userRole") === "Admin" ||
                    sessionStorage.getItem("userRole") === "Admin";
    if (isAdmin) {
        window.location.replace("/app/admin_dashboard.html");
        return false;
    }

    return true;
}

async function fetchDashboardSummary(isBackgroundRefresh = false) {
    const token = localStorage.getItem("sessionToken") || sessionStorage.getItem("sessionToken");
    if (!token) return;

    const loadingElem = document.getElementById("dashboardLoading");
    const emptyElem = document.getElementById("emptyStateSection");
    const dataContainer = document.getElementById("dashboardDataContainer");

    try {
        const response = await fetch("/api/dashboard/summary", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (response.status === 401) {
            console.warn("[Dashboard] Session expired or invalid.");
            try {
                localStorage.removeItem("sessionToken");
                sessionStorage.removeItem("sessionToken");
            } catch (e) {}
            window.location.replace("login.html?auth_msg=session_expired");
            return;
        }

        if (!response.ok) {
            throw new Error(`Server returned HTTP ${response.status}`);
        }

        const data = await response.json();
        currentSummaryData = data;

        // Server-side RBAC validation: If user is an admin, immediately redirect to admin console
        if (data && data.user && data.user.is_admin) {
            try {
                localStorage.setItem("isAdmin", "true");
                localStorage.setItem("userRole", "Admin");
                sessionStorage.setItem("isAdmin", "true");
                sessionStorage.setItem("userRole", "Admin");
            } catch (e) {}
            window.location.replace("/app/admin_dashboard.html");
            return;
        }

        if (loadingElem) loadingElem.style.display = "none";

        if (!data || data.total_interviews === 0) {
            // 10. EMPTY STATE
            if (emptyElem) emptyElem.style.display = "block";
            if (dataContainer) dataContainer.style.display = "none";
            updateUserGreeting(data ? data.user : null);
            return;
        }

        // Display Data Container
        if (emptyElem) emptyElem.style.display = "none";
        if (dataContainer) dataContainer.style.display = "block";

        updateUserGreeting(data.user);
        renderTopStatistics(data);
        renderProgressSummary(data.progress_comparison, data.total_interviews);
        renderProgressChart(data.score_progression || data.score_history);
        renderLatestInterview(data.latest_interview);
        renderSkillPerformance(data.skill_performance);
        renderRolePerformance(data.role_performance);
        renderStrengthsAndImprovements(data.strengths, data.improvements);
        renderAchievements(data.achievements);
        renderInterviewHistory(data.history);

    } catch (err) {
        console.error("[Dashboard] Error loading summary:", err);
        // During background refresh, gracefully retain existing rendered data without flashing error boxes
        if (!isBackgroundRefresh && loadingElem && (!currentSummaryData || !dataContainer || dataContainer.style.display === "none")) {
            loadingElem.innerHTML = `
                <div style="background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; padding: 20px; border-radius: 12px; max-width: 500px; margin: 0 auto;">
                    <i class="fas fa-circle-exclamation fa-2x"></i>
                    <h3 style="margin-top: 10px; font-size: 16px;">Unable to load dashboard data</h3>
                    <p style="font-size: 13px; margin-top: 6px;">Please check your connection and refresh the page.</p>
                    <button onclick="location.reload()" style="margin-top: 12px; padding: 8px 18px; background: #dc2626; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
                        Retry
                    </button>
                </div>
            `;
        }
    }
}

window.fetchDashboardSummary = fetchDashboardSummary;

// -------------------------------------------------------------
// Greeting & User Profile Details
// -------------------------------------------------------------
function updateUserGreeting(user) {
    const greeting = document.getElementById("greeting");
    const avatar = document.getElementById("userAvatar");

    const hour = new Date().getHours();
    let timeGreeting = "Welcome Back 👋";
    if (hour < 12) {
        timeGreeting = "Good Morning 👋";
    } else if (hour < 17) {
        timeGreeting = "Good Afternoon ☀️";
    } else {
        timeGreeting = "Good Evening 🌙";
    }

    const userName = (user && user.name) ? user.name : (
        localStorage.getItem("userName") || (
            (localStorage.getItem("userEmail") || sessionStorage.getItem("userEmail") || "").split("@")[0]
        )
    );

    if (userName && greeting) {
        const cleanName = userName.charAt(0).toUpperCase() + userName.slice(1);
        greeting.innerHTML = `${timeGreeting} <span style="font-weight: 500; color: #475569;">(${cleanName})</span>`;
    } else if (greeting) {
        greeting.innerHTML = timeGreeting;
    }

    if (avatar) {
        const displayLetter = userName ? userName.substring(0, 2).toUpperCase() : "CA";
        avatar.textContent = displayLetter;
        avatar.onclick = () => { window.location.href = "profile.html"; };
    }

    // Role check for admin link
    const userRole = localStorage.getItem("userRole") || sessionStorage.getItem("userRole");
    const adminLink = document.getElementById("sidebarAdminLink");
    if (adminLink && (userRole === "admin" || (user && user.is_admin))) {
        adminLink.style.display = "flex";
    }
}

// -------------------------------------------------------------
// 1. TOP STATISTICS CARDS
// -------------------------------------------------------------
function renderTopStatistics(data) {
    const totalElem = document.getElementById("statTotalInterviews");
    const avgElem = document.getElementById("statAverageScore");
    const bestElem = document.getElementById("statBestScore");
    const latestElem = document.getElementById("statLatestScore");
    const monthlyElem = document.getElementById("statMonthlyInterviews");

    if (totalElem) totalElem.textContent = data.total_interviews || "0";
    if (avgElem) avgElem.textContent = `${data.average_score || 0}%`;
    if (bestElem) bestElem.textContent = `${data.best_score || 0}%`;
    if (latestElem) latestElem.textContent = `${data.latest_score || 0}%`;
    if (monthlyElem) monthlyElem.textContent = data.monthly_interviews || "0";
}

// -------------------------------------------------------------
// 5. PROGRESS SUMMARY BANNER
// -------------------------------------------------------------
function renderProgressSummary(comp, totalInterviews) {
    const badge = document.getElementById("summaryTrendBadge");
    const badgeText = document.getElementById("summaryTrendText");
    const titleText = document.getElementById("summaryTitleText");
    const detailText = document.getElementById("summaryDetailText");

    if (!comp) return;

    if (badge && badgeText) {
        if (comp.improvement_pct > 0) {
            badge.className = "progress-trend-badge positive";
            badge.innerHTML = `<i class="fas fa-arrow-trend-up"></i> Improvement: +${comp.improvement_pct}%`;
        } else if (comp.improvement_pct < 0) {
            badge.className = "progress-trend-badge";
            badge.innerHTML = `<i class="fas fa-arrow-trend-down"></i> Shift: ${comp.improvement_pct}%`;
        } else {
            badge.className = "progress-trend-badge neutral";
            badge.innerHTML = `<i class="fas fa-minus"></i> Steady Performance`;
        }
    }

    if (titleText) {
        titleText.textContent = comp.text || "Your performance is tracked across every mock interview.";
    }

    if (detailText) {
        if (totalInterviews >= 5) {
            detailText.textContent = "Great consistency! Review your strengths and targeted areas to improve below.";
        } else if (totalInterviews >= 2) {
            detailText.textContent = "Continue practicing multiple roles to broaden your technical interview readiness.";
        } else {
            detailText.textContent = "First mock interview completed! Practice regularly to observe your upward score trajectory.";
        }
    }
}

// -------------------------------------------------------------
// 2. OVERALL PROGRESS CHART (Chronological Line Chart)
// -------------------------------------------------------------
function renderProgressChart(history) {
    const canvas = document.getElementById("progressChart");
    if (!canvas) return;

    if (!history || history.length === 0) {
        if (progressChartInstance) {
            progressChartInstance.destroy();
            progressChartInstance = null;
        }
        return;
    }

    const labels = history.map((h, i) => `Interview ${i + 1}`);
    const scores = history.map(h => h.score);
    const roles = history.map(h => h.role);
    const dates = history.map(h => h.date);

    // If Chart.js library is loaded
    if (typeof Chart !== "undefined") {
        if (progressChartInstance) {
            progressChartInstance.destroy();
            progressChartInstance = null;
        }

        const ctx = canvas.getContext("2d");
        const gradient = ctx.createLinearGradient(0, 0, 0, 260);
        gradient.addColorStop(0, "rgba(37, 99, 235, 0.35)");
        gradient.addColorStop(1, "rgba(37, 99, 235, 0.0)");

        progressChartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [{
                    label: "Overall Score (%)",
                    data: scores,
                    borderColor: "#2563eb",
                    borderWidth: 3,
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: "#ffffff",
                    pointBorderColor: "#2563eb",
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    pointHoverBackgroundColor: "#2563eb",
                    pointHoverBorderColor: "#ffffff"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: "#0f172a",
                        titleColor: "#ffffff",
                        bodyColor: "#e2e8f0",
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            title: function(items) {
                                const idx = items[0].dataIndex;
                                return `Interview ${idx + 1} (${roles[idx] || "General"})`;
                            },
                            label: function(item) {
                                const idx = item.dataIndex;
                                return ` Score: ${item.raw}%  •  Date: ${dates[idx] || ""}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        min: 0,
                        max: 100,
                        ticks: {
                            stepSize: 20,
                            callback: function(val) { return val + "%"; },
                            font: { family: "Poppins", size: 11 },
                            color: "#64748b"
                        },
                        grid: {
                            color: "#f1f5f9"
                        }
                    },
                    x: {
                        ticks: {
                            autoSkip: true,
                            maxTicksLimit: 20,
                            font: { family: "Poppins", size: 11 },
                            color: "#64748b"
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    } else {
        // Fallback Canvas drawing if Chart.js is not present
        drawCanvasFallbackLineChart(canvas, history);
    }
}

function drawCanvasFallbackLineChart(canvas, history) {
    const ctx = canvas.getContext("2d");
    const width = canvas.width = canvas.parentElement.clientWidth || 600;
    const height = canvas.height = 280;

    ctx.clearRect(0, 0, width, height);

    const padLeft = 45;
    const padRight = 25;
    const padTop = 25;
    const padBottom = 35;
    const chartW = width - padLeft - padRight;
    const chartH = height - padTop - padBottom;

    // Draw horizontal grid lines
    ctx.strokeStyle = "#f1f5f9";
    ctx.lineWidth = 1;
    ctx.fillStyle = "#64748b";
    ctx.font = "11px Poppins, sans-serif";

    for (let pct = 0; pct <= 100; pct += 25) {
        const y = padTop + chartH - (pct / 100) * chartH;
        ctx.beginPath();
        ctx.moveTo(padLeft, y);
        ctx.lineTo(width - padRight, y);
        ctx.stroke();
        ctx.fillText(pct + "%", 10, y + 4);
    }

    if (history.length === 0) return;

    // Calculate points
    const stepX = history.length > 1 ? chartW / (history.length - 1) : chartW / 2;
    const points = history.map((item, i) => {
        const x = (history.length > 1) ? padLeft + i * stepX : padLeft + chartW / 2;
        const y = padTop + chartH - (item.score / 100) * chartH;
        return { x, y, score: item.score, role: item.role };
    });

    // Draw line
    ctx.beginPath();
    ctx.strokeStyle = "#2563eb";
    ctx.lineWidth = 3;
    points.forEach((pt, i) => {
        if (i === 0) ctx.moveTo(pt.x, pt.y);
        else ctx.lineTo(pt.x, pt.y);
    });
    ctx.stroke();

    // Draw points & labels
    points.forEach((pt, i) => {
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 5, 0, Math.PI * 2);
        ctx.fillStyle = "#ffffff";
        ctx.fill();
        ctx.strokeStyle = "#2563eb";
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.fillStyle = "#334155";
        ctx.fillText(`${pt.score}%`, pt.x - 12, pt.y - 10);
        ctx.fillText(`Int ${i + 1}`, pt.x - 14, height - 10);
    });
}

// -------------------------------------------------------------
// 8. LATEST INTERVIEW CARD
// -------------------------------------------------------------
function renderLatestInterview(latest) {
    const cardBody = document.getElementById("latestCardBody");
    if (!cardBody) return;

    if (!latest) {
        cardBody.innerHTML = `<p style="color: #64748b; font-style: italic;">No interview data available.</p>`;
        return;
    }

    const isLatestTerm = (latest.status || "").toLowerCase() === "terminated";
    const latestScoreText = (!isLatestTerm && latest.overall_score !== null && latest.overall_score !== undefined) ? `${latest.overall_score}%` : "--";

    cardBody.innerHTML = `
        <div class="latest-role-header">
            <span class="latest-role-title">${latest.role}</span>
            <span class="latest-date"><i class="far fa-calendar-alt"></i> ${latest.date}</span>
        </div>

        <div class="latest-score-display">
            <span class="latest-score-value" style="color: ${isLatestTerm ? '#dc2626' : '#2563eb'};">${latestScoreText}</span>
            <span class="latest-score-label">Overall Score</span>
        </div>

        <div class="latest-meta-row">
            <span class="latest-meta-chip">
                <i class="fas fa-arrow-trend-up" style="color: #2563eb;"></i> ${latest.comparison}
            </span>
            <span class="latest-meta-chip">
                <i class="fas fa-circle-question" style="color: #64748b;"></i> ${latest.total_questions} Questions
            </span>
            <span class="latest-meta-chip">
                ${(latest.status || "").toLowerCase() === "terminated" ? '<i class="fas fa-triangle-exclamation" style="color: #dc2626;"></i> <span style="color: #dc2626; font-weight: 600;">Terminated</span>' : `<i class="fas fa-circle-check" style="color: #16a34a;"></i> ${latest.status}`}
            </span>
        </div>

        <button class="btn-full-report" onclick="window.location.href='${latest.report_url}'">
            <i class="fas fa-file-lines"></i> View Full Report
        </button>
    `;
}

// -------------------------------------------------------------
// 3. SKILL PERFORMANCE
// -------------------------------------------------------------
function renderSkillPerformance(skills) {
    const container = document.getElementById("skillsContainer");
    if (!container) return;

    if (!skills || skills.length === 0) {
        container.innerHTML = `<p class="skill-empty-note">Evaluation dimensions will appear after completing an interview.</p>`;
        return;
    }

    container.innerHTML = skills.map(sk => {
        const hasScore = (sk.score !== null && sk.score !== undefined && sk.available !== false);
        const scoreVal = hasScore ? sk.score : null;
        let colorClass = "mid";
        if (scoreVal >= 75) colorClass = "high";
        else if (scoreVal < 50) colorClass = "low";

        return `
            <div class="skill-item">
                <div class="skill-header">
                    <div class="skill-header-left">
                        <i class="fas ${sk.icon || 'fa-chart-pie'}"></i>
                        <span>${sk.label}</span>
                    </div>
                    <span class="skill-score-badge">
                        ${hasScore ? `${scoreVal}%` : '<span class="skill-empty-note">Not evaluated yet</span>'}
                    </span>
                </div>
                <div class="skill-bar-track">
                    <div class="skill-bar-fill ${colorClass}" style="width: ${hasScore ? scoreVal : 0}%;"></div>
                </div>
            </div>
        `;
    }).join("");
}

// -------------------------------------------------------------
// 7. ROLE-WISE PERFORMANCE
// -------------------------------------------------------------
function renderRolePerformance(roles) {
    const container = document.getElementById("rolesContainer");
    if (!container) return;

    if (!roles || roles.length === 0) {
        container.innerHTML = `<p class="skill-empty-note">Role performance statistics will populate after interviews.</p>`;
        return;
    }

    container.innerHTML = roles.map(r => `
        <div class="role-row">
            <div class="role-row-top">
                <span class="role-name">${r.role}</span>
                <span class="role-count-badge">${r.count} ${r.count === 1 ? 'Interview' : 'Interviews'}</span>
            </div>
            <div class="skill-bar-track" style="height: 6px;">
                <div class="skill-bar-fill mid" style="width: ${r.average_score}%;"></div>
            </div>
            <div class="role-stats-row">
                <span>Avg: <strong class="role-score-strong">${r.average_score}%</strong></span>
                <span>Best: <strong class="role-score-strong">${r.best_score}%</strong></span>
                <span>Latest: <strong class="role-score-strong">${r.latest_score}%</strong></span>
            </div>
        </div>
    `).join("");
}

// -------------------------------------------------------------
// 6. STRENGTHS & AREAS TO IMPROVE
// -------------------------------------------------------------
function renderStrengthsAndImprovements(strengths, improvements) {
    const strengthsList = document.getElementById("strengthsList");
    const improvementsList = document.getElementById("improvementsList");

    if (strengthsList) {
        if (!strengths || strengths.length === 0) {
            strengthsList.innerHTML = `<li class="feedback-empty-note">No evaluated strengths recorded yet. Complete an interview to generate AI feedback.</li>`;
        } else {
            strengthsList.innerHTML = strengths.map(s => `
                <li class="feedback-item">
                    <i class="fas fa-circle-check"></i>
                    <span>${s}</span>
                </li>
            `).join("");
        }
    }

    if (improvementsList) {
        if (!improvements || improvements.length === 0) {
            improvementsList.innerHTML = `<li class="feedback-empty-note">No priority improvement areas recorded yet. Complete an interview to generate recommendations.</li>`;
        } else {
            improvementsList.innerHTML = improvements.map(imp => `
                <li class="feedback-item">
                    <i class="fas fa-bullseye"></i>
                    <span>${imp}</span>
                </li>
            `).join("");
        }
    }
}

// -------------------------------------------------------------
// 9. GOALS / ACHIEVEMENTS
// -------------------------------------------------------------
function renderAchievements(achievements) {
    const grid = document.getElementById("achievementsGrid");
    if (!grid) return;

    if (!achievements || achievements.length === 0) {
        grid.innerHTML = `<p class="skill-empty-note">Goals and milestones will appear as you practice.</p>`;
        return;
    }

    grid.innerHTML = achievements.map(ach => `
        <div class="achievement-card ${ach.unlocked ? 'unlocked' : ''}">
            <div class="achievement-card-top">
                <div class="achievement-icon-circle">
                    <i class="fas ${ach.icon || 'fa-award'}"></i>
                </div>
                <span class="achievement-status-badge">
                    ${ach.unlocked ? '<i class="fas fa-check"></i> Unlocked' : 'In Progress'}
                </span>
            </div>
            <div class="achievement-title">${ach.title}</div>
            <div class="achievement-desc">${ach.desc}</div>
            ${!ach.unlocked ? `
                <div class="skill-bar-track" style="height: 5px; margin-top: 4px;">
                    <div class="skill-bar-fill mid" style="width: ${Math.min(100, Math.round((ach.progress / ach.target) * 100))}%;"></div>
                </div>
            ` : ''}
        </div>
    `).join("");
}

// -------------------------------------------------------------
// 4. INTERVIEW HISTORY TABLE & SEARCH FILTER
// -------------------------------------------------------------
function renderInterviewHistory(history) {
    const tableBody = document.getElementById("historyTableBody");
    const countBadge = document.getElementById("historyCountBadge");

    if (countBadge) {
        countBadge.textContent = `${history ? history.length : 0} ${history && history.length === 1 ? 'Interview' : 'Interviews'}`;
    }

    if (!tableBody) return;

    if (!history || history.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; color: #64748b; padding: 30px; font-style: italic;">
                    No interview history recorded.
                </td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = history.map(item => {
        const isTerm = (item.status || '').toLowerCase() === 'terminated';
        const scoreDisplay = (item.overall_score !== null && item.overall_score !== undefined)
            ? `<span style="font-size: 15px; font-weight: 700; color: #2563eb;">${item.overall_score}%</span>`
            : `<span style="font-size: 14px; font-weight: 600; color: #64748b;">--</span>`;
        const perfClass = isTerm ? 'perf-terminated' : (item.performance_class || 'perf-good');
        const perfLabel = isTerm ? 'Terminated' : (item.performance_label || 'Completed');
        const perfStyle = isTerm ? 'background: #fee2e2; color: #dc2626; border: 1px solid #fecaca;' : '';

        return `
        <tr data-role="${(item.role || '').toLowerCase()}" data-date="${(item.date || '').toLowerCase()}">
            <td style="font-weight: 500; color: #334155;">
                <i class="far fa-calendar" style="color: #64748b; margin-right: 6px;"></i> ${item.date}
            </td>
            <td>
                <strong style="color: #0f172a;">${item.role}</strong>
                <div style="font-size: 11.5px; color: #64748b;">${item.total_questions} Questions</div>
            </td>
            <td>
                ${scoreDisplay}
            </td>
            <td>
                <span class="perf-badge ${perfClass}" ${perfStyle ? `style="${perfStyle}"` : ''}>
                    ${perfLabel}
                </span>
            </td>
            <td>
                <span style="color: ${isTerm ? '#dc2626' : '#16a34a'}; font-weight: 500; font-size: 13px;">
                    <i class="${isTerm ? 'fas fa-triangle-exclamation' : 'fas fa-circle-check'}"></i> ${isTerm ? 'Terminated' : item.status}
                </span>
            </td>
            <td style="text-align: right;">
                <button class="btn-view-report" onclick="window.location.href='${item.report_url}'">
                    <i class="fas fa-file-lines"></i> View Report
                </button>
            </td>
        </tr>
    `;}).join("");

    // Initialize search filter
    initHistorySearchFilter();
}

function initHistorySearchFilter() {
    const searchInput = document.getElementById("historySearchInput");
    if (!searchInput) return;

    searchInput.addEventListener("input", function() {
        const query = this.value.toLowerCase().trim();
        const rows = document.querySelectorAll("#historyTableBody tr");

        rows.forEach(row => {
            const role = row.getAttribute("data-role") || "";
            const date = row.getAttribute("data-date") || "";
            if (role.includes(query) || date.includes(query) || query === "") {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        });
    });
}

// -------------------------------------------------------------
// Sidebar & Logout Handling
// -------------------------------------------------------------
function handleDashboardLogout() {
    const token = localStorage.getItem("sessionToken") || sessionStorage.getItem("sessionToken");
    if (token) {
        fetch("/api/auth/logout", {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` }
        }).catch(err => console.warn("Logout error:", err));
    }
    try {
        localStorage.clear();
        sessionStorage.clear();
    } catch (e) {}
    window.location.href = "login.html";
}

window.handleDashboardLogout = handleDashboardLogout;

function initSidebarEvents() {
    const menuBtn = document.querySelector(".menu-btn");
    const sidebar = document.querySelector(".sidebar");
    const mainContent = document.querySelector(".main-content");

    if (menuBtn && sidebar && mainContent) {
        menuBtn.addEventListener("click", () => {
            sidebar.classList.toggle("collapsed");
            mainContent.classList.toggle("expanded");
        });
    }

    const notification = document.querySelector(".notification");
    if (notification) {
        notification.addEventListener("click", () => {
            alert("No new notifications at this time.");
        });
    }
}

// -------------------------------------------------------------
// Auto-Refresh & Visibility Lifecycle
// -------------------------------------------------------------
let dashboardRefreshInterval = null;

function setupDashboardAutoRefresh() {
    // 1. Refresh when browser tab becomes visible again
    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") {
            fetchDashboardSummary(true);
        }
    });

    // 2. Refresh when window gains focus
    window.addEventListener("focus", () => {
        fetchDashboardSummary(true);
    });

    // 3. Lightweight background polling every 30 seconds
    if (dashboardRefreshInterval) {
        clearInterval(dashboardRefreshInterval);
    }
    dashboardRefreshInterval = setInterval(() => {
        if (document.visibilityState === "visible") {
            fetchDashboardSummary(true);
        }
    }, 30000);

    // 4. Clean up polling interval when navigating away
    window.addEventListener("pagehide", () => {
        if (dashboardRefreshInterval) {
            clearInterval(dashboardRefreshInterval);
            dashboardRefreshInterval = null;
        }
    });
    window.addEventListener("beforeunload", () => {
        if (dashboardRefreshInterval) {
            clearInterval(dashboardRefreshInterval);
            dashboardRefreshInterval = null;
        }
    });
}

// -------------------------------------------------------------
// DOM Ready Lifecycle
// -------------------------------------------------------------
function initDashboard() {
    if (!checkCandidateAuth()) return;
    initSidebarEvents();
    fetchDashboardSummary(false);
    setupDashboardAutoRefresh();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDashboard);
} else {
    initDashboard();
}