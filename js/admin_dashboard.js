// =========================================================
// SUPER ADMIN CONSOLE CONTROLLER
// Multi-Model AI Interview Evaluation System
// =========================================================

let currentAdminUser = null;
let chartsInstances = {};
let allUsersCache = [];
let allInterviewsCache = [];
let allQuestionsCache = [];
let allReportsCache = [];
let allAuditCache = [];

// =========================================================
// UTILITIES & HELPERS
// =========================================================

function getAuthToken() {
    return localStorage.getItem("sessionToken") || sessionStorage.getItem("sessionToken");
}

function getAuthHeaders() {
    const token = getAuthToken();
    return {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
    };
}

function showToast(message, type = "info") {
    const toast = document.getElementById("adminToast");
    if (!toast) return;

    let icon = "fa-circle-info";
    let bg = "#0f172a";

    if (type === "success") {
        icon = "fa-circle-check";
        bg = "#15803d";
    } else if (type === "error") {
        icon = "fa-circle-xmark";
        bg = "#b91c1c";
    } else if (type === "warning") {
        icon = "fa-triangle-exclamation";
        bg = "#b45309";
    }

    toast.innerHTML = `<i class="fas ${icon}" style="margin-right: 8px;"></i> ${escapeHtml(message)}`;
    toast.style.background = bg;
    toast.style.display = "block";

    clearTimeout(toast._timeout);
    toast._timeout = setTimeout(() => {
        toast.style.display = "none";
    }, 4000);
}

function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function toggleSidebar() {
    const sidebar = document.getElementById("adminSidebar");
    if (sidebar) sidebar.classList.toggle("open");
}

// =========================================================
// AUTHENTICATION GUARD
// =========================================================

async function verifyAdminAuth() {
    const token = getAuthToken();
    if (!token) {
        window.location.replace("/app/login.html?redirect=admin_dashboard.html&auth_msg=admin_required");
        return false;
    }

    try {
        let res = await fetch("/api/auth/me", {
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (res.status === 401) {
            try {
                localStorage.clear();
                sessionStorage.clear();
            } catch (_) {}
            window.location.replace("/app/login.html?redirect=admin_dashboard.html&auth_msg=session_expired");
            return false;
        }

        if (!res.ok) {
            res = await fetch("/api/dashboard/profile", {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!res.ok) {
                throw new Error(`Authentication check failed with HTTP ${res.status}`);
            }
        }

        const data = await res.json();
        currentAdminUser = data.user || data;

        if (!currentAdminUser || !currentAdminUser.is_admin) {
            console.warn("[Admin Guard] Candidate user attempted admin console access:", currentAdminUser);
            try {
                localStorage.setItem("isAdmin", "false");
                localStorage.setItem("userRole", "User");
                sessionStorage.setItem("isAdmin", "false");
                sessionStorage.setItem("userRole", "User");
            } catch (_) {}
            window.location.replace("/app/dashboard.html?auth_msg=admin_denied");
            return false;
        }

        // Confirmed as admin
        try {
            localStorage.setItem("isAdmin", "true");
            localStorage.setItem("userRole", "Admin");
            sessionStorage.setItem("isAdmin", "true");
            sessionStorage.setItem("userRole", "Admin");
        } catch (_) {}

        // Dismiss security overlay
        const overlay = document.getElementById("adminAuthOverlay");
        if (overlay) {
            overlay.style.display = "none";
        }

        const navNameElem = document.getElementById("navAdminName");
        if (navNameElem) {
            navNameElem.textContent = currentAdminUser.name || currentAdminUser.email;
        }

        return true;
    } catch (err) {
        console.error("[Admin Auth Error]", err);
        showToast("Error verifying admin credentials. Reconnecting...", "error");
        return false;
    }
}

async function handleAdminLogout() {
    const token = getAuthToken();
    if (token) {
        try {
            await fetch("/api/auth/logout", {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` }
            });
        } catch (_) {}
    }
    try {
        localStorage.clear();
        sessionStorage.clear();
    } catch (_) {}
    window.location.replace("/app/login.html?auth_msg=logged_out");
}

// =========================================================
// NAVIGATION & TAB SWITCHING
// =========================================================

function switchAdminTab(tabName) {
    // 1. Update Sidebar Links
    document.querySelectorAll(".sidebar-link").forEach(link => {
        if (link.getAttribute("data-tab") === tabName) {
            link.classList.add("active");
        } else {
            link.classList.remove("active");
        }
    });

    // 2. Hide all tab panes, show targeted pane
    document.querySelectorAll(".admin-tab-pane").forEach(pane => {
        pane.classList.remove("active");
    });

    const targetPane = document.getElementById(`pane-${tabName}`);
    if (targetPane) {
        targetPane.classList.add("active");
    }

    // 3. Update Breadcrumb
    const breadcrumb = document.getElementById("breadcrumbActiveTitle");
    if (breadcrumb) {
        const titleMap = {
            "command-center": "Command Center",
            "analytics": "Analytics Center",
            "users": "User Management",
            "interviews": "Interviews",
            "evaluations": "AI Evaluation Center",
            "questions": "Question Bank",
            "roles": "Interview Roles",
            "recordings": "Recordings & Media",
            "reports": "Report Center",
            "security": "Security Center",
            "audit-logs": "Audit Logs",
            "system-health": "System Health",
            "settings": "System Settings"
        };
        breadcrumb.textContent = titleMap[tabName] || "Console";
    }

    // Close mobile sidebar if open
    const sidebar = document.getElementById("adminSidebar");
    if (sidebar && sidebar.classList.contains("open")) {
        sidebar.classList.remove("open");
    }

    // 4. Trigger on-demand loading for tab
    if (tabName === "command-center") loadDashboardMetrics();
    else if (tabName === "users") loadUsersTable();
    else if (tabName === "interviews") loadInterviewsTable();
    else if (tabName === "questions") loadQuestionsTable();
    else if (tabName === "roles") loadRolesTable();
    else if (tabName === "recordings") loadRecordingsTable();
    else if (tabName === "reports") loadReportsTable();
    else if (tabName === "security") loadSecurityData();
    else if (tabName === "analytics") loadAnalyticsData();
    else if (tabName === "audit-logs") loadAuditLogsTable();
    else if (tabName === "system-health") loadSystemHealth();
    else if (tabName === "settings") loadSettings();
}

// =========================================================
// TAB 1: COMMAND CENTER (METRICS & CHARTS)
// =========================================================

async function loadDashboardMetrics() {
    try {
        const res = await fetch("/api/admin/dashboard", { headers: getAuthHeaders() });
        if (!res.ok) throw new Error("Failed to fetch dashboard metrics");
        const data = await res.json();
        const cards = data.cards || {};

        // Update 12 metric cards
        document.getElementById("statTotalCandidates").textContent = cards.total_candidates ?? "--";
        document.getElementById("statActiveCandidates").textContent = cards.active_candidates ?? "--";
        document.getElementById("statInactiveCandidates").textContent = cards.inactive_candidates ?? "--";
        document.getElementById("statTotalAdmins").textContent = cards.total_admins ?? "--";

        document.getElementById("statTotalInterviews").textContent = cards.total_interviews ?? "--";
        document.getElementById("statCompletedInterviews").textContent = cards.completed_interviews ?? "--";
        document.getElementById("statTerminatedInterviews").textContent = cards.terminated_interviews ?? "--";
        document.getElementById("statSecurityViolations").textContent = cards.security_violations ?? "--";
        const sideBadge = document.getElementById("sidebarViolationsBadge");
        if (sideBadge) sideBadge.textContent = cards.security_violations ?? "0";

        document.getElementById("statAverageScore").textContent = (cards.average_score !== undefined) ? `${cards.average_score}%` : "--%";
        document.getElementById("statHighestScore").textContent = (cards.highest_score !== undefined) ? `${cards.highest_score}%` : "--%";
        document.getElementById("statInterviewsToday").textContent = cards.interviews_today ?? "--";
        document.getElementById("statInterviewsThisWeek").textContent = cards.interviews_this_week ?? "--";

        // Render Recent Sessions table
        renderRecentSessions(data.recent_interviews || []);

        // Render 4 interactive charts
        if (data.charts) {
            renderDashboardCharts(data.charts);
        }
    } catch (err) {
        console.error("[Dashboard Metrics Error]", err);
        showToast("Error loading command center metrics", "error");
    }
}

function renderRecentSessions(interviews) {
    const tbody = document.getElementById("recentSessionsTableBody");
    if (!tbody) return;

    if (!interviews || interviews.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 24px; color: #64748b;">No recent evaluation sessions recorded.</td></tr>`;
        return;
    }

    tbody.innerHTML = interviews.map(i => {
        const isTerm = String(i.status).toLowerCase() === "terminated";
        const statusBadge = isTerm
            ? `<span class="badge-status terminated"><i class="fas fa-ban"></i> Terminated</span>`
            : `<span class="badge-status completed"><i class="fas fa-check"></i> Completed</span>`;

        const scoreDisplay = (isTerm || i.overall_score === null)
            ? `<span style="color: #94a3b8; font-weight: 600;">--</span>`
            : `<strong>${i.overall_score}%</strong>`;

        return `
            <tr>
                <td><strong>#${i.id}</strong></td>
                <td><strong>${escapeHtml(i.candidate_name)}</strong></td>
                <td style="color: #64748b;">${escapeHtml(i.candidate_email)}</td>
                <td><span class="badge-role candidate">${escapeHtml(i.role)}</span></td>
                <td>${scoreDisplay}</td>
                <td>${statusBadge}</td>
                <td style="color: #64748b; font-size: 11.5px;">${escapeHtml(i.created_at || "N/A")}</td>
                <td style="text-align: right;">
                    <button class="btn-action primary" onclick="downloadInterviewReport(${i.id})" title="Download PDF Report">
                        <i class="fas fa-file-pdf"></i>
                    </button>
                    <a href="result.html?id=${i.id}" target="_blank" class="btn-action" title="View Result Page">
                        <i class="fas fa-arrow-up-right-from-square"></i>
                    </a>
                </td>
            </tr>
        `;
    }).join("");
}

function renderDashboardCharts(chartsData) {
    if (typeof Chart === "undefined") return;

    // Helper to safely destroy and re-create canvas
    function getCleanCtx(canvasId) {
        if (chartsInstances[canvasId]) {
            chartsInstances[canvasId].destroy();
        }
        const canvas = document.getElementById(canvasId);
        return canvas ? canvas.getContext("2d") : null;
    }

    // Chart 1: Interview Activity Trend
    const ctx1 = getCleanCtx("chartInterviewActivity");
    if (ctx1 && chartsData.interview_activity) {
        chartsInstances["chartInterviewActivity"] = new Chart(ctx1, {
            type: "line",
            data: {
                labels: chartsData.interview_activity.labels || [],
                datasets: [{
                    label: "Interviews Conducted",
                    data: chartsData.interview_activity.data || [],
                    borderColor: "#2563eb",
                    backgroundColor: "rgba(37, 99, 235, 0.1)",
                    fill: true,
                    tension: 0.35,
                    borderWidth: 2,
                    pointBackgroundColor: "#2563eb"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, ticks: { precision: 0 } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // Chart 2: Completion vs Termination
    const ctx2 = getCleanCtx("chartCompletionRatio");
    if (ctx2 && chartsData.completed_vs_terminated) {
        const comp = chartsData.completed_vs_terminated.completed || 0;
        const term = chartsData.completed_vs_terminated.terminated || 0;
        chartsInstances["chartCompletionRatio"] = new Chart(ctx2, {
            type: "doughnut",
            data: {
                labels: ["Completed", "Terminated"],
                datasets: [{
                    data: [comp, term],
                    backgroundColor: ["#16a34a", "#dc2626"],
                    borderWidth: 2,
                    borderColor: "#ffffff"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom" }
                },
                cutout: "65%"
            }
        });
    }

    // Chart 3: Score Distribution
    const ctx3 = getCleanCtx("chartScoreDistribution");
    if (ctx3 && chartsData.score_distribution) {
        const dist = chartsData.score_distribution;
        chartsInstances["chartScoreDistribution"] = new Chart(ctx3, {
            type: "bar",
            data: {
                labels: Object.keys(dist),
                datasets: [{
                    label: "Candidates in Cohort",
                    data: Object.values(dist),
                    backgroundColor: ["#ef4444", "#f59e0b", "#3b82f6", "#10b981"],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, ticks: { precision: 0 } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // Chart 4: Average Score by Role
    const ctx4 = getCleanCtx("chartRoleScores");
    if (ctx4 && chartsData.role_scores) {
        const roles = Object.keys(chartsData.role_scores);
        const scores = Object.values(chartsData.role_scores);
        chartsInstances["chartRoleScores"] = new Chart(ctx4, {
            type: "bar",
            data: {
                labels: roles,
                datasets: [{
                    label: "Average Score (%)",
                    data: scores,
                    backgroundColor: "#0284c7",
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { beginAtZero: true, max: 100 },
                    y: { grid: { display: false } }
                }
            }
        });
    }
}

// =========================================================
// TAB 2: USER MANAGEMENT
// =========================================================

let userFilterTimeout = null;
function debounceFilterUsers() {
    clearTimeout(userFilterTimeout);
    userFilterTimeout = setTimeout(loadUsersTable, 250);
}

async function loadUsersTable() {
    const tbody = document.getElementById("usersTableBody");
    if (!tbody) return;

    const search = (document.getElementById("usersSearchInput")?.value || "").trim();
    const role = (document.getElementById("userRoleFilter")?.value || "").trim();
    const accountType = (document.getElementById("userAccountTypeFilter")?.value || "").trim();
    const status = (document.getElementById("userStatusFilter")?.value || "").trim();

    const query = new URLSearchParams();
    if (search) query.append("search", search);
    if (role) query.append("role", role);
    if (accountType) query.append("account_type", accountType);
    if (status) query.append("status", status);

    try {
        const res = await fetch(`/api/admin/users?${query.toString()}`, { headers: getAuthHeaders() });
        if (!res.ok) throw new Error("Failed to load users");
        const data = await res.json();
        allUsersCache = data.users || [];

        if (allUsersCache.length === 0) {
            tbody.innerHTML = `<tr><td colspan="11" style="text-align: center; padding: 30px; color: #64748b;">No users match the selected filters.</td></tr>`;
            return;
        }

        tbody.innerHTML = allUsersCache.map(u => {
            const isSelf = currentAdminUser && currentAdminUser.id === u.id;
            const statusBadge = u.is_active
                ? `<span class="badge-status active"><i class="fas fa-circle-check"></i> Active</span>`
                : `<span class="badge-status inactive"><i class="fas fa-circle-xmark"></i> Inactive</span>`;

            const toggleStatusBtn = isSelf ? "" : `
                <button class="btn-action ${u.is_active ? 'danger' : 'success'}" onclick="toggleUserActive(${u.id}, ${u.is_active})" title="${u.is_active ? 'Deactivate Account' : 'Activate Account'}">
                    <i class="fas ${u.is_active ? 'fa-user-slash' : 'fa-user-check'}"></i>
                </button>
            `;

            const deleteBtn = isSelf ? "" : `
                <button class="btn-action danger" onclick="openDeleteUserModal(${u.id}, '${escapeHtml(u.name)}', '${escapeHtml(u.email)}')" title="Delete User">
                    <i class="fas fa-trash-can"></i>
                </button>
            `;

            return `
                <tr>
                    <td><strong>#${u.id}</strong></td>
                    <td><strong>${escapeHtml(u.name)}</strong></td>
                    <td style="color: #64748b;">${escapeHtml(u.email)}</td>
                    <td><span class="badge-role candidate">${escapeHtml(u.preferred_role)}</span></td>
                    <td>
                        <span class="badge-role ${u.is_admin ? 'admin' : 'candidate'}">
                            ${u.is_admin ? 'ADMIN' : 'USER'}
                        </span>
                    </td>
                    <td>${statusBadge}</td>
                    <td><strong>${u.interview_count}</strong></td>
                    <td>${u.average_score !== null ? `<strong>${u.average_score}%</strong>` : '<span style="color:#94a3b8;">--</span>'}</td>
                    <td style="color: #64748b; font-size: 11.5px;">${escapeHtml(u.created_at)}</td>
                    <td style="color: #64748b; font-size: 11.5px;">${escapeHtml(u.last_interview_at)}</td>
                    <td style="text-align: right;">
                        <button class="btn-action primary" onclick="viewUserInterviews(${u.id}, '${escapeHtml(u.name)}')" title="View Interview History">
                            <i class="fas fa-clock-rotate-left"></i>
                        </button>
                        <button class="btn-action" onclick="openEditUserModal(${u.id}, '${escapeHtml(u.name)}', '${escapeHtml(u.email)}', '${escapeHtml(u.preferred_role)}', ${u.is_admin})" title="Edit User">
                            <i class="fas fa-pen"></i>
                        </button>
                        <button class="btn-action" onclick="openResetPasswordModal(${u.id}, '${escapeHtml(u.name)}', '${escapeHtml(u.email)}')" title="Reset Password">
                            <i class="fas fa-key"></i>
                        </button>
                        ${toggleStatusBtn}
                        ${deleteBtn}
                    </td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        console.error("[Users Table Error]", err);
        tbody.innerHTML = `<tr><td colspan="11" style="text-align: center; padding: 30px; color: #dc2626;">Error loading users list.</td></tr>`;
    }
}

// User Action Modals
function openCreateUserModal() {
    document.getElementById("createUserForm").reset();
    document.getElementById("createUserModal").style.display = "flex";
}
function closeCreateUserModal() {
    document.getElementById("createUserModal").style.display = "none";
}

async function handleCreateUserSubmit(event) {
    event.preventDefault();
    const name = document.getElementById("createUserName").value.trim();
    const email = document.getElementById("createUserEmail").value.trim();
    const password = document.getElementById("createUserPassword").value;
    const preferred_role = document.getElementById("createUserRole").value;
    const is_admin = document.getElementById("createUserIsAdmin").checked;

    const btn = document.getElementById("btnSubmitCreateUser");
    btn.disabled = true;
    btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Creating...`;

    try {
        const res = await fetch("/api/admin/users", {
            method: "POST",
            headers: getAuthHeaders(),
            body: jsonPayload({ name, email, password, preferred_role, is_admin })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to create user");

        showToast("User account created successfully!", "success");
        closeCreateUserModal();
        loadUsersTable();
    } catch (err) {
        alert(err.message || "Failed to create user");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fas fa-plus"></i> Create User`;
    }
}

function openEditUserModal(userId, name, email, preferredRole, isAdmin) {
    document.getElementById("editUserId").value = userId;
    document.getElementById("editUserName").value = name;
    document.getElementById("editUserEmail").value = email;
    document.getElementById("editUserRole").value = preferredRole || "Python Developer";
    document.getElementById("editUserIsAdmin").checked = Boolean(isAdmin);
    document.getElementById("editUserModal").style.display = "flex";
}
function closeEditUserModal() {
    document.getElementById("editUserModal").style.display = "none";
}

async function handleSaveUserEdit(event) {
    event.preventDefault();
    const userId = document.getElementById("editUserId").value;
    const name = document.getElementById("editUserName").value.trim();
    const preferredRole = document.getElementById("editUserRole").value;
    const isAdmin = document.getElementById("editUserIsAdmin").checked;

    try {
        const res = await fetch(`/api/admin/users/${userId}`, {
            method: "PUT",
            headers: getAuthHeaders(),
            body: jsonPayload({ name, preferred_role: preferredRole, is_admin: isAdmin })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Update failed");

        showToast("User updated successfully", "success");
        closeEditUserModal();
        loadUsersTable();
    } catch (err) {
        alert(err.message || "Error updating user");
    }
}

async function toggleUserActive(userId, currentlyActive) {
    const newStatus = !currentlyActive;
    const actionLabel = newStatus ? "activate" : "deactivate";
    if (!confirm(`Are you sure you want to ${actionLabel} this user account?`)) return;

    try {
        const res = await fetch(`/api/admin/users/${userId}/status`, {
            method: "PATCH",
            headers: getAuthHeaders(),
            body: jsonPayload({ is_active: newStatus })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to update status");

        showToast(`User ${newStatus ? 'activated' : 'deactivated'} successfully!`, "success");
        loadUsersTable();
    } catch (err) {
        alert(err.message || "Error toggling status");
    }
}

function openResetPasswordModal(userId, name, email) {
    document.getElementById("resetUserId").value = userId;
    document.getElementById("resetUserMessage").textContent = `Resetting password for ${name} (${email}).`;
    document.getElementById("resetNewPassword").value = "";
    document.getElementById("resetPasswordModal").style.display = "flex";
}
function closeResetPasswordModal() {
    document.getElementById("resetPasswordModal").style.display = "none";
}

async function handleResetPasswordSubmit(event) {
    event.preventDefault();
    const userId = document.getElementById("resetUserId").value;
    const newPassword = document.getElementById("resetNewPassword").value;

    try {
        const res = await fetch(`/api/admin/users/${userId}/reset-password`, {
            method: "POST",
            headers: getAuthHeaders(),
            body: jsonPayload({ new_password: newPassword })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Reset failed");

        showToast("Password reset successfully!", "success");
        closeResetPasswordModal();
    } catch (err) {
        alert(err.message || "Failed to reset password");
    }
}

function openDeleteUserModal(userId, name, email) {
    document.getElementById("deleteUserId").value = userId;
    document.getElementById("deleteUserMessage").innerHTML = `Are you sure you want to delete user <strong>${escapeHtml(name)}</strong> (<code>${escapeHtml(email)}</code>)?`;
    document.getElementById("deleteUserModal").style.display = "flex";
}
function closeDeleteUserModal() {
    document.getElementById("deleteUserModal").style.display = "none";
}

async function handleConfirmDeleteUser() {
    const userId = document.getElementById("deleteUserId").value;
    const btn = document.getElementById("confirmDeleteBtn");
    btn.disabled = true;

    try {
        const res = await fetch(`/api/admin/users/${userId}`, {
            method: "DELETE",
            headers: getAuthHeaders()
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Delete failed");

        showToast("User deleted successfully. Past interview history preserved.", "success");
        closeDeleteUserModal();
        loadUsersTable();
    } catch (err) {
        alert(err.message || "Failed to delete user");
    } finally {
        btn.disabled = false;
    }
}

async function viewUserInterviews(userId, userName) {
    document.getElementById("modalUserTitle").textContent = `${userName}'s Interview History`;
    document.getElementById("modalUserSubtitle").textContent = `Candidate ID: #${userId}`;
    const tbody = document.getElementById("modalInterviewsBody");
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 20px;"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>`;
    document.getElementById("userInterviewsModal").style.display = "flex";

    try {
        const res = await fetch(`/api/admin/users/${userId}/interviews`, { headers: getAuthHeaders() });
        const data = await res.json();
        const list = data.interviews || [];

        if (list.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 20px; color: #64748b;">No interviews found for this candidate.</td></tr>`;
            return;
        }

        tbody.innerHTML = list.map(i => {
            const isTerm = String(i.status).toLowerCase() === "terminated";
            return `
                <tr>
                    <td><strong>#${i.id}</strong></td>
                    <td>${escapeHtml(i.role)}</td>
                    <td><strong>${isTerm ? '--' : (i.overall_score !== null ? i.overall_score + '%' : '--')}</strong></td>
                    <td>${isTerm ? '--' : (i.technical_score !== null ? i.technical_score + '%' : '--')}</td>
                    <td>${isTerm ? '--' : (i.communication_score !== null ? i.communication_score + '%' : '--')}</td>
                    <td>${isTerm ? '--' : (i.confidence_score !== null ? i.confidence_score + '%' : '--')}</td>
                    <td><span class="badge-status ${isTerm ? 'terminated' : 'completed'}">${escapeHtml(i.status)}</span></td>
                    <td style="font-size: 11px;">${i.created_at ? i.created_at.split('T')[0] : 'N/A'}</td>
                    <td style="text-align: right;">
                        <button class="btn-action primary" onclick="downloadInterviewReport(${i.id})"><i class="fas fa-file-pdf"></i></button>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 20px; color: #dc2626;">Error loading candidate history.</td></tr>`;
    }
}
function closeUserInterviewsModal() {
    document.getElementById("userInterviewsModal").style.display = "none";
}

// =========================================================
// TAB 3: INTERVIEW MANAGEMENT
// =========================================================

let intFilterTimeout = null;
function debounceFilterInterviews() {
    clearTimeout(intFilterTimeout);
    intFilterTimeout = setTimeout(loadInterviewsTable, 250);
}

async function loadInterviewsTable() {
    const tbody = document.getElementById("interviewsTableBody");
    if (!tbody) return;

    const search = (document.getElementById("interviewsSearchInput")?.value || "").trim();
    const role = (document.getElementById("interviewRoleFilter")?.value || "").trim();
    const status = (document.getElementById("interviewStatusFilter")?.value || "").trim();
    const violation = (document.getElementById("interviewViolationFilter")?.value || "").trim();

    const query = new URLSearchParams();
    if (search) query.append("search", search);
    if (role) query.append("role", role);
    if (status) query.append("status", status);
    if (violation) query.append("security_violation", violation);

    try {
        const res = await fetch(`/api/admin/interviews?${query.toString()}`, { headers: getAuthHeaders() });
        const data = await res.json();
        allInterviewsCache = data.interviews || [];

        if (allInterviewsCache.length === 0) {
            tbody.innerHTML = `<tr><td colspan="11" style="text-align: center; padding: 30px; color: #64748b;">No interviews match the criteria.</td></tr>`;
            return;
        }

        tbody.innerHTML = allInterviewsCache.map(i => {
            const isTerm = String(i.status).toLowerCase() === "terminated";
            const secBadge = (i.security_violation || i.tab_switch_count > 0)
                ? `<span class="badge-violation-yes"><i class="fas fa-triangle-exclamation"></i> YES (${i.tab_switch_count})</span>`
                : `<span class="badge-violation-no">NO</span>`;

            const scoreDisplay = (isTerm || i.overall_score === null)
                ? `<span style="color: #94a3b8; font-weight: 600;">--</span>`
                : `<strong>${i.overall_score}%</strong>`;

            const recBadge = i.recording_available
                ? `<span style="color: #16a34a; font-weight: 600;"><i class="fas fa-circle-play"></i> Ready</span>`
                : `<span style="color: #94a3b8;">None</span>`;

            return `
                <tr>
                    <td><strong>#${i.id}</strong></td>
                    <td><strong>${escapeHtml(i.candidate_name)}</strong></td>
                    <td style="color: #64748b;">${escapeHtml(i.candidate_email)}</td>
                    <td><span class="badge-role candidate">${escapeHtml(i.role)}</span></td>
                    <td style="font-size: 11.5px; color: #64748b;">${escapeHtml(i.created_at)}</td>
                    <td>${scoreDisplay}</td>
                    <td><span class="badge-status ${isTerm ? 'terminated' : 'completed'}">${escapeHtml(i.status)}</span></td>
                    <td><strong>${i.tab_switch_count}</strong></td>
                    <td>${secBadge}</td>
                    <td>${recBadge}</td>
                    <td style="text-align: right;">
                        <button class="btn-action primary" onclick="viewInterviewDetail(${i.id})" title="Inspect Details">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn-action" onclick="downloadInterviewReport(${i.id})" title="Download PDF Report">
                            <i class="fas fa-file-pdf"></i>
                        </button>
                        <a href="result.html?id=${i.id}" target="_blank" class="btn-action" title="View Web Result">
                            <i class="fas fa-arrow-up-right-from-square"></i>
                        </a>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="11" style="text-align: center; padding: 30px; color: #dc2626;">Error loading interviews.</td></tr>`;
    }
}

async function viewInterviewDetail(intId) {
    document.getElementById("intDetailTitle").textContent = `Interview Evaluation Details: #${intId}`;
    const body = document.getElementById("intDetailBody");
    body.innerHTML = `<div style="text-align: center; padding: 30px;"><i class="fas fa-spinner fa-spin"></i> Loading interview evaluation...</div>`;
    document.getElementById("interviewDetailModal").style.display = "flex";

    try {
        const res = await fetch(`/api/admin/interviews/${intId}`, { headers: getAuthHeaders() });
        const data = await res.json();
        const intItem = data.interview || {};
        const answers = data.answers || [];
        const isTerm = String(intItem.status).toLowerCase() === "terminated";

        body.innerHTML = `
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                    <div><strong>Role:</strong> ${escapeHtml(intItem.role)}</div>
                    <div><strong>Status:</strong> <span class="badge-status ${isTerm ? 'terminated' : 'completed'}">${escapeHtml(intItem.status)}</span></div>
                    <div><strong>Overall Score:</strong> ${isTerm ? '--' : (intItem.overall_score || '--') + '%'}</div>
                    <div><strong>Security Violations:</strong> ${intItem.tab_switch_count || 0}</div>
                </div>
                ${isTerm ? `<div style="color: #dc2626; font-size: 12px; margin-top: 8px;"><strong>Termination Notice:</strong> ${escapeHtml(intItem.terminated_reason || "Tab Switch Detected")}</div>` : ''}
            </div>

            <h4 style="font-size: 14px; font-weight: 600; margin-bottom: 10px;">Question-By-Question Responses (${answers.length})</h4>
            ${answers.map(a => `
                <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-bottom: 10px; background: white;">
                    <div style="font-weight: 600; font-size: 13px; color: #1e3a8a; margin-bottom: 4px;">Q${a.question_number}: ${escapeHtml(a.question_text)}</div>
                    <div style="font-size: 12px; color: #334155; margin-bottom: 8px; background: #f8fafc; padding: 8px; border-radius: 6px;">
                        <strong>Candidate Answer:</strong> ${escapeHtml(a.answer_text || "No verbal answer recorded.")}
                    </div>
                    <div style="display: flex; gap: 14px; font-size: 11.5px; color: #64748b; flex-wrap: wrap;">
                        <span>Technical: <strong>${a.technical_score !== null ? a.technical_score + '%' : '--'}</strong></span>
                        <span>Relevance: <strong>${a.relevance_score !== null ? a.relevance_score + '%' : '--'}</strong></span>
                        <span>Communication: <strong>${a.communication_score !== null ? a.communication_score + '%' : '--'}</strong></span>
                        <span>Confidence: <strong>${a.confidence_score !== null ? a.confidence_score + '%' : '--'}</strong></span>
                    </div>
                </div>
            `).join("")}
        `;
    } catch (err) {
        body.innerHTML = `<div style="color: #dc2626; padding: 20px;">Error loading evaluation details.</div>`;
    }
}
function closeInterviewDetailModal() {
    document.getElementById("interviewDetailModal").style.display = "none";
}

// =========================================================
// TAB 4: AI EVALUATION INSPECTOR
// =========================================================

async function inspectInterviewAI() {
    const input = document.getElementById("inspectInterviewIdInput");
    const intId = (input.value || "").trim();
    if (!intId) {
        alert("Please enter a valid Interview ID.");
        return;
    }

    const container = document.getElementById("aiInspectionDetailsContainer");
    container.style.display = "block";
    container.innerHTML = `<div style="text-align: center; padding: 30px;"><i class="fas fa-spinner fa-spin"></i> Retrieving evaluation data...</div>`;

    try {
        const res = await fetch(`/api/admin/interviews/${intId}`, { headers: getAuthHeaders() });
        if (!res.ok) throw new Error("Interview not found or unauthorized.");
        const data = await res.json();
        const intItem = data.interview || {};
        const answers = data.answers || [];
        const isTerm = String(intItem.status).toLowerCase() === "terminated";

        container.innerHTML = `
            <div class="admin-card-section">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 12px; margin-bottom: 16px;">
                    <div>
                        <h3 style="font-size: 16px; font-weight: 700; color: #1e3a8a;">Session #${intItem.id} &mdash; ${escapeHtml(intItem.role)}</h3>
                        <p style="font-size: 12px; color: #64748b;">Conducted: ${escapeHtml(intItem.created_at || 'Recent')}</p>
                    </div>
                    <button class="btn-primary" onclick="downloadInterviewReport(${intItem.id})"><i class="fas fa-file-pdf"></i> Download PDF Report</button>
                </div>

                ${isTerm ? `
                    <div style="background: #fef2f2; border: 1px solid #f87171; border-radius: 8px; padding: 14px; color: #991b1b; font-size: 13px; margin-bottom: 16px;">
                        <strong>⚠️ TERMINATED SESSION:</strong> Tab Switch Detected. AI Evaluation was not generated for this session to maintain academic integrity.
                    </div>
                ` : ''}

                <h4 style="font-size: 14px; font-weight: 700; margin-bottom: 12px;">Concept Breakdown & Semantic Accuracy</h4>
                ${answers.map(a => `
                    <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; margin-bottom: 14px; background: white;">
                        <h5 style="font-size: 13px; font-weight: 700; color: #2563eb; margin-bottom: 6px;">Q${a.question_number}: ${escapeHtml(a.question_text)}</h5>
                        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; font-size: 12.5px; color: #1e293b; margin-bottom: 10px;">
                            <strong>Transcribed Speech:</strong> <em>"${escapeHtml(a.answer_text || 'No speech recorded')}"</em>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; font-size: 12px; margin-bottom: 10px;">
                            <div style="background: #eff6ff; padding: 8px; border-radius: 6px;">
                                <strong style="color: #1d4ed8;">Expected Concepts:</strong><br/>
                                ${escapeHtml(Array.isArray(a.expected_concepts) ? a.expected_concepts.join(", ") : a.expected_topics || 'Standard topics')}
                            </div>
                            <div style="background: #f0fdf4; padding: 8px; border-radius: 6px;">
                                <strong style="color: #15803d;">Matched Concepts:</strong><br/>
                                ${escapeHtml(a.matched_concepts || 'None identified')}
                            </div>
                            <div style="background: #fef2f2; padding: 8px; border-radius: 6px;">
                                <strong style="color: #b91c1c;">Missing Concepts:</strong><br/>
                                ${escapeHtml(a.missing_concepts || 'None')}
                            </div>
                        </div>
                        <div style="font-size: 12px; color: #475569;">
                            Scores: Technical: <strong>${a.technical_score ?? '--'}%</strong> | Relevance: <strong>${a.relevance_score ?? '--'}%</strong> | Comm: <strong>${a.communication_score ?? '--'}%</strong> | Conf: <strong>${a.confidence_score ?? '--'}%</strong>
                        </div>
                    </div>
                `).join("")}
            </div>
        `;
    } catch (err) {
        container.innerHTML = `<div style="color: #dc2626; padding: 20px;">${escapeHtml(err.message)}</div>`;
    }
}

// =========================================================
// TAB 5: QUESTION BANK MANAGEMENT
// =========================================================

let qFilterTimeout = null;
function debounceFilterQuestions() {
    clearTimeout(qFilterTimeout);
    qFilterTimeout = setTimeout(loadQuestionsTable, 250);
}

async function loadQuestionsTable() {
    const tbody = document.getElementById("questionsTableBody");
    if (!tbody) return;

    const role = (document.getElementById("questionRoleFilter")?.value || "").trim();
    const difficulty = (document.getElementById("questionDifficultyFilter")?.value || "").trim();
    const search = (document.getElementById("questionsSearchInput")?.value || "").trim();

    const query = new URLSearchParams();
    if (role) query.append("role", role);
    if (difficulty) query.append("difficulty", difficulty);
    if (search) query.append("search", search);

    try {
        const res = await fetch(`/api/admin/questions?${query.toString()}`, { headers: getAuthHeaders() });
        const data = await res.json();
        allQuestionsCache = data.questions || [];

        if (allQuestionsCache.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 30px; color: #64748b;">No questions found.</td></tr>`;
            return;
        }

        tbody.innerHTML = allQuestionsCache.map(q => {
            return `
                <tr>
                    <td><strong>#${q.id}</strong></td>
                    <td><span class="badge-role candidate">${escapeHtml(q.role_name)}</span></td>
                    <td><span class="badge-status ${q.difficulty === 'Hard' ? 'terminated' : (q.difficulty === 'Easy' ? 'active' : 'inactive')}">${escapeHtml(q.difficulty)}</span></td>
                    <td>${escapeHtml(q.category)}</td>
                    <td style="max-width: 320px; white-space: normal;"><strong>${escapeHtml(q.question_text)}</strong></td>
                    <td style="max-width: 220px; white-space: normal; color: #64748b; font-size: 11.5px;">${escapeHtml(q.expected_topics)}</td>
                    <td><span class="badge-status ${q.is_active ? 'active' : 'inactive'}">${q.is_active ? 'Active' : 'Disabled'}</span></td>
                    <td style="text-align: right;">
                        <button class="btn-action" onclick="openEditQuestionModal(${q.id})" title="Edit Question"><i class="fas fa-pen"></i></button>
                        <button class="btn-action danger" onclick="deleteQuestion(${q.id})" title="Delete/Disable"><i class="fas fa-trash"></i></button>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 30px; color: #dc2626;">Error loading questions.</td></tr>`;
    }
}

function openCreateQuestionModal() {
    document.getElementById("questionModalTitle").innerHTML = `<i class="fas fa-plus"></i> Add Question`;
    document.getElementById("questionId").value = "";
    document.getElementById("questionForm").reset();
    document.getElementById("questionModal").style.display = "flex";
}

function openEditQuestionModal(qId) {
    const q = allQuestionsCache.find(x => x.id === qId);
    if (!q) return;

    document.getElementById("questionModalTitle").innerHTML = `<i class="fas fa-pen"></i> Edit Question #${qId}`;
    document.getElementById("questionId").value = q.id;
    document.getElementById("qRoleSelect").value = q.role_name;
    document.getElementById("qDifficultySelect").value = q.difficulty;
    document.getElementById("qPromptText").value = q.question_text;
    document.getElementById("qExpectedTopics").value = q.expected_topics;
    document.getElementById("qReferenceAnswer").value = q.reference_answer || "";
    document.getElementById("questionModal").style.display = "flex";
}
function closeQuestionModal() {
    document.getElementById("questionModal").style.display = "none";
}

async function handleQuestionSubmit(event) {
    event.preventDefault();
    const qId = document.getElementById("questionId").value;
    const role_name = document.getElementById("qRoleSelect").value;
    const difficulty = document.getElementById("qDifficultySelect").value;
    const question_text = document.getElementById("qPromptText").value.trim();
    const expected_topics = document.getElementById("qExpectedTopics").value.trim();
    const reference_answer = document.getElementById("qReferenceAnswer").value.trim();

    const payload = {
        role_name,
        category: "Technical",
        difficulty,
        question_text,
        expected_topics,
        reference_answer
    };

    const isEdit = Boolean(qId);
    const url = isEdit ? `/api/admin/questions/${qId}` : `/api/admin/questions`;
    const method = isEdit ? "PUT" : "POST";

    try {
        const res = await fetch(url, {
            method,
            headers: getAuthHeaders(),
            body: jsonPayload(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to save question");

        showToast(isEdit ? "Question updated successfully!" : "Question added to Question Bank!", "success");
        closeQuestionModal();
        loadQuestionsTable();
    } catch (err) {
        alert(err.message || "Error saving question");
    }
}

async function deleteQuestion(qId) {
    if (!confirm(`Are you sure you want to delete or disable Question #${qId}?`)) return;

    try {
        const res = await fetch(`/api/admin/questions/${qId}`, {
            method: "DELETE",
            headers: getAuthHeaders()
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Delete failed");

        showToast("Question safely removed/disabled", "success");
        loadQuestionsTable();
    } catch (err) {
        alert(err.message || "Failed to delete question");
    }
}

// =========================================================
// TAB 6: INTERVIEW ROLE MANAGEMENT
// =========================================================

async function loadRolesTable() {
    const tbody = document.getElementById("rolesTableBody");
    if (!tbody) return;

    try {
        const res = await fetch("/api/admin/roles", { headers: getAuthHeaders() });
        const data = await res.json();
        const roles = data.roles || [];

        tbody.innerHTML = roles.map(r => `
            <tr>
                <td><strong>#${r.id}</strong></td>
                <td><strong>${escapeHtml(r.role_name)}</strong></td>
                <td><code>${escapeHtml(r.slug)}</code></td>
                <td style="max-width: 240px; white-space: normal; font-size: 11.5px; color: #475569;">${escapeHtml(r.description)}</td>
                <td style="max-width: 200px; white-space: normal; font-size: 11px; color: #64748b;">${escapeHtml(r.topics)}</td>
                <td><strong>${r.question_count}</strong></td>
                <td><strong>${r.interview_count}</strong></td>
                <td><span class="badge-status ${r.is_active ? 'active' : 'inactive'}">${r.is_active ? 'Active' : 'Disabled'}</span></td>
                <td style="text-align: right;">
                    <button class="btn-action" onclick="alert('Role configuration is active.')"><i class="fas fa-sliders"></i></button>
                </td>
            </tr>
        `).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 20px; color: #dc2626;">Error loading roles.</td></tr>`;
    }
}

// =========================================================
// TAB 7 & 8: RECORDINGS & REPORTS
// =========================================================

async function loadRecordingsTable() {
    const tbody = document.getElementById("recordingsTableBody");
    if (!tbody) return;

    try {
        const res = await fetch("/api/admin/interviews?limit=100", { headers: getAuthHeaders() });
        const data = await res.json();
        const list = data.interviews || [];

        tbody.innerHTML = list.map(i => `
            <tr>
                <td><strong>#${i.id}</strong></td>
                <td><strong>${escapeHtml(i.candidate_name)}</strong></td>
                <td><span class="badge-role candidate">${escapeHtml(i.role)}</span></td>
                <td>${i.duration_seconds ? `${i.duration_seconds}s` : 'N/A'}</td>
                <td><span class="badge-status ${String(i.status).toLowerCase() === 'terminated' ? 'terminated' : 'completed'}">${escapeHtml(i.status)}</span></td>
                <td>${i.recording_available ? '<span style="color:#16a34a; font-weight:600;"><i class="fas fa-check"></i> Stored</span>' : '<span style="color:#94a3b8;">None</span>'}</td>
                <td><span style="color: #64748b;">Faster-Whisper STT</span></td>
                <td style="text-align: right;">
                    ${i.recording_available ? `
                        <button class="btn-action primary" onclick="playAdminVideo(${i.id}, '${escapeHtml(i.role)}')" title="Play Video">
                            <i class="fas fa-play"></i> Play Video
                        </button>
                    ` : '<span style="color:#94a3b8; font-size:11px;">Unavailable</span>'}
                </td>
            </tr>
        `).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: #dc2626;">Error loading recordings.</td></tr>`;
    }
}

function playAdminVideo(interviewId, roleName) {
    const player = document.getElementById("adminVideoPlayer");
    const link = document.getElementById("adminDownloadVideoLink");
    const recUrl = `/interview/${interviewId}/recording`;

    if (player) {
        player.src = recUrl;
        player.play().catch(() => {});
    }
    if (link) {
        link.href = recUrl;
        link.download = `interview_${interviewId}.webm`;
    }
    document.getElementById("videoModal").style.display = "flex";
}
function closeVideoModal() {
    const player = document.getElementById("adminVideoPlayer");
    if (player) {
        player.pause();
        player.src = "";
    }
    document.getElementById("videoModal").style.display = "none";
}

let reportFilterTimeout = null;
function debounceFilterReports() {
    clearTimeout(reportFilterTimeout);
    reportFilterTimeout = setTimeout(loadReportsTable, 250);
}

async function loadReportsTable() {
    const tbody = document.getElementById("reportsTableBody");
    if (!tbody) return;

    const search = (document.getElementById("reportsSearchInput")?.value || "").trim();
    const query = new URLSearchParams();
    if (search) query.append("search", search);

    try {
        const res = await fetch(`/api/admin/interviews?${query.toString()}`, { headers: getAuthHeaders() });
        const data = await res.json();
        const list = data.interviews || [];

        tbody.innerHTML = list.map(i => `
            <tr>
                <td><strong>#${i.id}</strong></td>
                <td><strong>${escapeHtml(i.candidate_name)}</strong></td>
                <td><span class="badge-role candidate">${escapeHtml(i.role)}</span></td>
                <td>${escapeHtml(i.created_at)}</td>
                <td><strong>${String(i.status).toLowerCase() === 'terminated' ? '--' : (i.overall_score !== null ? i.overall_score + '%' : '--')}</strong></td>
                <td><span class="badge-status ${String(i.status).toLowerCase() === 'terminated' ? 'terminated' : 'completed'}">${escapeHtml(i.status)}</span></td>
                <td>${(i.security_violation || i.tab_switch_count > 0) ? '<span class="badge-violation-yes">Security Flagged</span>' : '<span class="badge-violation-no">Clean</span>'}</td>
                <td style="text-align: right;">
                    <button class="btn-primary" onclick="downloadInterviewReport(${i.id})">
                        <i class="fas fa-file-pdf"></i> Download PDF
                    </button>
                </td>
            </tr>
        `).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: #dc2626;">Error loading reports catalog.</td></tr>`;
    }
}

// Central PDF Download Function
async function downloadInterviewReport(interviewId) {
    showToast(`Generating report for Interview #${interviewId}...`, "info");
    try {
        const token = getAuthToken();
        const url = `/api/interview/${interviewId}/report/pdf` + (token ? `?token=${encodeURIComponent(token)}` : "");
        const res = await fetch(url, { headers: { "Authorization": `Bearer ${token}` } });
        if (!res.ok) throw new Error("Failed to download PDF report");

        const blob = await res.blob();
        const blobUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.style.display = "none";
        a.href = blobUrl;
        a.download = `AI_Interview_Report_${interviewId}.pdf`;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
            window.URL.revokeObjectURL(blobUrl);
            document.body.removeChild(a);
        }, 1000);
        showToast("PDF report downloaded successfully!", "success");
    } catch (err) {
        alert(err.message || "Failed to download PDF report");
    }
}

// =========================================================
// TAB 9: SECURITY CENTER
// =========================================================

async function loadSecurityData() {
    try {
        const res = await fetch("/api/admin/security", { headers: getAuthHeaders() });
        const data = await res.json();

        document.getElementById("secTotalViolations").textContent = data.total_violations || "0";
        document.getElementById("secTerminatedInterviews").textContent = data.terminated_count || "0";

        const tbody = document.getElementById("securityEventsTableBody");
        if (!tbody) return;

        const events = data.events || [];
        if (events.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 24px; color: #16a34a;"><i class="fas fa-shield-check"></i> No security violations detected.</td></tr>`;
            return;
        }

        tbody.innerHTML = events.map(e => `
            <tr>
                <td><strong>#${e.interview_id}</strong></td>
                <td><strong>${escapeHtml(e.candidate_name)}</strong></td>
                <td><span class="badge-role candidate">${escapeHtml(e.role)}</span></td>
                <td><strong style="color: #dc2626;">Tab Switch</strong></td>
                <td>${escapeHtml(e.reason)}</td>
                <td><span class="badge-violation-yes">${e.tab_switch_count} Strike</span></td>
                <td><span class="badge-status terminated">${escapeHtml(e.action)}</span></td>
                <td style="font-size: 11.5px; color: #64748b;">${escapeHtml(e.timestamp)}</td>
                <td style="text-align: right;">
                    <button class="btn-action primary" onclick="downloadInterviewReport(${e.interview_id})" title="Download Security Report">
                        <i class="fas fa-file-pdf"></i>
                    </button>
                </td>
            </tr>
        `).join("");
    } catch (err) {
        showToast("Error loading security events", "error");
    }
}

// =========================================================
// TAB 10: ANALYTICS CENTER
// =========================================================

async function loadAnalyticsData() {
    try {
        const res = await fetch("/api/admin/analytics", { headers: getAuthHeaders() });
        const data = await res.json();

        // 1. Difficult Questions
        const qBody = document.getElementById("difficultQuestionsTableBody");
        if (qBody) {
            const diffQuestions = data.difficult_questions || [];
            qBody.innerHTML = diffQuestions.map(q => `
                <tr>
                    <td style="max-width: 260px; white-space: normal;"><strong>${escapeHtml(q.question)}</strong></td>
                    <td><span class="badge-status terminated">${escapeHtml(q.difficulty)}</span></td>
                    <td><strong style="color: #dc2626;">${q.average_score}%</strong></td>
                    <td>${q.attempts} attempts</td>
                </tr>
            `).join("");
        }

        // 2. Missed Concepts
        const cBody = document.getElementById("missedConceptsTableBody");
        if (cBody) {
            const missed = data.top_missed_concepts || [];
            cBody.innerHTML = missed.map(c => `
                <tr>
                    <td><strong>${escapeHtml(c.concept)}</strong></td>
                    <td><span class="badge-violation-yes">${c.frequency} misses</span></td>
                </tr>
            `).join("");
        }

        // 3. Role Performance
        const rBody = document.getElementById("roleAnalyticsTableBody");
        if (rBody) {
            const roles = data.role_analytics || [];
            rBody.innerHTML = roles.map(r => `
                <tr>
                    <td><strong>${escapeHtml(r.role)}</strong></td>
                    <td><strong>${r.total_interviews}</strong></td>
                    <td>${r.completed}</td>
                    <td>${r.terminated}</td>
                    <td><span class="badge-status active">${escapeHtml(r.completion_rate)}</span></td>
                    <td><strong>${r.average_score}%</strong></td>
                </tr>
            `).join("");
        }
    } catch (err) {
        showToast("Error loading advanced analytics", "error");
    }
}

// =========================================================
// TAB 11: AUDIT LOGS
// =========================================================

let auditFilterTimeout = null;
function debounceFilterAudit() {
    clearTimeout(auditFilterTimeout);
    auditFilterTimeout = setTimeout(loadAuditLogsTable, 250);
}

async function loadAuditLogsTable() {
    const tbody = document.getElementById("auditLogsTableBody");
    if (!tbody) return;

    const search = (document.getElementById("auditSearchInput")?.value || "").trim();
    const query = new URLSearchParams();
    if (search) query.append("search", search);

    try {
        const res = await fetch(`/api/admin/audit-logs?${query.toString()}`, { headers: getAuthHeaders() });
        const data = await res.json();
        allAuditCache = data.logs || [];

        if (allAuditCache.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 30px; color: #64748b;">No audit records found.</td></tr>`;
            return;
        }

        tbody.innerHTML = allAuditCache.map(l => `
            <tr>
                <td><strong>#${l.id}</strong></td>
                <td><strong>${escapeHtml(l.admin_name)}</strong></td>
                <td style="color: #64748b;">${escapeHtml(l.admin_email)}</td>
                <td><span class="badge-role candidate">${escapeHtml(l.action)}</span></td>
                <td>${escapeHtml(l.target_type)}</td>
                <td><strong>#${escapeHtml(l.target_id)}</strong></td>
                <td><span class="badge-status active">${escapeHtml(l.result)}</span></td>
                <td style="font-size: 11.5px; color: #64748b;">${escapeHtml(l.created_at)}</td>
                <td style="text-align: right;">
                    <button class="btn-action" onclick="alert('${escapeHtml(l.details || 'No additional context.')}')" title="Inspect context">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: #dc2626;">Error loading audit logs.</td></tr>`;
    }
}

// =========================================================
// TAB 12: SYSTEM HEALTH
// =========================================================

async function loadSystemHealth() {
    const container = document.getElementById("systemHealthCardsContainer");
    if (!container) return;

    container.innerHTML = `<div style="text-align: center; padding: 40px; color: #64748b;"><i class="fas fa-spinner fa-spin"></i> Running live diagnostic checks...</div>`;

    try {
        const res = await fetch("/api/admin/system-health", { headers: getAuthHeaders() });
        const data = await res.json();
        const services = data.services || {};

        container.innerHTML = Object.keys(services).map(key => {
            const s = services[key];
            const ind = s.indicator || "green";
            const iconMap = {
                backend_api: "fa-server",
                database: "fa-database",
                authentication: "fa-shield-halved",
                smtp: "fa-envelope-circle-check",
                transcription: "fa-microphone-lines",
                ai_evaluation: "fa-brain",
                storage: "fa-hard-drive"
            };

            return `
                <div class="health-card ${ind}">
                    <div class="health-icon-wrapper">
                        <i class="fas ${iconMap[key] || 'fa-gear'}"></i>
                    </div>
                    <div class="health-details">
                        <div class="health-details-top">
                            <h4>${escapeHtml(s.name)}</h4>
                            <span class="health-status-badge ${ind}">${escapeHtml(s.status)}</span>
                        </div>
                        <p>${escapeHtml(s.details || '')}</p>
                    </div>
                </div>
            `;
        }).join("");
    } catch (err) {
        container.innerHTML = `<div style="color: #dc2626; padding: 20px;">Health diagnostics check failed.</div>`;
    }
}

// =========================================================
// TAB 13: SETTINGS
// =========================================================

async function loadSettings() {
    try {
        const res = await fetch("/api/admin/settings", { headers: getAuthHeaders() });
        const data = await res.json();

        if (data.general) {
            document.getElementById("setAppName").textContent = data.general.system_name || "--";
            document.getElementById("setAppVersion").textContent = data.general.version || "--";
            document.getElementById("setAppEnv").textContent = data.general.environment || "--";
            document.getElementById("setAppOrg").textContent = data.general.organization || "--";
        }
        if (data.email_smtp) {
            document.getElementById("setSmtpHost").textContent = data.email_smtp.host || "--";
            document.getElementById("setSmtpPort").textContent = data.email_smtp.port || "--";
            document.getElementById("setSmtpSender").textContent = data.email_smtp.sender_masked || "--";
        }
    } catch (err) {
        console.error("[Settings Load Error]", err);
    }
}

// =========================================================
// ADMIN PROFILE & PASSWORD MODAL
// =========================================================

function openAdminProfileModal() {
    if (currentAdminUser) {
        document.getElementById("adminProfileName").value = currentAdminUser.name || "";
        document.getElementById("adminProfileEmail").value = currentAdminUser.email || "";
    }
    document.getElementById("adminProfileModal").style.display = "flex";
}
function closeAdminProfileModal() {
    document.getElementById("adminProfileModal").style.display = "none";
}

async function handleAdminProfileSubmit(event) {
    event.preventDefault();
    const name = document.getElementById("adminProfileName").value.trim();
    const email = document.getElementById("adminProfileEmail").value.trim();

    try {
        const res = await fetch("/api/admin/profile", {
            method: "PUT",
            headers: getAuthHeaders(),
            body: jsonPayload({ name, email })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Profile update failed");

        currentAdminUser.name = name;
        currentAdminUser.email = email;
        document.getElementById("navAdminName").textContent = name;
        showToast("Administrator profile updated successfully!", "success");
    } catch (err) {
        alert(err.message || "Failed to update profile");
    }
}

async function handleAdminPasswordSubmit(event) {
    event.preventDefault();
    const current_password = document.getElementById("adminCurrentPassword").value;
    const new_password = document.getElementById("adminNewPassword").value;
    const confirm_password = document.getElementById("adminConfirmPassword").value;

    if (new_password !== confirm_password) {
        alert("New passwords do not match.");
        return;
    }

    try {
        const res = await fetch("/api/admin/change-password", {
            method: "POST",
            headers: getAuthHeaders(),
            body: jsonPayload({ current_password, new_password, confirm_password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Password change failed");

        showToast("Administrator password updated successfully!", "success");
        document.getElementById("adminPasswordForm").reset();
    } catch (err) {
        alert(err.message || "Failed to change password");
    }
}

function jsonPayload(obj) {
    return JSON.stringify(obj);
}

// =========================================================
// INITIALIZATION
// =========================================================

document.addEventListener("DOMContentLoaded", async () => {
    const isAuthed = await verifyAdminAuth();
    if (isAuthed) {
        // Load default tab
        loadDashboardMetrics();
    }
});
