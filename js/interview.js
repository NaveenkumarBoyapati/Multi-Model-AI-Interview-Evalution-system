// =========================================
// AI INTERVIEW - QUESTION MANAGEMENT
// =========================================

// =========================================
// ROLE QUESTION DATASET
// =========================================

const roleQuestions = {

    "Python Developer": [
        "What is Python and what are its main features?",
        "What is the difference between a list and a tuple in Python?",
        "What are Python dictionaries and how are they used?",
        "Explain the concept of mutable and immutable objects in Python.",
        "What is the difference between == and is in Python?",
        "What are functions in Python?",
        "What are *args and **kwargs in Python?",
        "Explain Python exception handling.",
        "What is the purpose of try, except and finally?",
        "What are Python modules and packages?",
        "What is object-oriented programming in Python?",
        "Explain inheritance in Python.",
        "What is polymorphism in Python?",
        "What is encapsulation in Python?",
        "What is abstraction in Python?",
        "What are constructors in Python?",
        "What is the difference between class and object?",
        "What are decorators in Python?",
        "What are lambda functions?",
        "What is list comprehension?",
        "What is the difference between shallow copy and deep copy?",
        "What is a generator in Python?",
        "What is the use of the yield keyword?",
        "What is an iterator in Python?",
        "What is recursion?",
        "How does garbage collection work in Python?",
        "What is PEP 8?",
        "What are virtual environments in Python?",
        "What is pip?",
        "How do you read and write files in Python?",
        "What is JSON and how can Python work with JSON?",
        "What is the difference between append() and extend()?",
        "What is the difference between remove(), pop() and del?",
        "How can you reverse a string in Python?",
        "How can you find duplicate elements in a list?",
        "How do you sort a list in Python?",
        "What is the difference between sort() and sorted()?",
        "What are sets in Python?",
        "What are set operations?",
        "What is a Python namespace?",
        "What is variable scope in Python?",
        "Explain local, global and nonlocal variables.",
        "What is method overriding?",
        "Does Python support method overloading?",
        "What is multiple inheritance?",
        "What is MRO in Python?",
        "What is duck typing?",
        "What is dynamic typing?",
        "What are Python libraries?",
        "What is NumPy used for?",
        "What is Pandas used for?",
        "What is Matplotlib used for?",
        "What is the difference between NumPy and Pandas?",
        "What is a DataFrame?",
        "What is a Series in Pandas?",
        "How do you handle missing data using Pandas?",
        "How do you remove duplicate records using Pandas?",
        "How do you merge two DataFrames?",
        "What is groupby() in Pandas?",
        "What is data filtering in Pandas?",
        "How can you read a CSV file using Pandas?",
        "How can you export a DataFrame to CSV?",
        "What is Flask?",
        "What is Django?",
        "What is FastAPI?",
        "What is an API?",
        "What is REST API?",
        "What is HTTP?",
        "What are GET and POST requests?",
        "What is JSON?",
        "How do you connect Python with MySQL?",
        "What is SQLAlchemy?",
        "What is unit testing?",
        "What is pytest?",
        "How do you debug a Python program?",
        "What are logging mechanisms in Python?",
        "What is multithreading?",
        "What is multiprocessing?",
        "What is asynchronous programming?",
        "What is asyncio?",
        "What is a process?",
        "What is a thread?",
        "What is a race condition?",
        "What is a deadlock?",
        "What is time complexity?",
        "What is space complexity?",
        "How do you optimize Python code?",
        "What are algorithms?",
        "What are data structures?",
        "Explain stack and queue in Python.",
        "How can you implement a stack in Python?",
        "How can you implement a queue in Python?",
        "What is a linked list?",
        "What is binary search?",
        "What is linear search?",
        "What is sorting?",
        "Explain bubble sort.",
        "Explain selection sort.",
        "Explain insertion sort.",
        "How would you optimize a slow Python application?"
    ],

    "Java Developer": [
        "What is Java and what are its main features?",
        "What is JVM?",
        "What is JDK?",
        "What is JRE?",
        "What is the difference between JDK, JRE and JVM?",
        "What is object-oriented programming?",
        "What is a class in Java?",
        "What is an object in Java?",
        "Explain inheritance in Java.",
        "Explain polymorphism in Java.",
        "What is encapsulation?",
        "What is abstraction?",
        "What is method overloading?",
        "What is method overriding?",
        "What is a constructor?",
        "What is the difference between this and super?",
        "What are access modifiers in Java?",
        "What is a static keyword?",
        "What is a final keyword?",
        "What are interfaces in Java?",
        "What are abstract classes?",
        "Difference between interface and abstract class?",
        "What is exception handling?",
        "Difference between checked and unchecked exceptions?",
        "What are try, catch and finally?",
        "What is multithreading?",
        "What is synchronization?",
        "What is a thread?",
        "What is garbage collection?",
        "What is Java Collections Framework?",
        "What is ArrayList?",
        "What is LinkedList?",
        "What is HashMap?",
        "What is HashSet?",
        "Difference between ArrayList and LinkedList?",
        "Difference between HashMap and HashSet?",
        "What is an Iterator?",
        "What are generics?",
        "What is String in Java?",
        "Difference between String and StringBuilder?",
        "What is StringBuffer?",
        "Why is String immutable in Java?",
        "What is the equals() method?",
        "What is hashCode()?",
        "Difference between == and equals()?",
        "What are wrapper classes?",
        "What is autoboxing?",
        "What is unboxing?",
        "What are Java packages?",
        "What is Maven?",
        "What is Spring Framework?",
        "What is Spring Boot?",
        "What is REST API?",
        "What is JDBC?",
        "How do you connect Java with MySQL?",
        "What is SQL?",
        "What is concurrency?",
        "What is a deadlock?",
        "What is a race condition?",
        "What is serialization?",
        "What is deserialization?",
        "What is an enum?",
        "What are lambda expressions?",
        "What is the Stream API?",
        "What is functional programming?",
        "What is Optional in Java?",
        "What are annotations?",
        "What is dependency injection?",
        "What is inversion of control?",
        "What is unit testing?",
        "What is JUnit?",
        "How do you debug Java applications?",
        "What is JVM memory?",
        "What is stack memory?",
        "What is heap memory?",
        "What is recursion?",
        "What are data structures?",
        "What is a stack?",
        "What is a queue?",
        "What is a linked list?",
        "What is binary search?",
        "What is sorting?",
        "What is time complexity?",
        "What is space complexity?",
        "How would you optimize a Java application?",
        "What is microservices architecture?",
        "What is Docker?",
        "What is Git?",
        "How do you handle conflicts in Git?",
        "What is CI/CD?",
        "How would you design a scalable Java application?",
        "How do you debug a production issue?"
    ],

    "Data Analyst": [
        "What is data analysis?",
        "What is the difference between data and information?",
        "What are structured and unstructured data?",
        "What is data cleaning?",
        "Why is data preprocessing important?",
        "What is exploratory data analysis?",
        "What is descriptive analysis?",
        "What is diagnostic analysis?",
        "What is predictive analysis?",
        "What is prescriptive analysis?",
        "What is SQL?",
        "What is a primary key?",
        "What is a foreign key?",
        "What is normalization?",
        "What is denormalization?",
        "What is an SQL JOIN?",
        "Explain INNER JOIN.",
        "Explain LEFT JOIN.",
        "Explain RIGHT JOIN.",
        "What is GROUP BY?",
        "What is ORDER BY?",
        "What is HAVING?",
        "Difference between WHERE and HAVING?",
        "What is a subquery?",
        "What is a database index?",
        "What is Excel?",
        "What are Excel pivot tables?",
        "What is VLOOKUP?",
        "What is XLOOKUP?",
        "What is conditional formatting?",
        "What are Excel charts?",
        "What is Power BI?",
        "What is a Power BI dashboard?",
        "What is Power Query?",
        "What is DAX?",
        "What is data visualization?",
        "Why is data visualization important?",
        "What is a KPI?",
        "What is a dashboard?",
        "Difference between dashboard and report?",
        "What is Pandas?",
        "What is NumPy?",
        "What is a DataFrame?",
        "What is a Pandas Series?",
        "How do you handle missing values?",
        "How do you remove duplicate data?",
        "How do you identify outliers?",
        "What is correlation?",
        "What is regression?",
        "What is mean?",
        "What is median?",
        "What is mode?",
        "What is standard deviation?",
        "What is variance?",
        "What is probability?",
        "What is sampling?",
        "What is hypothesis testing?",
        "What is a normal distribution?",
        "What is a scatter plot?",
        "What is a histogram?",
        "What is a bar chart?",
        "What is a line chart?",
        "What is a pie chart?",
        "What is a box plot?",
        "How do you choose the right visualization?",
        "How do you validate data?",
        "How do you handle inconsistent data?",
        "How do you combine datasets?",
        "What is ETL?",
        "What is data transformation?",
        "What is data integration?",
        "What is business intelligence?",
        "What is descriptive statistics?",
        "What is an outlier?",
        "What is data profiling?",
        "What is data quality?",
        "What is data governance?",
        "What is a data warehouse?",
        "What is a data mart?",
        "What is OLAP?",
        "What is OLTP?",
        "What is a fact table?",
        "What is a dimension table?",
        "What is a star schema?",
        "What is a snowflake schema?",
        "How do you optimize an SQL query?",
        "What is a window function?",
        "What is ROW_NUMBER()?",
        "What is RANK()?",
        "What is a CTE?",
        "What is a stored procedure?",
        "How do you analyze sales data?",
        "How do you find trends in a dataset?",
        "How do you communicate analytical findings?",
        "How would you explain a complex analysis to a non-technical person?"
    ],

    "Web Developer": [
        "What is HTML5 and what are semantic elements?",
        "What is CSS Flexbox and how does it work?",
        "What is CSS Grid and when do you use it?",
        "What is responsive web design and media queries?",
        "What is the difference between let, const, and var in JavaScript?",
        "What are closures in JavaScript?",
        "What is the Event Loop in JavaScript?",
        "What are Promises and async/await?",
        "What is the DOM and how do you manipulate it?",
        "What is the difference between client-side and server-side rendering?",
        "What are RESTful APIs and how do you call them with fetch?",
        "How do you optimize website load performance?",
        "What is CORS and how do you handle it?",
        "What is Git and how do you manage branches?",
        "How do you secure web applications against XSS and CSRF?",
        "What is a single page application (SPA)?",
        "What are browser storage options (LocalStorage vs SessionStorage)?",
        "How do you debug JavaScript issues using browser DevTools?"
    ]
};


// =========================================
// HR QUESTION DATASET
// =========================================

const hrQuestions = [

    "What are your strengths?",
    "What are your weaknesses?",
    "Why should we hire you?",
    "Why do you want to join our company?",
    "Why did you choose this career?",
    "Where do you see yourself in five years?",
    "What motivates you?",
    "How do you handle pressure?",
    "How do you handle failure?",
    "How do you handle criticism?",
    "Tell me about a challenging situation you faced.",
    "Tell me about a time you worked in a team.",
    "How do you handle conflicts with team members?",
    "What is your biggest achievement?",
    "Tell me about a project you are proud of.",
    "What did you learn from your previous project?",
    "How do you manage your time?",
    "How do you prioritize your tasks?",
    "Are you comfortable working in a team?",
    "Are you comfortable working independently?",
    "How do you react when you make a mistake?",
    "What are your short-term goals?",
    "What are your long-term goals?",
    "Why should we select you over other candidates?",
    "What makes you different from other candidates?",
    "What kind of work environment do you prefer?",
    "How do you stay motivated during difficult tasks?",
    "How do you learn new technologies?",
    "What are your expectations from this job?",
    "Are you willing to relocate?",
    "How do you deal with deadlines?",
    "How do you handle multiple tasks?",
    "Tell me about a time you showed leadership.",
    "Tell me about a time you solved a difficult problem.",
    "What would you do if you disagreed with your manager?",
    "What would you do if a teammate was not contributing?",
    "How do you respond to negative feedback?",
    "What does success mean to you?",
    "What does teamwork mean to you?",
    "What is your ideal workplace?",
    "What are your expectations from your manager?",
    "What are your hobbies?",
    "How do your hobbies help you professionally?",
    "What is one skill you want to improve?",
    "What is your biggest professional goal?",
    "How do you keep yourself updated with technology?",
    "What would you do if you were given an unfamiliar task?",
    "How do you handle unexpected changes?",
    "Do you have any questions for us?"
];


// =========================================
// FIXED QUESTIONS
// =========================================

const fixedQuestions = [

    {
        question:
            "Tell me about yourself.",

        hint:
            "Introduce yourself, your education, skills, projects and career interests.",

        difficulty:
            "Easy",

        type:
            "HR"
    },

    {
        question:
            "What are your strengths and how can they help you in this role?",

        hint:
            "Mention relevant strengths and support them with a short example.",

        difficulty:
            "Easy",

        type:
            "HR"
    }

];


// =========================================
// VARIABLES
// =========================================

let currentQuestionIndex = 0;

// URL parameter parsing for interview_id and role
try {
    const urlParams = new URLSearchParams(window.location.search);
    const queryInterviewId = urlParams.get("interview_id") || urlParams.get("id");
    if (queryInterviewId && queryInterviewId.trim() !== "" && queryInterviewId.trim() !== "null" && queryInterviewId.trim() !== "undefined") {
        sessionStorage.setItem("interviewId", queryInterviewId.trim());
        localStorage.setItem("interviewId", queryInterviewId.trim());
        console.log("[Interview Setup] Detected interview_id from URL parameter:", queryInterviewId.trim());
    } else {
        // Fresh interview session: clear stale interviewId so a new interview row is created!
        sessionStorage.removeItem("interviewId");
        localStorage.removeItem("interviewId");
        console.log("[Interview Setup] Fresh interview session initialized (no URL interview_id).");
    }
    // Cleanly clear previous session results & termination flags for a fresh interview session,
    // while preserving legitimate interviewId if already set.
    sessionStorage.removeItem("interviewResult");
    localStorage.removeItem("interviewResult");
    sessionStorage.removeItem("recordingURL");
    localStorage.removeItem("recordingURL");
    sessionStorage.removeItem("transcript");
    localStorage.removeItem("transcript");
    sessionStorage.removeItem("interviewStatus");
    localStorage.removeItem("interviewStatus");
    sessionStorage.removeItem("terminationType");
    localStorage.removeItem("terminationType");
    sessionStorage.removeItem("terminatedReason");
    localStorage.removeItem("terminatedReason");
    sessionStorage.removeItem("securityViolation");
    localStorage.removeItem("securityViolation");
    sessionStorage.removeItem("terminatedAt");
    localStorage.removeItem("terminatedAt");
    sessionStorage.removeItem("tabSwitchCount");
    localStorage.removeItem("tabSwitchCount");
    sessionStorage.removeItem("clientSessionId");
    localStorage.removeItem("clientSessionId");

    const queryRole = urlParams.get("role");
    if (queryRole && queryRole.trim() !== "") {
        localStorage.setItem("selectedRole", queryRole.trim());
        sessionStorage.setItem("selectedRole", queryRole.trim());
    }
} catch (urlErr) {
    console.warn("[Interview Setup] URL parsing notice:", urlErr);
}

let selectedRole =
    sessionStorage.getItem("selectedRole") ||
    localStorage.getItem("selectedRole") ||
    "Python Developer";

let interviewQuestions = [];


// =========================================
// CANDIDATE ANSWER TRACKING
// =========================================

let candidateAnswers = [];

// =========================================
// QUESTION RECORDING TIMING
// =========================================

let interviewRecordingStartTime = null;

const questionStartTimes = {};
const questionEndTimes = {};

function getRecordingTime() {
    if (!interviewRecordingStartTime) {
        return 0;
    }

    return (Date.now() - interviewRecordingStartTime) / 1000;
}


// =========================================
// TIMER
// =========================================

let timeLeft = 40 * 60;

let timerInterval = null;


// =========================================
// RECORDING
// =========================================

let isRecording = false;

let mediaRecorder = null;

let recordedChunks = [];

let recordedBlob = null;

let recordedVideoURL = null;

let isFinishing = false;


// =========================================
// TAB SWITCH SECURITY & FINISH STATE
// =========================================

let tabSwitchCount = 0;
let interviewTerminated = false;
let interviewTerminating = false;
let interviewFinishingNormally = false;
let interviewActive = false;


// =========================================
// CAMERA
// =========================================

let interviewStream = null;


// =========================================
// GET HTML ELEMENTS
// =========================================

const currentQuestionElement =
    document.getElementById(
        "currentQuestion"
    );

const totalQuestionsElement =
    document.getElementById(
        "totalQuestions"
    );

const timerElement =
    document.getElementById(
        "timer"
    );

const questionTextElement =
    document.getElementById(
        "questionText"
    );

const questionHintElement =
    document.querySelector(
        ".question-hint"
    );

const difficultyElement =
    document.querySelector(
        ".difficulty"
    );

const questionNumberElement =
    document.querySelector(
        ".question-number"
    );

const recordButton =
    document.getElementById(
        "recordBtn"
    );

const stopButton =
    document.getElementById(
        "stopBtn"
    );

const previousButton =
    document.getElementById(
        "previousBtn"
    );

const nextButton =
    document.getElementById(
        "nextBtn"
    );

const finishButton =
    document.getElementById(
        "finishBtn"
    );

const recordingStatus =
    document.getElementById(
        "recordingStatus"
    );

const recordingStatusTitle =
    recordingStatus.querySelector(
        "strong"
    );

const recordingStatusText =
    recordingStatus.querySelector(
        "p"
    );

const cameraButton =
    document.getElementById(
        "cameraBtn"
    );

const cameraStatus =
    document.getElementById(
        "cameraStatus"
    );

const micStatus =
    document.getElementById(
        "micStatus"
    );

// Initial control states according to specification
if (recordButton) recordButton.disabled = true;
if (stopButton) stopButton.disabled = true;
if (previousButton) previousButton.disabled = true;
if (cameraButton) cameraButton.disabled = false;
if (finishButton) finishButton.disabled = false;


// =========================================
// SHUFFLE ARRAY
// =========================================

function shuffleArray(array) {

    const shuffled =
        [...array];

    for (
        let i =
            shuffled.length - 1;

        i > 0;

        i--
    ) {

        const randomIndex =
            Math.floor(
                Math.random() *
                (i + 1)
            );

        [
            shuffled[i],
            shuffled[randomIndex]
        ] = [
                shuffled[randomIndex],
                shuffled[i]
            ];

    }

    return shuffled;
}


// =========================================
// CREATE INTERVIEW QUESTIONS
// =========================================

function createInterviewQuestions() {

    const rolePool =
        roleQuestions[selectedRole] ||
        roleQuestions["Python Developer"];


    const selectedRoleQuestions =
        shuffleArray(
            rolePool
        ).slice(
            0,
            13
        );


    const selectedHRQuestions =
        shuffleArray(
            hrQuestions
        ).slice(
            0,
            5
        );


    const roleFormatted =
        selectedRoleQuestions.map(
            question => {

                return {

                    question:
                        question,

                    hint:
                        "Explain the concept clearly and provide a suitable example.",

                    difficulty:
                        "Medium",

                    type:
                        "ROLE",

                    candidateAnswer:
                        ""
                };

            }
        );


    const hrFormatted =
        selectedHRQuestions.map(
            question => {

                return {

                    question:
                        question,

                    hint:
                        "Answer naturally and support your answer with a relevant example.",

                    difficulty:
                        "Medium",

                    type:
                        "HR",

                    candidateAnswer:
                        ""
                };

            }
        );


    /*
        Q1       = Fixed HR
        Q2       = Fixed HR

        Q3-Q15   = 13 Role Questions

        Q16-Q20  = 5 HR Questions
    */


    interviewQuestions = [

        ...fixedQuestions.map(
            q => ({
                ...q,
                candidateAnswer: ""
            })
        ),

        ...roleFormatted,

        ...hrFormatted

    ];


    candidateAnswers = new Array(
        interviewQuestions.length
    ).fill("");

    for (const key in questionStartTimes) {
        delete questionStartTimes[key];
    }

    for (const key in questionEndTimes) {
        delete questionEndTimes[key];
    }


    console.log(
        "Selected Role:",
        selectedRole
    );

    console.log(
        "Total Questions:",
        interviewQuestions.length
    );

    console.log(
        "Interview Questions:",
        interviewQuestions
    );

}


// =========================================
// SAVE CURRENT QUESTION ANSWER
// =========================================

function saveCurrentQuestionAnswer() {

    // =====================================
    // SAVE QUESTION END TIME
    // =====================================

    if (interviewRecordingStartTime !== null && typeof questionEndTimes[currentQuestionIndex] === "undefined") {
        questionEndTimes[currentQuestionIndex] = Date.now();
    }

    // =====================================
    // SAVE CANDIDATE ANSWER (Do not classify empty as answered)
    // =====================================

    let capturedAnswer = "";

    if (typeof answerInput !== "undefined" && answerInput && answerInput.value) {
        capturedAnswer = answerInput.value.trim();
    } else if (
        interviewQuestions &&
        interviewQuestions[currentQuestionIndex] &&
        typeof interviewQuestions[currentQuestionIndex].candidateAnswer === "string" &&
        interviewQuestions[currentQuestionIndex].candidateAnswer.trim() !== ""
    ) {
        capturedAnswer = interviewQuestions[currentQuestionIndex].candidateAnswer.trim();
    } else if (candidateAnswers[currentQuestionIndex]) {
        capturedAnswer = String(candidateAnswers[currentQuestionIndex]).trim();
    }

    candidateAnswers[currentQuestionIndex] = capturedAnswer;

    console.log(
        `Q${currentQuestionIndex + 1} status: ${capturedAnswer ? "Answered" : "Unanswered"}`
    );

    console.log(
        "Start:",
        questionStartTimes[currentQuestionIndex]
    );

    console.log(
        "End:",
        questionEndTimes[currentQuestionIndex]
    );
}


// =========================================
// DISPLAY QUESTION
// =========================================

function displayQuestion() {

    const currentQuestion =
        interviewQuestions[
        currentQuestionIndex
        ];


    if (!currentQuestion) {

        return;

    }


    questionTextElement.textContent =
        currentQuestion.question;


    questionHintElement.textContent =
        currentQuestion.hint;


    difficultyElement.textContent =
        currentQuestion.difficulty;


    currentQuestionElement.textContent =
        currentQuestionIndex + 1;


    questionNumberElement.textContent =
        `Question ${String(
            currentQuestionIndex + 1
        ).padStart(
            2,
            "0"
        )}`;


    totalQuestionsElement.textContent =
        interviewQuestions.length;


    previousButton.disabled =
        currentQuestionIndex === 0;


    if (
        currentQuestionIndex ===
        interviewQuestions.length - 1
    ) {

        nextButton.innerHTML =
            `Finish Interview
             <i class="fa-solid fa-flag-checkered"></i>`;

    } else {

        nextButton.innerHTML =
            `Next Question
             <i class="fa-solid fa-arrow-right"></i>`;

    }

}

function showQuestion(index) {
    if (typeof index !== "undefined" && index >= 0 && index < interviewQuestions.length) {
        currentQuestionIndex = index;
    }
    displayQuestion();
}


// =========================================
// TIMER
// =========================================

function updateTimer() {

    const minutes =
        Math.floor(
            timeLeft / 60
        );

    const seconds =
        timeLeft % 60;


    timerElement.textContent =
        `${String(minutes).padStart(
            2,
            "0"
        )}:${String(seconds).padStart(
            2,
            "0"
        )}`;


    if (
        timeLeft <= 0
    ) {

        clearInterval(
            timerInterval
        );

        timerInterval =
            null;

        finishInterview();

        return;

    }


    timeLeft--;

}


// =========================================
// START TIMER
// =========================================

function startTimer() {

    if (
        timerInterval !== null
    ) {

        return;

    }


    timerInterval =
        setInterval(
            updateTimer,
            1000
        );

}


// =========================================
// CAMERA + MICROPHONE (PROGRESSIVE ACQUISITION + VIRTUAL AVATAR FALLBACK)
// =========================================

let virtualCanvasAnimationId = null;
let isVirtualCamera = false;
let lastCameraError = null;

function createVirtualCameraStream(existingAudioStream = null) {
    isVirtualCamera = true;
    const canvas = document.createElement("canvas");
    canvas.width = 1280;
    canvas.height = 720;
    const ctx = canvas.getContext("2d");

    const candidateName = localStorage.getItem("userName") || sessionStorage.getItem("userName") || "Candidate";
    const candidateRole = selectedRole || localStorage.getItem("selectedRole") || "Interview Candidate";
    const initials = candidateName.split(" ").map(w => w[0]).filter(Boolean).slice(0, 2).join("").toUpperCase() || "AI";

    let analyser = null;
    let dataArray = null;
    let audioTrack = null;

    if (existingAudioStream) {
        const aTracks = existingAudioStream.getAudioTracks();
        if (aTracks.length > 0 && aTracks[0].readyState === "live") {
            audioTrack = aTracks[0];
            try {
                const AudioContextClass = window.AudioContext || window.webkitAudioContext;
                if (AudioContextClass) {
                    const audioCtx = new AudioContextClass();
                    const source = audioCtx.createMediaStreamSource(new MediaStream([audioTrack]));
                    analyser = audioCtx.createAnalyser();
                    analyser.fftSize = 64;
                    source.connect(analyser);
                    dataArray = new Uint8Array(analyser.frequencyBinCount);
                }
            } catch (aErr) {
                console.warn("[Virtual Camera] Audio analyser note:", aErr);
            }
        }
    }

    if (!audioTrack) {
        try {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            if (AudioContextClass) {
                const audioCtx = new AudioContextClass();
                const dest = audioCtx.createMediaStreamDestination();
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                gain.gain.value = 0;
                osc.connect(gain);
                gain.connect(dest);
                osc.start();
                audioTrack = dest.stream.getAudioTracks()[0];
            }
        } catch (e) {
            console.warn("[Virtual Camera] Silent audio track note:", e);
        }
    }

    let frame = 0;
    function renderFrame() {
        frame++;
        const w = canvas.width;
        const h = canvas.height;

        const grad = ctx.createLinearGradient(0, 0, w, h);
        grad.addColorStop(0, "#090d16");
        grad.addColorStop(0.5, "#0f172a");
        grad.addColorStop(1, "#1e293b");
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, w, h);

        ctx.strokeStyle = "rgba(255, 255, 255, 0.03)";
        ctx.lineWidth = 1;
        for (let x = 0; x < w; x += 60) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, h);
            ctx.stroke();
        }
        for (let y = 0; y < h; y += 60) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(w, y);
            ctx.stroke();
        }

        // Header chip
        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
        ctx.strokeStyle = "rgba(59, 130, 246, 0.4)";
        ctx.lineWidth = 1.5;
        const chipW = 320;
        const chipH = 42;
        const chipX = (w - chipW) / 2;
        const chipY = 40;
        ctx.beginPath();
        if (typeof ctx.roundRect === "function") {
            ctx.roundRect(chipX, chipY, chipW, chipH, 20);
        } else {
            ctx.rect(chipX, chipY, chipW, chipH);
        }
        ctx.fill();
        ctx.stroke();

        const pulse = (Math.sin(frame * 0.08) + 1) / 2;
        const hasLiveMic = audioTrack && audioTrack.readyState === "live" && analyser !== null;
        ctx.fillStyle = hasLiveMic ? `rgba(16, 185, 129, ${0.7 + pulse * 0.3})` : `rgba(59, 130, 246, ${0.7 + pulse * 0.3})`;
        ctx.beginPath();
        ctx.arc(chipX + 24, chipY + 21, 6 + pulse * 2, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = "#f8fafc";
        ctx.font = "bold 15px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
        ctx.textAlign = "left";
        ctx.fillText(hasLiveMic ? "LIVE AUDIO \u2022 VIRTUAL CAMERA" : "VIRTUAL INTERVIEW CAMERA", chipX + 42, chipY + 26);

        // Central Avatar Circle
        const centerX = w / 2;
        const centerY = h / 2 - 25;
        const avatarRadius = 90;

        const glowRad = ctx.createRadialGradient(centerX, centerY, avatarRadius, centerX, centerY, avatarRadius + 35);
        glowRad.addColorStop(0, "rgba(37, 99, 235, 0.35)");
        glowRad.addColorStop(1, "rgba(37, 99, 235, 0)");
        ctx.fillStyle = glowRad;
        ctx.beginPath();
        ctx.arc(centerX, centerY, avatarRadius + 35, 0, Math.PI * 2);
        ctx.fill();

        const avatarGrad = ctx.createLinearGradient(centerX - avatarRadius, centerY - avatarRadius, centerX + avatarRadius, centerY + avatarRadius);
        avatarGrad.addColorStop(0, "#2563eb");
        avatarGrad.addColorStop(1, "#1d4ed8");
        ctx.fillStyle = avatarGrad;
        ctx.beginPath();
        ctx.arc(centerX, centerY, avatarRadius, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = "#60a5fa";
        ctx.lineWidth = 3.5;
        ctx.stroke();

        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 58px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(initials, centerX, centerY);
        ctx.textBaseline = "alphabetic";

        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 28px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(candidateName, centerX, centerY + avatarRadius + 48);

        ctx.fillStyle = "#94a3b8";
        ctx.font = "500 18px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
        ctx.fillText(candidateRole, centerX, centerY + avatarRadius + 80);

        // Sound Wave Visualizer
        let volumeLevel = 0;
        if (analyser && dataArray) {
            analyser.getByteFrequencyData(dataArray);
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
            volumeLevel = sum / (dataArray.length * 255);
        } else {
            volumeLevel = (Math.sin(frame * 0.05) + 1) * 0.12;
        }

        const barCount = 28;
        const barWidth = 7;
        const barGap = 6;
        const totalBarW = barCount * barWidth + (barCount - 1) * barGap;
        const barStartX = (w - totalBarW) / 2;
        const barBaseY = h - 85;

        for (let i = 0; i < barCount; i++) {
            let barH = 8;
            if (analyser && dataArray && dataArray[i]) {
                barH = Math.max(6, (dataArray[i] / 255) * 70);
            } else {
                const waveOffset = Math.sin(frame * 0.12 + i * 0.35);
                barH = Math.max(6, (volumeLevel + 0.1) * 45 * Math.abs(waveOffset) + 8);
            }

            const bx = barStartX + i * (barWidth + barGap);
            const by = barBaseY - barH / 2;

            const bGrad = ctx.createLinearGradient(bx, by, bx, by + barH);
            bGrad.addColorStop(0, "#38bdf8");
            bGrad.addColorStop(1, "#2563eb");
            ctx.fillStyle = bGrad;

            ctx.beginPath();
            if (typeof ctx.roundRect === "function") {
                ctx.roundRect(bx, by, barWidth, barH, 3);
            } else {
                ctx.rect(bx, by, barWidth, barH);
            }
            ctx.fill();
        }

        ctx.fillStyle = "#64748b";
        ctx.font = "14px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("Virtual Camera active. Answers and speech will be evaluated normally.", centerX, h - 35);
    }

    if (virtualCanvasAnimationId) {
        clearInterval(virtualCanvasAnimationId);
    }
    virtualCanvasAnimationId = setInterval(renderFrame, 40);

    const canvasStream = canvas.captureStream ? canvas.captureStream(25) : canvas.mozCaptureStream(25);
    const videoTrack = canvasStream.getVideoTracks()[0];

    const compositeTracks = [videoTrack];
    if (audioTrack) {
        compositeTracks.push(audioTrack);
    }

    return new MediaStream(compositeTracks);
}

function handleCameraFailure(error) {
    lastCameraError = error;
    console.error("[Camera] Physical device access error:", error);

    const video = document.getElementById("cameraPreview");
    const placeholder = document.getElementById("cameraPlaceholder");
    const cameraNotice = document.getElementById("cameraNotice");
    const virtualBtn = document.getElementById("virtualCameraBtn");

    if (video) video.style.display = "none";
    if (placeholder) placeholder.style.display = "flex";

    let errDetail = "Unable to open physical camera.";
    if (error) {
        if (error.name === "NotAllowedError" || error.name === "PermissionDeniedError") {
            errDetail = "Camera or microphone permission was blocked. Click the lock \uD83D\uDD12 or camera icon in your browser address bar to Allow access, or click 'Use Virtual Camera' below to start immediately.";
        } else if (error.name === "NotFoundError" || error.name === "DevicesNotFoundError") {
            errDetail = "No webcam device was detected on your PC. You can proceed with the interview using the Virtual Camera below.";
        } else if (error.name === "NotReadableError" || error.name === "TrackStartError") {
            errDetail = "Camera is currently in use by another app (Zoom, Teams, or Windows Camera). Close other apps and retry, or use Virtual Camera below.";
        } else if (error.name === "OverconstrainedError") {
            errDetail = "Camera does not support requested resolution. Click 'Use Virtual Camera' to start without delays.";
        } else {
            errDetail = `Camera notice: ${error.message || error.name || "Device unavailable"}. Click 'Use Virtual Camera' to start your interview.`;
        }
    }

    if (cameraNotice) {
        cameraNotice.textContent = errDetail;
        cameraNotice.style.color = "#fca5a5";
    }

    if (cameraButton) {
        cameraButton.innerHTML = `<i class="fa-solid fa-arrows-rotate"></i> Retry Real Camera`;
        cameraButton.style.background = "#2563eb";
        cameraButton.disabled = false;
    }

    if (virtualBtn) {
        virtualBtn.style.display = "inline-flex";
    }

    if (cameraStatus) cameraStatus.textContent = "Not Connected";
    if (micStatus) micStatus.textContent = "Not Connected";

    const cameraStatusBadge = document.querySelector(".camera-status");
    if (cameraStatusBadge) {
        cameraStatusBadge.innerHTML = `<span class="status-dot" style="background:#ef4444;"></span> Not Connected`;
    }
}

async function initVirtualCamera(existingAudioStream = null) {
    let audioStream = existingAudioStream;
    if (!audioStream && navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === "function") {
        try {
            audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            console.log("[Virtual Camera] Microphone connected for virtual camera stream.");
        } catch (mErr) {
            console.warn("[Virtual Camera] Microphone unavailable, using silent audio track:", mErr.name);
        }
    }

    interviewStream = createVirtualCameraStream(audioStream);

    const video = document.getElementById("cameraPreview");
    const placeholder = document.getElementById("cameraPlaceholder");
    const cameraNotice = document.getElementById("cameraNotice");
    const virtualBtn = document.getElementById("virtualCameraBtn");

    if (video) {
        video.classList.add("virtual-camera-mode");
        video.srcObject = interviewStream;
        video.autoplay = true;
        video.muted = true;
        video.playsInline = true;
        video.style.display = "block";
        try {
            await video.play();
        } catch (pErr) {
            console.warn("Virtual video play notice:", pErr);
        }
    }

    if (placeholder) placeholder.style.display = "none";

    const hasAudio = interviewStream.getAudioTracks().length > 0 && audioStream !== null;
    if (cameraStatus) cameraStatus.textContent = "Camera Ready";
    if (micStatus) micStatus.textContent = hasAudio ? "Connected" : "Ready";

    const cameraStatusBadge = document.querySelector(".camera-status");
    if (cameraStatusBadge) {
        cameraStatusBadge.innerHTML = `<span class="status-dot" style="background:#10b981;"></span> Camera Ready (Virtual)`;
    }

    if (cameraButton) {
        cameraButton.innerHTML = `<i class="fa-solid fa-check"></i> Camera Enabled`;
        cameraButton.style.background = "#16a34a";
        cameraButton.disabled = true;
    }

    if (recordButton) {
        recordButton.disabled = false;
    }

    if (virtualBtn) {
        virtualBtn.style.display = "none";
    }

    if (cameraNotice) {
        cameraNotice.textContent = "Virtual Camera is active. You can now start the interview.";
        cameraNotice.style.color = "#94a3b8";
    }

    console.log("Virtual interview camera stream successfully initialized.");
    return true;
}

async function initCameraPreview(forceVirtual = false) {
    if (forceVirtual) {
        return await initVirtualCamera();
    }

    // Do not request a second camera stream if an existing stream is already active and real
    if (interviewStream && interviewStream.active && !isVirtualCamera) {
        const tracks = interviewStream.getTracks();
        if (tracks.some(track => track.readyState === "live")) {
            console.log("Existing physical camera stream is active.");
            return true;
        }
    }

    let realStream = null;
    let micStream = null;
    let lastErr = null;

    if (navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === "function") {
        // Attempt 1: Combined with flexible constraints
        try {
            realStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280, min: 320 },
                    height: { ideal: 720, min: 240 }
                },
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });
            console.log("[Camera] Physical camera + microphone connected (Attempt 1).");
        } catch (err1) {
            lastErr = err1;
            console.warn("[Camera] Attempt 1 failed:", err1.name, err1.message);

            // Attempt 2: Minimal boolean constraints
            try {
                realStream = await navigator.mediaDevices.getUserMedia({
                    video: true,
                    audio: true
                });
                console.log("[Camera] Physical camera + microphone connected (Attempt 2).");
            } catch (err2) {
                lastErr = err2;
                console.warn("[Camera] Attempt 2 failed:", err2.name, err2.message);

                // Attempt 3: Separate acquisition (try video alone, audio alone)
                let vStream = null;
                try {
                    vStream = await navigator.mediaDevices.getUserMedia({ video: true });
                } catch (vErr) {
                    lastErr = vErr;
                    console.warn("[Camera] Video-only acquisition failed:", vErr.name, vErr.message);
                }

                try {
                    micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                } catch (aErr) {
                    console.warn("[Camera] Audio-only acquisition failed:", aErr.name, aErr.message);
                }

                if (vStream && micStream) {
                    realStream = new MediaStream([...vStream.getVideoTracks(), ...micStream.getAudioTracks()]);
                } else if (vStream) {
                    realStream = vStream;
                } else if (micStream) {
                    // Microphone works but physical camera failed -> use Virtual Camera with real mic
                    console.log("[Camera] Microphone connected; camera unavailable. Switching to Virtual Avatar with mic.");
                    return await initVirtualCamera(micStream);
                }
            }
        }
    } else {
        lastErr = new Error("navigator.mediaDevices.getUserMedia is not supported or not running in a secure context.");
    }

    if (realStream) {
        if (virtualCanvasAnimationId) {
            clearInterval(virtualCanvasAnimationId);
            virtualCanvasAnimationId = null;
        }
        isVirtualCamera = false;
        interviewStream = realStream;

        const video = document.getElementById("cameraPreview");
        const placeholder = document.getElementById("cameraPlaceholder");
        const virtualBtn = document.getElementById("virtualCameraBtn");

        if (video) {
            video.classList.remove("virtual-camera-mode");
            video.srcObject = interviewStream;
            video.autoplay = true;
            video.muted = true;
            video.playsInline = true;
            video.style.display = "block";
            try {
                await video.play();
            } catch (playErr) {
                console.warn("Video play notice:", playErr);
            }
        }

        if (placeholder) {
            placeholder.style.display = "none";
        }

        if (cameraStatus) cameraStatus.textContent = "Camera Ready";
        const hasAudio = interviewStream.getAudioTracks().length > 0;
        if (micStatus) micStatus.textContent = hasAudio ? "Connected" : "Ready";

        const cameraStatusBadge = document.querySelector(".camera-status");
        if (cameraStatusBadge) {
            cameraStatusBadge.innerHTML = `<span class="status-dot"></span> Camera Ready`;
        }

        if (cameraButton) {
            cameraButton.innerHTML = `<i class="fa-solid fa-check"></i> Camera Enabled`;
            cameraButton.style.background = "#16a34a";
            cameraButton.disabled = true;
        }

        if (recordButton) {
            recordButton.disabled = false;
        }

        if (virtualBtn) {
            virtualBtn.style.display = "none";
        }

        console.log("Physical camera and microphone stream established.");
        return true;
    }

    handleCameraFailure(lastErr);
    return false;
}

if (cameraButton) {
    cameraButton.addEventListener("click", async function () {
        cameraButton.disabled = true;
        cameraButton.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Connecting...`;
        const connected = await initCameraPreview(false);
        if (!connected) {
            cameraButton.disabled = false;
        }
    });
}

const virtualCameraBtn = document.getElementById("virtualCameraBtn");
if (virtualCameraBtn) {
    virtualCameraBtn.addEventListener("click", async function () {
        virtualCameraBtn.disabled = true;
        await initVirtualCamera();
    });
}

if (stopButton) {
    stopButton.addEventListener("click", function () {
        stopRecording();
    });
}



// =========================================
// START ACTUAL RECORDING
// =========================================

recordButton.addEventListener(
    "click",
    async function () {

        if (isRecording) {

            return;

        }


        if (!interviewStream || !interviewStream.active) {
            let connected = await initCameraPreview(false);
            if (!connected) {
                console.log("[Interview] Physical camera unavailable. Automatically starting Virtual Camera stream so candidate can take interview...");
                connected = await initVirtualCamera();
            }
            if (!connected) {
                alert(
                    "Unable to initialize interview stream. Please try in another browser."
                );
                return;
            }
        }


        recordedChunks =
            [];

        recordedBlob =
            null;

        recordedVideoURL =
            null;


        if (!window.MediaRecorder) {

            alert(
                "Video recording is not supported in this browser."
            );

            return;

        }


        const supportedTypes = [

            "video/webm;codecs=vp9,opus",

            "video/webm;codecs=vp8,opus",

            "video/webm"

        ];


        let mimeType =
            "";


        for (
            const type
            of supportedTypes
        ) {

            if (
                MediaRecorder
                    .isTypeSupported(
                        type
                    )
            ) {

                mimeType =
                    type;

                break;

            }

        }


        try {

            if (mimeType) {

                mediaRecorder =
                    new MediaRecorder(
                        interviewStream,
                        {
                            mimeType:
                                mimeType
                        }
                    );

            } else {

                mediaRecorder =
                    new MediaRecorder(
                        interviewStream
                    );

            }

        } catch (error) {

            console.error(
                "MediaRecorder Error:",
                error
            );

            alert(
                "Unable to start video recording."
            );

            return;

        }


        // =====================================
        // COLLECT VIDEO CHUNKS
        // =====================================

        mediaRecorder.ondataavailable =
            function (event) {

                if (
                    event.data &&
                    event.data.size > 0
                ) {

                    recordedChunks.push(
                        event.data
                    );

                }

            };


        // =====================================
        // RECORDING ERROR
        // =====================================

        mediaRecorder.onerror =
            function (event) {

                console.error(
                    "MediaRecorder error:",
                    event.error
                );

            };


        // =====================================
        // RECORDING STOPPED
        // =====================================

        mediaRecorder.onstop =
            async function () {

                console.log(
                    "MediaRecorder stopped."
                );


                const finalMimeType =
                    mediaRecorder.mimeType ||
                    "video/webm";


                recordedBlob =
                    new Blob(
                        recordedChunks,
                        {
                            type:
                                finalMimeType
                        }
                    );


                recordedVideoURL =
                    URL.createObjectURL(
                        recordedBlob
                    );


                console.log(
                    "Recording completed."
                );


                console.log(
                    "Recording size:",
                    recordedBlob.size,
                    "bytes"
                );


                // =================================
                // UPLOAD AFTER FINISH
                // =================================

                if (
                    isFinishing
                ) {

                    recordingStatusTitle.textContent =
                        "Uploading Recording";


                    recordingStatusText.textContent =
                        "Please wait while your interview is being uploaded.";


                    const uploadSuccess =
                        await uploadInterviewRecording();


                    if (
                        uploadSuccess
                    ) {

                        finalizeInterview();

                    } else {

                        isFinishing =
                            false;


                        recordingStatusTitle.textContent =
                            "Upload Failed";


                        recordingStatusText.textContent =
                            "Your recording could not be uploaded. Please try again.";

                    }

                }

            };


        // =====================================
        // START RECORDING
        // =====================================

        interviewRecordingStartTime = Date.now();

        questionStartTimes[currentQuestionIndex] = interviewRecordingStartTime;

        console.log(
            "Q1 recording start timestamp (ms):",
            questionStartTimes[currentQuestionIndex]
        );

        try {

            mediaRecorder.start(
                1000
            );

        } catch (error) {

            console.error(
                "Recording start error:",
                error
            );

            alert(
                "Unable to start recording."
            );

            return;

        }


        isRecording = true;
        interviewActive = true;
        interviewTerminated = false;
        interviewTerminating = false;
        interviewFinishingNormally = false;
        tabSwitchCount = 0;

        sessionStorage.setItem("interviewStatus", "In Progress");
        sessionStorage.setItem("tabSwitchCount", "0");
        sessionStorage.setItem("securityViolation", "false");
        sessionStorage.removeItem("terminationType");
        sessionStorage.removeItem("terminatedReason");
        sessionStorage.removeItem("terminatedAt");
        localStorage.removeItem("terminationType");
        localStorage.removeItem("terminatedReason");
        localStorage.removeItem("securityViolation");
        localStorage.removeItem("tabSwitchCount");
        localStorage.removeItem("terminatedAt");

        // Clean any stale interviewId if this is a fresh interview session (no URL param)
        const urlParams = new URLSearchParams(window.location.search);
        const queryInterviewId = urlParams.get("interview_id") || urlParams.get("id");
        if (!queryInterviewId || queryInterviewId.trim() === "" || queryInterviewId.trim() === "null" || queryInterviewId.trim() === "undefined") {
            sessionStorage.removeItem("interviewId");
            localStorage.removeItem("interviewId");
        }

        recordButton.disabled = true;
        stopButton.disabled = false;
        if (finishButton) finishButton.disabled = false;


        recordingStatus.classList.add(
            "recording-active"
        );


        recordingStatusTitle.textContent =
            "Recording in Progress";


        recordingStatusText.textContent =
            "Your complete interview is being recorded. Continue answering the questions.";


        recordButton.innerHTML =
            `<i class="fa-solid fa-circle"></i>
             Recording...`;


        micStatus.textContent =
            "Recording";


        startTimer();

        console.log(
            "MediaRecorder started."
        );

    }
);


// =========================================
// STOP RECORDING
// =========================================

function stopRecording() {

    if (!isRecording) {

        return;

    }


    if (
        mediaRecorder &&
        mediaRecorder.state !==
        "inactive"
    ) {

        mediaRecorder.stop();

    }


    isRecording =
        false;


    recordButton.disabled = false;
    stopButton.disabled = true;
    if (finishButton) finishButton.disabled = false;


    recordingStatus.classList.remove(
        "recording-active"
    );


    recordButton.innerHTML =
        `<i class="fa-solid fa-microphone"></i>
         Start Recording`;


    micStatus.textContent =
        "Ready";


    console.log(
        "Interview recording stopped."
    );

}


// =========================================
// NEXT QUESTION
// =========================================

nextButton.addEventListener(
    "click",
    function () {

        // Close current question with exact transition timestamp
        const transitionTime = Date.now();
        questionEndTimes[currentQuestionIndex] = transitionTime;
        saveCurrentQuestionAnswer();

        if (
            currentQuestionIndex ===
            interviewQuestions.length - 1
        ) {

            finishInterview();

            return;

        }

        currentQuestionIndex++;

        if (currentQuestionIndex < interviewQuestions.length) {

            // Next question starts at exact same transition timestamp (seamless boundary)
            questionStartTimes[currentQuestionIndex] = transitionTime;

            console.log(
                `Q${currentQuestionIndex + 1} started at (ms):`,
                questionStartTimes[currentQuestionIndex]
            );

            displayQuestion();
        }

    }
);


// =========================================
// PREVIOUS QUESTION
// =========================================

previousButton.addEventListener(
    "click",
    function () {

        if (
            currentQuestionIndex === 0
        ) {

            return;

        }

        currentQuestionIndex--;

        displayQuestion();

    }
);


// =========================================
// FINISH BUTTON
// =========================================

finishButton.addEventListener(
    "click",
    function () {

        // Prevent race condition if interview is not active or already terminating/finishing
        if (!interviewActive || interviewTerminating || interviewFinishingNormally || isFinishing) {
            return;
        }

        // Set normal finish guard FIRST THING before any UI, recorder or window events
        interviewFinishingNormally = true;
        isFinishing = true;

        if (finishButton) finishButton.disabled = true;
        if (recordButton) recordButton.disabled = true;
        if (stopButton) stopButton.disabled = true;
        if (nextButton) nextButton.disabled = true;
        if (previousButton) previousButton.disabled = true;

        // Correctly record the active question's end timestamp at the moment finish is clicked
        if (interviewRecordingStartTime !== null && typeof questionEndTimes[currentQuestionIndex] === "undefined") {
            questionEndTimes[currentQuestionIndex] = Date.now();
        }

        finishInterview();

    }
);


// =========================================
// STRICT TAB SWITCH POLICY TERMINATION
// =========================================

// interviewTerminating is declared at top scope (line 534)

function terminateInterviewForTabSwitch() {

    console.log("=================================");
    console.log("TAB SWITCH FUNCTION CALLED");
    console.log("isRecording:", isRecording);
    console.log("isFinishing:", isFinishing);
    console.log("interviewTerminating:", interviewTerminating);
    console.log("interviewTerminated:", interviewTerminated);
    console.log("document.hidden:", document.hidden);
    console.log("=================================");

    // If already terminating or terminated or finishing normally, ignore!
    if (!interviewActive || interviewTerminating || interviewTerminated || interviewFinishingNormally || isFinishing) {
        console.log("Tab switch ignored - interview already terminating, terminated, or finishing normally.");
        return;
    }

    // Tab switch termination happens ONLY when candidate leaves during active interview
    if (!isRecording) {
        console.log("Tab switch ignored - recording is not active.");
        return;
    }

    // Set guards immediately to prevent duplicate events or API calls
    interviewTerminating = true;
    interviewTerminated = true;
    isFinishing = true;
    tabSwitchCount = 1;

    // Strict tab switch violation details
    const termTimestamp = new Date().toISOString();
    sessionStorage.setItem("interviewStatus", "Terminated");
    sessionStorage.setItem("terminationType", "TAB_SWITCH");
    sessionStorage.setItem("terminatedReason", "Tab Switch Detected");
    sessionStorage.setItem("securityViolation", "true");
    sessionStorage.setItem("terminatedAt", termTimestamp);
    sessionStorage.setItem("tabSwitchCount", "1");

    console.warn("=================================");
    console.warn("STRICT TAB SWITCH DETECTED - IMMEDIATE TERMINATION");
    console.warn("tab_switch_count: 1");
    console.warn("interview_status: Terminated");
    console.warn("termination_type: TAB_SWITCH");
    console.warn("termination_reason: Tab Switch Detected");
    console.warn("security_violation: true");
    console.warn("terminated_at:", termTimestamp);
    console.warn("=================================");

    // Stop timer
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }

    // Preserve all answers collected until this point
    saveCurrentQuestionAnswer();
    if (typeof questionEndTimes[currentQuestionIndex] === "undefined") {
        questionEndTimes[currentQuestionIndex] = Date.now();
    }

    // Update status banner
    if (recordingStatusTitle) {
        recordingStatusTitle.textContent = "Interview Terminated";
    }
    if (recordingStatusText) {
        recordingStatusText.textContent = "Interview terminated due to tab switch security violation. Submitting your interview...";
    }

    // Disable all buttons and question inputs so candidate cannot continue
    if (recordButton) recordButton.disabled = true;
    if (stopButton) stopButton.disabled = true;
    if (previousButton) previousButton.disabled = true;
    if (nextButton) nextButton.disabled = true;
    if (finishButton) finishButton.disabled = true;
    if (cameraButton) cameraButton.disabled = true;

    const answerTextArea = document.getElementById("candidateAnswer") || document.getElementById("answerInput");
    // Call authoritative termination API immediately
    try {
        const existingId = sessionStorage.getItem("interviewId") || localStorage.getItem("interviewId");
        const termPayload = {
            interview_id: (existingId && existingId !== "null" && existingId !== "undefined") ? existingId : null,
            role: selectedRole,
            total_questions: (interviewQuestions && interviewQuestions.length) ? interviewQuestions.length : 20,
            termination_type: "TAB_SWITCH",
            termination_reason: "Tab Switch Detected",
            tab_switch_count: 1,
            security_violation: true,
            user_id: sessionStorage.getItem("userId") || localStorage.getItem("userId") || null,
            user_email: sessionStorage.getItem("userEmail") || localStorage.getItem("userEmail") || null
        };
        fetch("/interview/terminate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-API-Key": "AI_INTERVIEW_2026_SECRET"
            },
            body: JSON.stringify(termPayload)
        }).then(function(res) {
            return res.json();
        }).then(function(termJson) {
            if (termJson && termJson.interview_id) {
                sessionStorage.setItem("interviewId", String(termJson.interview_id));
                localStorage.setItem("interviewId", String(termJson.interview_id));
                console.log("[Termination API] State locked for interview #", termJson.interview_id);
            }
        }).catch(function(tErr) {
            console.warn("[Termination API] Async notification notice:", tErr);
        });
    } catch (e) {
        console.warn("[Termination API] Dispatch notice:", e);
    }

    // Stop MediaRecorder safely
    if (
        mediaRecorder &&
        mediaRecorder.state !== "inactive"
    ) {
        console.log("Stopping MediaRecorder due to tab switch violation...");
        mediaRecorder.stop();
        isRecording = false;
        // mediaRecorder.onstop will uploadInterviewRecording() and finalizeInterview()
    } else if (recordedBlob && recordedBlob.size > 0) {
        isRecording = false;
        uploadInterviewRecording().then(function (uploaded) {
            if (uploaded) {
                finalizeInterview();
            }
        });
    } else {
        isRecording = false;
        recordedBlob = new Blob([], { type: "video/webm" });
        uploadInterviewRecording().then(function (uploaded) {
            if (uploaded) {
                finalizeInterview();
            }
        });
    }
}


// =========================================
// VISIBILITY CHANGE DETECTION
// =========================================

document.addEventListener(
    "visibilitychange",
    function () {
        console.log("[SECURITY] visibilitychange: visibilityState=" + document.visibilityState + ", hidden=" + document.hidden);

        // Strict tab switch policy:
        // Ignore if page is visible, interview is not active, or already finishing/terminating/terminated
        if (
            document.visibilityState !== "hidden" ||
            !interviewActive ||
            interviewFinishingNormally ||
            interviewTerminating ||
            interviewTerminated ||
            isFinishing ||
            !isRecording
        ) {
            return;
        }

        console.warn(
            "PAGE BECAME HIDDEN - STRICT TAB SWITCH VIOLATION"
        );
        terminateInterviewForTabSwitch();
    }
);


// =========================================
// WINDOW BLUR DETECTION (NEVER TERMINATE)
// =========================================

window.addEventListener(
    "blur",
    function () {
        console.log("[SECURITY] window blur");

        // Window blur is NOT sufficient evidence of a tab switch.
        // It can occur on camera/mic permissions, window focus shifts, devtools, browser controls.
        // Guards check retained; terminateInterviewForTabSwitch is NEVER called from blur.
        if (
            !interviewActive ||
            interviewTerminating ||
            interviewTerminated ||
            interviewFinishingNormally ||
            isFinishing ||
            !isRecording
        ) {
            return;
        }

        return;
    }
);


// =========================================
// UPLOAD INTERVIEW RECORDING
// =========================================

let isUploading = false;

async function uploadInterviewRecording() {

    // Prevent duplicate upload
    if (isUploading) {

        console.warn(
            "Upload already in progress. Skipping duplicate call."
        );

        return false;
    }


    // =====================================
    // CHECK RECORDING
    // =====================================

    if (
        !recordedBlob ||
        recordedBlob.size === 0
    ) {

        console.error(
            "No valid recording found."
        );

        return false;
    }


    isUploading = true;


    try {

        console.log(
            "================================="
        );

        console.log(
            "UPLOADING INTERVIEW"
        );

        console.log(
            "Role:",
            selectedRole
        );

        console.log(
            "Tab Switch Count:",
            tabSwitchCount
        );

        console.log(
            "Terminated:",
            interviewTerminated
        );

        console.log(
            "================================="
        );


        // =====================================
        // CREATE FORM DATA
        // =====================================

        const formData =
            new FormData();


        // =====================================
        // QUESTION DATA
        // PRESERVE GENUINELY DISPLAYED QUESTIONS (ANSWERED OR UNANSWERED)
        // =====================================

        const finishTimeNow = Date.now();
        if (interviewRecordingStartTime !== null && typeof questionEndTimes[currentQuestionIndex] === "undefined") {
            questionEndTimes[currentQuestionIndex] = finishTimeNow;
        }

        // Only include questions that were genuinely displayed (have a recorded start_time)
        // or have an explicitly typed candidate_answer.
        const displayedIndices = Object.keys(questionStartTimes)
            .map(Number)
            .filter(idx => !isNaN(idx) && questionStartTimes[idx] !== null && questionStartTimes[idx] !== undefined);

        const maxDisplayedIndex = displayedIndices.length > 0
            ? Math.max(currentQuestionIndex, ...displayedIndices)
            : currentQuestionIndex;

        const attemptedQuestions = interviewQuestions
            .slice(0, maxDisplayedIndex + 1)
            .map((q, index) => {
                const sTime = typeof questionStartTimes[index] !== "undefined" ? questionStartTimes[index] : null;
                let eTime = typeof questionEndTimes[index] !== "undefined" ? questionEndTimes[index] : null;

                // Ensure end_time is properly bounded for every displayed question
                if (sTime !== null) {
                    if (eTime === null || eTime < sTime) {
                        if (index < maxDisplayedIndex && typeof questionStartTimes[index + 1] !== "undefined") {
                            eTime = questionStartTimes[index + 1];
                        } else {
                            eTime = finishTimeNow;
                        }
                        questionEndTimes[index] = eTime;
                    }
                }

                const rawAns = candidateAnswers[index] || "";
                const cleanAns = typeof rawAns === "string" ? rawAns.trim() : "";

                return {
                    question_number: index + 1,
                    question: q.question,
                    type: q.type,
                    start_time: sTime,
                    end_time: eTime,
                    start_ms: sTime !== null ? Math.round(sTime) : null,
                    end_ms: eTime !== null ? Math.round(eTime) : null,
                    candidate_answer: cleanAns,
                    is_answered: cleanAns.length > 0
                };
            })
            .filter(q =>
                (q.candidate_answer && q.candidate_answer.trim() !== "") ||
                (q.start_time !== null && q.start_time !== undefined)
            );

        const clientAttemptedCount = attemptedQuestions.length;
        const clientAnsweredCount = attemptedQuestions.filter(q => q.candidate_answer && q.candidate_answer.trim() !== "").length;
        const clientUnansweredCount = Math.max(0, clientAttemptedCount - clientAnsweredCount);

        console.log(
            "Questions being sent for evaluation:",
            attemptedQuestions
        );

        console.log(
            `Question tracking: Attempted=${clientAttemptedCount}, Answered=${clientAnsweredCount}, Unanswered=${clientUnansweredCount}`
        );

        formData.append(
            "role",
            selectedRole
        );

        formData.append(
            "total_questions",
            String(clientAttemptedCount)
        );

        formData.append(
            "attempted_questions",
            String(clientAttemptedCount)
        );

        formData.append(
            "answered_questions",
            String(clientAnsweredCount)
        );

        formData.append(
            "unanswered_questions",
            String(clientUnansweredCount)
        );

        formData.append(
            "recording_start_time",
            String(interviewRecordingStartTime || questionStartTimes[0] || Date.now())
        );

        formData.append(
            "question_data",
            JSON.stringify(attemptedQuestions)
        );

        const existingInterviewId = sessionStorage.getItem("interviewId") || localStorage.getItem("interviewId");
        if (existingInterviewId && existingInterviewId !== "null" && existingInterviewId !== "undefined" && existingInterviewId.trim() !== "") {
            formData.append("interview_id", existingInterviewId.trim());
        }

        const userEmail = sessionStorage.getItem("userEmail") || localStorage.getItem("userEmail");
        if (userEmail && userEmail !== "null" && userEmail !== "undefined" && userEmail.trim() !== "") {
            formData.append("user_email", userEmail.trim());
        }

        const userId = sessionStorage.getItem("userId") || localStorage.getItem("userId");
        if (userId && userId !== "null" && userId !== "undefined" && userId.trim() !== "") {
            formData.append("user_id", userId.trim());
        }


        // =====================================
        // RECORDING
        // =====================================

        const safeRole =
            selectedRole.replace(
                /\s+/g,
                "_"
            );


        formData.append(
            "recording",
            recordedBlob,
            `${safeRole}_interview.webm`
        );


        // =====================================
        // TAB SWITCH & SECURITY VIOLATION METADATA
        // =====================================

        const clientSessionId = sessionStorage.getItem("clientSessionId") || (`client_session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`);
        sessionStorage.setItem("clientSessionId", clientSessionId);
        formData.append("client_session_id", clientSessionId);

        formData.append(
            "tab_switch_count",
            interviewTerminated ? "1" : "0"
        );

        formData.append(
            "terminated_reason",
            interviewTerminated ? "Tab Switch Detected" : ""
        );

        formData.append(
            "termination_type",
            interviewTerminated ? "TAB_SWITCH" : ""
        );

        formData.append(
            "security_violation",
            interviewTerminated ? "true" : "false"
        );

        formData.append(
            "interview_status",
            interviewTerminated ? "Terminated" : "COMPLETED"
        );

        if (interviewTerminated) {
            formData.append(
                "terminated_at",
                sessionStorage.getItem("terminatedAt") || new Date().toISOString()
            );
        }


        // ATTACH LOGGED IN USER
        const loggedUserEmail = localStorage.getItem("userEmail") || sessionStorage.getItem("userEmail");
        if (loggedUserEmail) {
            formData.append("user_email", loggedUserEmail);
        }
        const loggedUserId = localStorage.getItem("userId") || sessionStorage.getItem("userId");
        if (loggedUserId) {
            formData.append("user_id", loggedUserId);
        }

        console.log("=================================");
        console.log("[Upload Debug] SENDING INTERVIEW PAYLOAD TO FASTAPI");
        console.log("[Upload Debug] Target URL: /interview/upload");
        console.log("[Upload Debug] Role:", selectedRole);
        console.log("[Upload Debug] Interview ID to send:", existingInterviewId || "(none - new interview will be created)");
        console.log("[Upload Debug] Total / Attempted Questions:", clientAttemptedCount);
        console.log("[Upload Debug] Answered Questions (Typed):", clientAnsweredCount);
        console.log("[Upload Debug] Unanswered Questions:", clientUnansweredCount);
        console.log("[Upload Debug] Question details payload:", attemptedQuestions);
        console.log("[Upload Debug] Recording Blob size:", recordedBlob ? recordedBlob.size : 0, "bytes");
        console.log("=================================");

        // =====================================
        // SEND TO FASTAPI
        // =====================================

        const response =
            await fetch(
                "/interview/upload",
                {

                    method: "POST",

                    headers: {

                        "X-API-Key":
                            "AI_INTERVIEW_2026_SECRET"

                    },

                    body:
                        formData

                }
            );


        // =====================================
        // READ FASTAPI RESPONSE
        // =====================================

        const result =
            await response.json();


        console.log(
            "================================="
        );

        console.log(
            "FASTAPI RESPONSE:"
        );

        console.log(
            result
        );

        console.log(
            "================================="
        );


        // =====================================
        // CHECK HTTP RESPONSE
        // =====================================

        if (
            !response.ok
        ) {

            throw new Error(
                result.detail ||
                result.message ||
                "Upload failed."
            );

        }


        // =====================================
        // SUCCESS
        // =====================================

        if (
            result.status === "success"
        ) {

            console.log(
                "================================="
            );

            console.log(
                "INTERVIEW UPLOAD SUCCESS"
            );

            console.log(
                "Interview ID:",
                result.interview_id
            );

            console.log(
                "Attempted Questions:",
                attemptedQuestions.length
            );

            console.log(
                "Backend Question Answers:",
                result.question_answers
            );

            console.log(
                "Overall Score:",
                result.evaluation
                    ?.overall_score
            );

            console.log(
                "================================="
            );


            // =================================
            // CREATE COMPLETE RESULT
            // =================================

            // Calculate consistent counts from backend or client fallback
            const finalAttempted = Number(result.attempted_questions ?? result.total_questions ?? attemptedQuestions.length);
            const finalAnswered = Number(result.answered_questions ?? (
                Array.isArray(result.question_answers)
                    ? result.question_answers.filter(q => q && typeof q.candidate_answer === "string" && q.candidate_answer.trim().length > 0).length
                    : clientAnsweredCount
            ));
            const finalUnanswered = Number(result.unanswered_questions ?? Math.max(0, finalAttempted - finalAnswered));

            const completeResult = {

                ...result,

                role:
                    result.role ||
                    selectedRole,

                total_questions:
                    finalAttempted,

                attempted_questions:
                    finalAttempted,

                answered_questions:
                    finalAnswered,

                unanswered_questions:
                    finalUnanswered,

                interviewDate:
                    new Date()
                        .toLocaleString(),

                recording_available: true,

                recording_url:
                    result.recording_url ||
                    (result.interview_id ? `/interview/${result.interview_id}/recording` : "") ||
                    (result.filename ? `/uploads/${result.filename}` : ""),

                recordingURL:
                    result.recording_url ||
                    (result.interview_id ? `/interview/${result.interview_id}/recording` : "") ||
                    (result.filename ? `/uploads/${result.filename}` : "")

            };


            // =================================
            // SAVE RESULT
            // =================================

            sessionStorage.setItem(
                "interviewResult",
                JSON.stringify(
                    completeResult
                )
            );


            // Backup
            localStorage.setItem(
                "interviewResult",
                JSON.stringify(
                    completeResult
                )
            );


            // =================================
            // SAVE OTHER SESSION DATA
            // =================================

            sessionStorage.setItem(
                "interviewId",
                String(
                    result.interview_id ?? ""
                )
            );


            sessionStorage.setItem(
                "interviewDate",
                completeResult.interviewDate
            );


            sessionStorage.setItem(
                "selectedRole",
                selectedRole
            );


            sessionStorage.setItem(
                "totalQuestions",
                String(finalAttempted)
            );


            sessionStorage.setItem(
                "attemptedQuestions",
                String(finalAttempted)
            );

            sessionStorage.setItem(
                "answeredQuestions",
                String(finalAnswered)
            );

            sessionStorage.setItem(
                "unansweredQuestions",
                String(finalUnanswered)
            );

            sessionStorage.setItem(
                "interviewDuration",
                String(result.duration_seconds ?? completeResult.duration_seconds ?? "")
            );


            sessionStorage.setItem(
                "recordingAvailable",
                "true"
            );


            sessionStorage.setItem(
                "recordingURL",
                completeResult.recordingURL
            );


            sessionStorage.setItem(
                "transcript",
                result.transcript || ""
            );


            // Tab switch and termination metadata
            const finalStatus = interviewTerminated ? "Terminated" : (result.interview_status || result.status || "COMPLETED");
            const finalTabCount = interviewTerminated ? 1 : Number(result.tab_switch_count ?? tabSwitchCount ?? 0);
            const finalTermReason = interviewTerminated ? "Tab Switch Detected" : (result.terminated_reason || "");
            const finalTermType = interviewTerminated ? "TAB_SWITCH" : (result.termination_type || "");
            const finalSecViolation = interviewTerminated ? true : Boolean(result.security_violation);
            const finalTermAt = interviewTerminated ? (sessionStorage.getItem("terminatedAt") || new Date().toISOString()) : (result.terminated_at || null);

            completeResult.interview_status = finalStatus;
            completeResult.status = finalStatus;
            completeResult.tab_switch_count = finalTabCount;
            completeResult.terminated_reason = finalTermReason;
            completeResult.termination_type = finalTermType;
            completeResult.security_violation = finalSecViolation;
            completeResult.terminated_at = finalTermAt;

            sessionStorage.setItem("interviewStatus", finalStatus);
            sessionStorage.setItem("terminationType", finalTermType);
            sessionStorage.setItem("terminatedReason", finalTermReason);
            sessionStorage.setItem("securityViolation", finalSecViolation ? "true" : "false");
            sessionStorage.setItem("tabSwitchCount", String(finalTabCount));
            if (finalTermAt) {
                sessionStorage.setItem("terminatedAt", finalTermAt);
            }


            // =================================
            // SAVE ATTEMPTED QUESTIONS
            // =================================

            sessionStorage.setItem(
                "submittedQuestions",
                JSON.stringify(
                    attemptedQuestions
                )
            );


            // =================================
            // DEBUG STORAGE
            // =================================

            console.log(
                "================================="
            );

            console.log(
                "RESULT SAVED"
            );

            console.log(
                "Attempted Questions:",
                attemptedQuestions.length
            );

            console.log(
                "Complete Result:",
                completeResult
            );

            console.log(
                "Session Result:",
                sessionStorage.getItem(
                    "interviewResult"
                )
            );

            console.log(
                "Local Result:",
                localStorage.getItem(
                    "interviewResult"
                )
            );

            console.log(
                "================================="
            );


            isUploading =
                false;


            return true;

        }


        // =====================================
        // BACKEND RETURNED ERROR
        // =====================================

        throw new Error(
            result.message ||
            "Recording upload failed."
        );


    }
    catch (error) {

        isUploading =
            false;


        console.error(
            "================================="
        );

        console.error(
            "UPLOAD ERROR"
        );

        console.error(
            error
        );

        console.error(
            "================================="
        );


        alert(
            "Recording upload failed.\n\n" +
            error.message
        );


        return false;

    }

}


// =========================================
// FINISH INTERVIEW
// =========================================

function finishInterview() {

    // Already terminating, or finishing normally
    if (
        interviewTerminating ||
        interviewTerminated ||
        (isFinishing && !interviewFinishingNormally)
    ) {
        return;
    }

    // Set normal finish state FIRST
    interviewFinishingNormally = true;
    isFinishing = true;

    // Immediately disable buttons to prevent rapid double-clicks
    if (finishButton) finishButton.disabled = true;
    if (nextButton) nextButton.disabled = true;
    if (previousButton) previousButton.disabled = true;

    // Capture the timestamp when finish was clicked as active question's end time
    if (interviewRecordingStartTime !== null && typeof questionEndTimes[currentQuestionIndex] === "undefined") {
        questionEndTimes[currentQuestionIndex] = Date.now();
    }

    saveCurrentQuestionAnswer();


    // =====================================
    // CHECK RECORDING
    // =====================================

    if (
        !isRecording &&
        !recordedBlob &&
        !interviewTerminated
    ) {

        alert(
            "Please start recording before finishing the interview."
        );
        interviewFinishingNormally = false;
        isFinishing = false;
        if (finishButton) finishButton.disabled = false;
        if (recordButton) recordButton.disabled = false;
        if (nextButton) nextButton.disabled = false;
        if (previousButton) previousButton.disabled = (currentQuestionIndex === 0);
        return;

    }


    // =====================================
    // MARK FINISHING
    // =====================================

    isFinishing = true;


    // =====================================
    // STOP TIMER
    // =====================================

    clearInterval(
        timerInterval
    );

    timerInterval = null;


    // =====================================
    // UPDATE STATUS
    // =====================================

    if (
        interviewTerminated
    ) {

        recordingStatusTitle.textContent =
            "Interview Terminated";

        recordingStatusText.textContent =
            "Your recording is being uploaded.";

    }
    else {

        recordingStatusTitle.textContent =
            "Processing Recording";

        recordingStatusText.textContent =
            "Uploading your interview recording. Please wait...";

    }


    // =====================================
    // DISABLE BUTTONS
    // =====================================

    recordButton.disabled = true;

    stopButton.disabled = true;

    previousButton.disabled = true;

    nextButton.disabled = true;

    finishButton.disabled = true;


    // =====================================
    // STOP MEDIA RECORDER
    // =====================================

    if (
        mediaRecorder &&
        mediaRecorder.state !== "inactive"
    ) {

        console.log(
            "Stopping MediaRecorder..."
        );

        mediaRecorder.stop();

        isRecording = false;

        return;

    }


    // =====================================
    // BLOB ALREADY AVAILABLE
    // =====================================

    if (
        recordedBlob &&
        recordedBlob.size > 0
    ) {

        uploadInterviewRecording()
            .then(
                function (uploaded) {

                    if (
                        uploaded
                    ) {

                        finalizeInterview();

                    }
                    else {

                        isFinishing =
                            false;

                    }

                }
            );

        return;

    }


    console.error(
        "No recording available."
    );

}


// =========================================
// FINALIZE INTERVIEW
// =========================================

async function finalizeInterview() {

    console.log(
        "================================="
    );

    console.log(
        "FINALIZING INTERVIEW"
    );

    console.log(
        "Tab Switch Count:",
        tabSwitchCount
    );

    console.log(
        "Interview Terminated:",
        interviewTerminated
    );

    console.log(
        "================================="
    );


    // =====================================
    // STOP CAMERA + MICROPHONE
    // =====================================

    if (
        interviewStream
    ) {

        if (virtualCanvasAnimationId) {
            clearInterval(virtualCanvasAnimationId);
            virtualCanvasAnimationId = null;
        }

        interviewStream
            .getTracks()
            .forEach(
                function (track) {

                    track.stop();

                }
            );

        interviewStream = null;

    }


    // =====================================
    // SAVE FINAL SESSION DATA
    // =====================================

    sessionStorage.setItem(
        "recordingAvailable",
        "true"
    );


    sessionStorage.setItem(
        "tabSwitchCount",
        interviewTerminated ? "1" : "0"
    );

    sessionStorage.setItem(
        "interviewStatus",
        interviewTerminated ? "Terminated" : "COMPLETED"
    );

    sessionStorage.setItem(
        "terminationType",
        interviewTerminated ? "TAB_SWITCH" : ""
    );

    sessionStorage.setItem(
        "terminatedReason",
        interviewTerminated ? "Tab Switch Detected" : ""
    );

    sessionStorage.setItem(
        "securityViolation",
        interviewTerminated ? "true" : "false"
    );


    sessionStorage.setItem(
        "interviewQuestions",
        JSON.stringify(
            interviewQuestions
        )
    );


    sessionStorage.setItem(
        "candidateAnswers",
        JSON.stringify(
            candidateAnswers
        )
    );


    sessionStorage.setItem(
        "questionStartTimes",
        JSON.stringify(
            questionStartTimes
        )
    );


    sessionStorage.setItem(
        "questionEndTimes",
        JSON.stringify(
            questionEndTimes
        )
    );


    // =====================================
    // VERIFY UPLOAD / RESULT STORED BEFORE NAVIGATING
    // =====================================

    let uploadSuccess = false;

    if (sessionStorage.getItem("interviewResult") || localStorage.getItem("interviewResult")) {
        uploadSuccess = true;
    } else {
        uploadSuccess = await uploadInterviewRecording();
    }

    if (uploadSuccess) {
        // =====================================
        // RESET STATES BEFORE NAVIGATION
        // =====================================

        interviewActive = false;
        isRecording = false;
        isFinishing = false;
        interviewFinishingNormally = true;


        // =====================================
        // GO TO RESULT PAGE
        // =====================================

        const targetId = sessionStorage.getItem("interviewId");
        window.location.href = targetId ? `result.html?id=${encodeURIComponent(targetId)}` : "result.html";

    } else {

        isFinishing = false;

        alert(
            "Upload was not completed. Cannot navigate to result page."
        );

    }

}


// =========================================
// INITIALIZE INTERVIEW
// =========================================

createInterviewQuestions();

displayQuestion();

updateTimer();

// Auto-initialize camera preview on page load
if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    initCameraPreview().catch(function (err) {
        console.log("Auto-preview prompt note:", err);
    });
}