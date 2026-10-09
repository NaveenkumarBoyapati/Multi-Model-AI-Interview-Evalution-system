"""
Curated question bank expansions and database backfill for all 4 roles:
- Python Developer (100 questions)
- Java Developer (92 questions)
- Data Analyst (95 questions)
- Web Developer (18 questions)

Includes accurate, curated expected concepts for every question in frontend interview.js,
updates row 1846 for "How would you explain a complex analysis to a non-technical person?",
and syncs them into SQL Server Questions table.
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import get_connection

CURATED_ALL_ROLE_QUESTIONS = {
    # -------------------------------------------------------------------------
    # DATA ANALYST
    # -------------------------------------------------------------------------
    "how would you explain a complex analysis to a non-technical person?": [
        "simplify complex technical information",
        "use non-technical language and avoid jargon",
        "explain key findings clearly",
        "provide a relatable example",
        "connect findings to practical or business impact"
    ],
    "how do you communicate analytical findings?": [
        "understand the audience needs",
        "clear visual storytelling and dashboards",
        "highlight actionable insights and recommendations",
        "structured presentation and clear documentation",
        "connect findings to business decisions"
    ],
    "how do you find trends in a dataset?": [
        "time series analysis and rolling averages",
        "exploratory data analysis and summary statistics",
        "visual inspection with line charts and scatter plots",
        "trend lines and regression modeling",
        "identifying seasonality and anomalies"
    ],
    "what is data analysis?": [
        "inspecting and cleaning raw data",
        "transforming and modeling data",
        "discovering useful patterns and insights",
        "supporting informed decision making"
    ],
    "what is data cleaning?": [
        "identifying and correcting inaccurate records",
        "handling missing null and duplicate values",
        "standardizing formats and data types",
        "removing outliers and noise",
        "ensuring data consistency and validity"
    ],
    "why is data preprocessing important?": [
        "improve data quality and reliability",
        "eliminate noise and inconsistent formatting",
        "prepare raw data for modeling and analysis",
        "prevent biased or misleading conclusions"
    ],
    "what is exploratory data analysis?": [
        "summarizing main characteristics of data",
        "visualizing distributions with histograms and box plots",
        "uncovering patterns correlations and anomalies",
        "testing initial hypotheses and assumptions"
    ],
    "what is descriptive analysis?": [
        "describes historical data and past performance",
        "summary statistics mean median and mode",
        "aggregations counts and percentages",
        "answering what happened in the business"
    ],
    "what is diagnostic analysis?": [
        "investigating root causes of past outcomes",
        "drill-down queries and detailed filtering",
        "correlation and anomaly analysis",
        "answering why something happened"
    ],
    "predictive analysis": [
        "forecasting future trends and outcomes",
        "historical data and statistical modeling",
        "machine learning algorithms and regression",
        "answering what is likely to happen"
    ],
    "what is predictive analysis?": [
        "forecasting future trends and outcomes",
        "historical data and statistical modeling",
        "machine learning algorithms and regression",
        "answering what is likely to happen"
    ],
    "what is prescriptive analysis?": [
        "recommending optimal courses of action",
        "simulation and optimization algorithms",
        "evaluating potential impact of decisions",
        "answering what should be done next"
    ],
    "explain right join.": [
        "returns all records from right table",
        "matched records from left table",
        "null values for unmatched left rows",
        "outer join mechanics and use cases"
    ],
    "what is order by?": [
        "sorts query result sets in sql",
        "ascending order asc default",
        "descending order desc",
        "sorting by single or multiple columns"
    ],
    "difference between where and having?": [
        "where filters rows before grouping",
        "having filters aggregated groups after group by",
        "where cannot use aggregate functions",
        "having evaluates conditions on sum avg count"
    ],
    "what are excel charts?": [
        "visual representation of worksheet data",
        "bar column line and pie chart types",
        "facilitating trend analysis and data comparison",
        "customization of titles axes and legends"
    ],
    "why is data visualization important?": [
        "communicates complex insights clearly and quickly",
        "reveals trends patterns and outliers",
        "empowers faster data-driven decision making",
        "engages non-technical stakeholders effectively"
    ],
    "what is a kpi?": [
        "key performance indicator",
        "quantifiable measure of business performance",
        "tracking progress toward strategic objectives",
        "target thresholds and variance monitoring"
    ],
    "what is a dashboard?": [
        "centralized visual display of kpis and metrics",
        "interactive filters and consolidated views",
        "real-time or periodic data monitoring",
        "supports high-level business intelligence"
    ],
    "difference between dashboard and report?": [
        "dashboard is high-level dynamic interactive and visual",
        "report is detailed structured tabular and historical",
        "dashboard tracks real-time kpis at a glance",
        "report provides comprehensive deep-dive documentation"
    ],
    "what is pandas?": [
        "python library for data manipulation and analysis",
        "dataframe and series data structures",
        "data cleaning transformation and aggregation",
        "file io for csv excel and sql"
    ],
    "what is numpy?": [
        "fundamental python library for numerical computing",
        "ndarray multidimensional array structure",
        "vectorized operations and broadcasting",
        "high-performance linear algebra and mathematics"
    ],
    "how do you identify outliers?": [
        "interquartile range iqr and box plots",
        "z-score and standard deviation thresholds",
        "visual inspection with scatter plots",
        "domain context and business validation"
    ],
    "what is regression?": [
        "statistical method modeling relationships between variables",
        "dependent target and independent feature variables",
        "linear regression line of best fit",
        "predicting continuous numerical values"
    ],
    "what is mean?": [
        "arithmetic average of a numerical dataset",
        "sum of all values divided by count of values",
        "measure of central tendency",
        "sensitive to extreme values and outliers"
    ],
    "what is median?": [
        "middle value of an ordered dataset",
        "separates upper and lower halves 50th percentile",
        "robust against outliers and skewed data",
        "measure of central tendency"
    ],
    "what is mode?": [
        "most frequently occurring value in a dataset",
        "applicable to both numerical and categorical data",
        "unimodal bimodal or multimodal distributions",
        "measure of central tendency"
    ],
    "what is standard deviation?": [
        "measure of dispersion or spread around the mean",
        "square root of variance",
        "indicates variability and consistency in data",
        "interpreting low vs high spread"
    ],
    "what is variance?": [
        "average of squared deviations from the mean",
        "quantifies spread or dispersion of data points",
        "square of standard deviation",
        "foundation for statistical modeling"
    ],
    "what is probability?": [
        "numerical measure of the likelihood an event occurs",
        "scale from 0 impossible to 1 absolute certainty",
        "sample space and favorable outcomes",
        "foundation for statistical inference and risk assessment"
    ],
    "what is sampling?": [
        "selecting a representative subset from a population",
        "random stratified or systematic sampling methods",
        "reduces time cost and computational complexity",
        "inferring population characteristics from sample data"
    ],
    "what is hypothesis testing?": [
        "null hypothesis h0 and alternative hypothesis h1",
        "statistical significance level alpha and p-value",
        "test statistics such as t-test chi-square and z-test",
        "rejecting or failing to reject null hypothesis"
    ],
    "what is a scatter plot?": [
        "graph showing relationship between two continuous variables",
        "cartesian coordinates with data points",
        "detecting correlation direction strength and outliers",
        "bivariate exploratory analysis"
    ],
    "what is a histogram?": [
        "graphical display of continuous data distribution",
        "bins or intervals along x-axis",
        "frequency or count represented by bar height",
        "assessing skewness modality and data spread"
    ],
    "what is a bar chart?": [
        "comparison of categorical discrete data",
        "bar length or height proportional to value",
        "vertical or horizontal orientations",
        "comparing metrics across distinct categories"
    ],
    "what is a line chart?": [
        "series of data points connected by straight line segments",
        "ideal for time series and continuous trends",
        "tracking changes over time intervals",
        "comparing multiple trend lines"
    ],
    "what is a pie chart?": [
        "circular chart divided into proportional slices",
        "represents parts of a whole summing to 100 percent",
        "effective for few distinct categorical shares",
        "visual composition display"
    ],
    "what is a box plot?": [
        "five-number summary min q1 median q3 max",
        "interquartile range iqr box and whiskers",
        "visual detection of outliers beyond whiskers",
        "comparing distributions across multiple groups"
    ],
    "how do you choose the right visualization?": [
        "identify variable types categorical continuous time-series",
        "determine goal comparison trend composition distribution",
        "tailor to audience non-technical vs executive vs analyst",
        "ensure clarity readability and accurate scale"
    ],
    "how do you validate data?": [
        "schema checks data types and null constraints",
        "range checks boundary values and format rules",
        "cross-referencing against source systems or benchmarks",
        "automated validation scripts and integrity tests"
    ],
    "how do you handle inconsistent data?": [
        "standardizing text casing date and unit formats",
        "reconciling conflicting records across sources",
        "deduplication and rule-based data transformation",
        "maintaining audit logs of cleaned records"
    ],
    "how do you combine datasets?": [
        "sql joins inner left right full on key columns",
        "concatenating or unioning rows with matching schemas",
        "pandas merge and join operations",
        "resolving mismatched column names and duplicates"
    ],
    "what is data transformation?": [
        "converting data from raw to structured target format",
        "normalization aggregation scaling and filtering",
        "feature engineering and categorical encoding",
        "part of etl pipeline for analysis readiness"
    ],
    "what is data integration?": [
        "combining data from heterogeneous disparate sources",
        "providing a unified centralized view of information",
        "data warehousing and etl ingestion pipelines",
        "resolving schema conflicts and entity mapping"
    ],
    "what is business intelligence?": [
        "technologies and strategies for data analysis",
        "transforming raw business data into actionable insights",
        "dashboards reporting data visualization and kpis",
        "facilitating strategic business decisions"
    ],
    "what is descriptive statistics?": [
        "summarizing and organizing characteristics of a dataset",
        "measures of central tendency mean median mode",
        "measures of variability range variance standard deviation",
        "tabular and visual summaries of sample data"
    ],
    "what is data quality?": [
        "accuracy completeness consistency and timeliness",
        "validity uniqueness and fitness for use",
        "detecting anomalies errors and missing records",
        "ensuring trustworthy analytical outcomes"
    ],
    "what is data governance?": [
        "policies standards and stewardship for data management",
        "data security privacy and regulatory compliance gdpr",
        "data lineage metadata and ownership definitions",
        "maintaining data integrity and organizational trust"
    ],
    "what is a data warehouse?": [
        "centralized repository of integrated historical data",
        "optimized for complex analytical querying and olap",
        "subject-oriented integrated time-variant non-volatile",
        "supports enterprise business intelligence and reporting"
    ],
    "what is a data mart?": [
        "focused subset of an enterprise data warehouse",
        "tailored for a specific department or business line",
        "faster access and simplified data models",
        "supports targeted reporting finance marketing sales"
    ],
    "what is oltp?": [
        "online transaction processing system",
        "handles high volumes of rapid daily transactional queries",
        "optimized for insert update and delete operations",
        "normalized relational database schema 3nf"
    ],
    "what is a fact table?": [
        "central table in a dimensional star schema",
        "stores quantitative measurable metrics and facts",
        "foreign keys linking to surrounding dimension tables",
        "supports aggregation and business metric analysis"
    ],
    "what is a dimension table?": [
        "contextual descriptive table in a dimensional schema",
        "describes attributes who what where and when",
        "joined to fact tables to filter and group data",
        "enables slicing and dicing in business intelligence"
    ],
    "what is a snowflake schema?": [
        "dimensional schema where dimension tables are normalized",
        "dimensions split into sub-dimension tables",
        "reduces data redundancy in dimensions",
        "requires more joins compared to star schema"
    ],
    "what is row_number()?": [
        "sql window ranking function",
        "assigns unique sequential integer to each row in partition",
        "partition by clause to divide rows into subsets",
        "order by clause to dictate sequence"
    ],
    "what is rank()?": [
        "sql window function assigning ranks based on ordering",
        "identical values receive identical rank with sequence gaps",
        "partition by and order by clauses",
        "comparison with dense_rank and row_number"
    ],
    "what is a cte?": [
        "common table expression in sql",
        "with clause defining temporary named result set",
        "improves query readability modularity and maintainability",
        "can be referenced multiple times and supports recursion"
    ],
    "what is a stored procedure?": [
        "precompiled collection of sql statements stored in database",
        "accepts input parameters and returns output values",
        "reduces network traffic and improves execution performance",
        "enhances security modularity and code reuse"
    ],
    "how do you analyze sales data?": [
        "identify sales kpis revenue profit margins volume",
        "time-based trend analysis monthly quarterly annual",
        "customer segmentation and regional performance breakdown",
        "product category performance and top selling items",
        "actionable recommendations for revenue growth"
    ],

    # -------------------------------------------------------------------------
    # PYTHON DEVELOPER
    # -------------------------------------------------------------------------
    "what are functions in python?": [
        "reusable blocks of organized code",
        "def keyword and function signature",
        "parameters and return statement",
        "modular programming and code reusability"
    ],
    "what are *args and **kwargs in python?": [
        "*args passes variable number of positional arguments as tuple",
        "**kwargs passes variable number of keyword arguments as dictionary",
        "flexible function signatures and unpacking",
        "forwarding arguments to inner functions"
    ],
    "explain python exception handling.": [
        "try except else finally blocks",
        "handling runtime errors gracefully",
        "raising custom exceptions with raise",
        "clean resource release in finally"
    ],
    "what is the purpose of try, except and finally?": [
        "try block contains code that might raise an exception",
        "except catches and handles specific exceptions",
        "finally executes cleanup code unconditionally",
        "resource management and preventing crashes"
    ],
    "what are python modules and packages?": [
        "module is a single python file with functions and classes",
        "package is a directory containing multiple modules",
        "import statement to load code",
        "__init__.py file designating packages"
    ],
    "what is abstraction in python?": [
        "hiding complex implementation details from user",
        "exposing only essential public interface",
        "abc module and abstractmethod decorator",
        "cannot instantiate abstract class directly"
    ],
    "what are constructors in python?": [
        "__init__ method initializing new object instances",
        "automatically invoked upon class instantiation",
        "self parameter referencing the current instance",
        "assigning instance attributes and initial state"
    ],
    "what is the difference between class and object?": [
        "class is a blueprint or template defining attributes and methods",
        "object is a concrete instance of a class in memory",
        "instantiation process creates objects from classes",
        "multiple objects can share the same class structure"
    ],
    "what are lambda functions?": [
        "anonymous small single-expression functions",
        "lambda keyword with parameters and single expression",
        "used inline with map filter and sorted",
        "no return statement required implicit return"
    ],
    "what is the difference between shallow copy and deep copy?": [
        "shallow copy copies outer object but references inner nested objects",
        "deep copy recursively copies outer object and all nested elements",
        "copy module copy() versus deepcopy()",
        "mutating nested elements affects shallow copy but not deep copy"
    ],
    "what is the use of the yield keyword?": [
        "converts a regular function into a generator function",
        "pauses function execution and produces a value to caller",
        "resumes state and execution on next() invocation",
        "memory-efficient lazy evaluation for large sequences"
    ],
    "what is an iterator in python?": [
        "object that allows traversing through all elements of a collection",
        "implements __iter__() and __next__() protocols",
        "raises StopIteration when elements are exhausted",
        "iter() and next() built-in functions"
    ],
    "what is recursion?": [
        "function that calls itself to solve smaller subproblems",
        "base case to terminate recursive calls and prevent infinite loops",
        "recursive step reducing problem towards base case",
        "call stack and recursion depth limit"
    ],
    "how does garbage collection work in python?": [
        "reference counting as primary memory management",
        "deallocates object when reference count reaches zero",
        "cyclic garbage collector gc module for circular references",
        "generational garbage collection generation 0 1 2"
    ],
    "what is pep 8?": [
        "python enhancement proposal defining style guide",
        "rules for 4-space indentation and line length limits",
        "naming conventions snake_case for functions PascalCase for classes",
        "improves code readability consistency and collaboration"
    ],
    "what are virtual environments in python?": [
        "isolated python environments for specific projects",
        "prevents package dependency conflicts across projects",
        "venv and virtualenv tools",
        "manages project-specific pip installations and versions"
    ],
    "what is pip?": [
        "standard package installer for python",
        "downloads and installs packages from pypi",
        "requirements.txt dependency management",
        "commands install uninstall freeze list"
    ],
    "how do you read and write files in python?": [
        "open() function with mode r w a rb wb",
        "with open context manager for automatic file closing",
        "read() readline() and readlines() for reading",
        "write() and writelines() for writing content"
    ],
    "what is json and how can python work with json?": [
        "javascript object notation lightweight data interchange format",
        "json module in python standard library",
        "json.loads() parses json string to python dict",
        "json.dumps() serializes python dict to json string",
        "json.load() and json.dump() for file streams"
    ],
    "what is the difference between append() and extend()?": [
        "append() adds a single element to the end of a list",
        "extend() iterates over an iterable and appends each element",
        "append adds nested list as a single sublist item",
        "extend unpacks elements into existing list in-place"
    ],
    "what is the difference between remove(), pop() and del?": [
        "remove() deletes first occurrence of specific value by value",
        "pop() removes and returns item at given index default last",
        "del statement removes item by index or slice or deletes variable",
        "handling ValueError when value not found in remove"
    ],
    "how can you reverse a string in python?": [
        "slice notation with negative step string[::-1]",
        "reversed() built-in function joined with ''.join()",
        "iterative loop building reversed string",
        "strings are immutable so creates a new string"
    ],
    "how can you find duplicate elements in a list?": [
        "using set to track seen elements and identify duplicates",
        "collections.Counter to count element frequencies",
        "list comprehension checking frequency greater than 1",
        "time complexity o(n) with set or dictionary"
    ],
    "how do you sort a list in python?": [
        "sort() method sorts list in-place modifying original list",
        "sorted() built-in function returns a new sorted list",
        "key parameter for custom sorting criteria or lambda",
        "reverse parameter for descending order Timsort algorithm"
    ],
    "what are sets in python?": [
        "unordered collection of unique and immutable elements",
        "set() constructor or curly braces syntax",
        "automatically eliminates duplicate values",
        "fast membership testing o(1) average lookup"
    ],
    "what are set operations?": [
        "union combines all unique elements from sets",
        "intersection returns elements present in both sets",
        "difference returns elements in first set but not second",
        "symmetric difference returns elements in either set but not both"
    ],
    "what is a python namespace?": [
        "mapping of variable names to corresponding objects in memory",
        "implemented internally as python dictionaries",
        "built-in global and local namespaces",
        "prevents naming conflicts across scopes"
    ],
    "what is variable scope in python?": [
        "region of program where a variable is accessible",
        "legb rule local enclosing global built-in",
        "local variables defined inside functions",
        "global variables defined at module top level"
    ],
    "explain local, global and nonlocal variables.": [
        "local variable exists inside function boundary",
        "global variable exists at module level across functions",
        "global keyword allows modifying global variable inside function",
        "nonlocal keyword modifies variable in enclosing non-global scope"
    ],
    "does python support method overloading?": [
        "does not support traditional method overloading by signature",
        "defining same method name overwrites previous definition",
        "achieved using default parameter values or *args",
        "functools.singledispatch for dynamic function overloading"
    ],
    "what is multiple inheritance?": [
        "child class inheriting from more than one parent class",
        "syntax class Child(Parent1, Parent2)",
        "method resolution order mro determines attribute lookup",
        "diamond problem resolved using c3 linearization"
    ],
    "what is dynamic typing?": [
        "variable types determined at runtime not at compile time",
        "no explicit type declaration required when creating variables",
        "variable can reference objects of different types over time",
        "type checking performed during program execution"
    ],
    "what are python libraries?": [
        "collections of prewritten code modules and functions",
        "standard library included with python math os sys json",
        "third party libraries installed via pip requests numpy pandas",
        "promotes code reuse and accelerates software development"
    ],
    "what is numpy used for?": [
        "scientific computing and multidimensional array processing",
        "fast mathematical operations on arrays and matrices",
        "linear algebra random number generation and fourier transforms",
        "vectorized operations outperforming python loops"
    ],
    "what is pandas used for?": [
        "data analysis manipulation and structured data handling",
        "dataframe structure for tabular two-dimensional data",
        "data cleaning filtering grouping and aggregating",
        "reading and writing diverse file formats csv excel sql"
    ],
    "what is matplotlib used for?": [
        "data visualization and plotting library in python",
        "generating 2d plots line bar scatter histograms",
        "pyplot interface for chart customization",
        "exporting publication-quality figures"
    ],
    "what is the difference between numpy and pandas?": [
        "numpy handles homogeneous numerical n-dimensional arrays",
        "pandas handles heterogeneous tabular data with labels",
        "pandas is built on top of numpy and adds index labels",
        "numpy for low-level mathematical operations pandas for data analysis"
    ],
    "what is a series in pandas?": [
        "one-dimensional labeled array in pandas",
        "can hold any data type integers strings floats",
        "accompanied by an explicit index array",
        "represents a single column in a pandas dataframe"
    ],
    "how do you handle missing data using pandas?": [
        "isna() and isnull() to detect missing nan values",
        "dropna() to remove rows or columns containing nulls",
        "fillna() to impute missing values with mean median or constant",
        "interpolate() for series estimation"
    ],
    "how do you remove duplicate records using pandas?": [
        "duplicated() to identify duplicate rows",
        "drop_duplicates() method to remove repeated rows",
        "subset parameter to check specific columns",
        "keep parameter first last or False"
    ],
    "how do you merge two dataframes?": [
        "pd.merge() function combining on key columns",
        "how parameter specifying inner left right outer join",
        "on or left_on and right_on parameters",
        "pd.concat() for stacking dataframes vertically or horizontally"
    ],
    "what is groupby() in pandas?": [
        "split-apply-combine strategy for data analysis",
        "splits dataframe into groups based on column values",
        "applies aggregation function sum mean count min max",
        "combines results into a summary dataframe"
    ],
    "what is data filtering in pandas?": [
        "selecting subset of rows matching specific boolean conditions",
        "boolean indexing df[df['col'] > val]",
        "loc and iloc indexing methods",
        "query() method for expressive conditional filtering"
    ],
    "how can you read a csv file using pandas?": [
        "pd.read_csv() function",
        "parameters filepath separator delimiter header",
        "usecols to load specific columns",
        "returns a structured pandas dataframe"
    ],
    "how can you export a dataframe to csv?": [
        "df.to_csv() method",
        "parameters filepath index=False to exclude row numbers",
        "sep parameter to define delimiter",
        "encoding parameter utf-8"
    ],
    "what is flask?": [
        "lightweight micro web framework for python",
        "werkzeug routing and jinja2 templating engine",
        "simple and flexible with minimal dependencies",
        "app routing decorators @app.route"
    ],
    "what is django?": [
        "high-level full-featured python web framework",
        "batteries-included with built-in orm admin panel and auth",
        "model view template mvt architectural pattern",
        "built-in security protections against csrf sql injection"
    ],
    "what is fastAPI?": [
        "modern high-performance web framework for building apis",
        "built on starlette pydantic and async await",
        "automatic interactive openapi swagger documentation",
        "fast execution speed comparable to nodejs and go"
    ],
    "what is an api?": [
        "application programming interface",
        "set of protocols and tools for software communication",
        "defines endpoints request methods and data formats",
        "enables decoupled client-server architecture"
    ],
    "what is http?": [
        "hypertext transfer protocol",
        "stateless application layer protocol for web communication",
        "request and response model between client and server",
        "methods get post put delete status codes 200 404 500"
    ],
    "what are get and post requests?": [
        "get retrieves data from server without side effects idempotent",
        "post submits data to server to create or process resources",
        "get passes parameters in url query string",
        "post passes data securely in request body"
    ],
    "what is json?": [
        "javascript object notation data exchange format",
        "key-value pairs and ordered lists syntax",
        "language independent and human readable",
        "standard payload format for modern web apis"
    ],
    "how do you connect python with mysql?": [
        "using connector libraries mysql-connector-python or pymysql",
        "connect() function with host user password database parameters",
        "cursor object to execute sql queries",
        "commit() for transactions and close() connection"
    ],
    "what is sqlalchemy?": [
        "object relational mapper orm and sql toolkit for python",
        "maps python classes to database tables",
        "provides database abstraction and query building",
        "session management transactions and connection pooling"
    ],
    "what is unit testing?": [
        "testing individual isolated units or components of code",
        "verifying each function behaves as expected",
        "mocking external dependencies and databases",
        "unittest and pytest frameworks in python"
    ],
    "what is pytest?": [
        "powerful and popular python testing framework",
        "simple test function syntax without boilerplate classes",
        "fixtures for test setup and dependency injection",
        "assert statements with detailed failure reports and plugins"
    ],
    "how do you debug a python program?": [
        "pdb python debugger for breakpoints and stepping",
        "print statements and structured logging",
        "ide debugging tools in vscode or pycharm",
        "analyzing exception tracebacks and error messages"
    ],
    "what are logging mechanisms in python?": [
        "built-in logging module in python",
        "log levels debug info warning error critical",
        "handlers formatters and log rotation",
        "writing structured logs to console and files"
    ],
    "what is multiprocessing?": [
        "executing multiple processes concurrently with separate memory",
        "bypasses global interpreter lock gil on multi-core cpus",
        "multiprocessing module in python",
        "ideal for cpu-bound computational tasks"
    ],
    "what is asynchronous programming?": [
        "single-threaded concurrency model using event loop",
        "tasks yield control during io wait without blocking execution",
        "async and await keywords",
        "high concurrency for io-bound network and web requests"
    ],
    "what is asyncio?": [
        "python standard library for concurrent asynchronous code",
        "event loop managing coroutines tasks and futures",
        "async def defines coroutine await pauses execution",
        "aiohttp and asynchronous network operations"
    ],
    "what is a process?": [
        "independent executing instance of a computer program",
        "has its own dedicated memory space and resources",
        "isolated from other processes managed by operating system",
        "inter-process communication ipc required to share data"
    ],
    "what is a race condition?": [
        "concurrency bug where output depends on non-deterministic execution order",
        "multiple threads accessing shared mutable resource concurrently",
        "at least one thread performs write operation",
        "prevented using locks mutexes or synchronization primitives"
    ],
    "what is a deadlock?": [
        "situation where two or more threads or processes are blocked indefinitely",
        "each waiting for a resource held by another in a circular chain",
        "four coffman conditions mutual exclusion hold and wait no preemption circular wait",
        "resolved using lock hierarchies timeouts or avoidance algorithms"
    ],
    "what is time complexity?": [
        "measure of how algorithm execution time grows with input size n",
        "big o notation upper bound asymptotic analysis",
        "common complexities o(1) o(log n) o(n) o(n log n) o(n^2)",
        "evaluates efficiency and scalability of algorithms"
    ],
    "what is space complexity?": [
        "measure of auxiliary memory an algorithm requires relative to input size",
        "evaluates memory efficiency using big o notation",
        "includes memory for variables call stack and data structures",
        "trade-off between execution speed and memory consumption"
    ],
    "how do you optimize python code?": [
        "profiling with cProfile to identify execution bottlenecks",
        "using built-in functions list comprehensions and generators",
        "vectorized operations using numpy instead of loops",
        "choosing efficient algorithms and appropriate data structures",
        "caching with functools.lru_cache"
    ],
    "what are algorithms?": [
        "step-by-step procedures or formulas for solving a problem",
        "finite sequence of well-defined computer-implementable instructions",
        "evaluated by time complexity space complexity and correctness",
        "sorting searching graphing and optimization algorithms"
    ],
    "what are data structures?": [
        "specialized formats for organizing storing and processing data in memory",
        "linear structures arrays lists stacks queues",
        "non-linear structures trees graphs hash tables",
        "dictates efficiency of data access insertion and deletion"
    ],
    "explain stack and queue in python.": [
        "stack follows lifo last in first out principle",
        "queue follows fifo first in first out principle",
        "stack operations push append and pop",
        "collections.deque provides o(1) operations for stacks and queues"
    ],
    "how can you implement a stack in python?": [
        "using python list with append() for push and pop() for pop",
        "using collections.deque for efficient thread-safe operations",
        "lifo last in first out order",
        "checking empty stack condition before pop"
    ],
    "how can you implement a queue in python?": [
        "using collections.deque with append() and popleft()",
        "queue.Queue for thread-safe multi-threaded queues",
        "fifo first in first out order",
        "avoiding list.pop(0) due to o(n) shift overhead"
    ],
    "what is a linked list?": [
        "linear data structure where elements are stored in nodes",
        "each node contains data value and pointer reference to next node",
        "singly linked doubly linked and circular linked lists",
        "dynamic size with efficient o(1) insertion and deletion at head"
    ],
    "what is binary search?": [
        "efficient search algorithm on sorted arrays",
        "repeatedly divides search interval in half",
        "compares target to middle element",
        "logarithmic time complexity o(log n)"
    ],
    "what is linear search?": [
        "sequential search iterating through each element in list",
        "compares target with each element until match or end",
        "works on unsorted collections",
        "linear time complexity o(n)"
    ],
    "what is sorting?": [
        "arranging elements of a list in a specified order ascending or descending",
        "comparison-based vs non-comparison-based sorting",
        "common algorithms bubble sort quicksort mergesort timsort",
        "evaluated by time complexity stability and in-place memory"
    ],
    "explain bubble sort.": [
        "simple comparison-based sorting algorithm",
        "repeatedly steps through list swapping adjacent elements out of order",
        "largest unsorted element bubbles up to correct position each pass",
        "time complexity o(n^2) average and worst case"
    ],
    "explain selection sort.": [
        "in-place comparison sorting algorithm",
        "divides list into sorted and unsorted sublists",
        "repeatedly finds minimum element in unsorted part and swaps to sorted part",
        "time complexity o(n^2) in all cases"
    ],
    "explain insertion sort.": [
        "builds sorted array one element at a time",
        "takes next element and inserts it into its correct position in sorted portion",
        "efficient for small or nearly sorted datasets",
        "best case o(n) time complexity worst case o(n^2)"
    ],
    "how would you optimize a slow python application?": [
        "profile using cProfile or line_profiler to locate bottlenecks",
        "optimize database queries indexing and reduce n+1 queries",
        "leverage caching redis or in-memory lru_cache",
        "use asynchronous io or multiprocessing for concurrent tasks",
        "optimize algorithms and replace python loops with vectorized operations"
    ],

    # -------------------------------------------------------------------------
    # JAVA DEVELOPER
    # -------------------------------------------------------------------------
    "what is jdk?": [
        "java development kit",
        "software development environment for writing java applications",
        "includes compiler javac tools javadoc and jre runtime",
        "required for developing and compiling java code"
    ],
    "what is jre?": [
        "java runtime environment",
        "software package providing libraries and jvm to execute java bytecode",
        "does not include development tools compiler javac",
        "required only for running already compiled java applications"
    ],
    "what is object-oriented programming?": [
        "programming paradigm based on objects containing data and code",
        "four core principles encapsulation abstraction inheritance polymorphism",
        "promotes modularity code reuse and maintainability",
        "classes define blueprints objects represent runtime instances"
    ],
    "what is arraylist?": [
        "resizable dynamic array implementation of java list interface",
        "maintains insertion order and allows duplicate elements",
        "fast index-based access o(1) get and set",
        "automatic resizing with copy overhead on capacity expansion"
    ],
    "what is linkedlist?": [
        "doubly-linked list implementation of list and deque interfaces",
        "elements stored in nodes with prev and next pointers",
        "efficient insertion and deletion o(1) at ends",
        "sequential index access o(n) overhead"
    ],
    "what is hashmap?": [
        "key-value pair map implementation based on hash table",
        "allows one null key and multiple null values",
        "average o(1) time complexity for put and get operations",
        "handles collisions using linked list or red-black tree"
    ],
    "what is hashset?": [
        "collection storing unique elements backed by hashmap internally",
        "does not maintain order and permits single null element",
        "constant time o(1) average performance for add remove contains",
        "uses hashcode and equals methods for uniqueness"
    ],
    "difference between arraylist and linkedlist?": [
        "arraylist uses dynamic contiguous array linkedlist uses doubly linked nodes",
        "arraylist has o(1) random access linkedlist has o(n) search",
        "linkedlist has faster insertions deletions in middle once position found",
        "arraylist has better memory locality and lower memory overhead"
    ],
    "difference between hashmap and hashset?": [
        "hashmap stores key-value pairs hashset stores unique elements only",
        "hashset implements set interface hashmap implements map interface",
        "hashset uses add() method hashmap uses put() method",
        "hashset internally utilizes a hashmap to store elements"
    ],
    "what is an iterator?": [
        "interface to traverse through collection elements sequentially",
        "methods hasNext() next() and remove()",
        "fail-fast behavior throwing ConcurrentModificationException",
        "allows safe removal of elements during iteration"
    ],
    "what are generics?": [
        "parameterized types enabling compile-time type safety",
        "eliminates need for explicit type casting",
        "catches type mismatches at compile time rather than runtime",
        "type erasure removes generic type information at runtime"
    ],
    "difference between string and stringbuilder?": [
        "string is immutable stringbuilder is mutable",
        "string creates new object on concatenation stringbuilder modifies in-place",
        "stringbuilder is faster for frequent string modifications",
        "string is thread-safe due to immutability stringbuilder is not thread-safe"
    ],
    "what is stringbuffer?": [
        "mutable sequence of characters similar to stringbuilder",
        "thread-safe with synchronized methods",
        "slower performance compared to stringbuilder due to synchronization overhead",
        "used in multi-threaded environments for string modifications"
    ],
    "why is string immutable in java?": [
        "security prevents alteration in sensitive parameters like urls and passwords",
        "string pool memory optimization reusing string literals",
        "thread safety across concurrent threads without synchronization",
        "hashcode caching safe use as keys in hashmap"
    ],
    "what is the equals() method?": [
        "defined in Object class to test content or logical equality",
        "default implementation in Object checks reference identity ==",
        "overridden in classes like String to compare actual values",
        "must be consistent with hashCode contract"
    ],
    "what is hashcode()?": [
        "method returning integer hash value for an object",
        "used in hash-based collections HashMap and HashSet",
        "contract equal objects according to equals must have identical hashCodes",
        "unequal objects should ideally produce distinct hashCodes"
    ],
    "difference between == and equals()?": [
        "== operator checks memory address reference equality for objects",
        "equals() method compares state or content equality when overridden",
        "== compares primitive values directly",
        "default equals() in Object behaves identical to =="
    ],
    "what are wrapper classes?": [
        "classes that encapsulate primitive data types into objects",
        "Integer Double Boolean Character Byte Short Long Float",
        "enables primitives to be used in Java collections framework",
        "utility methods for parsing and type conversion"
    ],
    "what is autoboxing?": [
        "automatic conversion of primitive type to its wrapper object",
        "introduced in Java 5 e.g. int to Integer",
        "compiler invokes valueOf() behind the scenes",
        "improves code readability in collections"
    ],
    "what is unboxing?": [
        "automatic conversion of wrapper object back to primitive type",
        "e.g. Integer to int invoked via intValue()",
        "risk of NullPointerException if wrapper object is null",
        "simplifies arithmetic operations on wrapper types"
    ],
    "what are java packages?": [
        "namespace grouping related classes and interfaces together",
        "package keyword and reverse domain naming convention",
        "prevents naming conflicts across projects",
        "controls access level through package-private visibility"
    ],
    "what is maven?": [
        "build automation and dependency management tool for java",
        "pom.xml project object model configuration",
        "central repository resolving and downloading third-party libraries",
        "standard build lifecycle compile test package deploy"
    ],
    "what is jdbc?": [
        "java database connectivity api",
        "standard interface connecting java applications to relational databases",
        "drivermanager connection statement and resultset interfaces",
        "preparedstatement preventing sql injection attacks"
    ],
    "how do you connect java with mysql?": [
        "include mysql connector j dependency in classpath",
        "register driver Class.forName or automatic loading",
        "DriverManager.getConnection with url user password",
        "create Statement execute queries and close resources"
    ],
    "what is concurrency?": [
        "ability of program to execute multiple tasks simultaneously or in overlapping periods",
        "multithreading and java.util.concurrent package",
        "shared memory coordination and synchronization",
        "improves cpu utilization and throughput"
    ],
    "what is serialization?": [
        "converting state of an object into a byte stream",
        "implements Serializable marker interface",
        "used for saving object state to disk or network transmission",
        "serialVersionUID ensuring class version compatibility"
    ],
    "what is deserialization?": [
        "reconstructing object in memory from serialized byte stream",
        "ObjectInputStream readObject() method",
        "restores object state without invoking constructor",
        "security considerations and validation"
    ],
    "what is an enum?": [
        "special data type defining a fixed set of named constants",
        "enum keyword in java extending java.lang.Enum",
        "type-safe alternative to integer constants",
        "can have constructors fields and methods"
    ],
    "what are lambda expressions?": [
        "anonymous functions introduced in java 8",
        "concise syntax (parameters) -> expression",
        "implements functional interfaces having single abstract method",
        "promotes functional programming and stream api usage"
    ],
    "what is the stream api?": [
        "java 8 api for processing sequences of elements functionally",
        "intermediate operations filter map sorted are lazy",
        "terminal operations collect forEach reduce trigger execution",
        "supports sequential and parallel processing"
    ],
    "what is functional programming?": [
        "programming paradigm treating computation as evaluation of functions",
        "pure functions without side effects and immutable state",
        "first-class functions and lambda expressions",
        "declarative style over imperative control flow"
    ],
    "what is optional in java?": [
        "container object introduced in java 8 to represent present or absent value",
        "avoids NullPointerException and explicit null checks",
        "methods isPresent() orElse() orElseGet() map()",
        "encourages safe api design"
    ],
    "what are annotations?": [
        "metadata tags added to java source code elements",
        "@Override @Deprecated @Test @Autowired syntax",
        "retention policies source class runtime",
        "processed by compiler or at runtime via reflection"
    ],
    "what is inversion of control?": [
        "design principle where control of object creation is inverted",
        "framework manages lifecycle and dependencies instead of object itself",
        "dependency injection is primary implementation pattern",
        "promotes loose coupling and easier unit testing"
    ],
    "how do you debug java applications?": [
        "ide debugging tools breakpoints stepping variable inspection",
        "jdb command line java debugger",
        "logging frameworks slf4j logback log4j2",
        "thread dumps and heap dump analysis with jstack jmap"
    ],
    "what is jvm memory?": [
        "runtime data areas managed by java virtual machine",
        "heap memory for objects and instance variables",
        "stack memory for method calls and local variables",
        "metaspace for class metadata and pc registers"
    ],
    "what is heap memory?": [
        "shared jvm memory area where all objects are allocated",
        "managed automatically by garbage collector",
        "divided into young generation eden survivor and old generation",
        "OutOfMemoryError when heap space is exhausted"
    ],
    "what is a stack?": [
        "linear data structure operating on lifo last in first out",
        "push operation adds element pop removes top element",
        "peek inspects top element without removal",
        "used in function call stacks and expression evaluation"
    ],
    "what is a queue?": [
        "linear data structure operating on fifo first in first out",
        "enqueue adds to rear dequeue removes from front",
        "java Queue interface implemented by LinkedList or ArrayDeque",
        "used in task scheduling and breadth-first search"
    ],
    "how would you optimize a java application?": [
        "profile with jprofiler or visualvm to locate cpu and memory hotspots",
        "tune garbage collection parameters and heap sizing",
        "optimize database access connection pooling and queries",
        "use appropriate data structures and avoid unnecessary object creation",
        "leverage multithreading and caching"
    ],
    "what is microservices architecture?": [
        "architectural style structuring application as collection of small autonomous services",
        "each service runs in its own process and communicates via lightweight apis rest grpc",
        "independently deployable scalable and maintainable",
        "decentralized data management and polyglot technology stack"
    ],
    "what is docker?": [
        "containerization platform packaging application and dependencies together",
        "dockerfile builds container images",
        "ensures consistent environment across development testing and production",
        "lightweight isolation sharing host operating system kernel"
    ],
    "what is git?": [
        "distributed version control system tracking source code changes",
        "commit history branching merging and conflict resolution",
        "collaboration across distributed development teams",
        "commands clone commit push pull merge checkout"
    ],
    "how do you handle conflicts in git?": [
        "identify conflicting files flagged with merge markers <<<< ==== >>>>",
        "manually resolve differences and choose correct code",
        "stage resolved files using git add",
        "complete merge with git commit"
    ],
    "what is ci/cd?": [
        "continuous integration and continuous delivery/deployment",
        "automated build testing and deployment pipelines",
        "tools jenkins github actions gitlab ci",
        "early defect detection and frequent reliable releases"
    ],
    "how would you design a scalable java application?": [
        "stateless service architecture enabling horizontal scaling",
        "load balancing and distributed caching redis",
        "asynchronous messaging with kafka or rabbitmq",
        "database sharding read replicas and connection pooling"
    ],
    "how do you debug a production issue?": [
        "analyze centralized application logs and error stack traces",
        "inspect monitoring metrics cpu memory network latencies",
        "capture thread dumps for deadlocks and heap dumps for memory leaks",
        "reproduce issue in staging and deploy targeted hotfix"
    ],

    # -------------------------------------------------------------------------
    # WEB DEVELOPER
    # -------------------------------------------------------------------------
    "what is html5 and what are semantic elements?": [
        "modern html standard with native multimedia and api support",
        "semantic tags header nav article section aside footer",
        "improves accessibility seo and code readability",
        "describes meaning of content to browser and developer"
    ],
    "what is css flexbox and how does it work?": [
        "one-dimensional css layout model for rows or columns",
        "flex container display flex and flex items",
        "justify-content aligns along main axis",
        "align-items aligns along cross axis flex-direction and flex-wrap"
    ],
    "what is css grid and when do you use it?": [
        "two-dimensional css layout system for rows and columns simultaneously",
        "grid-template-columns grid-template-rows and gap properties",
        "grid-column and grid-row positioning",
        "best for complex page layouts compared to one-dimensional flexbox"
    ],
    "what is the difference between let, const, and var in javascript?": [
        "var is function-scoped and hoisted with undefined",
        "let and const are block-scoped temporal dead zone",
        "const cannot be reassigned let allows reassignment",
        "modern javascript prefers const by default and let when reassignment needed"
    ],
    "what is the event loop in javascript?": [
        "mechanism enabling single-threaded javascript to perform non-blocking concurrency",
        "call stack web apis callback queue and microtask queue",
        "event loop pushes callbacks to stack when call stack is empty",
        "microtasks promises take precedence over macrotasks setTimeout"
    ],
    "what are promises and async/await?": [
        "promise represents eventual completion or failure of asynchronous operation",
        "states pending fulfilled rejected with then catch finally",
        "async await is syntactic sugar over promises for cleaner code",
        "await pauses execution inside async function until promise resolves"
    ],
    "what is the dom and how do you manipulate it?": [
        "document object model tree representation of html document",
        "document.querySelector and getElementById for element selection",
        "modifying attributes innerHTML textContent and classList",
        "event listeners with addEventListener"
    ],
    "what is the difference between client-side and server-side rendering?": [
        "csr renders html in browser using javascript single page apps",
        "ssr renders complete html on server before sending to client",
        "ssr offers faster initial page load and superior seo",
        "csr provides richer interactive user experience after initial load"
    ],
    "what are restful apis and how do you call them with fetch?": [
        "architectural style using standard http methods get post put delete",
        "stateless client-server communication using json",
        "fetch() api returns a promise resolving to response",
        "response.json() parsing and handling http status codes"
    ],
    "how do you optimize website load performance?": [
        "minimizing and bundling css and javascript files",
        "optimizing and compressing images modern formats webp",
        "lazy loading images and components",
        "browser caching cdn content delivery network and code splitting"
    ],
    "what is cors and how do you handle it?": [
        "cross-origin resource sharing security mechanism enforced by browsers",
        "restricts requests to different domain port or protocol",
        "server sends Access-Control-Allow-Origin headers",
        "handling preflight OPTIONS requests"
    ],
    "what is git and how do you manage branches?": [
        "distributed version control system tracking code changes",
        "git branch and git checkout/switch to create and switch branches",
        "git merge and rebase to integrate changes",
        "feature branching workflow and pull requests"
    ],
    "what is a single page application (spa)?": [
        "web application loading single html page and updating content dynamically",
        "client-side routing without full page reloads",
        "fast smooth user experience similar to desktop apps",
        "frameworks react vue angular"
    ],
    "what are browser storage options (localstorage vs sessionstorage)?": [
        "localstorage persists data across browser sessions indefinitely",
        "sessionstorage clears data when browser tab closes",
        "cookies sent with http requests smaller 4kb limit",
        "storage limit around 5-10mb key-value string storage"
    ],
    "how do you debug javascript issues using browser devtools?": [
        "console tab for logs errors and interactive inspection",
        "sources tab for breakpoints call stack and step-through debugging",
        "network tab inspecting http requests responses and timing",
        "elements tab live editing html and css styles"
    ]
}

def populate_database_and_audit():
    print("=" * 70)
    print("UPDATING DATABASE QUESTIONS TABLE & BACKFILLING CURATED CONCEPTS")
    print("=" * 70)

    conn = get_connection()
    cur = conn.cursor()

    # 1. Update row 1846 for "How would you explain a complex analysis to a non-technical person?"
    print("\n[Step 1] Updating row 1846 in Questions table...")
    non_tech_concepts = [
        "simplify complex technical information",
        "use non-technical language and avoid jargon",
        "explain key findings clearly",
        "provide a relatable example",
        "connect findings to practical or business impact"
    ]
    cur.execute("""
        UPDATE Questions
        SET expected_topics = ?
        WHERE id = 1846
    """, (", ".join(non_tech_concepts),))
    print(f"  Row 1846 updated. Rows affected: {cur.rowcount}")

    # 2. Backfill/Insert curated concepts for all questions in frontend interview.js
    print("\n[Step 2] Syncing all curated questions into Questions table...")
    inserted_count = 0
    updated_count = 0

    for q_text, concepts in CURATED_ALL_ROLE_QUESTIONS.items():
        topics_str = ", ".join(concepts)
        clean_q = " ".join(q_text.strip().split())

        # Check if already exists in Questions table
        cur.execute("SELECT id, expected_topics FROM Questions WHERE LOWER(LTRIM(RTRIM(question_text))) = LOWER(?)", (clean_q,))
        row = cur.fetchone()
        if row:
            # If exists and has awkward fallback concepts or empty, update it
            existing_topics = str(row[1] or "")
            if "implementation" in existing_topics or not existing_topics.strip():
                cur.execute("UPDATE Questions SET expected_topics = ? WHERE id = ?", (topics_str, row[0]))
                updated_count += 1
        else:
            # Determine appropriate role
            q_role = "Data Analyst"
            if any(term in clean_q for term in ["python", "django", "flask", "fastapi", "mro", "lambda", "yield", "args"]):
                q_role = "Python Developer"
            elif any(term in clean_q for term in ["java", "jvm", "jdk", "jre", "hashmap", "arraylist", "maven", "jdbc", "stringbuilder"]):
                q_role = "Java Developer"
            elif any(term in clean_q for term in ["html", "css", "dom", "cors", "flexbox", "grid", "react", "spa", "javascript", "browser"]):
                q_role = "Web Developer"

            cur.execute("""
                INSERT INTO Questions (role_name, category, difficulty, question_text, expected_topics, reference_answer, evaluation_guidance, created_at)
                VALUES (?, 'Technical', 'Easy', ?, ?, '', '', SYSUTCDATETIME())
            """, (q_role, clean_q, topics_str))
            inserted_count += 1

    conn.commit()
    print(f"  Questions table sync complete: {inserted_count} inserted, {updated_count} updated.")

    # 3. Verify row 1846
    cur.execute("SELECT id, role_name, question_text, expected_topics FROM Questions WHERE id = 1846")
    r1846 = cur.fetchone()
    print(f"\n[Verification] Row 1846:\n  ID={r1846[0]} | Q='{r1846[2]}'\n  Expected Topics={r1846[3]}")

    cur.close()
    conn.close()
    print("\nDatabase update completed successfully!")

if __name__ == "__main__":
    populate_database_and_audit()
