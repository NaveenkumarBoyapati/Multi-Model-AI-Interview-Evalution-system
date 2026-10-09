# ===================================================
# QUESTION BANK & EXPECTED CONCEPTS REPOSITORY
# ===================================================

import re

try:
    from database import get_connection
except ImportError:
    try:
        from backend.database import get_connection
    except ImportError:
        get_connection = None


# ===================================================
# SEMANTIC SYNONYM CLUSTERS
# Maps concepts & key terms to their semantic equivalents
# ===================================================

CONCEPT_SYNONYMS = {
    "redundancy": ["redundancy", "redundant", "duplicate", "duplication", "duplicates", "repeated", "copies", "repetition", "unnecessary copy"],
    "organize": ["organize", "organizing", "organization", "structure", "structuring", "arranging", "systematize", "manage", "clean", "format", "relational"],
    "integrity": ["integrity", "consistency", "accuracy", "reliable", "reliability", "correctness", "validity", "quality", "constraint", "acid"],
    "normalize": ["normalize", "normalization", "normal forms", "1nf", "2nf", "3nf", "bcnf", "tables", "decompose"],
    "outlier": ["outlier", "outliers", "unusual", "extreme", "anomaly", "anomalies", "deviant", "atypical", "far off", "irregular", "noise", "box plot"],
    "optimize": ["optimize", "optimizing", "optimization", "performance", "faster", "speed", "speedup", "efficient", "efficiency", "tune", "tuning", "index", "indexes"],
    "missing": ["missing", "null", "nulls", "nan", "none", "blank", "empty", "absent", "impute", "imputation", "dropna", "fillna"],
    "remove": ["remove", "removing", "delete", "deleting", "drop", "dropping", "clean", "eliminate", "filter", "purge"],
    "combine": ["combine", "combining", "merge", "merging", "join", "joining", "integrate", "integrating", "aggregate", "append", "concat"],
    "extract": ["extract", "extracting", "extraction", "pull", "retrieve", "ingest", "fetch", "source"],
    "transform": ["transform", "transforming", "transformation", "clean", "cleaning", "convert", "converting", "process", "processing", "reshape", "format"],
    "load": ["load", "loading", "save", "saving", "store", "storing", "insert", "warehouse", "destination", "target"],
    "mutable": ["mutable", "changeable", "modifiable", "editable", "update in place", "can change"],
    "immutable": ["immutable", "unchangeable", "unmodifiable", "read only", "cannot change", "fixed"],
    "unique": ["unique", "distinct", "individual", "not duplicate", "single", "primary key"],
    "relationship": ["relationship", "relationships", "relation", "association", "connection", "link", "foreign key", "correlated"],
    "teamwork": ["teamwork", "team", "collaborate", "collaboration", "cooperation", "together", "group", "cross functional", "helping others", "help others", "team player", "supportive", "support teammates"],
    "strength": ["strength", "strengths", "skills", "proficient", "proficiency", "good at", "ability", "expertise", "competence", "consistent", "consistency", "loyal", "loyalty", "reliable", "reliability", "punctual", "punctuality", "on time", "doing work on time", "work on time", "meet deadlines", "time management", "helping others", "help others"],
    "communication": ["communication", "communications", "communicate", "communicating", "communicator", "interpersonal skills", "verbal", "articulate", "convey ideas", "presentation skills", "listening skills"],
    "punctuality": ["punctual", "punctuality", "on time", "doing work on time", "work on time", "meet deadlines", "time management"],
    "weakness": ["weakness", "weaknesses", "improve", "improving", "improvement", "learning", "growth", "challenge"],
    "pressure": ["pressure", "stress", "deadlines", "calm", "prioritize", "manage", "handle", "coping"],
    "structured": ["structured", "schema", "relational", "tables", "rows", "columns", "sql", "rdbms"],
    "unstructured": ["unstructured", "no schema", "flexible", "documents", "images", "videos", "audio", "text", "nosql"],
    "correlation": ["correlation", "relationship", "association", "dependency", "pearson", "positive", "negative", "scatter plot"],
    "olap": ["olap", "online analytical processing", "multidimensional", "analysis", "cube", "reporting", "bi", "data warehouse"],
    "visualization": ["visualization", "charts", "graphs", "plots", "dashboards", "patterns", "visual representation", "insights"],
    "vlookup": ["vlookup", "vertical lookup", "lookup function", "lookup value", "search key"],
    "lookup": ["lookup", "search", "find", "match", "retrieve", "query", "vlookup", "xlookup"],
    "array": ["array", "range", "table", "dataset", "table array", "reference range"],
    "column": ["column", "columns", "field", "fields", "col", "column index", "column number"],
    "exact": ["exact", "exact match", "approximate", "approximate match", "false", "true", "zero", "precision"],
    "pivot": ["pivot", "pivot table", "pivot tables", "summary table", "aggregation", "cross tab"],
    "dax": ["dax", "data analysis expressions", "formula", "measures", "calculated columns"],
    "problem-solving": ["problem-solving", "problem solving", "problem solver", "problem solvers", "quick problem solver", "quick problem-solver", "problem solve", "solve problems", "solving problems", "analytical", "troubleshooting", "critical thinking", "resolve issues"],
    "dataset structure": ["dataset structure", "data structure", "examining dataset structure", "table structure", "schema", "shape of data", "rows and columns", "column structure"],
    "data types": ["data types", "variable types", "column types", "dtypes", "data type"],
    "missing values": ["missing values", "missing data", "nulls", "null values", "nan", "empty cells", "blank values", "null records"],
    "duplicates": ["duplicates", "duplicate rows", "duplicate records", "redundancy", "redundant rows", "deduplication"],
    "distributions": ["distributions", "data distribution", "value distribution", "spread", "variance", "frequency", "standard deviation", "percentiles", "quantiles", "mean and median"],
    "quality issues": ["quality issues", "data quality", "inconsistencies", "invalid values", "anomalies", "outliers", "data cleanliness", "errors in data"],
    "lexical scope": ["lexical scope", "lexical scoping", "lexically", "static scope", "enclosing scope", "parent scope", "outer scope"],
    "inner function": ["inner function", "inner functions", "nested function", "nested functions", "child function", "returned function"],
    "outer function variables": ["outer function variables", "outer variables", "parent variables", "enclosing variables", "variables of outer", "outer function"],
    "scope chain": ["scope chain", "scope chaining", "chain of scopes", "scope lookup", "identifier resolution"],
    "retained access after the outer function returns": [
        "retained access after the outer function returns", "retains access", "retained access",
        "access after outer function returns", "remember variables", "preserves scope", "keeps access",
        "access to outer function variables even after the outer function returns", "retaining access"
    ],
    "java unit testing framework": [
        "java unit testing framework", "unit testing framework", "unit test framework",
        "testing framework for java", "java testing framework", "test framework", "unit testing tool"
    ],
    "unit tests": [
        "unit tests", "unit test", "unit testing", "individual units of code",
        "testing components in isolation", "test individual methods", "test individual functions"
    ],
    "test annotations": [
        "test annotations", "test annotation", "@test", "annotations", "annotation",
        "test methods", "test method", "@beforeeach", "@aftereach", "@beforeall", "@afterall",
        "@before", "@after", "lifecycle annotations", "test methods and annotations", "test methods/annotations"
    ],
    "assertions": [
        "assertions", "assertion", "assert", "assertequals", "asserttrue", "assertfalse",
        "assertnull", "assertnotnull", "assertthrows", "assert statements", "expected vs actual",
        "expected and actual", "verification of results", "verify expected outcome"
    ],
    "test execution": [
        "test execution", "test runner", "running tests", "run tests", "executing tests",
        "execute tests", "automated test execution", "automated tests", "test suite execution",
        "reports test results", "test report", "pass fail results"
    ],
    "responsive web design": [
        "responsive web design", "responsive design", "rwd", "responsive", "adapts to screen size",
        "different screen sizes", "different devices", "mobile friendly"
    ],
    "media queries": [
        "media queries", "media query", "@media", "css media query", "screen query", "media rules"
    ],
    "viewport": [
        "viewport", "meta viewport", "viewport meta tag", "viewable area", "device width", "device-width", "initial-scale"
    ],
    "breakpoints": [
        "breakpoints", "breakpoint", "min-width", "max-width", "screen width trigger", "pixel threshold"
    ],
    "fluid layout and flexible images": [
        "fluid layout", "flexible images", "fluid grid", "relative units", "percentages", "percent widths",
        "rem", "em", "vw", "vh", "max-width: 100%"
    ],
    "mobile-first design": [
        "mobile-first", "mobile first", "mobile-first design", "progressive enhancement", "mobile first approach"
    ],
    "method resolution order (mro)": [
        "method resolution order (mro)", "method resolution order", "mro", "method resolution",
        "mro in python", "python mro"
    ],
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
    ],
    "simplify complex technical information": [
        "simplify complex technical information", "simplify", "simplifying", "break down",
        "breaking down complex", "translate technical", "digestible", "easy to understand",
        "simple terms", "demystify", "simplify data", "simplify technical concepts"
    ],
    "use non-technical language and avoid jargon": [
        "use non-technical language and avoid jargon", "avoid jargon", "no jargon",
        "non-technical language", "plain english", "layman terms", "layman's terms",
        "everyday language", "without technical terms", "simple vocabulary", "plain language"
    ],
    "explain key findings clearly": [
        "explain key findings clearly", "key findings", "main insights", "core takeaways",
        "highlight conclusions", "summary of findings", "clear results", "bottom line",
        "what the data shows", "key insights", "main findings", "clear findings"
    ],
    "provide a relatable example": [
        "provide a relatable example", "relatable example", "analogy", "analogies",
        "metaphor", "concrete scenario", "real-world example", "storytelling",
        "visual aid", "chart or graph", "relatable story", "simple example", "use an analogy"
    ],
    "connect findings to practical or business impact": [
        "connect findings to practical or business impact", "business impact",
        "actionable insights", "practical decision", "so what", "business value",
        "roi", "decision making", "drive business outcomes", "next steps",
        "practical impact", "actionable recommendations", "business decisions"
    ]
}


# ===================================================
# CURATED QUESTION CONCEPTS
# Core questions for Python, Java, Data Analyst, Web Developer, HR
# ===================================================

CURATED_QUESTION_BANK = {

    # -----------------------------------------------
    # FIXED QUESTIONS & COMMON INTERVIEW QUESTIONS
    # -----------------------------------------------

    "tell me about yourself.": [
        "education",
        "technical skills",
        "projects",
        "relevant experience",
        "career goals"
    ],

    "tell me about yourself": [
        "education",
        "technical skills",
        "projects",
        "relevant experience",
        "career goals"
    ],

    "tell me about yourself and your background.": [
        "education",
        "technical skills",
        "projects",
        "relevant experience",
        "career goals"
    ],

    "self-introduction": [
        "education",
        "technical skills",
        "projects",
        "relevant experience",
        "career goals"
    ],

    "what are your strengths and how can they help you in this role?": [
        "core strengths",
        "communication",
        "problem-solving",
        "practical example",
        "role contribution"
    ],

    "what are your strengths and how can they help you in this role": [
        "core strengths",
        "communication",
        "problem-solving",
        "practical example",
        "role contribution"
    ],

    "what are your strengths?": [
        "core strengths",
        "communication",
        "problem-solving",
        "practical example",
        "role contribution"
    ],

    "what are your strengths": [
        "core strengths",
        "communication",
        "problem-solving",
        "practical example",
        "role contribution"
    ],

    "what are your greatest strengths?": [
        "core strengths",
        "communication",
        "problem-solving",
        "practical example",
        "role contribution"
    ],

    # -----------------------------------------------
    # WEB DEVELOPER / JAVASCRIPT
    # -----------------------------------------------

    "what are closures in javascript?": [
        "lexical scope",
        "inner function",
        "outer function variables",
        "scope chain",
        "retained access after the outer function returns"
    ],

    "what are closures in javascript": [
        "lexical scope",
        "inner function",
        "outer function variables",
        "scope chain",
        "retained access after the outer function returns"
    ],

    "what are closures?": [
        "lexical scope",
        "inner function",
        "outer function variables",
        "scope chain",
        "retained access after the outer function returns"
    ],

    "what are closures": [
        "lexical scope",
        "inner function",
        "outer function variables",
        "scope chain",
        "retained access after the outer function returns"
    ],

    "explain closures and late binding.": [
        "lexical scope",
        "inner function",
        "outer function variables",
        "scope chain",
        "retained access after the outer function returns"
    ],

    "what is responsive web design and media queries?": [
        "responsive web design",
        "media queries",
        "viewport",
        "breakpoints",
        "fluid layout and flexible images",
        "mobile-first design"
    ],

    "what is responsive web design and media queries": [
        "responsive web design",
        "media queries",
        "viewport",
        "breakpoints",
        "fluid layout and flexible images",
        "mobile-first design"
    ],

    "what is responsive web design?": [
        "responsive web design",
        "media queries",
        "viewport",
        "breakpoints",
        "fluid layout and flexible images",
        "mobile-first design"
    ],

    "what is responsive web design": [
        "responsive web design",
        "media queries",
        "viewport",
        "breakpoints",
        "fluid layout and flexible images",
        "mobile-first design"
    ],

    "explain responsive web design and media queries.": [
        "responsive web design",
        "media queries",
        "viewport",
        "breakpoints",
        "fluid layout and flexible images",
        "mobile-first design"
    ],

    # -----------------------------------------------
    # JAVA DEVELOPER / JUNIT
    # -----------------------------------------------

    "what is junit?": [
        "java unit testing framework",
        "unit tests",
        "test annotations",
        "assertions",
        "test execution"
    ],

    "what is junit": [
        "java unit testing framework",
        "unit tests",
        "test annotations",
        "assertions",
        "test execution"
    ],

    "explain junit and its key features.": [
        "java unit testing framework",
        "unit tests",
        "test annotations",
        "assertions",
        "test execution"
    ],

    # -----------------------------------------------
    # DATA ANALYST / SQL / DATA CONCEPTS
    # -----------------------------------------------

    "what is data profiling?": [
        "examining dataset structure",
        "data types",
        "missing values",
        "duplicates",
        "distributions",
        "quality issues"
    ],

    "what is data profiling": [
        "examining dataset structure",
        "data types",
        "missing values",
        "duplicates",
        "distributions",
        "quality issues"
    ],

    "explain data profiling and its key components.": [
        "examining dataset structure",
        "data types",
        "missing values",
        "duplicates",
        "distributions",
        "quality issues"
    ],

    "what is normalization?": [
        "organize data",
        "reduce redundancy",
        "data integrity",
        "normal forms",
        "split tables"
    ],

    "what is normalization in sql?": [
        "organize data",
        "reduce redundancy",
        "data integrity",
        "normal forms",
        "eliminate duplicate data"
    ],

    "what is denormalization?": [
        "combine tables",
        "redundancy introduction",
        "faster read performance",
        "reduce joins",
        "data warehousing"
    ],

    "what are structured and unstructured data?": [
        "structured data",
        "unstructured data",
        "relational tables",
        "fixed schema",
        "documents and text",
        "multimedia images videos"
    ],

    "what is an outlier?": [
        "extreme value",
        "deviates from normal pattern",
        "unusual observation",
        "data distribution",
        "detection techniques"
    ],

    "what is the difference between data and information?": [
        "raw unorganized facts",
        "processed structured data",
        "meaning and context",
        "decision making value"
    ],

    "what is etl?": [
        "extract data",
        "transform and clean",
        "load to destination",
        "data pipeline",
        "data warehouse"
    ],

    "how do you handle missing values?": [
        "identify nulls",
        "remove records dropna",
        "imputation fillna",
        "mean median mode",
        "domain context"
    ],

    "how do you remove duplicate data?": [
        "identify duplicate records",
        "remove duplicates",
        "drop_duplicates in pandas",
        "distinct in sql"
    ],

    "what is correlation?": [
        "relationship between variables",
        "positive correlation",
        "negative correlation",
        "strength of association",
        "scatter plot analysis"
    ],

    "what is data visualization?": [
        "visual representation",
        "charts and graphs",
        "identifying patterns",
        "communicating insights",
        "dashboards"
    ],

    "how do you optimize an sql query?": [
        "create indexes",
        "avoid select star",
        "use proper joins",
        "execution plan analysis",
        "filter early with where"
    ],

    "what is a primary key?": [
        "unique identifier",
        "cannot be null",
        "identifies table row",
        "entity integrity"
    ],

    "what is a foreign key?": [
        "links two tables",
        "references primary key",
        "referential integrity",
        "relational constraints"
    ],

    "what is sql?": [
        "structured query language",
        "relational database management",
        "querying data",
        "crud operations",
        "schema definitions"
    ],

    "what is an sql join?": [
        "combine rows from tables",
        "common column match",
        "inner join",
        "left right full joins"
    ],

    "explain inner join.": [
        "matching records only",
        "both tables match",
        "intersection of data",
        "common key values"
    ],

    "explain left join.": [
        "all rows from left table",
        "matched rows from right table",
        "null values for non matches",
        "preserve left records"
    ],

    "what is group by?": [
        "aggregate rows",
        "group by column",
        "used with count sum avg",
        "summary reporting"
    ],

    "what is having?": [
        "filter grouped records",
        "used after group by",
        "filters aggregate results",
        "difference from where clause"
    ],

    "what is a subquery?": [
        "nested query",
        "query inside query",
        "inner query executes first",
        "used in where from select"
    ],

    "what is a database index?": [
        "faster data retrieval",
        "b-tree structure",
        "improves search speed",
        "tradeoff with write performance"
    ],

    "what is a pandas series?": [
        "one dimensional array",
        "labeled index",
        "pandas data structure",
        "homogeneous data type"
    ],

    "what is a dataframe?": [
        "two dimensional table",
        "rows and columns",
        "heterogeneous data types",
        "pandas data structure"
    ],

    "what is olap?": [
        "online analytical processing",
        "multidimensional analysis",
        "data cube aggregations",
        "business intelligence reporting"
    ],

    "how do you analyze sales data?": [
        "collect and clean data",
        "analyze trends and seasonality",
        "revenue metrics and kpis",
        "customer segmentation",
        "visualize insights"
    ],

    "what is vlookup?": [
        "vertical lookup",
        "lookup value",
        "table array",
        "column index number",
        "exact or approximate match"
    ],

    "what is xlookup?": [
        "successor to vlookup",
        "lookup value",
        "lookup array",
        "return array",
        "default exact match"
    ],

    "what is excel?": [
        "spreadsheet software",
        "cells rows and columns",
        "formulas and calculations",
        "data organization and analysis"
    ],

    "what are excel pivot tables?": [
        "summarize large datasets",
        "drag and drop fields",
        "aggregate metrics",
        "rows columns filters values"
    ],

    "what is conditional formatting?": [
        "format cells based on rules",
        "highlight data patterns",
        "color scales and data bars",
        "visual data analysis"
    ],

    "what is power bi?": [
        "business intelligence tool",
        "data visualization and dashboards",
        "data modeling and transformation",
        "connect multiple data sources"
    ],

    "what is a power bi dashboard?": [
        "single page visual summary",
        "interactive tiles and charts",
        "business kpis tracking",
        "real time insights"
    ],

    "what is power query?": [
        "data transformation tool",
        "etl in excel and power bi",
        "clean and shape data",
        "m code language"
    ],

    "what is dax?": [
        "data analysis expressions",
        "formula language in power bi",
        "calculated columns and measures",
        "advanced data aggregation"
    ],

    # -----------------------------------------------
    # PYTHON DEVELOPER CONCEPTS
    # -----------------------------------------------

    "what is python and what are its main features?": [
        "interpreted language",
        "high level dynamically typed",
        "object oriented",
        "simple readable syntax",
        "vast standard library"
    ],

    "what is the difference between a list and a tuple in python?": [
        "list is mutable",
        "tuple is immutable",
        "syntax brackets vs parentheses",
        "tuples faster performance",
        "tuples can be dictionary keys"
    ],

    "what are python dictionaries and how are they used?": [
        "key value pairs",
        "hash table lookup",
        "keys must be immutable",
        "fast retrieval o(1)",
        "curly braces syntax"
    ],

    "explain the concept of mutable and immutable objects in python.": [
        "mutable can be modified in place",
        "immutable cannot be changed",
        "memory id changes upon modification",
        "lists dicts sets are mutable",
        "strings tuples numbers are immutable"
    ],

    "what is the difference between == and is in python?": [
        "== checks value equality",
        "is checks object identity memory address",
        "id() comparison for is",
        "content comparison for =="
    ],

    "what are decorators in python?": [
        "modify function behavior",
        "wraps another function",
        "@ symbol syntax",
        "higher order functions",
        "code reusability"
    ],

    "what is list comprehension?": [
        "concise syntax for lists",
        "inline for loop and condition",
        "replaces map and filter",
        "more readable and efficient"
    ],

    "what is mro in python?": [
        "method resolution order (mro)",
        "order in which python searches for methods and attributes",
        "multiple inheritance",
        "c3 linearization algorithm",
        "classname.mro() or classname.__mro__"
    ],

    "what is mro in python": [
        "method resolution order (mro)",
        "order in which python searches for methods and attributes",
        "multiple inheritance",
        "c3 linearization algorithm",
        "classname.mro() or classname.__mro__"
    ],

    "what is mro?": [
        "method resolution order (mro)",
        "order in which python searches for methods and attributes",
        "multiple inheritance",
        "c3 linearization algorithm",
        "classname.mro() or classname.__mro__"
    ],

    "what is mro": [
        "method resolution order (mro)",
        "order in which python searches for methods and attributes",
        "multiple inheritance",
        "c3 linearization algorithm",
        "classname.mro() or classname.__mro__"
    ],

    "explain mro in python.": [
        "method resolution order (mro)",
        "order in which python searches for methods and attributes",
        "multiple inheritance",
        "c3 linearization algorithm",
        "classname.mro() or classname.__mro__"
    ],

    "explain method resolution order in python.": [
        "method resolution order (mro)",
        "order in which python searches for methods and attributes",
        "multiple inheritance",
        "c3 linearization algorithm",
        "classname.mro() or classname.__mro__"
    ],

    "what is a generator in python?": [
        "yield keyword",
        "lazy evaluation",
        "iterates values on demand",
        "memory efficient",
        "returns iterator object"
    ],

    "what is object-oriented programming in python?": [
        "classes and objects",
        "encapsulation",
        "inheritance",
        "polymorphism",
        "abstraction",
        "reusable modular code"
    ],

    "explain inheritance in python.": [
        "child class inherits parent class",
        "code reuse",
        "super() function",
        "method overriding",
        "multiple inheritance support"
    ],

    "what is polymorphism in python?": [
        "many forms",
        "same method name different behavior",
        "duck typing",
        "method overriding"
    ],

    "what is encapsulation in python?": [
        "bundling data and methods",
        "private and protected attributes",
        "underscore conventions",
        "data hiding and security"
    ],

    "what is exception handling in python?": [
        "try except finally blocks",
        "runtime error handling",
        "prevent program crash",
        "custom exceptions raise"
    ],

    "what is virtual environment in python?": [
        "isolated environment",
        "dependency isolation",
        "venv or virtualenv",
        "avoids version conflicts"
    ],

    "what is fastapi?": [
        "modern high performance web framework",
        "asynchronous support asyncio",
        "automatic swagger documentation",
        "pydantic type validation",
        "fast execution speed"
    ],

    "what is rest api?": [
        "representational state transfer",
        "stateless client server architecture",
        "http methods get post put delete",
        "json payload communication",
        "standard response status codes"
    ],

    # -----------------------------------------------
    # JAVA DEVELOPER CONCEPTS
    # -----------------------------------------------

    "what is java and what are its main features?": [
        "platform independent write once run anywhere",
        "object oriented",
        "robust and secure",
        "automatic garbage collection",
        "multithreading support"
    ],

    "what is jvm?": [
        "java virtual machine",
        "executes java bytecode",
        "platform dependent component",
        "memory management and jit compiler"
    ],

    "what is the difference between jdk, jre and jvm?": [
        "jdk is development kit with compiler",
        "jre is runtime environment with libraries",
        "jvm is execution engine",
        "jdk contains jre which contains jvm"
    ],

    "what is spring boot?": [
        "microservices framework",
        "auto configuration",
        "embedded web server tomcat",
        "production ready actuators",
        "rapid development without xml"
    ],

    "what is dependency injection?": [
        "inversion of control ioc",
        "supplies dependencies from outside",
        "loose coupling",
        "spring container management",
        "easier unit testing"
    ],

    # -----------------------------------------------
    # HR & BEHAVIORAL QUESTIONS
    # -----------------------------------------------

    "what are your strengths?": [
        "core skills and abilities",
        "problem solving mindset",
        "continuous learning",
        "adaptability",
        "practical example from projects"
    ],

    "what are your weaknesses?": [
        "self awareness",
        "genuine professional area for growth",
        "steps taken to improve",
        "positive constructive framing"
    ],

    "why should we hire you?": [
        "match with job requirements",
        "technical expertise",
        "work ethic and dedication",
        "eagerness to contribute",
        "cultural fit"
    ],

    "how do you handle pressure?": [
        "staying calm and composed",
        "task prioritization",
        "breaking problems into steps",
        "effective time management",
        "focused problem solving"
    ],

    "tell me about a time you worked in a team.": [
        "team collaboration",
        "clear communication",
        "role and responsibilities",
        "conflict resolution",
        "successful project outcome"
    ],

    "how do you manage your time?": [
        "prioritizing urgent and important tasks",
        "time blocking and schedules",
        "meeting deadlines",
        "using organization tools"
    ],

    "why did you choose this career?": [
        "passion for technology and problem solving",
        "interest in data or development",
        "continuous learning opportunities",
        "impact of software and insights"
    ],

    "what makes you different from other candidates?": [
        "unique blend of skills",
        "fast learner and adaptable",
        "strong practical project experience",
        "dedication to quality and outcomes"
    ],

    # -----------------------------------------------
    # JAVA DEVELOPER FOUNDATIONAL QUESTIONS
    # -----------------------------------------------

    "what is string in java?": [
        "object representing character sequence",
        "immutable",
        "string constant pool",
        "heap memory",
        "java.lang.String class"
    ],

    "what is multithreading?": [
        "concurrent execution of threads",
        "cpu utilization",
        "thread lifecycle",
        "context switching",
        "shared memory"
    ],

    "what is synchronization?": [
        "thread safety",
        "prevent race conditions",
        "synchronized keyword or locks",
        "mutual exclusion",
        "shared resource access"
    ],

    "what is a class in java?": [
        "blueprint or template for objects",
        "contains fields and methods",
        "defines state and behavior",
        "user-defined data type"
    ],

    "what is an object in java?": [
        "instance of a class",
        "has state and behavior",
        "allocated in heap memory",
        "created with new keyword"
    ],

    "explain inheritance in java.": [
        "extends keyword",
        "subclass inherits superclass",
        "code reusability",
        "single and multilevel inheritance",
        "method overriding"
    ],

    "explain polymorphism in java.": [
        "many forms",
        "compile-time overloading",
        "runtime overriding",
        "dynamic method dispatch",
        "polymorphic references"
    ],

    "what is encapsulation?": [
        "data hiding",
        "bundling data and methods",
        "private variables",
        "public getters and setters",
        "prevents unauthorized modification"
    ],

    "what is abstraction?": [
        "hiding implementation details",
        "showing essential features",
        "abstract classes and interfaces",
        "reduces complexity"
    ],

    "what is stack memory?": [
        "call stack and execution frames",
        "stores local variables and references",
        "lifo structure",
        "fast allocation and deallocation",
        "thread-specific memory"
    ],

    "what is garbage collection?": [
        "automatic memory management",
        "deallocates unreferenced heap objects",
        "prevents memory leaks",
        "runs in jvm background",
        "system.gc hint"
    ],

    "what is java collections framework?": [
        "unified architecture for data structures",
        "list set queue map interfaces",
        "arraylist linkedlist hashmap",
        "generics and iterators",
        "java.util package"
    ],

    "what is a thread?": [
        "lightweight unit of execution",
        "subdivision of a process",
        "runs concurrent tasks",
        "extends Thread or implements Runnable",
        "run() and start() methods"
    ],

    "what is exception handling?": [
        "handling runtime errors gracefully",
        "try catch finally throw throws",
        "checked and unchecked exceptions",
        "prevents abnormal termination",
        "exception hierarchy"
    ],

    "difference between checked and unchecked exceptions?": [
        "checked verified at compile time",
        "unchecked runtime exceptions",
        "checked inherits Exception",
        "unchecked inherits RuntimeException",
        "file not found vs null pointer"
    ],

    "what are try, catch and finally?": [
        "try block encloses risky code",
        "catch block handles exception",
        "finally block executes cleanup code",
        "finally executes regardless of exception",
        "resource release"
    ],

    "what is method overloading?": [
        "same method name different parameters",
        "compile-time polymorphism",
        "different type count or order of arguments",
        "within same class",
        "return type alone not sufficient"
    ],

    "what is method overriding?": [
        "subclass provides specific implementation of superclass method",
        "runtime polymorphism",
        "same method signature and return type",
        "@Override annotation",
        "dynamic binding"
    ],

    "what is a constructor?": [
        "special method to initialize objects",
        "same name as class",
        "no return type",
        "invoked with new keyword",
        "default and parameterized constructors"
    ],

    "what is the difference between this and super?": [
        "this refers to current class instance",
        "super refers to immediate parent class instance",
        "this() calls constructor in same class",
        "super() calls parent constructor",
        "method and variable access"
    ],

    "what are interfaces in java?": [
        "abstract type defining contract",
        "implements keyword",
        "public abstract methods and constants",
        "supports multiple inheritance",
        "default and static methods in java 8"
    ],

    "what are abstract classes?": [
        "class declared with abstract keyword",
        "cannot be instantiated directly",
        "can have abstract and concrete methods",
        "provides base structure for subclasses",
        "can hold instance variables"
    ],

    "difference between interface and abstract class?": [
        "interface cannot have state or instance fields",
        "abstract class can have constructors and state",
        "multiple interfaces can be implemented",
        "single class inheritance",
        "contract vs base class"
    ],

    "what is a static keyword?": [
        "belongs to class rather than instance",
        "shared among all instances",
        "static variables and methods",
        "accessed via class name without object",
        "static memory in metaspace"
    ],

    "what is a final keyword?": [
        "final variable cannot be reassigned",
        "final method cannot be overridden",
        "final class cannot be inherited",
        "ensures immutability and constancy"
    ],

    "what are access modifiers in java?": [
        "public protected default private",
        "controls scope and visibility",
        "encapsulation support",
        "package and subclass access rules"
    ],

    "what is the difference between == and equals() in java?": [
        "== checks memory reference identity",
        "equals() checks value or logical equality",
        "can override equals() in custom classes",
        "string and object comparisons"
    ],

    "how do you secure web applications against xss and csrf?": [
        "output encoding and input sanitization",
        "content security policy csp",
        "anti csrf tokens",
        "httponly and samesite cookies",
        "defense in depth"
    ]
}

try:
    from populate_all_curated_questions import CURATED_ALL_ROLE_QUESTIONS
    CURATED_QUESTION_BANK.update(CURATED_ALL_ROLE_QUESTIONS)
except ImportError:
    try:
        from backend.populate_all_curated_questions import CURATED_ALL_ROLE_QUESTIONS
        CURATED_QUESTION_BANK.update(CURATED_ALL_ROLE_QUESTIONS)
    except ImportError:
        pass


# ===================================================
# DYNAMIC CONCEPT GENERATOR
# Generates rich concepts for ANY question automatically
# ===================================================

def normalize_key(text):
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return " ".join(text.split())


def generate_fallback_concepts(question_text, role=None):
    """
    Intelligently extracts core terms and generates safe, topic-aligned
    expected concept phrases for any arbitrary interview question.
    Never invents concepts unrelated to the question, and avoids awkward phrases
    such as 'complex and analysis implementation'.
    """
    clean_q = normalize_key(question_text)
    words = [w for w in clean_q.split() if len(w) >= 2]

    stop_words = {
        "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
        "explain", "describe", "define", "discuss", "tell", "difference", "between",
        "and", "the", "are", "you", "your", "can", "they", "this", "that", "for",
        "with", "about", "would", "does", "from", "into", "help", "role", "use",
        "used", "using", "work", "works", "working", "versus", "vs", "please",
        "is", "in", "on", "at", "an", "a", "of", "to", "by", "as", "it", "its",
        "do", "did", "have", "has", "had", "call", "them", "person", "audience",
        "stakeholder", "stakeholders", "someone"
    }

    keywords = [w for w in words if w not in stop_words]

    concepts = []
    if keywords:
        main_topic = " ".join(keywords[:3])
        q_lower = question_text.lower()
        if any(w in q_lower for w in ["how would you explain", "how do you explain", "explain", "communicate"]):
            concepts.append(f"{main_topic} explanation and core meaning")
            concepts.append("clear structured communication and simple terminology")
            concepts.append("practical example, analogy, or real-world scenario")
            concepts.append("business value, impact, and actionable takeaways")
        elif any(w in q_lower for w in ["difference", "versus", "vs", "compare"]):
            concepts.append(f"core definitions and purpose of {main_topic}")
            concepts.append("key distinctions in syntax and architecture")
            concepts.append("appropriate use cases for each option")
            concepts.append("performance and trade-off considerations")
        else:
            concepts.append(f"{main_topic} definition and core purpose")
            concepts.append(f"key principles and mechanics of {keywords[0]}")
            concepts.append("practical application and real-world use cases")
            concepts.append("concrete example and best practices")
    else:
        concepts = [
            "clear technical explanation",
            "core principles and concepts",
            "practical application and use cases",
            "concrete example or scenario"
        ]

    return concepts


def get_expected_concepts(question_text, role=None):
    """
    Returns curated expected concepts for a question:
    1. Exact or substring match in curated in-memory bank.
    2. Direct lookup from SQL Server Questions table (expected_topics column).
    3. Token-overlap match against SQL Server Questions table.
    4. Reliable topic-aligned fallback derivation based on question keywords (never empty).
    """
    if not question_text:
        return ["clear explanation", "relevant technical concepts", "practical example"]

    normalized = normalize_key(question_text)

    # 1. Exact match in curated bank
    for bank_q, concepts in CURATED_QUESTION_BANK.items():
        if normalize_key(bank_q) == normalized:
            return concepts

    # 2. Fuzzy substring match in curated bank
    for bank_q, concepts in CURATED_QUESTION_BANK.items():
        bank_norm = normalize_key(bank_q)
        if bank_norm in normalized or normalized in bank_norm:
            return concepts

    # 3. Look up from Questions table in SQL Server if database connection is available
    if get_connection:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            clean_q = " ".join(question_text.strip().split())

            if role:
                cursor.execute(
                    "SELECT expected_topics FROM Questions WITH (NOLOCK) WHERE LOWER(LTRIM(RTRIM(question_text))) = LOWER(?) AND LOWER(role_name) = LOWER(?)",
                    (clean_q, role.strip())
                )
                row = cursor.fetchone()
                if row and row[0] and row[0].strip():
                    cursor.close()
                    conn.close()
                    return [t.strip() for t in row[0].split(",") if t.strip()]

            cursor.execute(
                "SELECT expected_topics FROM Questions WITH (NOLOCK) WHERE LOWER(LTRIM(RTRIM(question_text))) = LOWER(?)",
                (clean_q,)
            )
            row = cursor.fetchone()
            if row and row[0] and row[0].strip():
                cursor.close()
                conn.close()
                return [t.strip() for t in row[0].split(",") if t.strip()]

            # Also check without trailing punctuation
            cursor.execute(
                "SELECT expected_topics FROM Questions WITH (NOLOCK) WHERE LOWER(LTRIM(RTRIM(REPLACE(question_text, '?', '')))) = LOWER(?)",
                (clean_q.replace("?", ""),)
            )
            row = cursor.fetchone()
            if row and row[0] and row[0].strip():
                cursor.close()
                conn.close()
                return [t.strip() for t in row[0].split(",") if t.strip()]

            # 3b. Token-overlap match against Questions table
            stop_set = {
                "what", "is", "a", "an", "the", "in", "of", "and", "or", "how", "to", "for",
                "with", "are", "do", "you", "your", "can", "they", "used", "tell", "me",
                "about", "why", "which", "would", "will", "this", "role", "please", "difference", "between"
            }
            input_tokens = set(w for w in re.findall(r"[a-z0-9+#.]+", clean_q.lower()) if w not in stop_set and len(w) > 1)

            if input_tokens:
                if role:
                    cursor.execute(
                        "SELECT question_text, expected_topics FROM Questions WITH (NOLOCK) WHERE LOWER(role_name) = LOWER(?) AND expected_topics IS NOT NULL AND LTRIM(RTRIM(expected_topics)) <> ''",
                        (role.strip(),)
                    )
                else:
                    cursor.execute(
                        "SELECT question_text, expected_topics FROM Questions WITH (NOLOCK) WHERE expected_topics IS NOT NULL AND LTRIM(RTRIM(expected_topics)) <> ''"
                    )
                db_rows = cursor.fetchall()
                best_sim = 0.0
                best_topics = None
                for db_q, db_top in db_rows:
                    if not db_top or not str(db_top).strip():
                        continue
                    db_tokens = set(w for w in re.findall(r"[a-z0-9+#.]+", db_q.lower()) if w not in stop_set and len(w) > 1)
                    if not db_tokens:
                        continue
                    overlap = len(input_tokens & db_tokens)
                    union = len(input_tokens | db_tokens)
                    sim = overlap / float(union) if union > 0 else 0.0
                    if sim > best_sim:
                        best_sim = sim
                        best_topics = db_top

                if best_sim >= 0.60 and best_topics:
                    cursor.close()
                    conn.close()
                    return [t.strip() for t in best_topics.split(",") if t.strip()]

            cursor.close()
            conn.close()
        except Exception as db_err:
            pass

    # 4. Safe, topic-aligned fallback derivation for unknown / dynamic questions
    fallback = generate_fallback_concepts(question_text, role=role)
    print(f"[Question Bank Warning] Question '{question_text}' (role={role}) not found in curated bank or database. Generated safe fallback: {fallback}")
    return fallback
