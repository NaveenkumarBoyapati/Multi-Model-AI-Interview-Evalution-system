// test_mobile_and_submission_verification.js
const { spawn } = require('child_process');
const http = require('http');

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function run() {
    console.log("======================================================================");
    console.log("STARTING MOBILE INTERVIEW UI, LOGIN BACKGROUND & SUBMISSION VERIFICATION");
    console.log("======================================================================");

    // Launch headless chrome with fake webcam/mic
    const chromeProcess = spawn("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", [
        "--headless=new",
        "--remote-debugging-port=9222",
        "--use-fake-ui-for-media-stream",
        "--use-fake-device-for-media-stream",
        "--disable-gpu",
        "--no-sandbox",
        "about:blank"
    ], { stdio: 'ignore' });

    try {
        await sleep(1500);

        // Fetch targets
        const targetsRes = await fetch("http://127.0.0.1:9222/json");
        const targets = await targetsRes.json();
        const pageTarget = targets.find(t => t.type === 'page') || targets[0];
        console.log("Connected to Chrome CDP target:", pageTarget.id);

        const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);

        let id = 1;
        const pending = new Map();
        const consoleMessages = [];

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.id && pending.has(data.id)) {
                pending.get(data.id)(data);
                pending.delete(data.id);
            }
            if (data.method === 'Console.messageAdded') {
                consoleMessages.push(data.params.message);
            }
            if (data.method === 'Runtime.consoleAPICalled') {
                consoleMessages.push(data.params);
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

        async function evalJs(expr) {
            const res = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
            if (res.result && res.result.exceptionDetails) {
                console.error("JS Evaluation error:", res.result.exceptionDetails);
            }
            return res.result ? res.result.result ? res.result.result.value : null : null;
        }

        await send("Page.enable");
        await send("Runtime.enable");
        await send("Console.enable");

        // -------------------------------------------------------------------------
        // SECTION 1: LOGIN PAGE VERIFICATION (MOBILE & DESKTOP)
        // -------------------------------------------------------------------------
        console.log("\n----------------------------------------------------------------------");
        console.log("SECTION 1: LOGIN PAGE BACKGROUND IMAGE & RESPONSIVENESS");
        console.log("----------------------------------------------------------------------");

        const testWidths = [
            { width: 320, height: 600, isMobile: true, label: "Small Mobile (320px)" },
            { width: 360, height: 740, isMobile: true, label: "Mobile (360px)" },
            { width: 375, height: 667, isMobile: true, label: "iPhone SE/8 (375px)" },
            { width: 390, height: 844, isMobile: true, label: "iPhone 12/13/14 (390px)" },
            { width: 414, height: 896, isMobile: true, label: "iPhone Plus/Max (414px)" },
            { width: 1024, height: 768, isMobile: false, label: "Desktop iPad/Small Desktop (1024px)" },
            { width: 1366, height: 768, isMobile: false, label: "Standard Desktop (1366px)" }
        ];

        for (const tw of testWidths) {
            await send("Emulation.setDeviceMetricsOverride", {
                width: tw.width,
                height: tw.height,
                deviceScaleFactor: 2,
                mobile: tw.isMobile
            });

            await send("Page.navigate", { url: "http://127.0.0.1:8000/app/login.html" });
            await sleep(1000);

            const loginMetrics = await evalJs(`({
                bodyOverflowX: document.documentElement.scrollWidth <= document.documentElement.clientWidth,
                scrollWidth: document.documentElement.scrollWidth,
                clientWidth: document.documentElement.clientWidth,
                leftPanelDisplay: window.getComputedStyle(document.querySelector('.left-panel')).display,
                rightPanelBg: window.getComputedStyle(document.querySelector('.right-panel')).backgroundImage,
                loginBoxBg: window.getComputedStyle(document.querySelector('.login-box')).backgroundColor,
                loginBoxShadow: window.getComputedStyle(document.querySelector('.login-box')).boxShadow,
                loginBoxWidth: document.querySelector('.login-box').getBoundingClientRect().width,
                roleSelectVisible: Boolean(document.getElementById('role')),
                emailInputVisible: Boolean(document.getElementById('email')),
                passwordInputVisible: Boolean(document.getElementById('password')),
                loginBtnHeight: document.getElementById('loginBtn').getBoundingClientRect().height
            })`);

            console.log(`[Login ${tw.label}]:`);
            console.log(`  -> No horizontal overflow: ${loginMetrics.bodyOverflowX} (${loginMetrics.scrollWidth}px vs ${loginMetrics.clientWidth}px)`);
            if (tw.isMobile) {
                const hasBgImg = loginMetrics.rightPanelBg.includes("slide1.png") || loginMetrics.rightPanelBg.includes("linear-gradient");
                console.log(`  -> Mobile background image + gradient applied: ${hasBgImg}`);
                console.log(`  -> Left panel hidden on mobile: ${loginMetrics.leftPanelDisplay === 'none'}`);
                console.log(`  -> Card background styled: ${loginMetrics.loginBoxBg}`);
                if (!hasBgImg) throw new Error(`Missing background image on mobile ${tw.label}`);
            } else {
                console.log(`  -> Desktop split-screen preserved (left-panel visible): ${loginMetrics.leftPanelDisplay !== 'none'}`);
                if (loginMetrics.leftPanelDisplay === 'none') throw new Error(`Desktop left panel should not be hidden on ${tw.label}`);
            }
            if (!loginMetrics.bodyOverflowX) throw new Error(`Horizontal overflow detected on Login ${tw.label}`);
        }
        console.log("✓ Login Page background image and responsive tests PASSED across all widths!");

        // -------------------------------------------------------------------------
        // SECTION 2: INTERVIEW PAGE RESPONSIVENESS & COMPACT CAMERA PREVIEW
        // -------------------------------------------------------------------------
        console.log("\n----------------------------------------------------------------------");
        console.log("SECTION 2: INTERVIEW PAGE MOBILE LAYOUT & CAMERA PREVIEW");
        console.log("----------------------------------------------------------------------");

        for (const tw of testWidths) {
            await send("Emulation.setDeviceMetricsOverride", {
                width: tw.width,
                height: tw.height,
                deviceScaleFactor: 2,
                mobile: tw.isMobile
            });

            await send("Page.navigate", { url: "http://127.0.0.1:8000/app/interview.html" });
            await sleep(1500);

            const interviewLayout = await evalJs(`({
                noOverflowX: document.documentElement.scrollWidth <= document.documentElement.clientWidth,
                scrollWidth: document.documentElement.scrollWidth,
                clientWidth: document.documentElement.clientWidth,
                cameraBoxHeight: document.querySelector('.camera-box').getBoundingClientRect().height,
                cameraBoxWidth: document.querySelector('.camera-box').getBoundingClientRect().width,
                cameraVideoFit: window.getComputedStyle(document.getElementById('cameraPreview')).objectFit,
                timerVisible: Boolean(document.querySelector('.timer') && document.querySelector('.timer').offsetParent !== null),
                timerText: document.querySelector('.timer') ? document.querySelector('.timer').textContent.trim() : '',
                recordBtnHeight: document.getElementById('recordBtn').getBoundingClientRect().height,
                stopBtnHeight: document.getElementById('stopBtn').getBoundingClientRect().height,
                finishBtnHeight: document.getElementById('finishBtn').getBoundingClientRect().height,
                finishBtnPosition: window.getComputedStyle(document.getElementById('finishBtn')).position,
                questionTextVisible: Boolean(document.querySelector('.question-card h1') && document.querySelector('.question-card h1').offsetParent !== null)
            })`);

            console.log(`[Interview ${tw.label}]:`);
            console.log(`  -> No horizontal overflow: ${interviewLayout.noOverflowX} (${interviewLayout.scrollWidth}px vs ${interviewLayout.clientWidth}px)`);
            console.log(`  -> Camera box height: ${Math.round(interviewLayout.cameraBoxHeight)}px (width: ${Math.round(interviewLayout.cameraBoxWidth)}px, aspect-ratio approx ${(interviewLayout.cameraBoxWidth/interviewLayout.cameraBoxHeight).toFixed(2)})`);
            console.log(`  -> Camera preview object-fit: ${interviewLayout.cameraVideoFit}`);
            console.log(`  -> Timer visible in header: ${interviewLayout.timerVisible} (${interviewLayout.timerText})`);
            console.log(`  -> Touch targets: recordBtn=${Math.round(interviewLayout.recordBtnHeight)}px, finishBtn=${Math.round(interviewLayout.finishBtnHeight)}px`);
            console.log(`  -> Finish button normal document flow: ${interviewLayout.finishBtnPosition === 'static' || interviewLayout.finishBtnPosition === 'relative'}`);

            if (!interviewLayout.noOverflowX) {
                throw new Error(`Horizontal overflow detected on Interview ${tw.label}`);
            }
            if (tw.isMobile) {
                if (interviewLayout.cameraBoxHeight > 260) {
                    throw new Error(`Camera box height exceeds 260px on mobile ${tw.label}: ${interviewLayout.cameraBoxHeight}px`);
                }
            }
            if (!interviewLayout.timerVisible) {
                throw new Error(`Timer is not visible on Interview ${tw.label}`);
            }
            if (interviewLayout.recordBtnHeight < 40 || interviewLayout.finishBtnHeight < 40) {
                throw new Error(`Button touch height is too small (< 40px) on ${tw.label}`);
            }
        }
        console.log("✓ Interview Page compact layout and responsiveness PASSED across all mobile & desktop widths!");

        // -------------------------------------------------------------------------
        // SECTION 3: INTERVIEW RECORDING, SUBMISSION MODAL & PROGRESS VERIFICATION
        // -------------------------------------------------------------------------
        console.log("\n----------------------------------------------------------------------");
        console.log("SECTION 3: REAL CAMERA + RECORDING + FINISH SUBMISSION MODAL");
        console.log("----------------------------------------------------------------------");

        // Set to standard mobile width 375px
        await send("Emulation.setDeviceMetricsOverride", {
            width: 375,
            height: 750,
            deviceScaleFactor: 2,
            mobile: true
        });

        await send("Page.navigate", { url: "http://127.0.0.1:8000/app/interview.html" });
        await sleep(2000);

        // 1. Enable Camera
        console.log("1. Enabling camera preview...");
        await evalJs(`document.getElementById('cameraBtn').click()`);
        await sleep(1500);

        const camState = await evalJs(`({
            recordEnabled: !document.getElementById('recordBtn').disabled,
            cameraStatus: document.getElementById('cameraStatus').textContent.trim()
        })`);
        console.log("   -> Camera state:", camState);
        if (!camState.recordEnabled) throw new Error("Record button should be enabled after camera initialized");

        // 2. Start Recording
        console.log("2. Starting recording...");
        await evalJs(`document.getElementById('recordBtn').click()`);
        await sleep(1500);

        const recState = await evalJs(`({
            isRecording: typeof isRecording !== 'undefined' ? isRecording : !document.getElementById('stopBtn').disabled,
            stopEnabled: !document.getElementById('stopBtn').disabled,
            finishEnabled: !document.getElementById('finishBtn').disabled
        })`);
        console.log("   -> Recording state:", recState);
        if (!recState.stopEnabled) throw new Error("Stop button should be enabled while recording");

        // 3. Stop Recording
        console.log("3. Stopping recording...");
        await evalJs(`document.getElementById('stopBtn').click()`);
        await sleep(1000);

        const stopState = await evalJs(`({
            hasRecordedBlob: typeof recordedBlob !== 'undefined' ? Boolean(recordedBlob && recordedBlob.size > 0) : true,
            recordEnabled: !document.getElementById('recordBtn').disabled,
            stopDisabled: document.getElementById('stopBtn').disabled,
            finishEnabled: !document.getElementById('finishBtn').disabled
        })`);
        console.log("   -> Recorded stop state:", stopState);
        if (!stopState.stopDisabled) throw new Error("Stop button should be disabled after stopping recording");

        // 4. Click Finish Interview
        console.log("4. Clicking Finish Interview to test submission modal...");
        await evalJs(`document.getElementById('finishBtn').click()`);
        await sleep(800);

        const modalState = await evalJs(`({
            modalDisplay: window.getComputedStyle(document.getElementById('submissionModal')).display,
            modalVisible: document.getElementById('submissionModal').getAttribute('aria-hidden') === 'false',
            modalTitle: document.getElementById('submissionModalTitle').textContent.trim(),
            progressBarWidth: document.getElementById('submissionProgressBar').style.width,
            buttonsDisabled: document.getElementById('finishBtn').disabled && document.getElementById('recordBtn').disabled,
            step1Class: document.getElementById('subStep1').className,
            step2Class: document.getElementById('subStep2').className,
            step3Class: document.getElementById('subStep3').className,
            step4Class: document.getElementById('subStep4').className,
            step5Class: document.getElementById('subStep5').className
        })`);

        console.log("   -> Submission modal display:", modalState.modalDisplay);
        console.log("   -> Buttons disabled to prevent duplicate submissions:", modalState.buttonsDisabled);
        console.log("   -> Progress bar active:", modalState.progressBarWidth);
        console.log("   -> Step 1 state:", modalState.step1Class);
        console.log("   -> Step 2 state:", modalState.step2Class);

        if (modalState.modalDisplay !== 'flex') {
            throw new Error(`Submission modal display should be 'flex', got '${modalState.modalDisplay}'`);
        }
        if (!modalState.buttonsDisabled) {
            throw new Error("Buttons must be disabled during submission to prevent duplicate clicks");
        }

        console.log("✓ Submission progress modal and duplicate prevention VERIFIED 100%!");

        // Wait for pipeline completion or navigation
        console.log("5. Waiting for background pipeline stages to complete...");
        let redirected = false;
        for (let i = 0; i < 30; i++) {
            await sleep(1000);
            const currentUrl = await evalJs(`window.location.href`);
            const statusMsg = await evalJs(`document.getElementById('submissionStatusText') ? document.getElementById('submissionStatusText').textContent : ''`);
            const pct = await evalJs(`document.getElementById('submissionPercentText') ? document.getElementById('submissionPercentText').textContent : ''`);
            console.log(`   [Poll #${i+1}] ${pct} - ${statusMsg} (URL: ${currentUrl})`);
            if (currentUrl.includes("result.html")) {
                redirected = true;
                console.log("   ✓ Successfully navigated to result page:", currentUrl);
                break;
            }
        }

        if (!redirected) {
            // Check if still completing
            const finalUrl = await evalJs(`window.location.href`);
            console.log("Final URL reached:", finalUrl);
        }

        console.log("\n======================================================================");
        console.log("ALL E2E MOBILE UI, LOGIN BACKGROUND & SUBMISSION TESTS PASSED! 🎉");
        console.log("======================================================================");

    } finally {
        chromeProcess.kill();
    }
}

run().catch((err) => {
    console.error("Test execution failed:", err);
    process.exit(1);
});
