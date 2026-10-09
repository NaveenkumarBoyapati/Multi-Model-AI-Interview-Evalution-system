// =========================================
// AI Interview Evaluation System - Auth Logic
// =========================================

const images = [
    "images/slide1.png",
    "images/slide2.png",
    "images/slide3.png",
    "images/slide4.png",
    "images/slide5.png"
];

const titles = [
    "AI Interview Evaluation",
    "Mock Interview Practice",
    "Real-Time Feedback",
    "Performance Analysis",
    "Get Interview Ready"
];

const subtitles = [
    "Practice • Analyze • Improve",
    "Improve your confidence with AI",
    "Instant evaluation of your answers",
    "Get instant AI-powered insights and improve every interview.",
    "Prepare smarter and get hired"
];

let current = 0;
const slide = document.getElementById("slide");
const title = document.getElementById("title");
const subtitle = document.getElementById("subtitle");

if (slide && title && subtitle) {
    setInterval(() => {
        current = (current + 1) % images.length;
        slide.style.opacity = "0";
        setTimeout(() => {
            if (slide) slide.src = images[current];
            if (title) title.innerHTML = titles[current];
            if (subtitle) subtitle.innerHTML = subtitles[current];
            if (slide) slide.style.opacity = "1";
        }, 500);
    }, 3500);
}

// =========================================
// UI HELPERS
// =========================================

function showAlert(type, message) {
    const alertBox = document.getElementById("authAlert");
    if (!alertBox) return;

    alertBox.className = `auth-alert ${type}`;
    alertBox.textContent = message;
    alertBox.style.display = "block";
}

function clearAlert() {
    const alertBox = document.getElementById("authAlert");
    if (alertBox) {
        alertBox.style.display = "none";
        alertBox.textContent = "";
    }
}

function switchAuthTab(tab) {
    clearAlert();
    const tabLogin = document.getElementById("tabLogin");
    const tabRegister = document.getElementById("tabRegister");
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");
    const heading = document.getElementById("formHeading");
    const subheading = document.getElementById("formSubheading");

    if (tab === "register") {
        if (tabLogin) tabLogin.classList.remove("active");
        if (tabRegister) tabRegister.classList.add("active");
        if (loginForm) loginForm.style.display = "none";
        if (registerForm) registerForm.style.display = "block";
        if (heading) heading.textContent = "Create an Account";
        if (subheading) subheading.textContent = "Start your journey to interview mastery";
    } else {
        if (tabRegister) tabRegister.classList.remove("active");
        if (tabLogin) tabLogin.classList.add("active");
        if (registerForm) registerForm.style.display = "none";
        if (loginForm) loginForm.style.display = "block";
        if (heading) heading.textContent = "Welcome Back";
        if (subheading) subheading.textContent = "Please enter your credentials";
    }
}

// =========================================
// SHOW / HIDE PASSWORD TOGGLE
// =========================================

function togglePasswordVisibility(inputId, btnId) {
    const input = document.getElementById(inputId);
    const btn = document.getElementById(btnId);
    if (!input) return;

    const icon = btn ? btn.querySelector("i") : null;
    const isPassword = input.type === "password";

    if (isPassword) {
        input.type = "text";
        if (btn) {
            btn.setAttribute("aria-label", "Hide password");
            btn.setAttribute("title", "Hide password");
        }
        if (icon) {
            icon.className = "fas fa-eye-slash";
        }
    } else {
        input.type = "password";
        if (btn) {
            btn.setAttribute("aria-label", "Show password");
            btn.setAttribute("title", "Show password");
        }
        if (icon) {
            icon.className = "fas fa-eye";
        }
    }
}
window.togglePasswordVisibility = togglePasswordVisibility;

// =========================================
// PASSWORD RULES REAL-TIME CHECKLIST
// =========================================

const SPECIAL_CHARS_REGEX = /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`'"\\]/;

function setupPasswordValidation() {
    const regPassword = document.getElementById("regPassword");
    const ruleMinLength = document.getElementById("ruleMinLength");
    const ruleFirstUpper = document.getElementById("ruleFirstUpper");
    const ruleSpecialChar = document.getElementById("ruleSpecialChar");

    if (!regPassword) return;

    regPassword.addEventListener("input", function () {
        const val = this.value || "";

        // Rule 1: Min 8 chars
        const validLen = val.length >= 8;
        updateRuleUI(ruleMinLength, validLen);

        // Rule 2: First char uppercase A-Z
        const validFirst = val.length > 0 && val[0] >= "A" && val[0] <= "Z";
        updateRuleUI(ruleFirstUpper, validFirst);

        // Rule 3: Special char
        const validSpecial = SPECIAL_CHARS_REGEX.test(val);
        updateRuleUI(ruleSpecialChar, validSpecial);
    });
}

function updateRuleUI(elem, isValid) {
    if (!elem) return;
    const icon = elem.querySelector(".icon i");
    if (isValid) {
        elem.classList.add("valid");
        if (icon) {
            icon.className = "fas fa-circle-check";
            icon.style.color = "#16a34a";
        }
    } else {
        elem.classList.remove("valid");
        if (icon) {
            icon.className = "fas fa-circle-xmark";
            icon.style.color = "#94a3b8";
        }
    }
}

// =========================================
// LOGIN HANDLER
// =========================================

async function handleLogin(e) {
    if (e) {
        if (typeof e.preventDefault === "function") e.preventDefault();
        if (typeof e.stopPropagation === "function") e.stopPropagation();
    }

    clearAlert();

    const roleElem = document.getElementById("role");
    const emailElem = document.getElementById("email");
    const passwordElem = document.getElementById("password");
    const loginBtn = document.getElementById("loginBtn");

    const role = roleElem ? roleElem.value.trim() : "User";
    const email = emailElem ? emailElem.value.trim() : "";
    const password = passwordElem ? passwordElem.value : "";

    if (!email) {
        showAlert("error", "Please enter your email address.");
        if (emailElem) emailElem.focus();
        return false;
    }

    if (!password) {
        showAlert("error", "Please enter your password.");
        if (passwordElem) passwordElem.focus();
        return false;
    }

    try {
        if (loginBtn) {
            loginBtn.disabled = true;
            loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Authenticating...';
        }

        const response = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: email, password: password, role: role })
        });

        const data = await response.json();

        if (!response.ok) {
            const errorMsg = data.detail || data.message || "Invalid email or password.";
            showAlert("error", errorMsg);
            if (loginBtn) {
                loginBtn.disabled = false;
                loginBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Sign In';
            }
            return false;
        }

        // Store session tokens and user info
        const user = data.user;
        const token = data.token;
        const actualRole = user.is_admin ? "Admin" : "User";

        try {
            localStorage.setItem("sessionToken", token);
            localStorage.setItem("userRole", actualRole);
            localStorage.setItem("isAdmin", user.is_admin ? "true" : "false");
            localStorage.setItem("userEmail", user.email);
            localStorage.setItem("userName", user.name);
            localStorage.setItem("userId", user.id);
            localStorage.setItem("isLoggedIn", "true");
            if (user.preferred_role) {
                localStorage.setItem("selectedRole", user.preferred_role);
            }

            sessionStorage.setItem("sessionToken", token);
            sessionStorage.setItem("userRole", actualRole);
            sessionStorage.setItem("isAdmin", user.is_admin ? "true" : "false");
            sessionStorage.setItem("userEmail", user.email);
            sessionStorage.setItem("userName", user.name);
            sessionStorage.setItem("userId", user.id);
            sessionStorage.setItem("isLoggedIn", "true");
        } catch (storageErr) {
            console.warn("Storage warning:", storageErr);
        }

        showAlert("success", "Login successful! Redirecting...");

        setTimeout(() => {
            const params = new URLSearchParams(window.location.search);
            const redirectParam = params.get("redirect");

            if (user.is_admin) {
                // Administrator login ALWAYS redirects to /app/admin_dashboard.html
                // ADMIN MUST NEVER LAND ON THE CANDIDATE DASHBOARD.
                if (redirectParam && redirectParam.includes("admin") && !redirectParam.startsWith("http")) {
                    window.location.href = redirectParam.startsWith("/") ? redirectParam : `/app/${redirectParam}`;
                } else {
                    window.location.href = "/app/admin_dashboard.html";
                }
            } else {
                // Regular candidate user redirects to /app/dashboard.html
                // Candidates MUST NEVER be redirected to admin console.
                if (redirectParam && !redirectParam.includes("admin") && !redirectParam.startsWith("http")) {
                    window.location.href = redirectParam.startsWith("/") ? redirectParam : `/app/${redirectParam}`;
                } else {
                    window.location.href = "/app/dashboard.html";
                }
            }
        }, 600);

    } catch (networkErr) {
        console.error("Login request error:", networkErr);
        showAlert("error", "Unable to connect to the authentication server. Please ensure the backend is running.");
        if (loginBtn) {
            loginBtn.disabled = false;
            loginBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Sign In';
        }
    }

    return false;
}

// =========================================
// REGISTRATION HANDLER
// =========================================

async function handleRegister(e) {
    if (e) {
        if (typeof e.preventDefault === "function") e.preventDefault();
        if (typeof e.stopPropagation === "function") e.stopPropagation();
    }

    clearAlert();

    const nameElem = document.getElementById("regName");
    const roleElem = document.getElementById("regRole");
    const emailElem = document.getElementById("regEmail");
    const pwdElem = document.getElementById("regPassword");
    const confirmPwdElem = document.getElementById("regConfirmPassword");
    const regBtn = document.getElementById("registerBtn");

    const name = nameElem ? nameElem.value.trim() : "";
    const prefRole = roleElem ? roleElem.value : "Python Developer";
    const email = emailElem ? emailElem.value.trim() : "";
    const password = pwdElem ? pwdElem.value : "";
    const confirmPassword = confirmPwdElem ? confirmPwdElem.value : "";

    if (!name) {
        showAlert("error", "Please enter your full name.");
        if (nameElem) nameElem.focus();
        return false;
    }

    if (!email) {
        showAlert("error", "Please enter your email address.");
        if (emailElem) emailElem.focus();
        return false;
    }

    if (password.length < 8) {
        showAlert("error", "Password must be at least 8 characters long.");
        if (pwdElem) pwdElem.focus();
        return false;
    }

    if (!(password[0] >= "A" && password[0] <= "Z")) {
        showAlert("error", "The first character of the password must be an uppercase English letter (A-Z).");
        if (pwdElem) pwdElem.focus();
        return false;
    }

    if (!SPECIAL_CHARS_REGEX.test(password)) {
        showAlert("error", "Password must contain at least one special character (e.g. @, #, $, !).");
        if (pwdElem) pwdElem.focus();
        return false;
    }

    if (password !== confirmPassword) {
        showAlert("error", "Passwords do not match. Please re-enter.");
        if (confirmPwdElem) confirmPwdElem.focus();
        return false;
    }

    try {
        if (regBtn) {
            regBtn.disabled = true;
            regBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Account...';
        }

        const response = await fetch("/api/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: name,
                email: email,
                password: password,
                role: "User",
                preferred_role: prefRole
            })
        });

        const data = await response.json();

        if (!response.ok) {
            const errorMsg = data.detail || data.message || "Registration failed. Please try again.";
            showAlert("error", errorMsg);
            if (regBtn) {
                regBtn.disabled = false;
                regBtn.innerHTML = '<i class="fas fa-user-check"></i> Create Account';
            }
            return false;
        }

        // Store session tokens and user info
        const user = data.user;
        const token = data.token;

        try {
            localStorage.setItem("sessionToken", token);
            localStorage.setItem("userRole", "User");
            localStorage.setItem("userEmail", user.email);
            localStorage.setItem("userName", user.name);
            localStorage.setItem("userId", user.id);
            localStorage.setItem("selectedRole", prefRole);
            localStorage.setItem("isLoggedIn", "true");

            sessionStorage.setItem("sessionToken", token);
            sessionStorage.setItem("userRole", "User");
            sessionStorage.setItem("userEmail", user.email);
            sessionStorage.setItem("userName", user.name);
            sessionStorage.setItem("userId", user.id);
            sessionStorage.setItem("selectedRole", prefRole);
            sessionStorage.setItem("isLoggedIn", "true");
        } catch (storageErr) {
            console.warn("Storage warning:", storageErr);
        }

        showAlert("success", "Account created successfully! Preparing your dashboard...");

        setTimeout(() => {
            window.location.href = "dashboard.html";
        }, 800);

    } catch (networkErr) {
        console.error("Register request error:", networkErr);
        showAlert("error", "Unable to connect to the authentication server. Please ensure the backend is running.");
        if (regBtn) {
            regBtn.disabled = false;
            regBtn.innerHTML = '<i class="fas fa-user-check"></i> Create Account';
        }
    }

    return false;
}

// Expose handlers globally
window.handleLogin = handleLogin;
window.handleRegister = handleRegister;
window.switchAuthTab = switchAuthTab;

// Handle URL params such as redirected messages, tabs, and pre-selection
function handleUrlAuthMessages() {
    const urlParams = new URLSearchParams(window.location.search);
    const authMsg = urlParams.get("auth_msg");
    const redirectTarget = urlParams.get("redirect");
    const tabParam = urlParams.get("tab");
    const hash = window.location.hash;

    const roleElem = document.getElementById("role");
    if (roleElem && (redirectTarget === "admin_dashboard.html" || authMsg === "admin_required")) {
        roleElem.value = "Admin";
    }

    if (authMsg === "admin_required") {
        showAlert("info", "Authentication required. Please log in with administrator credentials.");
    } else if (authMsg === "session_expired") {
        showAlert("info", "Your session has expired or is invalid. Please sign in again.");
    } else if (authMsg === "login_required") {
        showAlert("info", "Please sign in to access your interview account.");
    } else if (authMsg === "admin_denied") {
        showAlert("error", "Access denied: Administrator privileges required.");
    } else if (authMsg === "logged_out") {
        showAlert("success", "You have been logged out successfully.");
    } else if (authMsg === "network_error") {
        showAlert("error", "Unable to verify session with server. Please sign in.");
    }

    if (tabParam === "register" || hash === "#register") {
        switchAuthTab("register");
    }

    const emailElem = document.getElementById("email");
    if (emailElem && roleElem) {
        emailElem.addEventListener("input", function() {
            if (this.value.trim().toLowerCase() === "admin@ai-interview.com") {
                roleElem.value = "Admin";
            }
        });
    }
}

// Bind form listeners
function initAuth() {
    setupPasswordValidation();
    handleUrlAuthMessages();

    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        loginForm.onsubmit = handleLogin;
    }

    const registerForm = document.getElementById("registerForm");
    if (registerForm) {
        registerForm.onsubmit = handleRegister;
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAuth);
} else {
    initAuth();
}