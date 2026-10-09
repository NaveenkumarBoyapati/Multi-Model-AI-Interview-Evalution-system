import os
import json
import re
import math
import urllib.request
import urllib.error
from difflib import SequenceMatcher

try:
    from question_bank import CONCEPT_SYNONYMS, get_expected_concepts
except ImportError:
    try:
        from backend.question_bank import CONCEPT_SYNONYMS, get_expected_concepts
    except ImportError:
        CONCEPT_SYNONYMS = {}
        def get_expected_concepts(q, role=None):
            return []



# =========================================================
# CONFIGURATION
# =========================================================

AI_PROVIDER = os.getenv(
    "AI_EVALUATION_PROVIDER",
    "local"
).lower().strip()

AI_API_KEY = os.getenv(
    "AI_EVALUATION_API_KEY",
    ""
).strip()

AI_MODEL = os.getenv(
    "AI_EVALUATION_MODEL",
    ""
).strip()

AI_BASE_URL = os.getenv(
    "AI_EVALUATION_BASE_URL",
    ""
).strip()


# =========================================================
# SCORE WEIGHTS
# =========================================================

WEIGHTS = {
    "technical_score": 0.35,
    "relevance_score": 0.20,
    "concept_score": 0.15,
    "completeness_score": 0.10,
    "communication_score": 0.10,
    "confidence_score": 0.05,
    "problem_solving_score": 0.05
}


# =========================================================
# UTILITY FUNCTIONS
# =========================================================

def clamp_score(value):
    """
    Keep score strictly between 0 and 100.
    """

    try:
        value = float(value)
    except Exception:
        return 0.0

    return round(
        max(0.0, min(100.0, value)),
        2
    )


def clean_text(text):
    if text is None:
        return ""

    text = str(text)

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def word_count(text):
    text = clean_text(text)

    if not text:
        return 0

    return len(
        re.findall(
            r"\b[\w+#.-]+\b",
            text
        )
    )


def normalize_words(text):
    text = clean_text(text).lower()

    words = re.findall(
        r"\b[a-zA-Z0-9+#.-]+\b",
        text
    )

    return set(words)


def safe_list(value):
    if isinstance(value, list):
        return value

    if value is None:
        return []

    return [value]


# =========================================================
# FRAGMENT & SHORT-ANSWER REPOSITORY
# =========================================================

FRAGMENT_WORDS = {
    # Fillers and disfluencies
    "um", "uh", "er", "ah", "hmm", "huh", "like", "you", "know", "mean", "yeah", "yep",
    # Stop words / prepositions / articles / conjunctions / pronouns alone
    "the", "a", "an", "is", "are", "was", "were", "it", "its", "to", "of",
    "in", "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "and", "but", "or", "so", "because", "then", "that", "this", "these",
    "those", "if", "when", "where", "why", "how", "all", "any", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "than", "too", "very", "can", "will",
    "just", "should", "now", "well", "actually", "basically", "literally",
    # Dangling sentence fragments / trailing cutoff words / noise
    "job", "thing", "things", "stuff", "okay", "ok", "fine", "alright",
    "test", "testing", "working", "work", "said", "saying", "part", "also", "done"
}

VALID_SHORT_ANSWERS = {
    # Affirmative / negative responses
    "yes", "no", "true", "false", "definitely", "absolutely", "certainly",
    "never", "always", "agreed", "correct", "sure", "of course", "not really",
    "not yet", "yes definitely", "no problem", "none", "neither",
    # Programming languages & tools
    "python", "java", "sql", "javascript", "typescript", "c++", "c#", "golang",
    "rust", "php", "ruby", "swift", "kotlin", "html", "css", "docker", "kubernetes",
    "git", "github", "linux", "aws", "azure", "gcp", "react", "angular", "vue",
    "django", "flask", "fastapi", "spring", "spring boot", "nodejs", "express",
    "pandas", "numpy", "tensorflow", "pytorch", "vlookup", "xlookup", "powerbi",
    "power bi", "tableau", "excel", "spark", "pyspark", "hadoop", "kafka",
    "mysql", "postgresql", "postgres", "mongodb", "sqlite", "oracle", "snowflake",
    "bigquery", "dsa", "oop", "object oriented", "relational database", "rest api",
    "machine learning", "deep learning", "data science", "data analysis",
    "clean code", "unit testing", "agile", "scrum", "hard working", "team player",
    "quick learner", "fast learner", "problem solving", "time management",
    "continuous learning", "communication skills", "leadership"
}


def is_valid_answer(text, question=None):
    """
    Checks whether candidate answer is a genuine substantive response.
    Returns False for empty answers, punctuation/noise, isolated transcription fragments
    (e.g., 'job.', 'the', 'um', 'and so'), while preserving legitimate short answers
    (e.g., 'Python', 'Yes', 'machine learning', 'hard working').
    """
    if text is None:
        return False

    cleaned = clean_text(text)
    if not cleaned:
        return False

    if not re.search(r"[a-zA-Z0-9]", cleaned):
        return False

    words = re.findall(r"\b[\w+#.-]+\b", cleaned)
    w_count = len(words)
    if w_count == 0:
        return False

    cleaned_lower = cleaned.lower().strip(" .,!?;:'\"-")
    lower_words = [w.lower().strip(" .,!?;:'\"-") for w in words]

    # 1-word answer
    if w_count == 1:
        w0 = lower_words[0]
        if w0 in FRAGMENT_WORDS:
            return False
        if w0 in VALID_SHORT_ANSWERS:
            return True
        # Check if question exists and the word matches expected concepts
        if question:
            exp = get_expected_concepts(question)
            for c in exp:
                c_clean = clean_text(c).lower()
                if w0 in c_clean or c_clean in w0:
                    return True
        # Standalone isolated single word that is not a known valid term is considered a fragment
        return False

    # 2-word answer
    if w_count == 2:
        if all(w in FRAGMENT_WORDS for w in lower_words):
            return False
        if any(w in FRAGMENT_WORDS for w in lower_words) and not any(w in VALID_SHORT_ANSWERS for w in lower_words) and cleaned_lower not in VALID_SHORT_ANSWERS:
            return False
        if cleaned_lower in VALID_SHORT_ANSWERS or (f"{lower_words[0]} {lower_words[1]}" in VALID_SHORT_ANSWERS):
            return True
        if question:
            exp = get_expected_concepts(question)
            for c in exp:
                c_clean = clean_text(c).lower()
                if cleaned_lower in c_clean or any(w in c_clean for w in lower_words if w not in FRAGMENT_WORDS):
                    return True
        # If one word is a filler and other is a fragment
        if lower_words[0] in FRAGMENT_WORDS or lower_words[1] in FRAGMENT_WORDS:
            return False
        if len(lower_words[0]) < 3 and len(lower_words[1]) < 3:
            return False

    # 3+ words: ensure not purely fillers/fragments
    if w_count <= 4 and all(w in FRAGMENT_WORDS for w in lower_words):
        return False

    return True


# =========================================================
# EMPTY ANSWER RESULT
# =========================================================

def empty_answer_result(expected_concepts=None):
    concepts = [
        clean_text(c)
        for c in safe_list(expected_concepts)
        if clean_text(c)
    ]
    return {
        "technical_score": 0.0,
        "relevance_score": 0.0,
        "concept_score": 0.0,
        "concept_coverage_score": 0.0,
        "completeness_score": 0.0,
        "communication_score": 0.0,
        "confidence_score": 0.0,
        "problem_solving_score": 0.0,
        "overall_score": 0.0,

        "matched_concepts": [],
        "missing_concepts": concepts,

        "strengths": [],
        "improvements": [
            "No answer was detected for this question."
        ],

        "evaluation_source": "empty_answer"
    }


# =========================================================
# CALCULATE OVERALL SCORE
# =========================================================

def calculate_overall(
    technical_score,
    relevance_score,
    concept_score,
    completeness_score,
    communication_score,
    confidence_score,
    problem_solving_score
):
    scores = {
        "technical_score": technical_score,
        "relevance_score": relevance_score,
        "concept_score": concept_score,
        "completeness_score": completeness_score,
        "communication_score": communication_score,
        "confidence_score": confidence_score,
        "problem_solving_score": problem_solving_score
    }
    active_weights = {k: WEIGHTS[k] for k, v in scores.items() if v is not None}
    denom = sum(active_weights.values())
    if denom <= 0:
        return 0.0
    weighted_sum = sum(clamp_score(scores[k]) * active_weights[k] for k in active_weights)
    return clamp_score(round(weighted_sum / denom, 2))


# =========================================================
# RELEVANCE GATING
# =========================================================

def apply_relevance_gate(result):
    """
    Prevent technically strong but completely
    unrelated answers from receiving high scores.
    Scores must reflect answer quality and relevance;
    no arbitrary minimum scores or artificial floors.
    """

    relevance = clamp_score(
        result.get(
            "relevance_score",
            0
        )
    )

    technical = clamp_score(
        result.get(
            "technical_score",
            0
        )
    )

    concept = clamp_score(
        result.get(
            "concept_score",
            0
        )
    )

    completeness = clamp_score(
        result.get(
            "completeness_score",
            0
        )
    )

    problem = clamp_score(
        result.get(
            "problem_solving_score",
            0
        )
    )

    confidence = clamp_score(
        result.get(
            "confidence_score",
            0
        )
    )

    has_concept_score = result.get("concept_score") is not None
    has_prob_score = result.get("problem_solving_score") is not None

    # Completely irrelevant or off-topic answer (relevance < 5)
    if relevance < 5:
        result["technical_score"] = 0.0
        if has_concept_score:
            result["concept_score"] = 0.0
            result["concept_coverage_score"] = 0.0
        result["completeness_score"] = 0.0
        if has_prob_score:
            result["problem_solving_score"] = 0.0
        result["confidence_score"] = clamp_score(min(confidence, 35.0))

    # Barely relevant (relevance < 20)
    elif relevance < 20:
        result["technical_score"] = clamp_score(min(technical, relevance * 0.5))
        if has_concept_score:
            result["concept_score"] = clamp_score(min(concept, relevance))
            result["concept_coverage_score"] = clamp_score(min(concept, relevance))
        result["completeness_score"] = clamp_score(min(completeness, relevance))
        if has_prob_score:
            result["problem_solving_score"] = clamp_score(min(problem, relevance * 0.5))
        result["confidence_score"] = clamp_score(min(confidence, 45.0))

    # Partially relevant (relevance < 40)
    elif relevance < 40:
        result["technical_score"] = clamp_score(min(technical, relevance))
        if has_concept_score:
            result["concept_score"] = clamp_score(min(concept, relevance))
            result["concept_coverage_score"] = clamp_score(min(concept, relevance))
        result["completeness_score"] = clamp_score(min(completeness, relevance * 1.2))

    # Moderate relevance (relevance < 60)
    elif relevance < 60:
        result["technical_score"] = clamp_score(min(technical, 60.0))

    return result


# =========================================================
# LLM JSON EXTRACTION
# =========================================================

def extract_json(text):

    if not text:
        return None

    text = text.strip()

    # Remove markdown code fences
    text = re.sub(
        r"```json",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"```",
        "",
        text
    )

    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    # Find first JSON object
    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL
    )

    if match:

        try:
            return json.loads(
                match.group(0)
            )

        except Exception:
            return None

    return None


# =========================================================
# OPENAI-COMPATIBLE LLM EVALUATION
# =========================================================

def evaluate_with_llm(
    question,
    answer,
    expected_concepts
):

    if not AI_API_KEY:
        return None

    if not AI_MODEL:
        return None

    if not AI_BASE_URL:
        return None

    prompt = f"""
You are a strict technical interview evaluator.

Evaluate ONLY the candidate answer against the question.

QUESTION:
{question}

CANDIDATE ANSWER:
{answer}

EXPECTED CONCEPTS:
{json.dumps(expected_concepts, ensure_ascii=False)}

IMPORTANT RULES:

1. Do NOT give marks merely because the candidate spoke.
2. Do NOT give minimum scores.
3. Do NOT reward unrelated information.
4. A greeting or introduction alone is not a technical answer.
5. If the answer is empty, every score must be 0.
6. If the answer is unrelated, relevance must be low.
7. Technical score must reflect actual technical correctness.
8. Concept score must reflect expected concepts actually covered.
9. Completeness measures whether the question was adequately answered.
10. Communication measures clarity, not technical correctness.
11. Confidence is based only on answer delivery signals visible in text.
12. Problem solving should be low if no problem-solving evidence exists.
13. Never invent concepts that the candidate did not mention.
14. Be strict and realistic.

SCORING:

technical_score:
0-100 technical correctness and depth.

relevance_score:
0-100 how directly the answer addresses the question.

concept_score:
0-100 expected concepts actually covered.

completeness_score:
0-100 whether the answer sufficiently addresses the question.

communication_score:
0-100 clarity and organization.

confidence_score:
0-100 confidence based only on wording and delivery evidence.

problem_solving_score:
0-100 reasoning/problem-solving evidence.

Return ONLY valid JSON.

Required JSON:

{{
    "technical_score": 0,
    "relevance_score": 0,
    "concept_score": 0,
    "completeness_score": 0,
    "communication_score": 0,
    "confidence_score": 0,
    "problem_solving_score": 0,
    "matched_concepts": [],
    "missing_concepts": [],
    "strengths": [],
    "improvements": []
}}
"""

    payload = {
        "model": AI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a strict interview evaluation "
                    "engine. Return JSON only."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0,
        "max_tokens": 1200
    }

    try:

        request = urllib.request.Request(
            AI_BASE_URL,
            data=json.dumps(
                payload
            ).encode("utf-8"),
            headers={
                "Content-Type":
                    "application/json",

                "Authorization":
                    f"Bearer {AI_API_KEY}"
            },
            method="POST"
        )

        with urllib.request.urlopen(
            request,
            timeout=45
        ) as response:

            response_data = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

        choices = response_data.get(
            "choices",
            []
        )

        if not choices:
            return None

        message = choices[0].get(
            "message",
            {}
        )

        content = message.get(
            "content",
            ""
        )

        result = extract_json(
            content
        )

        if not isinstance(
            result,
            dict
        ):
            return None

        return result

    except Exception as error:

        print(
            "[LLM Evaluation Warning]",
            error
        )

        return None


# =========================================================
# CONCEPT MATCHING & SYNONYM REPOSITORY
# =========================================================

SYNONYMS_EXPANDED = {
    "eliminate": ["eliminate", "eliminating", "remove", "removing", "delete", "deleting", "drop", "dropping", "reduce", "reducing", "avoid", "clean", "purge"],
    "reduce": ["reduce", "reducing", "reduction", "minimize", "minimizing", "decrease", "eliminate", "remove", "avoid", "drop", "prevent"],
    "redundancy": ["redundancy", "redundant", "duplicate", "duplication", "duplicates", "repeated", "copies", "repetition", "unnecessary copy"],
    "organize": ["organize", "organizing", "organization", "structure", "structuring", "arranging", "systematize", "manage", "clean", "format", "relational", "tables"],
    "integrity": ["integrity", "consistency", "accuracy", "reliable", "reliability", "correctness", "validity", "quality", "constraint", "acid"],
    "normal forms": ["normal forms", "normal form", "1nf", "2nf", "3nf", "bcnf", "first normal form", "second normal form", "third normal form", "normalization rules"],
    "duplicate": ["duplicate", "duplicates", "duplication", "redundant", "redundancy", "repeated", "copies"],
    "vlookup": ["vlookup", "vertical lookup", "lookup function", "lookup value", "search key"],
    "lookup value": ["lookup value", "search key", "search value", "value to find", "target value"],
    "table array": ["table array", "table range", "data range", "lookup table", "reference range", "source table"],
    "column index": ["column index", "column index number", "column number", "col index", "return column"],
    "exact match": ["exact match", "approximate match", "false for exact", "range lookup", "true for approximate"],
    "problem-solving": ["problem-solving", "problem solving", "problem solver", "problem solvers", "quick problem solver", "quick problem-solver", "solve problems", "solving problems"],
    "problem solving": ["problem-solving", "problem solving", "problem solver", "problem solvers", "quick problem solver", "quick problem-solver", "solve problems", "solving problems"],
    "examining dataset structure": ["examining dataset structure", "dataset structure", "data structure", "schema", "table structure", "shape of data", "rows and columns"],
    "data types": ["data types", "variable types", "column types", "dtypes", "data type"],
    "missing values": ["missing values", "missing data", "nulls", "null values", "nan", "empty cells", "blank values", "null records"],
    "duplicates": ["duplicates", "duplicate rows", "duplicate records", "redundancy", "deduplication"],
    "distributions": ["distributions", "data distributions", "value distributions", "spread", "frequency", "quantiles", "variance"],
    "quality issues": ["quality issues", "data quality", "inconsistencies", "invalid values", "anomalies", "data cleanliness", "quality problems"],
    "responsive web design": ["responsive web design", "responsive design", "rwd", "responsive", "adapts to screen size", "mobile friendly"],
    "media queries": ["media queries", "media query", "@media", "css media query", "screen query"],
    "viewport": ["viewport", "meta viewport", "viewport meta tag", "device-width", "initial-scale"],
    "breakpoints": ["breakpoints", "breakpoint", "min-width", "max-width", "screen width"],
    "fluid layout and flexible images": ["fluid layout", "flexible images", "fluid grid", "relative units", "percentages", "rem", "em", "vw", "vh"],
    "mobile-first design": ["mobile-first", "mobile first", "mobile-first design", "progressive enhancement"],
    "method resolution order (mro)": ["method resolution order (mro)", "method resolution order", "mro", "method resolution", "mro in python"],
    "method resolution order": ["method resolution order (mro)", "method resolution order", "mro", "method resolution"],
    "order in which python searches for methods and attributes": [
        "order in which python searches for methods and attributes", "search order for methods and attributes",
        "search order", "method lookup order", "lookup order", "order of method lookup",
        "searches for methods and attributes", "attribute lookup order", "method resolution",
        "order python resolves methods", "resolving methods in class hierarchy"
    ],
    "multiple inheritance": [
        "multiple inheritance", "multiple base classes", "inherit from multiple classes",
        "diamond problem", "class hierarchy", "multiple parents", "inheriting from multiple classes"
    ],
    "c3 linearization algorithm": [
        "c3 linearization algorithm", "c3 linearization", "c3 algorithm",
        "c3 superclass linearization", "linearization algorithm", "c3"
    ],
    "classname.mro() or classname.__mro__": [
        "classname.mro() or classname.__mro__", "classname.mro()", "classname.__mro__",
        "mro()", "__mro__", "mro method", "__mro__ attribute", "inspect mro", "print mro",
        "class.mro()", "cls.mro()", "cls.__mro__"
    ]
}

CONCEPT_PATTERNS = {
    "education": [
        r"\bpursuing\b", r"\bcurrently\s+pursuing\b", r"\bpresently\s+pursuing\b",
        r"\bstudying\b", r"\bcurrently\s+studying\b", r"\bstudied\b", r"\bstudent\b",
        r"\bfinal\s+year\b", r"\bin\s+my\s+final\s+year\b", r"\bthird\s+year\b",
        r"\bsecond\s+year\b", r"\bfirst\s+year\b", r"\blast\s+year\b", r"\bpre-?final\s+year\b",
        r"\b(?:4th|3rd|2nd|1st)\s+year\b", r"\bgraduation\b", r"\bgraduated\b", r"\bgraduating\b",
        r"\bundergraduate\b", r"\bpostgraduate\b", r"\bdegree\b", r"\bdiploma\b",
        r"\bbtech\b", r"\bmtech\b", r"\bbca\b", r"\bmca\b", r"\bbsc\b", r"\bmsc\b",
        r"\bbcom\b", r"\bbba\b", r"\bmba\b", r"\bphd\b", r"\bbachelor\b", r"\bbachelors\b",
        r"\bmaster\b", r"\bmasters\b", r"\buniversity\b", r"\bcollege\b", r"\binstitute\b",
        r"\bcampus\b", r"\bschool\b", r"\bacademics\b", r"\bcoursework\b", r"\bengineering\b",
        r"\bsemester\b", r"\bpp\s+savani\b", r"\bsavani\b", r"\bacadeic\s+background\b",
        r"\beducational\s+background\b", r"\bcompleted\s+my\b", r"\bmajor\s+in\b", r"\bmajoring\s+in\b"
    ],
    "technical skills": [
        r"\btechnical\s+skills?\b", r"\btech\s+skills?\b", r"\btechnical\s+background\b",
        r"\bprogramming\s+skills?\b", r"\bcoding\s+skills?\b", r"\bskill\s+set\b",
        r"\bskills?\s+in\b", r"\bproficient\s+in\b", r"\btechnologies\b", r"\btech\s+stack\b",
        r"\bpython\b", r"\bsql\b", r"\bpowerbi\b", r"\bexcel\b", r"\btableau\b", r"\bpandas\b",
        r"\bnumpy\b", r"\bscipy\b", r"\bmatplotlib\b", r"\bseaborn\b", r"\bscikit\b",
        r"\bsklearn\b", r"\bspark\b", r"\bpyspark\b", r"\bhadoop\b", r"\bkafka\b",
        r"\bdbt\b", r"\bairflow\b", r"\bsnowflake\b", r"\bbigquery\b", r"\bmysql\b",
        r"\bpostgresql\b", r"\bpostgres\b", r"\bsql\s+server\b", r"\bmongodb\b", r"\bnosql\b",
        r"\bsqlite\b", r"\boracle\b", r"\bjava\b", r"\bc\+\+\b", r"\bc#\b", r"\bc\s+language\b",
        r"\bc\s+programming\b", r"\br\s+programming\b", r"\br\s+language\b", r"\bjavascript\b",
        r"\btypescript\b", r"\bhtml\b", r"\bcss\b", r"\breact\b", r"\bangular\b", r"\bvue\b",
        r"\bnode\b", r"\bnodejs\b", r"\bdjango\b", r"\bflask\b", r"\bfastapi\b", r"\bspring\b",
        r"\bspring\s+boot\b", r"\bgit\b", r"\bgithub\b", r"\bdocker\b", r"\bkubernetes\b",
        r"\baws\b", r"\bazure\b", r"\bgcp\b", r"\blinux\b", r"\bdata\s+analysis\b",
        r"\bdata\s+analytics\b", r"\bmachine\s+learning\b", r"\bdeep\s+learning\b",
        r"\bdata\s+science\b", r"\bdata\s+structures\b", r"\balgorithms\b", r"\bdsa\b",
        r"\betl\b", r"\bdata\s+warehous\w*\b", r"\bdata\s+pipelin\w*\b", r"\bpower\s*query\b",
        r"\bdax\b", r"\bvlookup\b", r"\bpivot\s+tables?\b", r"\brest\s+api\b", r"\boop\b"
    ],
    "relevant experience": [
        r"\binternships?\b", r"\bintern\b", r"\binterned\b", r"\binterning\b", r"\btrainee\b",
        r"\bwork\s+experience\b", r"\bworking\s+experience\b", r"\bprior\s+experience\b",
        r"\bindustry\s+experience\b", r"\bprofessional\s+experience\b", r"\bhands-on\s+experience\b",
        r"\bworked\s+at\b", r"\bworked\s+in\b", r"\bworked\s+as\b", r"\bworking\s+as\b",
        r"\bworking\s+at\b", r"\bworked\s+with\b", r"\bprevious\s+company\b", r"\bprior\s+role\b",
        r"\bcurrent\s+role\b", r"\bjob\s+at\b", r"\bemployment\b", r"\bfreelance\b", r"\bfreelancing\b",
        r"\bcorporate\s+experience\b"
    ],
    "introduction": [
        r"\bmy\s+name\s+is\b", r"\bname\s+is\b", r"\bname's\b",
        r"\bintroduce\s+myself\b", r"\bintroducing\s+myself\b", r"\bbriefly\s+introduce\b",
        r"\b(?:i\s+am|i'm|myself|this\s+is)\s+[a-z]{2,}(?:\s+[a-z]{2,})*\b"
    ],
    "projects": [
        r"\bprojects?\b", r"\bcapstone\b", r"\bportfolio\b", r"\bbuilt\s+an?\b",
        r"\bdeveloped\s+an?\b", r"\bcreated\s+an?\b", r"\bdesigned\s+an?\b",
        r"\bimplemented\s+an?\b", r"\bmini\s+project\b", r"\bmajor\s+project\b",
        r"\bacademic\s+project\b", r"\bpersonal\s+project\b", r"\bcollege\s+project\b",
        r"\bfinal\s+year\s+project\b"
    ],
    "career goals": [
        r"\bcareer\s+goals?\b", r"\bmy\s+goals?\b", r"\bmy\s+ambitions?\b", r"\baspire\s+to\b",
        r"\baspiring\s+to\b", r"\baim\s+to\b", r"\bshort\s+term\s+goal\b", r"\blong\s+term\s+goal\b",
        r"\bcareer\s+path\b", r"\blooking\s+to\s+work\b", r"\blooking\s+forward\s+to\s+work\b",
        r"\bdream\s+role\b", r"\bcareer\s+objective\b", r"\bfuture\s+role\b", r"\bpassionate\s+to\s+grow\b",
        r"\bwant\s+to\s+become\b", r"\bgrow\s+as\s+a\b", r"\bpursue\s+a\s+career\b"
    ],
    "core strengths": [
        r"\bcore\s+strengths?\b", r"\bmy\s+strengths?\b", r"\bgreatest\s+strength\b",
        r"\bkey\s+strength\b", r"\bstrong\s+at\b", r"\bgood\s+at\b", r"\bexcel\s+at\b",
        r"\bproficiency\s+in\b", r"\bproficient\s+in\b", r"\bskilled\s+at\b",
        r"\bstrengths?\s+are\b", r"\bstrengths?\s+include\b", r"\bhard[\s-]working\b",
        r"\bhardworking\b", r"\bquick\s+learner\b", r"\bfast\s+learner\b",
        r"\bdedicated\b", r"\badaptable\b", r"\badaptability\b", r"\bcore\s+stands?\b", r"\bcore\s+stand\b",
        r"\bcore\s+strands?\b", r"\bcore\s+stances?\b",
        r"\bconsistent\b", r"\bconsistency\b", r"\bloyal\b", r"\bloyalty\b",
        r"\bbeing\s+consistent\b", r"\bbeing\s+loyal\b",
        r"\bdoing\s+work\s+on\s+time\b", r"\bwork\s+on\s+time\b", r"\bon\s+time\b",
        r"\bpunctual\b", r"\bpunctuality\b", r"\btime\s+management\b", r"\bmeet\s+deadlines\b",
        r"\bhelping\s+others\b", r"\bhelp\s+others\b", r"\bteam\s+player\b",
        r"\bteamwork\b", r"\bcollaborative\b", r"\bsupport\s+teammates\b", r"\bcooperative\b",
        r"\bco[\s-]+strengths?\b", r"\bmotivated\b", r"\bself[\s-]motivated\b",
        r"\bbeing\s+motivated\b", r"\bbeing\s+motive\b", r"\bpositive\s+attitude\b", r"\bself[\s-]driven\b"
    ],
    "communication": [
        r"\bcommunications?\b",
        r"\bcommunicat\w*\b",
        r"\bcommunicator\b",
        r"\binterpersonal\s+skills?\b",
        r"\bpresentation\s+skills?\b",
        r"\bconvey\s+ideas\b",
        r"\blistening\s+skills?\b",
        r"\barticulate\b",
        r"\bexpress\s+ideas\b"
    ],
    "problem solving": [
        r"\bproblem[\s-]solv\w*\b",
        r"\bproblem[\s-]solving\b",
        r"\bproblem[\s-]solver\b",
        r"\bproblem[\s-]solvers\b",
        r"\bsolv\w*[\s-]problems?\b",
        r"\bquick[\s-]problem[\s-]solv\w*\b",
        r"\banalytical\s+skills?\b",
        r"\banalytical\s+mindset\b",
        r"\banalytical\s+thinking\b",
        r"\btroubleshoot\w*\b",
        r"\bdebugging\s+skills?\b",
        r"\bcritical\s+thinking\b",
        r"\bresolve\s+complex\b",
        r"\bresolv\w*\s+issues?\b",
        r"\bresolv\w*\s+problems?\b",
        r"\broot\s+cause\b"
    ],
    "examining dataset structure": [
        r"\b(?:dataset|data|table|schema)\s+structure\b",
        r"\bexamin\w*\s+(?:the\s+)?(?:dataset|data|schema|structure)\b",
        r"\bstructure\s+of\s+(?:the\s+)?data\b",
        r"\bschema\b",
        r"\bshape\s+of\s+(?:the\s+)?data\b",
        r"\brows?\s+and\s+columns?\b"
    ],
    "data types": [
        r"\bdata\s+types?\b",
        r"\bvariable\s+types?\b",
        r"\bcolumn\s+types?\b",
        r"\bdtypes?\b",
        r"\b(?:integers?|strings?|floats?|booleans?|datetime)\b"
    ],
    "missing values": [
        r"\bmissing\s+(?:values?|data|records?)\b",
        r"\bnulls?\b",
        r"\bnull\s+(?:values?|records?)\b",
        r"\bnan\b",
        r"\bempty\s+(?:values?|cells?|fields?)\b",
        r"\bblanks?\b"
    ],
    "duplicates": [
        r"\bduplicates?\b",
        r"\bduplicate\s+(?:rows?|records?|values?|data)\b",
        r"\bredundant\s+(?:rows?|records?|data)\b",
        r"\bredundancy\b",
        r"\bdeduplicat\w*\b"
    ],
    "distributions": [
        r"\bdistributions?\b",
        r"\bdata\s+distributions?\b",
        r"\bvalue\s+distributions?\b",
        r"\bfrequenc\w*\b",
        r"\bspread\b",
        r"\bquantiles?\b",
        r"\bpercentiles?\b",
        r"\bvariance\b",
        r"\bstandard\s+deviation\b",
        r"\bmean\s+(?:and|or)\s+median\b",
        r"\bmin\s+(?:and|to)\s+max\b"
    ],
    "quality issues": [
        r"\bquality\s+issues?\b",
        r"\bdata\s+quality\b",
        r"\binconsistenc\w*\b",
        r"\binvalid\s+(?:values?|data)\b",
        r"\banomal\w*\b",
        r"\boutliers?\b",
        r"\bdata\s+clean\w*\b",
        r"\berrors?\b"
    ],
    "practical example": [
        r"\bfor\s+example\b", r"\bfor\s+instance\b", r"\bin\s+my\s+experience\b",
        r"\bone\s+example\b", r"\bcase\s+in\s+point\b", r"\bto\s+illustrate\b",
        r"\bin\s+a\s+recent\s+project\b",
        r"\bin\s+my\s+(?:previous|past|last|recent|college|university)\s+(?:role|job|project|internship|experience)\b",
        r"\ba\s+time\s+when\s+i\b", r"\ban\s+instance\s+where\s+i\b",
        r"\bdemonstrated\s+this\s+when\b", r"\brecently\s+when\s+i\b"
    ],
    "role contribution": [
        r"\bhelp\s+(?:in\s+)?this\s+role\b", r"\bhelp\s+(?:me\s+)?(?:in|with)\s+(?:this|the|my)\s+role\b",
        r"\bcontribut\w*[\w\s]{0,40}\b(?:role|team|company|organization|project)\b",
        r"\bbenefit\s+the\s+team\b", r"\bhelp\s+the\s+team\b", r"\bvalue\s+to\b",
        r"\bbring\s+to\s+the\s+company\b", r"\bmake\s+an\s+impact\b", r"\badd\s+value\b",
        r"\bsupport\s+the\s+team\b", r"\bbenefit\s+(?:the\s+)?(?:company|role|project)\b",
        r"\bsucceed\s+in\s+this\s+role\b", r"\bfit\s+for\s+this\s+role\b",
        r"\bapply\s+(?:these\s+)?(?:skills|strengths)\s+(?:in|to)\b"
    ],
    "lexical scope": [
        r"\blexical\s+scop\w*\b", r"\blexically\b", r"\bstatic\s+scop\w*\b",
        r"\benclosing\s+scop\w*\b", r"\bparent\s+scop\w*\b"
    ],
    "inner function": [
        r"\binner\s+functions?\b", r"\bnested\s+functions?\b", r"\bchild\s+functions?\b",
        r"\breturned\s+functions?\b", r"\bfunction\s+inside\b"
    ],
    "outer function variables": [
        r"\bouter\s+(?:function\s+)?variables?\b", r"\benclosing\s+(?:function\s+)?variables?\b",
        r"\bparent\s+(?:function\s+)?variables?\b", r"\bvariables?\s+of\s+(?:the\s+)?outer\b",
        r"\bouter\s+scope\b", r"\bvariables?\s+from\s+(?:the\s+)?outer\b"
    ],
    "scope chain": [
        r"\bscope\s+chain\w*\b", r"\bchain\s+of\s+scopes?\b", r"\blookup\s+chain\b",
        r"\bidentifier\s+resolution\b"
    ],
    "retained access": [
        r"\bretain\w*\s+access\b", r"\bretains?\s+(?:access|variables?)\b",
        r"\baccess\s+(?:to\s+)?(?:the\s+)?outer\b",
        r"\bafter\s+(?:the\s+)?outer\s+function\s+returns?\b",
        r"\beven\s+after\s+(?:the\s+)?outer\b", r"\bkeeps?\s+access\b",
        r"\bremembers?\s+(?:the\s+)?variables?\b", r"\bpreserves?\s+(?:the\s+)?scope\b",
        r"\bhas\s+access\b", r"\bvariables?\s+(?:remain|persist)\b",
        r"\bkeeps?\s+using\s+a\s+variable\s+after\s+the\s+outer\b"
    ],
    "java unit testing framework": [
        r"\b(?:java\s+)?unit\s+test(?:ing)?\s+framework\b",
        r"\btesting\s+framework\s+(?:for\s+)?java\b",
        r"\bjava\s+testing\s+framework\b",
        r"\bopen[\s-]source\s+testing\s+framework\b",
        r"\bframework\s+(?:used\s+)?(?:for|to)\s+unit\s+test\w*\b",
        r"\bunit\s+test(?:ing)?\s+tool\b"
    ],
    "unit tests": [
        r"\bunit\s+tests?\b",
        r"\bunit\s+testing\b",
        r"\bunit[\s-]tests?\b",
        r"\btest\w*\s+individual\s+(?:units?|components?|methods?|classes)\b",
        r"\btesting\s+in\s+isolation\b",
        r"\bautomated\s+unit\s+tests?\b"
    ],
    "test annotations": [
        r"@test\b",
        r"\btest\s+annotations?\b",
        r"\bannotations?\b",
        r"\btest\s+methods?\b",
        r"@before(?:each|all)?\b",
        r"@after(?:each|all)?\b",
        r"\blifecycle\s+annotations?\b",
        r"\bannotat(?:ed|ing)\s+test\s+methods?\b",
        r"\btest\s+methods?\s+(?:and|or|with)\s+annotations?\b"
    ],
    "assertions": [
        r"\bassertions?\b",
        r"\bassert\s+statements?\b",
        r"\bassert(?:equals|true|false|null|notnull|throws|same|notsame|that)\b",
        r"\bassert\w*\s+methods?\b",
        r"\bexpected\s+(?:and|vs\.?|versus)\s+actual\b",
        r"\bverif(?:y|ying|ication)\s+of\s+results?\b",
        r"\bcheck\s+expected\s+outcomes?\b"
    ],
    "test execution": [
        r"\btest\s+execution\b",
        r"\bexecut\w*\s+(?:unit\s+)?tests?\b",
        r"\brunn?ing\s+(?:unit\s+)?tests?\b",
        r"\brun\s+(?:unit\s+)?tests?\b",
        r"\btest[\s-]runners?\b",
        r"\btest\s+runners?\b",
        r"\bautomated\s+test\s+run\w*\b",
        r"\btest\s+(?:results?|reports?)\s+(?:pass|fail)\b",
        r"\bexecute\s+test\s+(?:cases?|suites?)\b"
    ],
    "responsive web design": [
        r"\bresponsive\s+(?:web\s+)?design\b",
        r"\bresponsive\s+design\b",
        r"\bresponsive\s+layout\b",
        r"\brwd\b",
        r"\bresponsive\b",
        r"\badapt\w*\s+to\s+(?:different\s+)?(?:screen\s+sizes?|devices?)\b",
        r"\ball\s+devices\b",
        r"\bdesktop\s+(?:tablet\s+)?(?:and\s+)?mobile\b"
    ],
    "media queries": [
        r"\bmedia\s+quer(?:y|ies)\b",
        r"@media\b",
        r"\bcss\s+media\s+quer(?:y|ies)\b",
        r"\bmedia\s+rules?\b"
    ],
    "viewport": [
        r"\bviewport\b",
        r"\bmeta\s+viewport\b",
        r"\bviewport\s+meta\s+tag\b",
        r"\bdevice[\s-]width\b",
        r"\binitial[\s-]scale\b",
        r"\bviewable\s+area\b"
    ],
    "breakpoints": [
        r"\bbreakpoints?\b",
        r"\bmin[\s-]width\b",
        r"\bmax[\s-]width\b",
        r"\bscreen\s+widths?\b",
        r"\bpixel\s+thresholds?\b"
    ],
    "fluid layout and flexible images": [
        r"\bfluid\s+(?:layout|grid)s?\b",
        r"\bflexible\s+(?:images?|layouts?|grids?)\b",
        r"\bfluid\s+(?:and\s+flexible\s+)?(?:layout|grid|images?)\b",
        r"\brelative\s+units?\b",
        r"\bpercentages?\b",
        r"\bpercent\s+widths?\b",
        r"\bvw\s+(?:and|or)\s+vh\b",
        r"\brem\s+(?:and|or)\s+em\b",
        r"\bmax[\s-]width:\s*100%\b",
        r"\bauto\s+scaling\b",
        r"\bflexible\s+dimensions\b"
    ],
    "mobile-first design": [
        r"\bmobile[\s-]first\b",
        r"\bmobile\s+first\s+design\b",
        r"\bmobile\s+first\s+approach\b",
        r"\bmobile\s+devices?\s+first\b",
        r"\bprogressive\s+enhancement\b"
    ],
    "method resolution order (mro)": [
        r"\bmethod\s+resolution\s+order\b",
        r"\bmro\b",
        r"\bmethod\s+resolution\b"
    ],
    "order in which python searches for methods and attributes": [
        r"\border\s+(?:in\s+which\s+)?(?:python\s+)?search\w*\s+for\s+(?:methods?|attributes?|functions?)\b",
        r"\bsearch\w*\s+order\b",
        r"\border\s+of\s+(?:method\s+)?lookup\b",
        r"\blookup\s+order\b",
        r"\bsearches?\s+(?:for\s+)?methods?\s+and\s+attributes?\b",
        r"\battribute\s+lookup\s+order\b",
        r"\border\s+python\s+resolves?\b",
        r"\bhow\s+python\s+resolves?\s+(?:methods?|attributes?)\b",
        r"\bresolv\w*\s+methods?\s+(?:in\s+classes?|in\s+hierarchy)\b"
    ],
    "multiple inheritance": [
        r"\bmultiple\s+inheritance\b",
        r"\binherit(?:s|ing|ed)?\s+from\s+multiple\s+(?:parent\s+)?classes\b",
        r"\bmore\s+than\s+one\s+(?:parent|base)\s+class\b",
        r"\bdiamond\s+problem\b",
        r"\bclass\s+hierarchy\b"
    ],
    "c3 linearization algorithm": [
        r"\bc3\s+linearization(?:\s+algorithm)?\b",
        r"\bc3\s+algorithm\b",
        r"\bc3\s+method\b",
        r"\blinearization\s+algorithm\b",
        r"\bc3\b"
    ],
    "classname.mro() or classname.__mro__": [
        r"\b(?:\w+\.)?mro\(\)",
        r"\b(?:\w+\.)?__mro__\b",
        r"\bmro\(\)\b",
        r"\b__mro__\b",
        r"\bmro\s+method\b",
        r"\b__mro__\s+attribute\b"
    ],
    "simplify complex technical information": [
        r"\bsimplif\w*\s+(?:the\s+)?(?:data|information|analysis|technical\s+terms?|complex|concepts?)\b",
        r"\bbreak\s*(?:ing)?\s+down\s+(?:the\s+)?(?:complex|analysis|data|findings|technical)\b",
        r"\bmake\s+(?:it\s+)?(?:simple|digestible|easy\s+to\s+understand)\b",
        r"\btranslate\s+(?:the\s+)?technical\s+(?:terms?|details?)\b",
        r"\bdemystif\w*\b"
    ],
    "use non-technical language and avoid jargon": [
        r"\b(?:avoid|no|without|eliminate)\s+jargon\b",
        r"\bnon[\s-]technical\s+(?:language|words?|terms?|vocabulary)\b",
        r"\bplain\s+(?:english|language|terms?)\b",
        r"\blayman'?s?\s+terms?\b",
        r"\beveryday\s+(?:language|words?|terms?)\b",
        r"\bsimple\s+(?:words?|language|terms?|vocabulary)\b"
    ],
    "explain key findings clearly": [
        r"\b(?:key|main|core|primary)\s+(?:findings?|insights?|takeaways?|results?|conclusions?)\b",
        r"\bhighlight\s+(?:the\s+)?(?:findings?|insights?|results?|takeaways?)\b",
        r"\bwhat\s+the\s+data\s+(?:shows|means|tells\s+us)\b",
        r"\bbottom\s+line\b",
        r"\bsummary\s+of\s+(?:the\s+)?(?:findings?|results?|analysis)\b",
        r"\bclear\s+(?:results?|findings?|insights?)\b"
    ],
    "provide a relatable example": [
        r"\b(?:relatable|real[\s-]world|practical|concrete|simple)\s+(?:example|scenario|illustration|case|situation)\b",
        r"\buse\s+(?:an?\s+)?analog(?:y|ies)\b",
        r"\bmetaphor\b",
        r"\bstorytelling\b",
        r"\bvisual\s+(?:aid|chart|graph|dashboard)\b",
        r"\bfor\s+example\b"
    ],
    "connect findings to practical or business impact": [
        r"\b(?:business|practical|operational)\s+(?:impact|value|outcomes?|decisions?|goals?)\b",
        r"\bactionable\s+(?:insights?|recommendations?|next\s+steps?)\b",
        r"\bdecision[\s-]making\b",
        r"\bhelp\s+(?:them|the\s+business|stakeholders?)\s+make\s+decisions?\b",
        r"\broi\b",
        r"\bnext\s+steps?\b",
        r"\bso\s+what\b",
        r"\bhow\s+this\s+affects\s+(?:the\s+)?business\b"
    ]
}

def normalize_for_matching(text):
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"\bb\.?tech\b", "btech", text)
    text = re.sub(r"\bbtec\b", "btech", text)
    text = re.sub(r"\bb\s+tech\b", "btech", text)
    text = re.sub(r"\bm\.?tech\b", "mtech", text)
    text = re.sub(r"\bmtec\b", "mtech", text)
    text = re.sub(r"\bm\s+tech\b", "mtech", text)
    text = re.sub(r"\bb\.?c\.?a\b", "bca", text)
    text = re.sub(r"\bm\.?c\.?a\b", "mca", text)
    text = re.sub(r"\bb\.?sc\b", "bsc", text)
    text = re.sub(r"\bm\.?sc\b", "msc", text)
    text = re.sub(r"\bb\.?e\.?\s+(degree|in|engineering|graduate)\b", "btech", text)
    text = re.sub(r"\bb\.?e\.?\b", "btech", text)
    text = re.sub(r"\bpower\s*bi\b", "powerbi", text)
    text = re.sub(r"\bscikit\s*learn\b", "scikit", text)
    text = re.sub(r"\bv\s*lookup\b", "vlookup", text)
    text = re.sub(r"\bx\s*lookup\b", "xlookup", text)
    # Speech transcription phonetics and noise
    text = re.sub(r"\bmeeting\s+final\s+year\b", "in my final year", text)
    text = re.sub(r"\bfinal\s+(air|ear|hear|yea|yer)\b", "final year", text)
    text = re.sub(r"\bpersuing\b", "pursuing", text)
    text = re.sub(r"\bpp\s+savani\s+university\b", "pp savani university", text)
    text = re.sub(r"\bquick\s+problem\s+solvers?\b", "quick problem solver", text)
    text = re.sub(r"\bproblem[\s-]solvers?\b", "problem solver", text)
    text = re.sub(r"\bpaste\s+agitization\b", "pest digitization", text)
    text = re.sub(r"\bmulti[\s-]modally\s+interview\s+evolution\b", "multimodal interview evaluation", text)
    text = re.sub(r"\b(data\s*blue|diablo|tablo|tabloo)\b", "tableau", text)
    text = re.sub(r"\bmy\s+skill\s+serve\b", "my skills are", text)
    text = re.sub(r"\bi\s+don'?t\s+projects\b", "i did projects", text)
    text = re.sub(r"\bi\s+done\s+projects\b", "i did projects", text)
    text = re.sub(r"\bthose\s+in\s+this\s+detection\b", "drowsiness detection", text)
    text = re.sub(r"\bco[\s-]+strengths?\b", "core strengths", text)
    text = re.sub(r"\bbeing\s+(?:motive|module)\b", "being motivated", text)
    text = re.sub(r"\b(pursuing\s+btech\s+)finally(?:\s+here)?\b", r"\1final year", text)
    text = re.sub(r"\bfinally\s+(?:in|at|here)\b", "final year in", text)
    return text

def is_concept_matched(concept, raw_answer):
    if not concept or not raw_answer:
        return False

    c_norm = normalize_for_matching(concept)
    a_norm = normalize_for_matching(raw_answer)
    a_norm_spaced = re.sub(r"[-_/]", " ", a_norm)
    c_norm_spaced = re.sub(r"[-_/]", " ", c_norm)
    a_words = set(re.findall(r"\b[a-z0-9+#.]+\b", a_norm_spaced)) | set(re.findall(r"\b[a-z0-9+#.-]+\b", a_norm))

    # 1. Specialized canonical concept categories
    target_rule = None
    if re.search(r"\b(education|studies|academics|degree|university|college)\b", c_norm):
        target_rule = "education"
    elif re.search(r"\b(technical\s*skills?|tech\s*skills?|tools|technologies|skills)\b", c_norm) and not re.search(r"\b(soft|communication)\b", c_norm):
        target_rule = "technical skills"
    elif re.search(r"\b(experience|internships?|work\s*history|employment)\b", c_norm):
        target_rule = "relevant experience"
    elif re.search(r"\b(introduction|name|about\s*yourself|background)\b", c_norm):
        target_rule = "introduction"
    elif re.search(r"\b(projects?|portfolio|capstone)\b", c_norm):
        target_rule = "projects"
    elif re.search(r"\b(goals?|ambition|aspirations?|objectives?)\b", c_norm):
        target_rule = "career goals"
    elif re.search(r"\b(core\s*strengths?|key\s*strengths?|strengths?)\b", c_norm):
        target_rule = "core strengths"
    elif re.search(r"\b(communication|verbal|articulation)\b", c_norm):
        target_rule = "communication"
    elif re.search(r"\b(problem\s*solving|problem-solving|problem\s*solv\w*|analytical|troubleshooting)\b", c_norm_spaced):
        target_rule = "problem solving"
    elif re.search(r"\b(examin\w*\s+dataset\s+structure|dataset\s+structure)\b", c_norm_spaced):
        target_rule = "examining dataset structure"
    elif re.search(r"\b(data\s+types?|column\s+types?)\b", c_norm_spaced):
        target_rule = "data types"
    elif re.search(r"\b(missing\s+values?|missing\s+data|nulls?)\b", c_norm_spaced):
        target_rule = "missing values"
    elif re.search(r"\b(duplicates?|duplicate\s+rows?|deduplication)\b", c_norm_spaced):
        target_rule = "duplicates"
    elif re.search(r"\b(distributions?|data\s+distributions?|value\s+distributions?)\b", c_norm_spaced):
        target_rule = "distributions"
    elif re.search(r"\b(quality\s+issues?|data\s+quality)\b", c_norm_spaced):
        target_rule = "quality issues"
    elif re.search(r"\b(simplify|simplifying|break\s*down|breaking\s*down\s*complex)\b", c_norm_spaced):
        target_rule = "simplify complex technical information"
    elif re.search(r"\b(avoid\s*jargon|non\s*technical\s*language|layman|plain\s*english|plain\s*language)\b", c_norm_spaced):
        target_rule = "use non-technical language and avoid jargon"
    elif re.search(r"\b(key\s*findings|main\s*insights|core\s*takeaways|conclusions|clear\s*results|what\s+the\s+data\s+shows)\b", c_norm_spaced):
        target_rule = "explain key findings clearly"
    elif re.search(r"\b(relatable\s*example|analogy|metaphor|concrete\s*scenario|real\s*world\s*example|storytelling)\b", c_norm_spaced):
        target_rule = "provide a relatable example"
    elif re.search(r"\b(business\s*impact|actionable\s*insights?|business\s*value|roi|decision\s*making|practical\s*impact)\b", c_norm_spaced):
        target_rule = "connect findings to practical or business impact"
    elif re.search(r"\b(practical\s*example|examples?|illustration)\b", c_norm):
        target_rule = "practical example"
    elif re.search(r"\b(role\s*contribution|contribute|value\s*add)\b", c_norm):
        target_rule = "role contribution"
    elif re.search(r"\b(lexical\s*scop\w*)\b", c_norm_spaced):
        target_rule = "lexical scope"
    elif re.search(r"\b(inner\s*functions?)\b", c_norm_spaced):
        target_rule = "inner function"
    elif re.search(r"\b(outer\s*(?:function\s*)?variables?)\b", c_norm_spaced):
        target_rule = "outer function variables"
    elif re.search(r"\b(scope\s*chain\w*)\b", c_norm_spaced):
        target_rule = "scope chain"
    elif re.search(r"\b(retained?\s*access|outer\s*function\s*returns?)\b", c_norm_spaced):
        target_rule = "retained access"
    elif re.search(r"\b(unit\s*test(?:ing)?\s*framework|testing\s*framework|java\s*unit\s*testing)\b", c_norm_spaced):
        target_rule = "java unit testing framework"
    elif re.search(r"\b(unit\s*tests?|unit\s*testing)\b", c_norm_spaced):
        target_rule = "unit tests"
    elif re.search(r"\b(test\s*annotations?|test\s*methods?|annotations?)\b", c_norm_spaced):
        target_rule = "test annotations"
    elif re.search(r"\b(assertions?|assert\s*statements?|asserts?)\b", c_norm_spaced):
        target_rule = "assertions"
    elif re.search(r"\b(test\s*execution|test\s*runners?|execut\w*\s*tests?|running\s*tests?)\b", c_norm_spaced):
        target_rule = "test execution"
    elif re.search(r"\b(responsive\s*(?:web\s*)?design|responsive)\b", c_norm_spaced):
        target_rule = "responsive web design"
    elif re.search(r"\b(media\s*quer\w*)\b", c_norm_spaced):
        target_rule = "media queries"
    elif re.search(r"\b(viewport)\b", c_norm_spaced):
        target_rule = "viewport"
    elif re.search(r"\b(breakpoints?)\b", c_norm_spaced):
        target_rule = "breakpoints"
    elif re.search(r"\b(fluid\s*layout|flexible\s*images?|fluid\s*and\s*flexible)\b", c_norm_spaced):
        target_rule = "fluid layout and flexible images"
    elif re.search(r"\b(mobile\s*first\s*design|mobile\s*first)\b", c_norm_spaced):
        target_rule = "mobile-first design"
    elif re.search(r"\b(classname|mro\s*method|attribute)\b", c_norm_spaced) or "mro()" in c_norm or "__mro__" in c_norm or "classname" in c_norm:
        target_rule = "classname.mro() or classname.__mro__"
    elif re.search(r"\b(method\s*resolution\s*order)\b", c_norm_spaced) or c_norm.strip() in ("mro", "method resolution order (mro)", "mro in python", "python mro"):
        target_rule = "method resolution order (mro)"
    elif re.search(r"\b(search\s*order|lookup\s*order|search\w*\s+for\s+methods?|order\s+in\s+which)\b", c_norm_spaced):
        target_rule = "order in which python searches for methods and attributes"
    elif re.search(r"\b(multiple\s*inheritance)\b", c_norm_spaced):
        target_rule = "multiple inheritance"
    elif re.search(r"\b(c3|linearization)\b", c_norm_spaced):
        target_rule = "c3 linearization algorithm"

    if target_rule and target_rule in CONCEPT_PATTERNS:
        patterns = CONCEPT_PATTERNS[target_rule]
        for pat in patterns:
            if re.search(pat, a_norm) or re.search(pat, a_norm_spaced):
                return True
        return False

    # 2. Exact phrase match with word boundaries
    clean_c = re.sub(r"[^a-z0-9\s+#.]", " ", c_norm_spaced).strip()
    if clean_c and (
        re.search(r"\b" + re.escape(clean_c) + r"\b", a_norm) or
        re.search(r"\b" + re.escape(clean_c) + r"\b", a_norm_spaced)
    ):
        return True

    # 2b. Full concept phrase synonym expansion
    if clean_c in SYNONYMS_EXPANDED:
        for syn in SYNONYMS_EXPANDED[clean_c]:
            if len(syn) >= 2 and (
                re.search(r"\b" + re.escape(syn) + r"\b", a_norm) or
                re.search(r"\b" + re.escape(syn) + r"\b", a_norm_spaced)
            ):
                return True

    for syn_group in CONCEPT_SYNONYMS.values():
        if clean_c in syn_group:
            for syn in syn_group:
                if len(syn) >= 2 and (
                    re.search(r"\b" + re.escape(syn) + r"\b", a_norm) or
                    re.search(r"\b" + re.escape(syn) + r"\b", a_norm_spaced)
                ):
                    return True

    # 3. Token-based matching with synonym expansion & fuzzy similarity
    c_words = [w for w in re.findall(r"\b[a-z0-9+#.]+\b", c_norm_spaced) if len(w) > 1]
    stop_words = {"of", "the", "in", "to", "for", "from", "with", "a", "an", "is", "are", "and", "or", "by", "on", "at", "as", "into", "between"}
    sig_words = [w for w in c_words if w not in stop_words]

    if not sig_words:
        return bool(clean_c and (clean_c in a_norm or clean_c in a_norm_spaced))

    # Single significant term
    if len(sig_words) == 1:
        target = sig_words[0]
        if target in a_words:
            return True
        if target in SYNONYMS_EXPANDED and any(syn in a_words or syn in a_norm for syn in SYNONYMS_EXPANDED[target]):
            return True
        for syn_group in CONCEPT_SYNONYMS.values():
            if target in syn_group:
                if any(syn in a_words or syn in a_norm for syn in syn_group):
                    return True
        if len(target) >= 5:
            for aw in a_words:
                if len(aw) >= 4 and SequenceMatcher(None, target, aw).ratio() >= 0.85:
                    return True
        return False

    # Multi-term concept: prevent generic words from triggering a false positive match
    generic_words = {
        "data", "table", "tables", "record", "records", "row", "rows", "column", "columns",
        "value", "values", "database", "sql", "used", "test", "tests", "testing", "code",
        "java", "method", "methods", "framework", "tool", "tools", "program"
    }
    matched_terms = 0
    distinctive_matched = 0
    distinctive_count = 0

    for word in sig_words:
        is_distinctive = word not in generic_words
        if is_distinctive:
            distinctive_count += 1

        term_matched = False
        if word in a_words:
            term_matched = True
        elif word in SYNONYMS_EXPANDED and any(syn in a_words or syn in a_norm for syn in SYNONYMS_EXPANDED[word]):
            term_matched = True
        else:
            for syn_group in CONCEPT_SYNONYMS.values():
                if word in syn_group:
                    if any(syn in a_words or syn in a_norm for syn in syn_group):
                        term_matched = True
                        break
            if not term_matched and len(word) >= 5:
                for aw in a_words:
                    if len(aw) >= 4 and SequenceMatcher(None, word, aw).ratio() >= 0.85:
                        term_matched = True
                        break

        if term_matched:
            matched_terms += 1
            if is_distinctive:
                distinctive_matched += 1

    if distinctive_count == 0:
        return matched_terms == len(sig_words)

    if distinctive_matched == distinctive_count and (matched_terms / len(sig_words)) >= 0.60:
        return True

    return False


# =========================================================
# QUESTION TYPE HELPERS & RUBRICS
# =========================================================

def is_self_introduction(question, category=None):
    if category and str(category).lower() in ("introduction", "intro", "personal"):
        return True
    q = (question or "").lower()
    return any(p in q for p in [
        "tell me about yourself",
        "introduce yourself",
        "about yourself",
        "self introduction",
        "walk me through your resume",
        "brief introduction"
    ])


def is_strengths_question(question, category=None):
    if category and str(category).lower() in ("strengths", "hr", "behavioral"):
        q = (question or "").lower()
        if "strength" in q:
            return True
    q = (question or "").lower()
    return any(p in q for p in [
        "what are your strengths",
        "your strengths",
        "strengths and how can they help",
        "greatest strength",
        "key strengths",
        "core strengths"
    ])


# =========================================================
# LOCAL SEMANTIC EVALUATOR
# =========================================================

def local_evaluate(
    question,
    answer,
    expected_concepts,
    category=None
):

    question = clean_text(
        question
    )

    answer = clean_text(
        answer
    )

    concepts = [
        clean_text(c)
        for c in safe_list(
            expected_concepts
        )
        if clean_text(c)
    ]
    if expected_concepts is None and question:
        concepts = [
            clean_text(c)
            for c in safe_list(
                get_expected_concepts(question)
            )
            if clean_text(c)
        ]

    answer_words = normalize_words(
        answer
    )

    question_words = normalize_words(
        question
    )

    # -----------------------------------------------------
    # EMPTY
    # -----------------------------------------------------

    if not is_valid_answer(answer, question=question):
        return empty_answer_result(concepts or expected_concepts)

    # -----------------------------------------------------
    # WORD COUNT
    # -----------------------------------------------------

    words = word_count(
        answer
    )

    # -----------------------------------------------------
    # CONCEPT MATCHING
    # -----------------------------------------------------

    matched = []
    missing = []

    for concept in concepts:
        if is_concept_matched(concept, answer):
            matched.append(concept)
        else:
            missing.append(concept)

    if concepts:
        concept_score = round(
            (len(matched) / len(concepts)) * 100,
            2
        )
    else:
        concept_score = None

    # -----------------------------------------------------
    # RELEVANCE & QUESTION ALIGNMENT
    # -----------------------------------------------------

    concept_ratio = (len(matched) / len(concepts)) if concepts else None

    question_stop_words = {
        "what", "is", "are", "tell", "me", "about", "yourself", "how", "do", "you",
        "why", "explain", "describe", "define", "discuss", "the", "a", "an", "in",
        "to", "for", "with", "and", "or", "can", "would", "does", "from", "into",
        "your", "this", "that", "which", "who", "whom", "whose", "when", "where"
    }
    topic_words = set(w for w in question_words if w not in question_stop_words)
    def matches_topic_word(tw, words_set):
        if tw in words_set:
            return True
        tw_stem = tw.rstrip('s')
        if len(tw_stem) > 3 and any(w == tw_stem or w.rstrip('s') == tw_stem for w in words_set):
            return True
        return False
    matched_topic_count = sum(1 for tw in topic_words if matches_topic_word(tw, answer_words))
    topic_overlap = (matched_topic_count / len(topic_words) * 100.0) if topic_words else 0.0

    if concepts:
        concept_coverage_pct = (len(matched) / len(concepts)) * 100.0
        if len(matched) > 0:
            if topic_words:
                relevance_score = concept_coverage_pct * 0.75 + topic_overlap * 0.25
            else:
                relevance_score = concept_coverage_pct
        else:
            # No expected concepts were matched
            if topic_words and topic_overlap > 0:
                relevance_score = min(20.0, topic_overlap * 0.35)
            else:
                relevance_score = 0.0
    else:
        # Fallback when no curated concepts exist
        if topic_words and topic_overlap > 0:
            relevance_score = min(100.0, topic_overlap * 0.70 + min(30.0, (words / 30.0) * 30.0))
        elif not topic_words and words >= 5:
            relevance_score = min(50.0, (words / 30.0) * 50.0)
        else:
            relevance_score = 0.0

    relevance_score = clamp_score(relevance_score)

    # -----------------------------------------------------
    # TECHNICAL SCORE
    # -----------------------------------------------------

    if concepts:
        technical_score = clamp_score(
            concept_score * 0.75 + relevance_score * 0.25
        )
    else:
        technical_score = clamp_score(
            relevance_score
        )

    # -----------------------------------------------------
    # COMPLETENESS
    # -----------------------------------------------------

    if words == 0:
        completeness_score = 0.0
    elif concepts:
        if len(matched) == 0:
            completeness_score = 0.0
        else:
            depth_factor = min(100.0, (words / 35.0) * 100.0)
            completeness_score = clamp_score(
                concept_score * 0.70 + min(concept_score, depth_factor) * 0.30
            )
    else:
        depth_factor = min(100.0, (words / 35.0) * 100.0)
        completeness_score = clamp_score(
            relevance_score * 0.70 + min(relevance_score, depth_factor) * 0.30
        )

    # -----------------------------------------------------
    # COMMUNICATION
    # -----------------------------------------------------

    sentences = len(
        re.findall(
            r"[.!?]+",
            answer
        )
    )

    if words == 0:
        communication_score = 0.0
    elif words < 5:
        communication_score = 20.0
    elif words < 12:
        communication_score = 40.0
    else:
        comm_base = 60.0
        if sentences >= 2:
            comm_base += 15.0
        elif sentences == 1:
            comm_base += 5.0

        if 15 <= words <= 120:
            comm_base += 10.0
        elif words > 120:
            comm_base += 5.0

        hesitation_words = [
            "maybe", "perhaps", "i think", "not sure", "probably",
            "i don't know", "i guess"
        ]
        hesitation_count = sum(1 for item in hesitation_words if item in answer.lower())
        comm_base -= (hesitation_count * 8.0)
        communication_score = clamp_score(comm_base)

    # -----------------------------------------------------
    # CONFIDENCE
    # -----------------------------------------------------

    if words == 0:
        confidence_score = 0.0
    elif words < 5:
        confidence_score = 25.0
    elif words < 12:
        confidence_score = 40.0
    else:
        conf_base = 60.0
        assertive_phrases = [
            "i have", "i worked", "i built", "i designed", "i am proficient",
            "specifically", "for example", "i successfully", "i contributed"
        ]
        assertive_count = sum(1 for phrase in assertive_phrases if phrase in answer.lower())
        conf_base += min(20.0, assertive_count * 7.0)

        hesitation_words = [
            "maybe", "perhaps", "i think", "not sure", "probably",
            "i don't know", "i guess"
        ]
        hesitation_count = sum(1 for item in hesitation_words if item in answer.lower())
        conf_base -= (hesitation_count * 10.0)
        confidence_score = clamp_score(conf_base)

    # -----------------------------------------------------
    # PROBLEM SOLVING & QUESTION-TYPE RUBRIC
    # -----------------------------------------------------

    reasoning_words = [
        "because", "therefore", "solution", "solutions", "solve", "solved", "solving",
        "solves", "solver", "solvers", "problem solver", "problem solvers",
        "approach", "algorithm", "complexity", "resolved", "resolving",
        "resolve", "tradeoff", "tradeoffs", "optimized", "optimizing", "root cause",
        "analyzed", "analyzing", "analytical", "troubleshoot", "troubleshooting",
        "troubleshooted", "debug", "debugging", "debugged", "critical thinking",
        "steps taken", "overcome", "tackle", "tackled", "handled challenge"
    ]

    reasoning_count = sum(
        1 for item in reasoning_words
        if re.search(r"\b" + re.escape(item) + r"\b", answer.lower())
    )

    has_matched_problem_concept = any(
        "problem" in c or "troubleshoot" in c or "analytical" in c
        for c in matched
    )
    if has_matched_problem_concept and reasoning_count == 0:
        reasoning_count = 1

    if is_self_introduction(question, category):
        # Self-introductions assess background, education, skills, and career goals.
        # Problem-solving is not an expected dimension for introductions unless explicitly demonstrated.
        if reasoning_count >= 2:
            problem_solving_score = 60.0
        elif reasoning_count == 1:
            problem_solving_score = 35.0
        else:
            problem_solving_score = None
    elif is_strengths_question(question, category):
        # Strengths questions: evaluate relevant evidence instead of automatically assigning 0
        # when no explicit problem-solving example is given.
        has_problem_evidence = bool(
            has_matched_problem_concept
            or re.search(r"\bproblem[\s-]solv\w*\b", answer.lower())
            or re.search(r"\bquick[\s-]problem[\s-]solv\w*\b", answer.lower())
            or re.search(r"\banalytical\b", answer.lower())
            or re.search(r"\btroubleshoot\w*\b", answer.lower())
        )
        if reasoning_count >= 3:
            problem_solving_score = 80.0
        elif reasoning_count >= 2:
            problem_solving_score = 60.0
        elif has_problem_evidence or reasoning_count == 1:
            # Candidate provided relevant problem-solving evidence (e.g., explicitly identified
            # as problem solver / analytical) without an explicit multi-step practical example
            problem_solving_score = 45.0
        else:
            # Incomplete or non-demonstrated answer with no problem-solving evidence
            problem_solving_score = 0.0
    else:
        if reasoning_count >= 3:
            problem_solving_score = 80.0
        elif reasoning_count == 2:
            problem_solving_score = 60.0
        elif reasoning_count == 1:
            problem_solving_score = 35.0
        else:
            problem_solving_score = 0.0

    # -----------------------------------------------------
    # RELEVANCE GATE
    # -----------------------------------------------------

    result = {
        "technical_score": technical_score,
        "relevance_score": relevance_score,
        "concept_score": concept_score,
        "concept_coverage_score": concept_score,
        "completeness_score": completeness_score,
        "communication_score": communication_score,
        "confidence_score": confidence_score,
        "problem_solving_score": problem_solving_score,
        "matched_concepts": matched,
        "missing_concepts": missing,
        "strengths": [],
        "improvements": [],
        "evaluation_source": "local"
    }

    result = apply_relevance_gate(result)

    # -----------------------------------------------------
    # STRENGTHS
    # -----------------------------------------------------

    c_s = result.get("concept_score")
    if c_s is not None and c_s >= 70:
        result["strengths"].append("Strong coverage of expected key concepts.")
    elif c_s is not None and c_s >= 35:
        result["strengths"].append("Addressed several relevant concepts.")
    elif matched:
        result["strengths"].append(f"Demonstrated awareness of {matched[0]}.")

    has_heavy_disfluency_or_repetition = bool(
        re.search(r"\b(\w{3,})\b[\s.,;]+(?:\1)\b", answer.lower())
        or re.search(r"\betc(?:etera)?\b.*?\betc(?:etera)?\b", answer.lower())
        or (answer.lower().count("etc") >= 2)
    )
    if (
        result["communication_score"] >= 75
        and words >= 30
        and sentences >= 2
        and result["relevance_score"] >= 60
        and not has_heavy_disfluency_or_repetition
    ):
        result["strengths"].append("Communication was clear and structured.")

    if result["technical_score"] >= 70 and result["relevance_score"] >= 60:
        result["strengths"].append("Good technical depth and domain accuracy.")

    # -----------------------------------------------------
    # IMPROVEMENTS
    # -----------------------------------------------------

    if result["relevance_score"] < 20:
        result["improvements"].append("The response did not directly address the question asked.")
    elif result["relevance_score"] < 50:
        result["improvements"].append("Focus the response more directly on the question topic.")

    if words < 15 and result["relevance_score"] >= 20:
        result["improvements"].append("Elaborate more fully with complete explanations and supporting details.")

    if missing:
        if len(missing) <= 2:
            result["improvements"].append(f"Elaborate on: {', '.join(missing)}.")
        else:
            result["improvements"].append(f"Cover additional key concepts such as {', '.join(missing[:3])}.")

    if result["technical_score"] < 40 and result["relevance_score"] >= 20:
        result["improvements"].append("Provide more concrete technical details and terminology.")

    if not result["improvements"]:
        result["improvements"].append("Continue improving technical depth and clear examples.")

    return result


# =========================================================
# NORMALIZE EVALUATION RESULT
# =========================================================

def normalize_result(result):

    if not isinstance(
        result,
        dict
    ):
        return empty_answer_result()

    if "concept_coverage_score" not in result:
        result["concept_coverage_score"] = result.get("concept_score")
    if "concept_score" not in result:
        result["concept_score"] = result.get("concept_coverage_score")

    numeric_fields = [
        "technical_score",
        "relevance_score",
        "concept_score",
        "concept_coverage_score",
        "completeness_score",
        "communication_score",
        "confidence_score",
        "problem_solving_score"
    ]

    for field in numeric_fields:
        if field in ("concept_score", "concept_coverage_score", "problem_solving_score") and result.get(field) is None:
            continue
        result[field] = clamp_score(
            result.get(
                field,
                0
            )
        )

    result = apply_relevance_gate(
        result
    )

    for field in numeric_fields:
        if field in ("concept_score", "concept_coverage_score", "problem_solving_score") and result.get(field) is None:
            continue
        result[field] = clamp_score(
            result.get(
                field,
                0
            )
        )

    result["overall_score"] = calculate_overall(
        result["technical_score"],
        result["relevance_score"],
        result["concept_score"],
        result["completeness_score"],
        result["communication_score"],
        result["confidence_score"],
        result["problem_solving_score"]
    )

    result["matched_concepts"] = safe_list(
        result.get(
            "matched_concepts",
            []
        )
    )

    result["missing_concepts"] = safe_list(
        result.get(
            "missing_concepts",
            []
        )
    )

    result["strengths"] = safe_list(
        result.get(
            "strengths",
            []
        )
    )

    result["improvements"] = safe_list(
        result.get(
            "improvements",
            []
        )
    )

    return result


# =========================================================
# EVALUATE ONE QUESTION
# =========================================================

def evaluate_question(
    question,
    answer=None,
    expected_concepts=None,
    candidate_answer=None,
    category=None
):

    if answer is None and candidate_answer is not None:
        answer = candidate_answer

    question = clean_text(
        question
    )

    answer = clean_text(
        answer
    )

    # -----------------------------------------------------
    # EMPTY ANSWER
    # -----------------------------------------------------

    if not is_valid_answer(answer, question=question):

        return empty_answer_result(expected_concepts)

    # -----------------------------------------------------
    # TRY LLM
    # -----------------------------------------------------

    if (
        AI_PROVIDER != "local"
        and AI_API_KEY
        and AI_MODEL
        and AI_BASE_URL
    ):

        llm_result = evaluate_with_llm(
            question,
            answer,
            expected_concepts
        )

        if llm_result:

            llm_result[
                "evaluation_source"
            ] = AI_PROVIDER

            return normalize_result(
                llm_result
            )

    # -----------------------------------------------------
    # LOCAL FALLBACK
    # -----------------------------------------------------

    local_result = local_evaluate(
        question,
        answer,
        expected_concepts,
        category=category
    )

    return normalize_result(
        local_result
    )


# =========================================================
# MAIN INTERVIEW EVALUATION FUNCTION
# =========================================================

def evaluate_interview(
    question_answers
):

    if not isinstance(
        question_answers,
        list
    ):

        question_answers = []

    evaluated_questions = []

    print(
        "\n"
        + "=" * 60
    )

    print(
        "STARTING INTERVIEW EVALUATION"
    )

    print(
        "=" * 60
    )

    # =====================================================
    # EVALUATE ONLY QUESTIONS THAT EXIST
    # =====================================================

    for index, item in enumerate(
        question_answers
    ):

        question_number = item.get(
            "question_number",
            index + 1
        )

        question = clean_text(
            item.get(
                "question",
                ""
            )
        )

        answer = clean_text(
            item.get(
                "candidate_answer",
                ""
            )
        )

        expected_concepts = safe_list(
            item.get(
                "expected_concepts",
                []
            )
        )
        if not expected_concepts and question:
            expected_concepts = get_expected_concepts(question)

        print(
            f"\nQ{question_number}"
        )

        print(
            "Question:",
            question
        )

        print(
            "Answer:",
            answer
        )

        # =================================================
        # EVALUATE
        # =================================================

        category = item.get("category", "")
        evaluation = evaluate_question(
            question=question,
            answer=answer,
            expected_concepts=expected_concepts,
            category=category
        )

        # =================================================
        # BUILD RESULT
        # =================================================

        is_ans = is_valid_answer(answer, question=question)
        if item.get("is_answered") is False:
            is_ans = False

        question_result = {
            "question_number":
                question_number,

            "question":
                question,

            "candidate_answer":
                answer if is_ans else "",

            "is_answered":
                is_ans,

            "status":
                "answered" if is_ans else "not_answered",

            "expected_concepts":
                expected_concepts,

            "matched_concepts":
                evaluation.get(
                    "matched_concepts",
                    []
                ) if is_ans else [],

            "missing_concepts":
                evaluation.get(
                    "missing_concepts",
                    []
                ) if is_ans else expected_concepts,

            "technical_score":
                clamp_score(evaluation.get(
                    "technical_score",
                    0.0
                )) if is_ans else 0.0,

            "relevance_score":
                clamp_score(evaluation.get(
                    "relevance_score",
                    0.0
                )) if is_ans else 0.0,

            "concept_score":
                clamp_score(evaluation["concept_score"]) if (is_ans and evaluation.get("concept_score") is not None) else (0.0 if not is_ans else None),

            "concept_coverage_score":
                clamp_score(evaluation["concept_coverage_score"]) if (is_ans and evaluation.get("concept_coverage_score") is not None) else (0.0 if not is_ans else None),

            "completeness_score":
                clamp_score(evaluation.get(
                    "completeness_score",
                    0.0
                )) if is_ans else 0.0,

            "communication_score":
                clamp_score(evaluation.get(
                    "communication_score",
                    0.0
                )) if is_ans else 0.0,

            "confidence_score":
                clamp_score(evaluation.get(
                    "confidence_score",
                    0.0
                )) if is_ans else 0.0,

            "problem_solving_score":
                clamp_score(evaluation["problem_solving_score"]) if (is_ans and evaluation.get("problem_solving_score") is not None) else (0.0 if not is_ans else None),

            "overall_score":
                clamp_score(evaluation.get(
                    "overall_score",
                    0.0
                )) if is_ans else 0.0,

            "strengths":
                evaluation.get(
                    "strengths",
                    []
                ) if is_ans else [],

            "improvements":
                evaluation.get(
                    "improvements",
                    []
                ) if is_ans else [
                    "Question was not answered."
                ],

            "relative_start":
                item.get(
                    "relative_start"
                ),

            "relative_end":
                item.get(
                    "relative_end"
                ),

            "evaluation_source":
                evaluation.get(
                    "evaluation_source",
                    "local"
                ) if is_ans else "unanswered"
        }

        evaluated_questions.append(
            question_result
        )

        print(
            f"Technical: "
            f"{question_result['technical_score']}"
        )

        print(
            f"Relevance: "
            f"{question_result['relevance_score']}"
        )

        print(
            f"Concepts: "
            f"{question_result['concept_score']}"
        )

        print(
            f"Completeness: "
            f"{question_result['completeness_score']}"
        )

        print(
            f"Communication: "
            f"{question_result['communication_score']}"
        )

        print(
            f"Confidence: "
            f"{question_result['confidence_score']}"
        )

        print(
            f"Problem Solving: "
            f"{question_result['problem_solving_score']}"
        )

        print(
            f"Overall: "
            f"{question_result['overall_score']}"
        )

    # =====================================================
    # NO QUESTIONS
    # =====================================================

    if not evaluated_questions:

        return {

            "overall_score": 0.0,

            "technical_score": 0.0,

            "relevance_score": 0.0,

            "concept_score": 0.0,

            "completeness_score": 0.0,

            "communication_score": 0.0,

            "confidence_score": 0.0,

            "problem_solving_score": 0.0,

            "total_questions": 0,

            "attempted_questions": 0,

            "answered_questions": 0,

            "unanswered_questions": 0,

            "questions": [],

            "strengths": [],

            "improvements": [
                "No interview questions were evaluated."
            ]
        }

    # =====================================================
    # INTERVIEW LEVEL AVERAGES
    # =====================================================

    answered_items = [
        q for q in evaluated_questions
        if q.get("is_answered")
    ]

    target_for_avg = answered_items

    def average(field):
        if not target_for_avg:
            return 0.0

        if field in ("concept_score", "problem_solving_score"):
            valid_vals = [
                float(q[field])
                for q in target_for_avg
                if q.get(field) is not None
            ]
            if not valid_vals:
                return None
            return clamp_score(sum(valid_vals) / len(valid_vals))

        values = [
            float(
                q.get(
                    field,
                    0
                )
            )
            for q in target_for_avg
        ]

        if not values:
            return 0.0

        return clamp_score(
            sum(values)
            /
            len(values)
        )

    technical_score = average(
        "technical_score"
    )

    relevance_score = average(
        "relevance_score"
    )

    concept_score = average(
        "concept_score"
    )

    completeness_score = average(
        "completeness_score"
    )

    communication_score = average(
        "communication_score"
    )

    confidence_score = average(
        "confidence_score"
    )

    problem_solving_score = average(
        "problem_solving_score"
    )

    if target_for_avg:
        overall_score = calculate_overall(
            technical_score,
            relevance_score,
            concept_score,
            completeness_score,
            communication_score,
            confidence_score,
            problem_solving_score
        )
    else:
        overall_score = 0.0

    # =====================================================
    # INTERVIEW STRENGTHS
    # =====================================================

    strengths = []

    if technical_score is not None and technical_score >= 70:

        strengths.append(
            "Good technical understanding."
        )

    if relevance_score is not None and relevance_score >= 70:

        strengths.append(
            "Answers were generally relevant."
        )

    if communication_score is not None and communication_score >= 70:

        strengths.append(
            "Communication was generally clear."
        )

    if concept_score is not None and concept_score >= 60:

        strengths.append(
            "Good coverage of expected concepts."
        )

    # =====================================================
    # INTERVIEW IMPROVEMENTS
    # =====================================================

    improvements = []

    if not answered_items:

        improvements.append(
            "No answers were detected in this interview session. Please speak clearly into your microphone when answering questions."
        )

    else:

        if technical_score is not None and technical_score < 50:

            improvements.append(
                "Improve technical depth and correctness."
            )

        if relevance_score is not None and relevance_score < 50:

            improvements.append(
                "Keep answers directly focused on the question."
            )

        if concept_score is not None and concept_score < 50:

            improvements.append(
                "Cover more important concepts in each answer."
            )

        if completeness_score is not None and completeness_score < 50:

            improvements.append(
                "Provide more complete explanations."
            )

        if communication_score is not None and communication_score < 50:

            improvements.append(
                "Improve clarity and structure while answering."
            )

        if not improvements:

            improvements.append(
                "Continue improving technical depth and answer clarity."
            )

    # =====================================================
    # FINAL RESULT
    # =====================================================

    attempted_count = len(evaluated_questions)
    answered_count = len(answered_items)
    unanswered_count = max(0, attempted_count - answered_count)

    final_result = {

        "overall_score":
            overall_score,

        "technical_score":
            technical_score,

        "relevance_score":
            relevance_score,

        "concept_score":
            concept_score,

        "concept_coverage_score":
            concept_score,

        "completeness_score":
            completeness_score,

        "communication_score":
            communication_score,

        "confidence_score":
            confidence_score,

        "problem_solving_score":
            problem_solving_score,

        "total_questions":
            attempted_count,

        "attempted_questions":
            attempted_count,

        "answered_questions":
            answered_count,

        "unanswered_questions":
            unanswered_count,

        "questions":
            evaluated_questions,

        "strengths":
            strengths,

        "improvements":
            improvements
    }

    print(
        "\n"
        + "=" * 60
    )

    print(
        "INTERVIEW EVALUATION COMPLETE"
    )

    print(
        "=" * 60
    )

    print(
        "Questions:",
        len(evaluated_questions)
    )

    print(
        "Overall:",
        overall_score
    )

    print(
        "Technical:",
        technical_score
    )

    print(
        "Relevance:",
        relevance_score
    )

    print(
        "Concepts:",
        concept_score
    )

    print(
        "Completeness:",
        completeness_score
    )

    print(
        "Communication:",
        communication_score
    )

    print(
        "Confidence:",
        confidence_score
    )

    print(
        "Problem Solving:",
        problem_solving_score
    )

    print(
        "=" * 60
    )

    return final_result