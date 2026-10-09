// test_auth_redirect_cdp.js
// Automated End-to-End Chrome CDP test for Admin & Candidate Login Redirect and RBAC Flows

const { spawn } = require('child_process');

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

let chromeProcess = null;

async function runTest() {
    console.log("======================================================================");
    console.log("STARTING AUTOMATED CHROME E2E AUTH REDIRECT & RBAC VERIFICATION");
    console.log("======================================================================");

    console.log("[1/6] Launching real Google Chrome in headless mode...");
    chromeProcess = spawn("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", [
        "--headless=new",
        "--remote-debugging-port=9444",
        "--disable-extensions",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-gpu",
        "--no-sandbox",
        "about:blank"
    ], { stdio: 'ignore' });

    let passedTests = 0;
    let failedTests = 0;

    function assert(name, condition, details = "") {
        if (condition) {
            passedTests++;
            console.log(`  [PASS] ${name}${details ? ` (${details})` : ""}`);
        } else {
            failedTests++;
            console.error(`  [FAIL] ${name}${details ? ` (${details})` : ""}`);
        }
    }

    try {
        await sleep(2000);

        const targetsRes = await fetch("http://127.0.0.1:9444/json");
        const targets = await targetsRes.json();
        const pageTarget = targets.find(t => t.type === 'page' && !t.url.startsWith('chrome')) || targets.find(t => t.type === 'page');
        console.log("  Connected to Chrome page target:", pageTarget.url, pageTarget.id);

        const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
        let id = 1;
        const pending = new Map();

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.id && pending.has(data.id)) {
                pending.get(data.id)(data);
                pending.delete(data.id);
            }
        };

        await new Promise((resolve, reject) => {
            ws.onopen = resolve;
            ws.onerror = reject;
        });

        function send(method, params = {}) {
            const reqId = id++;
            return new Promise((resolve) => {
                pending.set(reqId, resolve);
                ws.send(JSON.stringify({ id: reqId, method, params }));
            });
        }

        await send("Page.enable");
        await send("Runtime.enable");
        await send("Network.enable");

        async function evalInBrowser(expr) {
            const res = await send("Runtime.evaluate", {
                expression: expr,
                returnByValue: true,
                awaitPromise: true
            });
            if (res.result && res.result.exceptionDetails) {
                console.error("  [JS Evaluation error]:", res.result.exceptionDetails);
            }
            if (res.result && res.result.result) {
                return res.result.result.value !== undefined ? res.result.result.value : null;
            }
            return null;
        }

        async function waitForCondition(fnExpr, maxMs = 6000) {
            const start = Date.now();
            while (Date.now() - start < maxMs) {
                const val = await evalInBrowser(fnExpr);
                if (val) return val;
                await sleep(150);
            }
            return false;
        }

        // ---------------------------------------------------------
        // TEST 1: Administrator Login Flow
        // ---------------------------------------------------------
        console.log("\n[2/6] Testing Administrator Login Flow in Chrome...");
        await send("Page.navigate", { url: "http://127.0.0.1:8000/app/login.html" });
        await waitForCondition("typeof window.handleLogin === 'function'");

        // Fill admin credentials & trigger login
        await evalInBrowser(`
            document.getElementById("role").value = "Admin";
            document.getElementById("email").value = "admin@ai-interview.com";
            document.getElementById("password").value = "Admin@Interview2026!";
            document.getElementById("loginBtn").click();
        `);

        // Wait for redirect to admin_dashboard.html
        await waitForCondition("window.location.href.includes('admin_dashboard.html')", 6000);
        await sleep(2000);

        const adminUrl = await evalInBrowser("window.location.href");
        assert(
            "Admin login redirects to /app/admin_dashboard.html",
            adminUrl.includes("/app/admin_dashboard.html"),
            adminUrl
        );

        assert(
            "Admin NEVER lands on candidate dashboard (/app/dashboard.html)",
            !adminUrl.includes("/app/dashboard.html"),
            adminUrl
        );

        // Verify Super Admin Console content & metrics
        const adminData = await evalInBrowser(`({
            navAdminName: document.getElementById("navAdminName") ? document.getElementById("navAdminName").textContent : "",
            paneActive: document.getElementById("pane-command-center") ? document.getElementById("pane-command-center").classList.contains("active") : false,
            statCandidates: document.getElementById("statTotalCandidates") ? document.getElementById("statTotalCandidates").textContent : "",
            statInterviews: document.getElementById("statTotalInterviews") ? document.getElementById("statTotalInterviews").textContent : "",
            overlayHidden: document.getElementById("adminAuthOverlay") ? (document.getElementById("adminAuthOverlay").style.display === "none") : true
        })`);

        assert("Super Admin Console loaded successfully", adminData && adminData.paneActive === true);
        assert("Admin topbar shows System Administrator", adminData && adminData.navAdminName.includes("Administrator"), adminData ? adminData.navAdminName : "N/A");
        assert("Command Center metric cards loaded real data", adminData && adminData.statCandidates !== "--" && adminData.statInterviews !== "--", `Candidates: ${adminData.statCandidates}, Interviews: ${adminData.statInterviews}`);
        assert("Auth security overlay is dismissed after verification", adminData && adminData.overlayHidden === true);

        // ---------------------------------------------------------
        // TEST 2: Admin Direct Access to Candidate Dashboard Protection
        // ---------------------------------------------------------
        console.log("\n[3/6] Testing Admin Direct URL Access to /app/dashboard.html...");
        await send("Page.navigate", { url: "http://127.0.0.1:8000/app/dashboard.html" });
        await waitForCondition("window.location.href.includes('admin_dashboard.html')", 5000);

        const currentUrlAfterDirectAccess = await evalInBrowser("window.location.href");
        assert(
            "Admin accessing /app/dashboard.html is automatically redirected back to /app/admin_dashboard.html",
            currentUrlAfterDirectAccess.includes("/app/admin_dashboard.html"),
            currentUrlAfterDirectAccess
        );

        // ---------------------------------------------------------
        // TEST 3: Admin Logout Flow
        // ---------------------------------------------------------
        console.log("\n[4/6] Testing Administrator Logout Flow...");
        await evalInBrowser(`
            const btn = document.querySelector(".btn-logout");
            if (btn) btn.click();
            else if (typeof handleAdminLogout === 'function') handleAdminLogout();
        `);
        await waitForCondition("window.location.href.includes('login.html')", 5000);

        const logoutUrl = await evalInBrowser("window.location.href");
        const tokenAfterLogout = await evalInBrowser("localStorage.getItem('sessionToken')");
        assert(
            "Admin logout redirects to login page with logged_out auth_msg",
            logoutUrl.includes("login.html") && logoutUrl.includes("auth_msg=logged_out"),
            logoutUrl
        );
        assert("Session token is completely cleared after logout", tokenAfterLogout === null);

        // ---------------------------------------------------------
        // TEST 4: Candidate Login Flow
        // ---------------------------------------------------------
        console.log("\n[5/6] Testing Candidate Login Flow...");
        await send("Page.navigate", { url: "http://127.0.0.1:8000/app/login.html" });
        await waitForCondition("typeof window.handleLogin === 'function'");

        // Login with candidate credentials
        await evalInBrowser(`
            document.getElementById("role").value = "User";
            document.getElementById("email").value = "live_cand_bcb73b3e@example.com";
            document.getElementById("password").value = "Secure@Candidate2026!";
            document.getElementById("loginBtn").click();
        `);

        await waitForCondition("window.location.href.includes('dashboard.html')", 6000);
        await sleep(1500);

        const candUrl = await evalInBrowser("window.location.href");
        assert(
            "Candidate login redirects to /app/dashboard.html",
            candUrl.includes("/app/dashboard.html"),
            candUrl
        );

        // Verify Candidate Dashboard UI
        const candData = await evalInBrowser(`({
            greeting: document.getElementById("greeting") ? document.getElementById("greeting").textContent : "",
            dataContainer: document.getElementById("dashboardDataContainer") ? document.getElementById("dashboardDataContainer").style.display : ""
        })`);
        assert("Candidate dashboard loaded with greeting", candData && (candData.greeting.includes("Welcome") || candData.greeting.includes("Good")), candData ? candData.greeting : "N/A");

        // ---------------------------------------------------------
        // TEST 5: Candidate Access to Admin Console Protection
        // ---------------------------------------------------------
        console.log("\n[6/6] Testing Candidate Unauthorized Access to /app/admin_dashboard.html...");
        await send("Page.navigate", { url: "http://127.0.0.1:8000/app/admin_dashboard.html" });
        await sleep(1000);
        await waitForCondition("window.location.href.includes('dashboard.html') && window.location.href.includes('admin_denied')", 6000);

        const candAfterAdminAccessUrl = await evalInBrowser("window.location.href");
        assert(
            "Candidate is blocked from admin console and redirected to /app/dashboard.html?auth_msg=admin_denied",
            candAfterAdminAccessUrl.includes("/app/dashboard.html") && candAfterAdminAccessUrl.includes("auth_msg=admin_denied"),
            candAfterAdminAccessUrl
        );

        console.log("\n======================================================================");
        console.log(`CHROME E2E RESULTS: ${passedTests} PASSED, ${failedTests} FAILED (TOTAL ${passedTests + failedTests})`);
        console.log("======================================================================");

        ws.close();
        if (chromeProcess) chromeProcess.kill();
        process.exit(failedTests > 0 ? 1 : 0);

    } catch (err) {
        console.error("Test error:", err);
        if (chromeProcess) chromeProcess.kill();
        process.exit(1);
    }
}

runTest();
