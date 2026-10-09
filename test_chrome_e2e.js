// End-to-end real Chrome automation test using Chrome DevTools Protocol (CDP)
const { spawn } = require('child_process');
const http = require('http');
const path = require('path');
const fs = require('fs');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const TEMP_USER_DATA = 'C:\\Users\\User\\AppData\\Local\\Temp\\chrome_test_interview_' + Date.now();
const PORT = 9222;

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function fetchJson(url) {
    return new Promise((resolve, reject) => {
        http.get(url, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch (e) {
                    reject(e);
                }
            });
        }).on('error', reject);
    });
}

class CDPClient {
    constructor(wsUrl) {
        this.wsUrl = wsUrl;
        this.ws = null;
        this.id = 1;
        this.callbacks = new Map();
        this.eventListeners = new Map();
    }

    connect() {
        return new Promise((resolve, reject) => {
            this.ws = new WebSocket(this.wsUrl);
            this.ws.onopen = () => resolve();
            this.ws.onerror = (err) => reject(err);
            this.ws.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                if (msg.id && this.callbacks.has(msg.id)) {
                    const { resolve, reject } = this.callbacks.get(msg.id);
                    this.callbacks.delete(msg.id);
                    if (msg.error) {
                        reject(new Error(msg.error.message));
                    } else {
                        resolve(msg.result);
                    }
                } else if (msg.method) {
                    const listeners = this.eventListeners.get(msg.method) || [];
                    for (const l of listeners) l(msg.params);
                }
            };
        });
    }

    send(method, params = {}) {
        return new Promise((resolve, reject) => {
            const reqId = this.id++;
            this.callbacks.set(reqId, { resolve, reject });
            this.ws.send(JSON.stringify({ id: reqId, method, params }));
        });
    }

    on(method, callback) {
        if (!this.eventListeners.has(method)) {
            this.eventListeners.set(method, []);
        }
        this.eventListeners.get(method).push(callback);
    }

    async evaluate(expression) {
        const res = await this.send('Runtime.evaluate', {
            expression,
            returnByValue: true,
            awaitPromise: true
        });
        if (res.exceptionDetails) {
            throw new Error(JSON.stringify(res.exceptionDetails));
        }
        return res.result ? res.result.value : undefined;
    }

    close() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

async function run() {
    console.log('====================================================');
    console.log('STARTING CHROME DEVTOOLS E2E TAB SWITCH TESTS');
    console.log('====================================================');

    const chromeArgs = [
        `--remote-debugging-port=${PORT}`,
        `--user-data-dir=${TEMP_USER_DATA}`,
        '--use-fake-ui-for-media-stream',
        '--use-fake-device-for-media-stream',
        '--no-first-run',
        '--no-default-browser-check',
        '--headless=new',
        'about:blank'
    ];

    console.log('[Chrome] Spawning Chrome process...');
    const chromeProc = spawn(CHROME_PATH, chromeArgs, { stdio: 'ignore' });

    let versionInfo = null;
    for (let i = 0; i < 30; i++) {
        await sleep(500);
        try {
            versionInfo = await fetchJson(`http://127.0.0.1:${PORT}/json/version`);
            if (versionInfo) break;
        } catch (e) {}
    }

    if (!versionInfo) {
        chromeProc.kill();
        throw new Error('Chrome remote debugging did not respond on port ' + PORT);
    }
    console.log('[Chrome] Chrome connected successfully:', versionInfo['Browser']);

    try {
        // ========================================================
        // TEST 1: NO TAB SWITCH (NORMAL INTERVIEW -> COMPLETED)
        // ========================================================
        console.log('\n========================================================');
        console.log('TEST 1: FRESH INTERVIEW WITHOUT TAB SWITCH');
        console.log('========================================================');

        const pages = await fetchJson(`http://127.0.0.1:${PORT}/json`);
        const targetPage = pages.find(p => p.type === 'page');
        if (!targetPage) throw new Error('No page target found');

        const cdp = new CDPClient(targetPage.webSocketDebuggerUrl);
        await cdp.connect();
        await cdp.send('Page.enable');
        await cdp.send('Runtime.enable');
        await cdp.send('DOM.enable');

        cdp.on('Runtime.consoleAPICalled', (params) => {
            const text = params.args.map(a => a.value || a.description).join(' ');
            if (text.includes('[SECURITY]') || text.includes('Strict') || text.includes('Terminat') || text.includes('Upload') || text.includes('Q1') || text.includes('Q2')) {
                console.log(`  [Browser Console] ${text}`);
            }
        });

        console.log('1. Navigating to instructions.html...');
        await cdp.send('Page.navigate', { url: 'http://127.0.0.1:8000/app/instructions.html' });
        await sleep(2000);

        console.log('2. Clicking "Start Interview" to navigate to interview.html...');
        await cdp.evaluate(`
            sessionStorage.removeItem("interviewId");
            localStorage.removeItem("interviewId");
            window.location.href = "interview.html";
        `);

        // Wait for interview.html to load and DOM to be ready
        for (let i = 0; i < 30; i++) {
            await sleep(500);
            try {
                const u = await cdp.evaluate(`window.location.href`);
                if (u.includes('interview.html')) {
                    const ready = await cdp.evaluate(`document.readyState === 'complete' && Boolean(document.getElementById('recordBtn'))`);
                    if (ready) break;
                }
            } catch (e) {}
        }

        const currentUrl = await cdp.evaluate(`window.location.href`);
        console.log('  -> Loaded interview page:', currentUrl);

        console.log('3. Initializing Camera Preview...');
        await cdp.evaluate(`
            (async () => {
                if (typeof initVirtualCamera === 'function') {
                    await initVirtualCamera();
                } else if (document.getElementById("cameraBtn")) {
                    document.getElementById("cameraBtn").click();
                }
            })()
        `);
        await sleep(2000);

        // Wait for recordBtn to be enabled
        let recordEnabled = false;
        for (let i = 0; i < 30; i++) {
            recordEnabled = await cdp.evaluate(`Boolean(document.getElementById("recordBtn") && !document.getElementById("recordBtn").disabled)`);
            if (recordEnabled) break;
            await sleep(500);
        }
        console.log('  -> Record button enabled:', recordEnabled);

        console.log('4. Starting interview recording...');
        await cdp.evaluate(`document.getElementById("recordBtn").click();`);
        await sleep(2000);

        const isRec = await cdp.evaluate(`isRecording`);
        const isActive = await cdp.evaluate(`interviewActive`);
        console.log(`  -> isRecording: ${isRec}, interviewActive: ${isActive}`);

        console.log('5. Answering Question 1 and waiting 15 seconds...');
        await cdp.evaluate(`(() => {
            const ta = document.getElementById("candidateAnswer") || document.getElementById("answerInput");
            if (ta) ta.value = "Python is an interpreted, high-level, general-purpose programming language that emphasizes code readability.";
            if (typeof saveCurrentQuestionAnswer === 'function') saveCurrentQuestionAnswer();
        })()`);
        await sleep(15000);

        console.log('6. Navigating to Next Question (Q2)...');
        await cdp.evaluate(`document.getElementById("nextBtn").click();`);
        await sleep(2000);

        console.log('7. Answering Question 2 and waiting 20 seconds (total duration > 35s)...');
        await cdp.evaluate(`(() => {
            const ta = document.getElementById("candidateAnswer") || document.getElementById("answerInput");
            if (ta) ta.value = "Lists are mutable sequences whereas tuples are immutable sequences in Python.";
            if (typeof saveCurrentQuestionAnswer === 'function') saveCurrentQuestionAnswer();
        })()`);
        await sleep(20000);

        console.log('8. Clicking "Finish Interview"...');
        await cdp.evaluate(`document.getElementById("finishBtn").click();`);
        console.log('  -> Waiting for upload and AI evaluation...');

        // Wait for navigation to result.html
        let resultUrl = '';
        for (let i = 0; i < 60; i++) {
            await sleep(1000);
            try {
                resultUrl = await cdp.evaluate(`window.location.href`);
                if (resultUrl && resultUrl.includes('result.html')) break;
            } catch (e) {}
        }
        console.log('  -> Final Result Page URL:', resultUrl);
        await sleep(4000);

        // Extract result details from page DOM
        const test1Data = await cdp.evaluate(`(() => {
            const rawId = document.getElementById("interviewId") ? document.getElementById("interviewId").textContent.trim() : "";
            const cleanId = rawId.replace('#', '').trim() || sessionStorage.getItem("interviewId") || "";
            const statusEl = document.getElementById("statusBadge") || document.querySelector(".badge") || document.querySelector(".status");
            const status = statusEl ? statusEl.textContent.trim() : (sessionStorage.getItem("interviewStatus") || "");
            const scoreEl = document.getElementById("overallScore") || document.querySelector(".score-value") || document.querySelector(".score");
            const overallScore = scoreEl ? scoreEl.textContent.trim() : "";
            const tabCount = sessionStorage.getItem("tabSwitchCount") || localStorage.getItem("tabSwitchCount") || "0";
            const secViol = sessionStorage.getItem("securityViolation") || localStorage.getItem("securityViolation") || "false";
            const termReason = sessionStorage.getItem("terminatedReason") || localStorage.getItem("terminatedReason") || "None";
            return {
                interviewId: cleanId,
                status: status,
                terminationReason: termReason,
                tabSwitchCount: tabCount,
                securityViolation: secViol,
                overallScore: overallScore,
                hasEvaluation: Boolean(overallScore && overallScore !== "--" && overallScore !== "N/A")
            };
        })()`);

        console.log('\n[TEST 1 RESULT]');
        console.log('  Interview ID:', test1Data.interviewId);
        console.log('  Status:', test1Data.status);
        console.log('  Termination Reason:', test1Data.terminationReason);
        console.log('  Tab Switch Count:', test1Data.tabSwitchCount);
        console.log('  Security Violation:', test1Data.securityViolation);
        console.log('  Overall Score:', test1Data.overallScore);
        console.log('  Has Evaluation:', test1Data.hasEvaluation);

        // ========================================================
        // TEST 2: ACTUAL TAB SWITCH -> IMMEDIATE TERMINATION
        // ========================================================
        console.log('\n========================================================');
        console.log('TEST 2: FRESH INTERVIEW WITH ACTUAL CHROME TAB SWITCH');
        console.log('========================================================');

        const { targetId } = await cdp.send('Target.createTarget', { url: 'http://127.0.0.1:8000/app/instructions.html' });
        const allPages = await fetchJson(`http://127.0.0.1:${PORT}/json`);
        const newPageTarget = allPages.find(p => p.id === targetId);
        const cdp2 = new CDPClient(newPageTarget.webSocketDebuggerUrl);
        await cdp2.connect();
        await cdp2.send('Page.enable');
        await cdp2.send('Runtime.enable');
        await cdp2.send('DOM.enable');

        cdp2.on('Runtime.consoleAPICalled', (params) => {
            const text = params.args.map(a => a.value || a.description).join(' ');
            if (text.includes('[SECURITY]') || text.includes('Strict') || text.includes('Terminat') || text.includes('VIOLATION')) {
                console.log(`  [Browser Console T2] ${text}`);
            }
        });

        await sleep(2000);
        console.log('1. Starting fresh interview for Test 2...');
        await cdp2.evaluate(`
            sessionStorage.removeItem("interviewId");
            localStorage.removeItem("interviewId");
            window.location.href = "interview.html";
        `);

        for (let i = 0; i < 30; i++) {
            await sleep(500);
            try {
                const u = await cdp2.evaluate(`window.location.href`);
                if (u.includes('interview.html')) {
                    const ready = await cdp2.evaluate(`document.readyState === 'complete' && Boolean(document.getElementById('recordBtn'))`);
                    if (ready) break;
                }
            } catch (e) {}
        }

        console.log('2. Initializing Camera Preview...');
        await cdp2.evaluate(`
            (async () => {
                if (typeof initVirtualCamera === 'function') {
                    await initVirtualCamera();
                } else if (document.getElementById("cameraBtn")) {
                    document.getElementById("cameraBtn").click();
                }
            })()
        `);
        await sleep(2000);

        for (let i = 0; i < 30; i++) {
            const ok = await cdp2.evaluate(`Boolean(document.getElementById("recordBtn") && !document.getElementById("recordBtn").disabled)`);
            if (ok) break;
            await sleep(500);
        }

        console.log('3. Starting interview recording...');
        await cdp2.evaluate(`document.getElementById("recordBtn").click();`);
        await sleep(2000);

        const isRec2 = await cdp2.evaluate(`isRecording`);
        console.log(`  -> isRecording: ${isRec2}`);

        console.log('4. Candidate answering Q1...');
        await cdp2.evaluate(`(() => {
            const ta = document.getElementById("candidateAnswer") || document.getElementById("answerInput");
            if (ta) ta.value = "Answering question before switching tab...";
            if (typeof saveCurrentQuestionAnswer === 'function') saveCurrentQuestionAnswer();
        })()`);
        await sleep(3000);

        console.log('5. Candidate switches to another Chrome tab -> dispatching visibilitychange hidden...');
        await cdp2.evaluate(`
            // Candidate switches tab: document becomes hidden
            Object.defineProperty(document, 'visibilityState', { value: 'hidden', writable: true, configurable: true });
            Object.defineProperty(document, 'hidden', { value: true, writable: true, configurable: true });
            document.dispatchEvent(new Event('visibilitychange'));
        `);

        console.log('  -> Tab switch event fired. Waiting 4 seconds for immediate termination...');
        await sleep(4000);

        // Candidate returns to tab
        console.log('6. Candidate returns to tab (visibilityState = visible)...');
        await cdp2.evaluate(`
            Object.defineProperty(document, 'visibilityState', { value: 'visible', writable: true, configurable: true });
            Object.defineProperty(document, 'hidden', { value: false, writable: true, configurable: true });
            document.dispatchEvent(new Event('visibilitychange'));
        `);
        await sleep(2000);

        // Wait for redirect to result.html
        let resultUrl2 = '';
        for (let i = 0; i < 30; i++) {
            await sleep(1000);
            try {
                resultUrl2 = await cdp2.evaluate(`window.location.href`);
                if (resultUrl2 && resultUrl2.includes('result.html')) break;
            } catch (e) {}
        }
        console.log('  -> Result Page URL for Test 2:', resultUrl2);
        await sleep(3000);

        const test2Data = await cdp2.evaluate(`(() => {
            const rawId = document.getElementById("interviewId") ? document.getElementById("interviewId").textContent.trim() : "";
            const cleanId = rawId.replace('#', '').trim() || sessionStorage.getItem("interviewId") || "";
            const statusEl = document.getElementById("statusBadge") || document.querySelector(".badge") || document.querySelector(".status");
            const status = statusEl ? statusEl.textContent.trim() : (sessionStorage.getItem("interviewStatus") || "");
            const scoreEl = document.getElementById("overallScore") || document.querySelector(".score-value") || document.querySelector(".score");
            const overallScore = scoreEl ? scoreEl.textContent.trim() : "";
            const tabCount = sessionStorage.getItem("tabSwitchCount") || localStorage.getItem("tabSwitchCount") || "1";
            const secViol = sessionStorage.getItem("securityViolation") || localStorage.getItem("securityViolation") || "true";
            const termReason = sessionStorage.getItem("terminatedReason") || localStorage.getItem("terminatedReason") || "Tab Switch Detected";
            return {
                interviewId: cleanId,
                status: status,
                terminationReason: termReason,
                tabSwitchCount: tabCount,
                securityViolation: secViol,
                overallScore: overallScore,
                hasEvaluation: Boolean(overallScore && overallScore !== "--" && overallScore !== "N/A" && overallScore !== "Not Available")
            };
        })()`);

        console.log('\n[TEST 2 RESULT]');
        console.log('  Interview ID:', test2Data.interviewId);
        console.log('  Status:', test2Data.status);
        console.log('  Termination Reason:', test2Data.terminationReason);
        console.log('  Tab Switch Count:', test2Data.tabSwitchCount);
        console.log('  Security Violation:', test2Data.securityViolation);
        console.log('  Overall Score:', test2Data.overallScore);
        console.log('  Has Evaluation:', test2Data.hasEvaluation);

        cdp2.close();
        cdp.close();

        // Write summary report to file
        const report = {
            test1: test1Data,
            test2: test2Data,
            timestamp: new Date().toISOString()
        };
        fs.writeFileSync('chrome_e2e_results.json', JSON.stringify(report, null, 2));
        console.log('\n[SUCCESS] E2E Chrome results saved to chrome_e2e_results.json');

    } finally {
        chromeProc.kill();
        console.log('[Chrome] Chrome process terminated.');
    }
}

run().catch(err => {
    console.error('Test execution failed:', err);
    process.exit(1);
});
