// test_show_hide_password_cdp.js
// Automated verification for Show/Hide Password Feature in Google Chrome CDP

const { spawn } = require('child_process');

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function run() {
    console.log("======================================================================");
    console.log("TESTING SHOW/HIDE PASSWORD FEATURE & AUTH FLOWS IN REAL CHROME CDP");
    console.log("======================================================================");

    const chromeProcess = spawn("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", [
        "--headless=new",
        "--remote-debugging-port=9466",
        "--disable-extensions",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-gpu",
        "--no-sandbox",
        "--window-size=1280,800",
        "about:blank"
    ], { stdio: 'ignore' });

    let exitCode = 0;

    try {
        await sleep(2000);

        const targetsRes = await fetch("http://127.0.0.1:9466/json");
        const targets = await targetsRes.json();
        const pageTarget = targets.find(t => t.type === 'page' && !t.url.startsWith('chrome')) || targets.find(t => t.type === 'page');
        console.log("Attached to Chrome CDP target:", pageTarget.id);

        const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
        let msgId = 1;
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
            const reqId = msgId++;
            return new Promise((resolve) => {
                pending.set(reqId, resolve);
                ws.send(JSON.stringify({ id: reqId, method, params }));
            });
        }

        async function evalJs(expr) {
            const res = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
            if (res.result && res.result.exceptionDetails) {
                throw new Error("JS Eval Exception: " + JSON.stringify(res.result.exceptionDetails));
            }
            return res.result ? (res.result.result ? res.result.result.value : null) : null;
        }

        async function waitForCondition(fnExpr, maxMs = 7000) {
            const start = Date.now();
            while (Date.now() - start < maxMs) {
                const val = await evalJs(fnExpr);
                if (val) return val;
                await sleep(150);
            }
            return false;
        }

        await send("Page.enable");
        await send("Runtime.enable");

        // Navigate to login page
        console.log("\n[1/5] Navigating to http://127.0.0.1:8000/app/login.html...");
        await send("Page.navigate", { url: "http://127.0.0.1:8000/app/login.html" });
        await waitForCondition("typeof window.handleLogin === 'function'");

        // Test 1: Initial state & visual alignment
        console.log("\n[2/5] Checking Initial State & Visual Alignment of Password Field...");
        const initialCheck = await evalJs(`
            (() => {
                const input = document.getElementById('password');
                const btn = document.getElementById('togglePasswordBtn');
                const icon = document.getElementById('togglePasswordIcon');
                if (!input || !btn || !icon) return { error: 'Elements missing' };

                const inRect = input.getBoundingClientRect();
                const btnRect = btn.getBoundingClientRect();

                // Button must be inside input's vertical bounds and near the right edge
                const insideHorizontally = btnRect.right <= (inRect.right + 2) && btnRect.left >= (inRect.left + inRect.width * 0.7);
                const insideVertically = btnRect.top >= (inRect.top - 5) && btnRect.bottom <= (inRect.bottom + 5);

                return {
                    defaultType: input.type,
                    buttonType: btn.type,
                    ariaLabel: btn.getAttribute('aria-label'),
                    title: btn.getAttribute('title'),
                    iconClass: icon.className,
                    insideHorizontally,
                    insideVertically,
                    inRect,
                    btnRect
                };
            })()
        `);
        console.log("  Initial check:", initialCheck);

        if (initialCheck.defaultType !== 'password') {
            throw new Error(`Default type must be 'password', got: ${initialCheck.defaultType}`);
        }
        if (initialCheck.buttonType !== 'button') {
            throw new Error(`Button type must be 'button' to prevent form submission, got: ${initialCheck.buttonType}`);
        }
        if (initialCheck.ariaLabel !== 'Show password' || initialCheck.title !== 'Show password') {
            throw new Error(`Accessibility labels incorrect: aria-label=${initialCheck.ariaLabel}, title=${initialCheck.title}`);
        }
        if (!initialCheck.insideHorizontally || !initialCheck.insideVertically) {
            throw new Error(`Button alignment issue: H=${initialCheck.insideHorizontally}, V=${initialCheck.insideVertically}`);
        }
        console.log("  ✓ Default type is 'password'");
        console.log("  ✓ Button type is 'button'");
        console.log("  ✓ Accessible aria-label and title: 'Show password'");
        console.log("  ✓ Eye button visually aligned inside password input field");

        // Test 2: Show/Hide toggle behavior
        console.log("\n[3/5] Testing Show/Hide Toggling with Password Value Integrity...");
        // Enter a password
        const testPassword = "MySecretPassword@2026!";
        await evalJs(`
            const input = document.getElementById('password');
            input.value = ${JSON.stringify(testPassword)};
        `);

        // Click eye button to show password
        await evalJs(`document.getElementById('togglePasswordBtn').click()`);
        await sleep(150);

        const stateShown = await evalJs(`
            (() => {
                const input = document.getElementById('password');
                const btn = document.getElementById('togglePasswordBtn');
                const icon = document.getElementById('togglePasswordIcon');
                return {
                    type: input.type,
                    value: input.value,
                    ariaLabel: btn.getAttribute('aria-label'),
                    title: btn.getAttribute('title'),
                    iconClass: icon.className,
                    url: window.location.href
                };
            })()
        `);
        console.log("  State after 1st click (Show):", stateShown);

        if (stateShown.type !== 'text') {
            throw new Error(`Expected input type to be 'text', got: ${stateShown.type}`);
        }
        if (stateShown.value !== testPassword) {
            throw new Error(`Password value was modified! Expected ${testPassword}, got ${stateShown.value}`);
        }
        if (stateShown.ariaLabel !== 'Hide password' || stateShown.title !== 'Hide password') {
            throw new Error(`Aria-label/title should be 'Hide password', got: ${stateShown.ariaLabel}`);
        }
        if (!stateShown.iconClass.includes('fa-eye-slash')) {
            throw new Error(`Icon should be fa-eye-slash, got: ${stateShown.iconClass}`);
        }
        if (!stateShown.url.includes('login.html')) {
            throw new Error(`Clicking eye button unexpectedly submitted form! URL: ${stateShown.url}`);
        }
        console.log("  ✓ First click toggled password -> text");
        console.log("  ✓ Password value completely preserved");
        console.log("  ✓ aria-label updated to 'Hide password'");
        console.log("  ✓ Icon switched to 'fa-eye-slash'");
        console.log("  ✓ Did NOT submit the form");

        // Click eye button again to hide password
        await evalJs(`document.getElementById('togglePasswordBtn').click()`);
        await sleep(150);

        const stateHiddenAgain = await evalJs(`
            (() => {
                const input = document.getElementById('password');
                const btn = document.getElementById('togglePasswordBtn');
                const icon = document.getElementById('togglePasswordIcon');
                return {
                    type: input.type,
                    value: input.value,
                    ariaLabel: btn.getAttribute('aria-label'),
                    title: btn.getAttribute('title'),
                    iconClass: icon.className
                };
            })()
        `);
        console.log("  State after 2nd click (Hide):", stateHiddenAgain);

        if (stateHiddenAgain.type !== 'password') {
            throw new Error(`Expected input type to be 'password', got: ${stateHiddenAgain.type}`);
        }
        if (stateHiddenAgain.value !== testPassword) {
            throw new Error(`Password value was modified! Expected ${testPassword}, got ${stateHiddenAgain.value}`);
        }
        if (stateHiddenAgain.ariaLabel !== 'Show password' || stateHiddenAgain.title !== 'Show password') {
            throw new Error(`Aria-label/title should be 'Show password', got: ${stateHiddenAgain.ariaLabel}`);
        }
        if (!stateHiddenAgain.iconClass.includes('fa-eye') || stateHiddenAgain.iconClass.includes('fa-eye-slash')) {
            throw new Error(`Icon should be fa-eye, got: ${stateHiddenAgain.iconClass}`);
        }
        console.log("  ✓ Second click toggled text -> password");
        console.log("  ✓ Password value completely preserved");
        console.log("  ✓ aria-label restored to 'Show password'");
        console.log("  ✓ Icon restored to 'fa-eye'");

        // Test 3: Wrong password rejection
        console.log("\n[4/5] Testing Wrong Password Rejection...");
        await evalJs(`
            document.getElementById('email').value = 'admin@ai-interview.com';
            document.getElementById('password').value = 'WrongPassword@123';
            document.getElementById('role').value = 'Admin';
            document.getElementById('loginForm').dispatchEvent(new Event('submit', { cancelable: true }));
        `);
        await sleep(1500);

        const wrongPwdResult = await evalJs(`
            (() => {
                const alertBox = document.getElementById('authAlert');
                return {
                    alertDisplay: alertBox ? alertBox.style.display : 'none',
                    alertText: alertBox ? alertBox.textContent : '',
                    currentUrl: window.location.href
                };
            })()
        `);
        console.log("  Wrong password result:", wrongPwdResult);
        if (!wrongPwdResult.alertText || !wrongPwdResult.currentUrl.includes('login.html')) {
            throw new Error(`Expected login rejection alert, but got: ${JSON.stringify(wrongPwdResult)}`);
        }
        console.log("  ✓ Invalid password properly blocked with alert:", wrongPwdResult.alertText);

        // Test 4: Candidate Login & Admin Login
        console.log("\n[5/5] Testing Candidate & Admin Logins with Password Toggle...");
        // Register a fresh candidate to guarantee valid credentials
        const candEmail = `cand_showhide_${Date.now()}@example.com`;
        const candPassword = `Candidate#2026`;
        const regRes = await fetch("http://127.0.0.1:8000/api/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: "Show Hide Test Candidate",
                email: candEmail,
                password: candPassword,
                preferred_role: "Python Developer"
            })
        });
        if (!regRes.ok) {
            const errData = await regRes.text();
            throw new Error("Failed to register test candidate: " + errData);
        }
        console.log("  ✓ Created test candidate:", candEmail);

        // Candidate login (with password in shown 'text' state to confirm visibility doesn't break auth)
        await evalJs(`
            document.getElementById('email').value = ${JSON.stringify(candEmail)};
            document.getElementById('password').value = ${JSON.stringify(candPassword)};
            document.getElementById('role').value = 'User';
            // Toggle to visible text
            document.getElementById('togglePasswordBtn').click();
            document.getElementById('loginForm').dispatchEvent(new Event('submit', { cancelable: true }));
        `);
        await waitForCondition("window.location.href.includes('dashboard.html')", 5000);
        const candUrl = await evalJs(`window.location.href`);
        console.log("  Candidate login URL:", candUrl);
        if (!candUrl.includes('dashboard.html')) {
            throw new Error(`Expected redirect to dashboard.html, got: ${candUrl}`);
        }
        console.log("  ✓ Candidate login succeeded (redirected to /app/dashboard.html).");

        // Return to login and test Admin login
        await send("Page.navigate", { url: "http://127.0.0.1:8000/app/login.html" });
        await waitForCondition("typeof window.handleLogin === 'function'");

        await evalJs(`
            document.getElementById('role').value = 'Admin';
            document.getElementById('email').value = 'admin@ai-interview.com';
            document.getElementById('password').value = 'Admin@Interview2026!';
            // Toggle to visible and back to hidden to test both
            document.getElementById('togglePasswordBtn').click();
            document.getElementById('togglePasswordBtn').click();
            document.getElementById('loginBtn').click();
        `);
        await waitForCondition("window.location.href.includes('admin_dashboard.html')", 5000);
        const adminUrl = await evalJs(`window.location.href`);
        console.log("  Admin login URL:", adminUrl);
        if (!adminUrl.includes('admin_dashboard.html')) {
            throw new Error(`Expected redirect to admin_dashboard.html, got: ${adminUrl}`);
        }
        console.log("  ✓ Admin login succeeded (redirected to /app/admin_dashboard.html).");

        console.log("\n======================================================================");
        console.log("ALL SHOW/HIDE PASSWORD & AUTH TESTS PASSED SUCCESSFULLY! 🎉");
        console.log("======================================================================");

    } catch (err) {
        console.error("Fatal test error:", err);
        exitCode = 1;
    } finally {
        try {
            chromeProcess.kill();
        } catch (e) {}
        process.exit(exitCode);
    }
}

run();
