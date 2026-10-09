// test_browser_cdp.js
const { spawn } = require('child_process');
const http = require('http');

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function run() {
    console.log("Starting headless Chrome with fake media stream...");
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
        console.log("Connected to Chrome target:", pageTarget.id);

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
            if (data.method === 'Runtime.exceptionThrown') {
                console.error("RUNTIME EXCEPTION IN BROWSER:", data.params.exceptionDetails);
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

        console.log("Navigating to http://127.0.0.1:8000/app/interview.html...");
        await send("Page.navigate", { url: "http://127.0.0.1:8000/app/interview.html" });
        await sleep(2500);

        // Check console exceptions
        const fatalExceptions = consoleMessages.filter(m => m.text && m.text.includes("SyntaxError"));
        console.log("Fatal Syntax Errors count:", fatalExceptions.length);
        if (fatalExceptions.length > 0) {
            console.error("Syntax errors found:", fatalExceptions);
        }

        // 1. Initial button states
        const initialStates = await evalJs(`({
            recordBtnDisabled: document.getElementById('recordBtn').disabled,
            stopBtnDisabled: document.getElementById('stopBtn').disabled,
            cameraBtnDisabled: document.getElementById('cameraBtn').disabled,
            cameraStatus: document.getElementById('cameraStatus').textContent.trim(),
            micStatus: document.getElementById('micStatus').textContent.trim()
        })`);
        console.log("Initial Button States:", initialStates);

        // 2. Enable Camera (with fake webcam in headless Chrome)
        console.log("Clicking Enable Camera button...");
        await evalJs(`document.getElementById('cameraBtn').click()`);
        await sleep(2000);

        const afterCameraStates = await evalJs(`({
            recordBtnDisabled: document.getElementById('recordBtn').disabled,
            stopBtnDisabled: document.getElementById('stopBtn').disabled,
            cameraBtnDisabled: document.getElementById('cameraBtn').disabled,
            cameraStatus: document.getElementById('cameraStatus').textContent.trim(),
            micStatus: document.getElementById('micStatus').textContent.trim(),
            hasStream: Boolean(window.interviewStream && window.interviewStream.active)
        })`);
        console.log("After Camera Enabled States:", afterCameraStates);

        // 3. Start Recording
        console.log("Clicking Start Recording button...");
        await evalJs(`document.getElementById('recordBtn').click()`);
        await sleep(1500);

        const afterRecordStates = await evalJs(`({
            isRecording: window.isRecording,
            interviewActive: window.interviewActive,
            recordBtnDisabled: document.getElementById('recordBtn').disabled,
            stopBtnDisabled: document.getElementById('stopBtn').disabled,
            finishBtnDisabled: document.getElementById('finishBtn').disabled,
            recordingText: document.getElementById('recordBtn').textContent.trim()
        })`);
        console.log("After Start Recording States:", afterRecordStates);

        // 4. Stop Recording
        console.log("Clicking Stop button...");
        await evalJs(`document.getElementById('stopBtn').click()`);
        await sleep(1000);

        const afterStopStates = await evalJs(`({
            isRecording: window.isRecording,
            recordBtnDisabled: document.getElementById('recordBtn').disabled,
            stopBtnDisabled: document.getElementById('stopBtn').disabled,
            finishBtnDisabled: document.getElementById('finishBtn').disabled
        })`);
        console.log("After Stop Recording States:", afterStopStates);

        // 5. Next Question
        console.log("Clicking Next Question button...");
        await evalJs(`document.getElementById('nextBtn').click()`);
        await sleep(500);
        const questionNumber = await evalJs(`document.getElementById('currentQuestion').textContent.trim()`);
        console.log("Current Question after Next Question:", questionNumber);

        // 6. Finish Interview
        console.log("Starting recording again before Finish...");
        await evalJs(`document.getElementById('recordBtn').click()`);
        await sleep(1500);

        console.log("Clicking Finish Interview button...");
        await evalJs(`document.getElementById('finishBtn').click()`);
        await sleep(1000);

        const finishingStates = await evalJs(`({
            interviewFinishingNormally: window.interviewFinishingNormally,
            isFinishing: window.isFinishing,
            recordBtnDisabled: document.getElementById('recordBtn').disabled,
            stopBtnDisabled: document.getElementById('stopBtn').disabled,
            finishBtnDisabled: document.getElementById('finishBtn').disabled
        })`);
        console.log("Finish Interview States:", finishingStates);

        ws.close();
        console.log("\nALL BROWSER CONTROL STEPS TESTED SUCCESSFULLY!");
    } finally {
        chromeProcess.kill('SIGKILL');
    }
}

run().catch(err => {
    console.error("Test failed:", err);
    process.exit(1);
});
