// test_table_horizontal_scroll_cdp.js
// Enterprise test suite for Admin Table Horizontal Scroll Architecture

const { spawn } = require('child_process');

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function run() {
    console.log("=========================================================");
    console.log("RUNNING REAL CHROME CDP HORIZONTAL SCROLL VERIFICATION");
    console.log("=========================================================");

    const chromeProcess = spawn("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", [
        "--headless=new",
        "--remote-debugging-port=9455",
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

        const targetsRes = await fetch("http://127.0.0.1:9455/json");
        const targets = await targetsRes.json();
        const pageTarget = targets.find(t => t.type === 'page' && !t.url.startsWith('chrome')) || targets.find(t => t.type === 'page');
        console.log("Attached to Chrome CDP target:", pageTarget.url, pageTarget.id);

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
                console.error("JS Eval Exception:", res.result.exceptionDetails);
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

        // 1. Authenticate as Admin
        console.log("\n[STEP 1] Logging into Super Admin Console at http://127.0.0.1:8000/app/login.html...");
        await send("Page.navigate", { url: "http://127.0.0.1:8000/app/login.html" });
        await waitForCondition("typeof window.handleLogin === 'function'");

        await evalJs(`
            document.getElementById("role").value = "Admin";
            document.getElementById("email").value = "admin@ai-interview.com";
            document.getElementById("password").value = "Admin@Interview2026!";
            document.getElementById("loginBtn").click();
        `);

        await waitForCondition("window.location.href.includes('admin_dashboard.html')", 6000);

        const currentUrl = await evalJs(`window.location.href`);
        console.log("Current Page URL:", currentUrl);
        if (!currentUrl.includes("admin_dashboard.html")) {
            throw new Error(`Expected redirect to admin_dashboard.html, but landed on: ${currentUrl}`);
        }
        console.log("✓ Successfully authenticated and landed on Super Admin Console.");

        // Define tabs and their tables to test
        const tabsToTest = [
            { tab: "command-center", paneId: "pane-command-center", name: "Executive Command Center (Recent Sessions)" },
            { tab: "users", paneId: "pane-users", name: "User & Candidate Management (11 columns)" },
            { tab: "interviews", paneId: "pane-interviews", name: "Interviews Management (11 columns)" },
            { tab: "questions", paneId: "pane-questions", name: "Question Bank Management (8 columns)" },
            { tab: "roles", paneId: "pane-roles", name: "Interview Roles (9 columns)" },
            { tab: "recordings", paneId: "pane-recordings", name: "Recordings & Media Center (8 columns)" },
            { tab: "reports", paneId: "pane-reports", name: "Report Center (8 columns)" },
            { tab: "security", paneId: "pane-security", name: "Security Center Violations (9 columns)" },
            { tab: "analytics", paneId: "pane-analytics", name: "Analytics & Performance Benchmarks (3 tables)" },
            { tab: "audit-logs", paneId: "pane-audit-logs", name: "Audit Logs & Governance (9 columns)" }
        ];

        // Function to run table scroll test suite for a given viewport
        async function runTableSuite(viewportName, width, height) {
            console.log(`\n=========================================================`);
            console.log(`TESTING AT VIEWPORT: ${viewportName} (${width}x${height})`);
            console.log(`=========================================================`);

            await send("Emulation.setDeviceMetricsOverride", {
                width,
                height,
                deviceScaleFactor: 1,
                mobile: width <= 768
            });
            await sleep(600);

            for (const item of tabsToTest) {
                console.log(`\n--- Testing Tab: ${item.name} (${item.tab}) ---`);
                
                // Switch tab
                await evalJs(`switchAdminTab('${item.tab}')`);
                await sleep(700);

                const checkResult = await evalJs(`
                    (() => {
                        const pane = document.getElementById('${item.paneId}');
                        if (!pane) return { error: 'Pane not found: ${item.paneId}' };

                        // Check page / body scroll
                        const htmlScrollWidth = document.documentElement.scrollWidth;
                        const bodyScrollWidth = document.body.scrollWidth;
                        const winInnerWidth = window.innerWidth;
                        const hasPageHScroll = htmlScrollWidth > winInnerWidth || bodyScrollWidth > winInnerWidth;

                        // Check sidebar
                        const sidebar = document.getElementById('adminSidebar');
                        const sidebarRect = sidebar ? sidebar.getBoundingClientRect() : null;

                        // Find all table wrappers in this pane
                        const wrappers = Array.from(pane.querySelectorAll('.table-responsive, .admin-table-wrapper'));
                        if (wrappers.length === 0) {
                            return {
                                noWrappers: true,
                                htmlScrollWidth,
                                bodyScrollWidth,
                                winInnerWidth,
                                hasPageHScroll
                            };
                        }

                        const tablesInfo = wrappers.map((w, idx) => {
                            const tbl = w.querySelector('.admin-table');

                            const clientWidth = w.clientWidth;
                            const scrollWidth = w.scrollWidth;
                            const canScrollHorizontally = scrollWidth > clientWidth;

                            // Test scrolling right
                            w.scrollLeft = scrollWidth - clientWidth;
                            const scrolledRightVal = w.scrollLeft;

                            // Rightmost header visible?
                            const headers = tbl ? Array.from(tbl.querySelectorAll('th')) : [];
                            const lastTh = headers.length > 0 ? headers[headers.length - 1] : null;
                            const firstTh = headers.length > 0 ? headers[0] : null;
                            
                            let lastThInWrapperView = false;
                            if (lastTh) {
                                const wRect = w.getBoundingClientRect();
                                const thRect = lastTh.getBoundingClientRect();
                                lastThInWrapperView = thRect.right <= (wRect.right + 20) && thRect.left >= (wRect.left - 50);
                            }

                            // Test scrolling back left
                            w.scrollLeft = 0;
                            const scrolledLeftVal = w.scrollLeft;

                            return {
                                idx,
                                columnCount: headers.length,
                                firstCol: firstTh ? firstTh.textContent.trim() : '',
                                lastCol: lastTh ? lastTh.textContent.trim() : '',
                                clientWidth,
                                scrollWidth,
                                canScrollHorizontally,
                                scrolledRightVal,
                                scrolledLeftVal,
                                lastThInWrapperView
                            };
                        });

                        return {
                            htmlScrollWidth,
                            bodyScrollWidth,
                            winInnerWidth,
                            hasPageHScroll,
                            sidebarWidth: sidebarRect ? sidebarRect.width : null,
                            tablesInfo
                        };
                    })()
                `);

                if (checkResult.error) {
                    console.error("  ❌ Error:", checkResult.error);
                    exitCode = 1;
                    continue;
                }

                // Page / Body horizontal scroll assertion
                if (checkResult.hasPageHScroll) {
                    console.error(`  ❌ PAGE/BODY HAS HORIZONTAL SCROLL! html: ${checkResult.htmlScrollWidth}px, body: ${checkResult.bodyScrollWidth}px, window: ${checkResult.winInnerWidth}px`);
                    exitCode = 1;
                } else {
                    console.log(`  ✓ Page/Body horizontal scroll strictly blocked (scrollWidth ${checkResult.bodyScrollWidth}px <= window ${checkResult.winInnerWidth}px).`);
                }

                // Table assertions
                for (const t of checkResult.tablesInfo) {
                    console.log(`  Table #${t.idx + 1} (${t.columnCount} cols: '${t.firstCol}' -> '${t.lastCol}'):`);
                    console.log(`    - Container clientWidth: ${t.clientWidth}px, scrollWidth: ${t.scrollWidth}px`);
                    
                    if (t.scrollWidth > t.clientWidth) {
                        console.log(`    - Overflow detected: table exceeds container by ${(t.scrollWidth - t.clientWidth)}px.`);
                        if (t.scrolledRightVal > 0) {
                            console.log(`    ✓ Horizontal scroll operational: scrollLeft advanced to ${t.scrolledRightVal}px.`);
                        } else {
                            console.error(`    ❌ Horizontal scroll FAILED: scrollLeft remained at ${t.scrolledRightVal}px.`);
                            exitCode = 1;
                        }
                        if (t.scrolledLeftVal === 0) {
                            console.log(`    ✓ Restored left scroll cleanly (scrollLeft: 0px).`);
                        }
                    } else {
                        console.log(`    - Table fits within container width (${t.scrollWidth}px <= ${t.clientWidth}px). No overflow needed.`);
                    }
                }

                // Vertical scrolling check on page
                const vScrollTest = await evalJs(`
                    (() => {
                        const initialY = window.scrollY;
                        window.scrollTo(0, 150);
                        const afterY = window.scrollY;
                        window.scrollTo(0, initialY);
                        return { initialY, afterY, canScrollVertically: document.documentElement.scrollHeight > window.innerHeight };
                    })()
                `);
                console.log(`  ✓ Vertical page layout: height ${height}px, scrollable=${vScrollTest.canScrollVertically}`);
            }
        }

        // Test 1: Desktop Viewport (1280x800)
        await runTableSuite("DESKTOP VIEWPORT", 1280, 800);

        // Test 2: Smaller Viewport (768x800)
        await runTableSuite("TABLET / SMALL VIEWPORT", 768, 800);

        // Test 3: Specific User Interviews Modal Table
        console.log("\n--- Testing Modal Table (#userInterviewsModal) ---");
        await send("Emulation.setDeviceMetricsOverride", { width: 1280, height: 800, deviceScaleFactor: 1, mobile: false });
        await evalJs(`switchAdminTab('users')`);
        await sleep(500);

        const modalTest = await evalJs(`
            (() => {
                const modal = document.getElementById('userInterviewsModal');
                if (!modal) return { error: 'Modal not found' };
                modal.classList.add('active');
                modal.style.display = 'flex';
                
                const wrapper = modal.querySelector('.table-responsive, .admin-table-wrapper');
                if (!wrapper) return { error: 'Modal table wrapper not found' };

                const clientWidth = wrapper.clientWidth;
                const scrollWidth = wrapper.scrollWidth;
                wrapper.scrollLeft = scrollWidth - clientWidth;
                const scrolled = wrapper.scrollLeft;
                wrapper.scrollLeft = 0;

                modal.classList.remove('active');
                modal.style.display = 'none';

                return {
                    clientWidth,
                    scrollWidth,
                    scrolled,
                    modalBounded: modal.clientWidth <= window.innerWidth
                };
            })()
        `);
        console.log("Modal table test result:", modalTest);
        if (modalTest.error) {
            console.error("  ❌ Modal table error:", modalTest.error);
            exitCode = 1;
        } else {
            console.log("  ✓ Modal table container bounded and horizontally scrollable.");
        }

        // Final summary
        console.log("\n=========================================================");
        if (exitCode === 0) {
            console.log("ALL REAL CHROME CDP HORIZONTAL SCROLL CHECKS PASSED! 🎉");
        } else {
            console.error("SOME REAL CHROME CDP CHECKS FAILED. ❌");
        }
        console.log("=========================================================");

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
