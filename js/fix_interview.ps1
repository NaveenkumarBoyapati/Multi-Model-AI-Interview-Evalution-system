$file = "D:\Nani Personal\multi model another work\js\interview.js"

if (!(Test-Path $file)) {
    Write-Host "interview.js not found!" -ForegroundColor Red
    exit
}

$js = Get-Content $file -Raw

# =========================================================
# 1. ADD TAB SWITCH VARIABLES
# =========================================================

if ($js -notmatch "let tabSwitchCount = 0;") {

    $js = $js -replace `
        'let isFinishing = false;', `
        @'
let isFinishing = false;

// =========================================
// TAB SWITCH / INTERVIEW TERMINATION
// =========================================

let tabSwitchCount = 0;
let interviewTerminated = false;
'@
}


# =========================================================
# 2. ADD TAB SWITCH DETECTION
# =========================================================

if ($js -notmatch 'document\.addEventListener\(\s*"visibilitychange"') {

    $tabCode = @'

// =========================================
// TAB SWITCH DETECTION
// =========================================

document.addEventListener(
    "visibilitychange",
    function () {

        // Ignore if interview is already finishing
        if (isFinishing) {
            return;
        }

        // Browser tab became hidden
        if (document.hidden) {

            // Only terminate if recording is active
            if (!isRecording) {
                return;
            }

            // Prevent duplicate termination
            if (interviewTerminated) {
                return;
            }

            // =====================================
            // MARK INTERVIEW AS TERMINATED
            // =====================================

            interviewTerminated = true;

            tabSwitchCount++;

            console.warn(
                "Tab switch detected."
            );

            console.warn(
                "Tab switch count:",
                tabSwitchCount
            );

            // =====================================
            // MARK AS FINISHING
            // =====================================

            isFinishing = true;

            // =====================================
            // STOP TIMER
            // =====================================

            clearInterval(timerInterval);

            timerInterval = null;

            // =====================================
            // UPDATE UI
            // =====================================

            recordingStatusTitle.textContent =
                "Interview Terminated";

            recordingStatusText.textContent =
                "Interview stopped because you switched to another browser tab.";

            // =====================================
            // STOP RECORDING
            // =====================================

            if (
                mediaRecorder &&
                mediaRecorder.state !== "inactive"
            ) {

                mediaRecorder.stop();

            }

            isRecording = false;

            // =====================================
            // STOP CAMERA + MICROPHONE
            // =====================================

            if (interviewStream) {

                interviewStream
                    .getTracks()
                    .forEach(
                        track => track.stop()
                    );

            }

            console.log(
                "Interview terminated due to tab switch."
            );
        }

    }
);

'@

    $marker = '// =========================================' + "`r`n" + '// FINISH INTERVIEW'

    if ($js.Contains($marker)) {
        $js = $js.Replace(
            $marker,
            $tabCode + $marker
        )
    }
}


# =========================================================
# 3. ADD TAB DATA TO FIRST UPLOAD FUNCTION
# =========================================================

$old1 = @'
const formData =
            new FormData();
'@

$new1 = @'
const formData =
            new FormData();

// =====================================
// TAB SWITCH INFORMATION
// =====================================

        formData.append(
            "tab_switch_count",
            tabSwitchCount
        );

        formData.append(
            "terminated_reason",
            interviewTerminated
                ? "Tab switch detected"
                : ""
        );
'@

$js = $js.Replace($old1, $new1)


# =========================================================
# 4. ADD TAB DATA TO SECOND UPLOAD FUNCTION
# =========================================================

$old2 = 'const formData = new FormData();'

$new2 = @'
const formData = new FormData();

// =====================================
// TAB SWITCH INFORMATION
// =====================================

    formData.append(
        "tab_switch_count",
        tabSwitchCount
    );

    formData.append(
        "terminated_reason",
        interviewTerminated
            ? "Tab switch detected"
            : ""
    );
'@

$js = $js.Replace($old2, $new2)


# =========================================================
# 5. ADD API KEY TO UPLOAD REQUESTS
# =========================================================

$oldFetch1 = @'
method: "POST",

                    body: formData
'@

$newFetch1 = @'
method: "POST",

                    headers: {
                        "X-API-Key":
                            "AI_INTERVIEW_2026_SECRET"
                    },

                    body: formData
'@

$js = $js.Replace(
    $oldFetch1,
    $newFetch1
)


$oldFetch2 = @'
method: "POST",
                body: formData
'@

$newFetch2 = @'
method: "POST",

                headers: {
                    "X-API-Key":
                        "AI_INTERVIEW_2026_SECRET"
                },

                body: formData
'@

$js = $js.Replace(
    $oldFetch2,
    $newFetch2
)


# =========================================================
# 6. SAVE MODIFIED FILE
# =========================================================

Set-Content `
    -Path $file `
    -Value $js `
    -Encoding UTF8

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " interview.js updated successfully!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Added:"
Write-Host "1. Tab switch detection"
Write-Host "2. Interview termination"
Write-Host "3. tab_switch_count"
Write-Host "4. terminated_reason"
Write-Host "5. X-API-Key"
Write-Host ""
Write-Host "File:"
Write-Host $file
Write-Host ""