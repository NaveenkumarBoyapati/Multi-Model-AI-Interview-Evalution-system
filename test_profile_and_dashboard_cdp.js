// test_profile_and_dashboard_cdp.js
const { spawn } = require('child_process');

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function run() {
    console.log("Starting headless Chrome on port 9333...");
    const chromeProcess = spawn("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", [
        "--headless=new",
        "--remote-debugging-port=9333",
        "--disable-gpu",
        "--no-sandbox",
        "about:blank"
    ], { stdio: 'ignore' });

    try {
        await sleep(1800);

        const targetsRes = await fetch("http://127.0.0.1:9333/json");
        const targets = await targetsRes.json();
        const pageTarget = targets.find(t => t.type === 'page') || targets[0];
        console.log("Connected to Chrome target:", pageTarget.id);

        const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
        let id = 1;
        const pending = new Map();

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.id && pending.has(data.id)) {
                pending.get(data.id)(data);
                pending.delete(data.id);
            }
            if (data.method === 'Runtime.consoleAPICalled') {
                console.log('BROWSER LOG:', data.params.args.map(a => a.value !== undefined ? a.value : a.description).join(' '));
            }
            if (data.method === 'Runtime.exceptionThrown') {
                console.error('BROWSER EXCEPTION:', JSON.stringify(data.params.exceptionDetails));
            }
        };

        await new Promise((resolve, reject) => {
            ws.onopen = resolve;
            ws.onerror = reject;
        });

        function send(method, params = {}) {
            const reqId = id++;
            return new Promise((resolve, reject) => {
                pending.set(reqId, (res) => {
                    if (res.error) reject(res.error);
                    else resolve(res.result);
                });
                ws.send(JSON.stringify({ id: reqId, method, params }));
            });
        }

        async function evalJs(expr) {
            const res = await send("Runtime.evaluate", {
                expression: expr,
                awaitPromise: true,
                returnByValue: true
            });
            if (res.exceptionDetails) {
                throw new Error("Evaluation error: " + JSON.stringify(res.exceptionDetails));
            }
            return res.result ? res.result.value : undefined;
        }

        await send("Page.enable");
        await send("Runtime.enable");

        // Step 1: Login page to set session tokens for User 31
        console.log("\n[1/5] Navigating to login.html to setup authenticated localStorage...");
        await send("Page.navigate", { url: "http://127.0.0.1:8000/app/login.html" });
        await sleep(1500);

        await evalJs(`
            localStorage.setItem('sessionToken', 'G7hiu_rb3sF3LDY1oy473L4IVGWDIzOHfQ1mJnDVLpo');
            localStorage.setItem('userName', 'Naveen Kumar');
            localStorage.setItem('userEmail', 'naveenboyapati48@gmail.com');
            localStorage.setItem('userRole', 'User');
            localStorage.setItem('selectedRole', 'Data Analyst');
        `);

        // Step 2: Navigate to profile.html
        console.log("\n[2/5] Navigating to profile.html...");
        await send("Page.navigate", { url: "http://127.0.0.1:8000/app/profile.html" });
        // Wait for async loadProfile() API response to populate UI
        for (let attempt = 0; attempt < 25; attempt++) {
            const nameVal = await evalJs(`document.getElementById('viewName') ? document.getElementById('viewName').innerText : ''`);
            if (nameVal && nameVal !== 'Loading...') break;
            await sleep(250);
        }

        const currentUrl = await evalJs(`window.location.href`);
        const profileText = await evalJs(`document.body.innerText`);
        console.log("Current URL:", currentUrl);
        console.log("Profile text:", profileText);
        console.log("Checking Profile content...");
        const lowerProfileText = profileText.toLowerCase();
        if (!lowerProfileText.includes("multi-model ai interview evaluation system")) throw new Error("Missing system brand title");
        if (!lowerProfileText.includes("personal information")) throw new Error("Missing Personal Information section");
        if (!lowerProfileText.includes("naveen kumar")) throw new Error("Missing user name Naveen Kumar");
        if (!lowerProfileText.includes("naveenboyapati48@gmail.com")) throw new Error("Missing user email");
        if (!lowerProfileText.includes("read-only")) throw new Error("Missing Read-only badge");
        if (!lowerProfileText.includes("account information")) throw new Error("Missing Account Information section");
        if (!lowerProfileText.includes("05 oct 2026")) throw new Error("Missing Member Since date");
        
        // Mobile Number verification
        if (profileText.toLowerCase().includes("mobile number") || profileText.includes("9876543210")) {
            throw new Error("Mobile Number is still displayed in Profile UI!");
        }
        console.log("  -> SUCCESS: Profile loaded real data, no mobile number present.");

        // Step 3: Test Edit & Cancel in Profile
        console.log("\n[3/5] Testing Profile Edit & Cancel...");
        await evalJs(`enterEditMode()`);
        await sleep(300);

        let editState = await evalJs(`({
            editNameVisible: document.getElementById('editName').style.display !== 'none',
            editRoleVisible: document.getElementById('editRole').style.display !== 'none',
            saveBtnVisible: document.getElementById('saveBtn').style.display !== 'none',
            cancelBtnVisible: document.getElementById('cancelBtn').style.display !== 'none'
        })`);
        if (!editState.editNameVisible || !editState.saveBtnVisible) throw new Error("Edit mode elements not visible");
        console.log("  -> Edit mode activated successfully.");

        await evalJs(`cancelEdit()`);
        await sleep(300);
        let cancelState = await evalJs(`({
            editNameVisible: document.getElementById('editName').style.display !== 'none',
            saveBtnVisible: document.getElementById('saveBtn').style.display !== 'none',
            editBtnVisible: document.getElementById('editBtn').style.display !== 'none'
        })`);
        if (cancelState.editNameVisible || !cancelState.editBtnVisible) throw new Error("Cancel did not revert edit mode");
        console.log("  -> Cancel reverted edit mode properly without modifying anything.");

        // Step 4: Test Save Changes
        console.log("\n[4/5] Testing Profile Save Changes...");
        await evalJs(`
            enterEditMode();
            document.getElementById('editRole').value = 'Python Developer';
        `);
        await evalJs(`saveProfile()`);
        await sleep(2000);

        let saveResult = await evalJs(`({
            alertText: document.getElementById('profileAlert').innerText,
            displayedRole: document.getElementById('roleText').innerText,
            isEditing: typeof isEditing !== 'undefined' ? isEditing : false
        })`);
        console.log("  Save result:", saveResult);
        if (!saveResult.alertText.includes("Profile updated successfully")) throw new Error("Missing success alert");
        if (saveResult.displayedRole !== "Python Developer") throw new Error("Displayed role not updated to Python Developer");

        // Restore role to Data Analyst
        await evalJs(`
            enterEditMode();
            document.getElementById('editRole').value = 'Data Analyst';
        `);
        await evalJs(`saveProfile()`);
        await sleep(2000);
        console.log("  -> Role restored to Data Analyst.");

        // Step 5: Dashboard verification
        console.log("\n[5/5] Testing Dashboard and Result Page Isolation...");
        await send("Page.navigate", { url: "http://127.0.0.1:8000/app/dashboard.html" });
        await sleep(3500);

        for (let attempt = 0; attempt < 15; attempt++) {
            const isReady = await evalJs(`!!document.body && document.readyState === 'complete'`);
            if (isReady) break;
            await sleep(500);
        }

        const dashState = await evalJs(`({
            hasProgressChartCanvas: !!document.getElementById('progressChart'),
            hasProgressChartTitle: (document.body ? document.body.innerText : '').includes('Overall Progress Chart')
        })`);
        console.log("  Dashboard Chart state:", dashState);
        if (!dashState.hasProgressChartCanvas || !dashState.hasProgressChartTitle) {
            throw new Error("Dashboard must have Overall Progress Chart!");
        }

        // Test dashboard visibility & background refresh
        console.log("  Testing dashboard visibilitychange & background refresh...");
        await evalJs(`document.dispatchEvent(new Event('visibilitychange'));`);
        await sleep(1500);
        await evalJs(`window.fetchDashboardSummary(true);`);
        await sleep(1500);
        const dashRefreshed = await evalJs(`({
            hasCanvas: !!document.getElementById('progressChart'),
            totalInterviews: document.getElementById('statTotalInterviews') ? document.getElementById('statTotalInterviews').innerText : null
        })`);
        console.log("  Dashboard after background refresh:", dashRefreshed);
        if (!dashRefreshed.hasCanvas) throw new Error("Progress chart canvas missing after refresh!");

        // Result Page (Completed)
        await send("Page.navigate", { url: "http://127.0.0.1:8000/app/result.html?id=116" });
        await sleep(3000);
        for (let attempt = 0; attempt < 15; attempt++) {
            const isReady = await evalJs(`!!document.body && document.readyState === 'complete'`);
            if (isReady) break;
            await sleep(500);
        }

        const resultCompletedState = await evalJs(`({
            hasProgressChartCanvas: !!document.getElementById('progressChart'),
            hasOverallProgressChartText: (document.body ? document.body.innerText : '').includes('Overall Progress Chart'),
            hasInterviewScore: (document.body ? document.body.innerText : '').includes('Overall Performance'),
            hasTechnicalBar: !!document.getElementById('technicalBar'),
            hasQuestionEval: !!document.getElementById('questionEvaluationContainer'),
            hasVideoModal: !!document.getElementById('videoModal'),
            hasFooterElement: !!document.querySelector('footer'),
            hasFooterCopyright: (document.body ? document.body.innerText : '').includes('© 2026 AI Interview Evaluation System'),
            hasPoweredByAi: (document.body ? document.body.innerText : '').includes('Powered by AI')
        })`);
        console.log("  Result Page (Completed #116) state:", resultCompletedState);
        if (resultCompletedState.hasProgressChartCanvas || resultCompletedState.hasOverallProgressChartText) {
            throw new Error("Result page #116 MUST NOT contain Overall Progress Chart!");
        }
        if (resultCompletedState.hasFooterElement || resultCompletedState.hasFooterCopyright || resultCompletedState.hasPoweredByAi) {
            throw new Error("Result page #116 MUST NOT contain footer or footer text!");
        }
        if (!resultCompletedState.hasInterviewScore || !resultCompletedState.hasQuestionEval) {
            throw new Error("Result page #116 is missing interview evaluation details!");
        }

        // Result Page (Terminated)
        await send("Page.navigate", { url: "http://127.0.0.1:8000/app/result.html?id=120" });
        await sleep(2500);
        for (let attempt = 0; attempt < 15; attempt++) {
            const isReady = await evalJs(`!!document.body && document.readyState === 'complete'`);
            if (isReady) break;
            await sleep(500);
        }

        const resultTerminatedState = await evalJs(`({
            hasProgressChartCanvas: !!document.getElementById('progressChart'),
            hasOverallProgressChartText: (document.body ? document.body.innerText : '').includes('Overall Progress Chart'),
            hasTerminatedBanner: (document.body ? document.body.innerText : '').includes('Terminated'),
            hasFooterElement: !!document.querySelector('footer'),
            hasFooterCopyright: (document.body ? document.body.innerText : '').includes('© 2026 AI Interview Evaluation System'),
            hasPoweredByAi: (document.body ? document.body.innerText : '').includes('Powered by AI')
        })`);
        console.log("  Result Page (Terminated #120) state:", resultTerminatedState);
        if (resultTerminatedState.hasProgressChartCanvas || resultTerminatedState.hasOverallProgressChartText) {
            throw new Error("Result page #120 MUST NOT contain Overall Progress Chart!");
        }
        if (resultTerminatedState.hasFooterElement || resultTerminatedState.hasFooterCopyright || resultTerminatedState.hasPoweredByAi) {
            throw new Error("Result page #120 MUST NOT contain footer or footer text!");
        }
        if (!resultTerminatedState.hasTerminatedBanner) {
            throw new Error("Result page #120 missing Terminated banner!");
        }

        console.log("\n==========================================");
        console.log("ALL CDP BROWSER VERIFICATIONS PASSED 100%!");
        console.log("==========================================\n");

        ws.close();
    } finally {
        chromeProcess.kill();
    }
}

run().catch(err => {
    console.error("FATAL ERROR in CDP test:", err);
    process.exit(1);
});
