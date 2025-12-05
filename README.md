# AI Research Agent

A Flask-based web application that automatically generates structured, citation-backed research reports using Large Language Models (LLMs) via the OpenRouter API.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Detailed Functionality](#detailed-functionality)
- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Usage](#usage)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [License](#license)

## Features

- 🤖 **Automated Research**: Generates comprehensive research reports from a simple topic input
- 📚 **Structured Reports**: Creates well-organized sections with clear headings and goals
- 🔗 **Inline Citations**: Clickable superscript citations that link directly to references
- 📖 **Source Management**: Automatically deduplicates and normalizes citations across sections
- 🎨 **Clean HTML Output**: Professional, readable reports with responsive design
- 📝 **Report History**: View and access all previously generated reports
- ⚡ **Fast Generation**: Typically completes reports in 30-90 seconds

## Quick Start

### Prerequisites

- Python 3.9 or higher
- OpenRouter API key ([Get one here](https://openrouter.ai/keys))

### Installation

1. **Clone or download the repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   
   Create a `.env` file in the project root:
   ```bash
   # .env
   OPENROUTER_API_KEY=your-api-key-here
   
   # Optional: Override the default model
   # OPENROUTER_MODEL=perplexity/sonar
   ```

4. **Run the application**:
   ```bash
   # Development mode
   flask run --host=0.0.0.0 --port=5001
   ```

5. **Open in browser**:
   Navigate to `http://localhost:5001`

### Production Deployment

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:app
```

## Detailed Functionality

### Report Generation Process

The AI Research Agent follows a sophisticated multi-stage pipeline to transform a simple topic into a comprehensive research report:

#### Stage 1: Topic Refinement

**Module**: `query_refiner.py`

The system takes the user's raw topic input and refines it through an LLM call:

1. **Input Processing**: 
   - Strips whitespace and validates non-empty input
   - Passes topic to LLM with refinement instructions

2. **LLM Refinement**:
   - Generates a cleaned, academic-style topic title
   - Creates 10 distinct research queries covering:
     - Historical context
     - Technical foundations
     - Economic implications
     - Social impacts
     - Policy considerations
     - Ethical dimensions
     - Future outlook

3. **Output**:
   ```json
   {
     "topic": "Refined, academic topic title",
     "queries": ["query1", "query2", ..., "query10"]
   }
   ```

**Error Handling**: If LLM call fails, falls back to using original topic with a single query.

#### Stage 2: Outline Building

**Module**: `outline_builder.py`

Creates a structured section plan for the report:

1. **Section Generation**:
   - LLM generates 5-7 sections based on refined topic and queries
   - Each section includes:
     - **Title**: Concise, informative heading
     - **Goal**: Description of what belongs in that section
     - **Priority**: Ordering (1-N, where 1 is first)

2. **Section Types** (typically):
   - Background and Historical Context
   - Mechanisms / Technical Foundations
   - Evidence, Applications, or Case Studies
   - Risks, Limitations, and Open Questions
   - Future Directions and Conclusion

3. **Validation**:
   - Ensures minimum 3 sections (adds fallback if needed)
   - Limits to maximum 7 sections
   - Sorts by priority
   - Normalizes priority numbers to 1..N

**Error Handling**: Falls back to default 3-section outline if LLM fails.

#### Stage 3: Section Research

**Module**: `section_researcher.py`

Researches and writes each section independently:

1. **For Each Section**:
   - LLM receives:
     - Overall topic context
     - Relevant research queries
     - Section title and goal
   
2. **LLM Output**:
   - Detailed section body text
   - Inline citations in `[1]`, `[2]` format
   - Source list with metadata

3. **Source Structure**:
   ```json
   {
     "id": 1,
     "title": "Source Title",
     "url": "https://example.com",
     "source_type": "study / article / report",
     "why_relevant": "Explanation of relevance"
   }
   ```

4. **Quality Controls**:
   - Minimum 3 sources per section (where possible)
   - Academic writing style
   - Citation-backed claims
   - Filters invalid sources (missing titles, etc.)

**Error Handling**: Returns fallback text if LLM fails, with empty source list.

#### Stage 4: Source Deduplication

**Module**: `pipeline.py` (function: `_source_key`)

Normalizes sources across all sections:

1. **Deduplication Logic**:
   - Creates unique key from (title, url) - case-insensitive
   - Assigns global IDs sequentially (1, 2, 3, ...)
   - Maps local section IDs to global IDs

2. **Process**:
   - Iterates through all sections
   - For each source, checks if already seen (by key)
   - If new, assigns next global ID
   - If duplicate, reuses existing global ID

3. **Result**: 
   - Single list of unique sources with global IDs
   - Mapping from local IDs to global IDs

#### Stage 5: Citation Normalization

**Module**: `pipeline.py`

Updates citation numbers in section bodies:

1. **Pattern Matching**:
   - Uses regex to find all `[1]`, `[2]`, etc. in text
   - For each citation:
     - Finds corresponding source in section's source list
     - Looks up global ID for that source
     - Replaces local ID with global ID

2. **Example**:
   - Section 1 has source with local ID 1 → becomes global ID 1
   - Section 2 has same source with local ID 1 → becomes global ID 1
   - All `[1]` citations now reference the same global source

3. **Edge Cases**:
   - Invalid citation numbers are left unchanged
   - Citations without matching sources are left unchanged
   - Sources without matching citations are still included

#### Stage 6: HTML Generation

**Module**: `html_writer.py`

Renders the final report as HTML:

1. **Section Rendering** (`_render_sections`):
   - Escapes HTML to prevent XSS
   - Splits body text into paragraphs (by `\n\n`)
   - Converts citation markers `[1]` to clickable superscript links:
     ```html
     <a href="#ref-1" class="citation-link" data-ref="1">[1]</a>
     ```
   - Wraps in semantic HTML (`<section>`, `<h2>`, `<p>`)

2. **Reference Rendering** (`_render_references`):
   - Creates ordered list of references
   - Each reference has:
     - ID anchor: `id="ref-1"` for linking
     - Formatted title, source type, relevance
     - Clickable URL (if provided)
   - HTML-escaped for security

3. **CSS Styling**:
   - Citation links styled as superscripts:
     - `vertical-align: super`
     - `font-size: 0.75em`
     - `top: -0.4em` for positioning
   - Hover effects for better UX
   - Smooth scrolling for citation clicks
   - Responsive design

4. **JavaScript**:
   - Highlights target reference when citation is clicked
   - 2-second highlight animation
   - Smooth scroll behavior

#### Stage 7: Metadata Storage

**Module**: `pipeline.py`

Saves report metadata as JSON:

```json
{
  "id": "run_id_hex",
  "user_topic": "Original user input",
  "refined_topic": "Cleaned topic",
  "report_type": "research",
  "queries": ["query1", "query2", ...],
  "outline_sections": [
    {
      "title": "Section Title",
      "goal": "Section goal",
      "priority": 1
    }
  ],
  "created_at": "2024-01-01T00:00:00Z",
  "html_filename": "run_id.html"
}
```

### Citation System Details

The citation system is a core feature that makes reports interactive and professional:

#### Citation Format

- **Input**: Text with `[1]`, `[2]` markers (from LLM)
- **Output**: Clickable superscript links inline in text

#### Technical Implementation

1. **HTML Structure**:
   ```html
   <p>Text content <a href="#ref-1" class="citation-link" data-ref="1">[1]</a> more text.</p>
   ```

2. **CSS Styling**:
   ```css
   .citation-link {
     vertical-align: super;    /* Superscript positioning */
     font-size: 0.75em;        /* Smaller font */
     top: -0.4em;              /* Raise above baseline */
     color: #0a7cff;          /* Blue color */
     cursor: pointer;          /* Clickable */
   }
   ```

3. **Reference Anchors**:
   ```html
   <li id="ref-1">
     <strong>[1] Source Title</strong>
     ...
   </li>
   ```

4. **JavaScript Interaction**:
   - Click handler on citation links
   - Scrolls to reference section
   - Highlights target reference for 2 seconds
   - Smooth scroll animation

#### Citation Features

- **Inline Placement**: Citations appear exactly where `[1]` markers were in text
- **Clickable**: All citations are clickable links
- **Visual Feedback**: Hover effects and highlight on click
- **Accessibility**: Proper anchor links for screen readers
- **Deduplication**: Same source across sections uses same citation number

### Web Interface

**Module**: `app.py`

#### Home Page (`GET /`)

- **Layout**: Two-column responsive grid
- **Left Column**: 
  - Topic input form
  - Generate button
  - Progress indicator (shows during generation)
- **Right Column**:
  - Past reports list
  - Sorted by creation date (newest first)
  - Shows refined topic, report type badge, timestamp

#### Generate Endpoint (`POST /generate`)

1. **Request**:
   ```json
   {
     "topic": "User's research topic"
   }
   ```

2. **Processing**:
   - Validates topic (non-empty)
   - Generates unique run ID (UUID hex)
   - Calls `generate_full_report()`
   - Returns report URL

3. **Response**:
   ```json
   {
     "id": "run_id",
     "report_type": "research",
     "report_url": "/report/run_id"
   }
   ```

4. **Error Handling**:
   - 400: Missing or empty topic
   - 500: Generation failure (with error message)

#### View Report (`GET /report/<run_id>`)

1. **Validation**:
   - Checks HTML and JSON files exist
   - Returns 404 if not found

2. **Response**:
   - Returns HTML file content directly
   - Browser renders with all styling and JavaScript

### LLM Client

**Module**: `llm_client.py`

Handles all communication with OpenRouter API:

#### Features

1. **API Key Management**:
   - Validates `OPENROUTER_API_KEY` environment variable
   - Raises `LLMError` if missing

2. **Request Configuration**:
   - Model: Configurable via `OPENROUTER_MODEL` (default: `perplexity/sonar`)
   - Temperature: Configurable per call
   - Max tokens: Configurable per call
   - Timeout: Default 60 seconds

3. **Retry Logic**:
   - Automatic retries on network errors (Timeout, ConnectionError)
   - Exponential backoff: 1.5s, 3s, 4.5s...
   - Configurable max retries (default: 2)
   - Raises `LLMError` after max retries

4. **Error Handling**:
   - HTTP errors: Raises `LLMError` with status code and body snippet
   - Invalid response format: Raises `LLMError` with response preview
   - Network errors: Retries, then raises `LLMError`

5. **Headers**:
   - Authorization: Bearer token
   - Content-Type: application/json
   - HTTP-Referer: Domain identifier
   - X-Title: Application name

## How It Works

### Complete Data Flow

```
┌─────────────────┐
│  User Input     │  "Long-term impacts of AI on engineering teams"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Topic Refinement│  → Refined: "Long-term Impacts of AI on Engineering Teams"
│                 │  → Queries: [10 research questions]
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Outline Builder │  → 5-7 sections with titles and goals
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ For Each Section│
│  ┌───────────┐  │
│  │ Research  │  │  → Body text with [1], [2] citations
│  │ Section   │  │  → Sources with metadata
│  └───────────┘  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Source          │  → Deduplicate sources
│ Deduplication   │  → Assign global IDs (1, 2, 3...)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Citation        │  → Replace [1] with [global_id]
│ Normalization   │  → Update all citation numbers
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ HTML Generation │  → Convert [1] to clickable superscript
│                 │  → Render sections and references
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Save Files      │  → HTML file + JSON metadata
└─────────────────┘
```

### Detailed Component Interactions

#### 1. Query Refiner → Outline Builder

- **Input**: Refined topic + 10 queries
- **Output**: Section outline
- **LLM Call**: Uses queries to understand topic scope

#### 2. Outline Builder → Section Researcher

- **Input**: Section title + goal
- **Output**: Researched section with citations
- **LLM Call**: Deep research on specific section

#### 3. Section Researcher → Pipeline

- **Input**: Multiple sections with local citations
- **Processing**: Deduplication and normalization
- **Output**: Global citation system

#### 4. Pipeline → HTML Writer

- **Input**: Sections + global sources
- **Processing**: Citation link conversion
- **Output**: HTML with clickable citations

### Citation Normalization Example

**Before Normalization**:

Section 1:
- Body: "Text [1] more text."
- Sources: [{"id": 1, "title": "Source A", ...}]

Section 2:
- Body: "Other text [1] and [2]."
- Sources: [
    {"id": 1, "title": "Source A", ...},  // Same as Section 1
    {"id": 2, "title": "Source B", ...}
  ]

**After Normalization**:

Global Sources:
- [{"global_id": 1, "title": "Source A", ...}]
- [{"global_id": 2, "title": "Source B", ...}]

Section 1:
- Body: "Text [1] more text."  // [1] → global ID 1

Section 2:
- Body: "Other text [1] and [2]."  // [1] → global ID 1, [2] → global ID 2

**Result**: Both sections' `[1]` citations now reference the same source.

## Architecture

### Core Components

#### 1. Web Interface (`app.py`)

**Responsibilities**:
- HTTP request handling
- User interface rendering
- Report history management
- Error handling and validation

**Key Functions**:
- `index()`: Renders home page with form and history
- `generate()`: Handles report generation requests
- `view_report()`: Serves generated HTML reports
- `load_history_items()`: Loads and sorts report metadata

**Dependencies**: Flask, pipeline module

#### 2. Pipeline Orchestration (`pipeline.py`)

**Responsibilities**:
- Coordinates entire report generation process
- Source deduplication
- Citation normalization
- File I/O for reports

**Key Functions**:
- `generate_full_report()`: Main entry point
- `_generate_research_report()`: Research report pipeline
- `_source_key()`: Creates unique source identifier

**Dependencies**: All research modules, html_writer

#### 3. LLM Client (`llm_client.py`)

**Responsibilities**:
- OpenRouter API communication
- Request/response handling
- Error handling and retries
- API key management

**Key Functions**:
- `call_llm()`: Makes API calls with retry logic
- `_check_api_key()`: Validates API key presence

**Dependencies**: requests library

#### 4. Query Refiner (`query_refiner.py`)

**Responsibilities**:
- Topic normalization
- Research query generation
- JSON parsing with fallbacks

**Key Functions**:
- `refine_topic_to_queries()`: Main refinement function
- `_robust_json_parse()`: Handles malformed JSON

**Dependencies**: llm_client

#### 5. Outline Builder (`outline_builder.py`)

**Responsibilities**:
- Section structure generation
- Priority assignment and sorting
- Fallback outline creation

**Key Functions**:
- `build_outline()`: Creates section plan
- `_robust_json_parse()`: JSON parsing

**Dependencies**: llm_client

#### 6. Section Researcher (`section_researcher.py`)

**Responsibilities**:
- Individual section research
- Citation generation
- Source extraction

**Key Functions**:
- `research_section()`: Researches one section
- `_robust_json_parse()`: JSON parsing

**Dependencies**: llm_client

#### 7. HTML Writer (`html_writer.py`)

**Responsibilities**:
- HTML report rendering
- Citation link conversion
- CSS styling
- JavaScript interactivity

**Key Functions**:
- `save_html()`: Main HTML generation
- `_render_sections()`: Converts sections to HTML
- `_render_references()`: Creates reference list

**Dependencies**: Standard library (html, typing)

#### 8. Storage (`storage.py`)

**Responsibilities**:
- Session-based file storage
- Metadata management
- Directory creation

**Key Functions**:
- `save_html()`: Saves HTML by session
- `load_html()`: Loads HTML by session
- `save_meta()`: Saves metadata
- `load_meta()`: Loads metadata

**Note**: Currently unused by main pipeline (uses `history/` directly), but available for alternative storage patterns.

### Module Dependencies

```
app.py
  └── pipeline.py
        ├── llm_client.py
        ├── query_refiner.py ──┐
        ├── outline_builder.py ─┤── llm_client.py
        ├── section_researcher.py┘
        └── html_writer.py
```

### Data Structures

#### Source Dictionary
```python
{
    "id": int,                    # Local ID within section
    "global_id": int,             # Global ID after deduplication
    "title": str,                 # Source title
    "url": str,                   # Source URL
    "source_type": str,           # Type (study, article, etc.)
    "why_relevant": str           # Relevance explanation
}
```

#### Section Dictionary
```python
{
    "title": str,                 # Section heading
    "goal": str,                  # Section purpose
    "priority": int,              # Order (1-N)
    "body": str                   # Section content with citations
}
```

#### Report Metadata
```python
{
    "id": str,                    # Run ID (UUID hex)
    "user_topic": str,           # Original input
    "refined_topic": str,        # Cleaned topic
    "report_type": str,          # Always "research"
    "queries": List[str],        # Research queries
    "outline_sections": List[Dict],  # Section outlines
    "created_at": str,           # ISO timestamp
    "html_filename": str        # HTML file name
}
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes | - | Your OpenRouter API key from https://openrouter.ai/keys |
| `OPENROUTER_MODEL` | No | `perplexity/sonar` | LLM model identifier (e.g., `openai/gpt-4`, `anthropic/claude-3`) |

### File Storage

- **Reports**: Stored in `history/` directory
  - Format: `{run_id}.html` and `{run_id}.json`
  - Persists across application restarts
  - No automatic cleanup (manual deletion required)

- **Sessions**: Alternative storage in `storage/sessions/`
  - Currently unused by main pipeline
  - Available for session-based workflows

### LLM Configuration

The system uses OpenRouter API which provides access to multiple LLM providers:

- **Default Model**: `perplexity/sonar` (research-optimized)
- **Alternative Models**: Can be changed via `OPENROUTER_MODEL`
- **Temperature**: Varies by module (0.2-0.7)
- **Max Tokens**: Varies by module (800-2400)

## Usage

### Web Interface

1. **Navigate to home page**: `http://localhost:5001`
2. **Enter topic**: Type your research topic in the textarea
3. **Generate**: Click "Generate report" button
4. **Wait**: Progress indicator shows current stage (30-90 seconds)
5. **View**: Report opens automatically when ready
6. **Navigate**: Click citations to jump to references
7. **History**: Access past reports from home page

### API Usage

#### Generate Report

```bash
curl -X POST http://localhost:5001/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "Your research topic here"}'
```

**Response**:
```json
{
  "id": "a1b2c3d4e5f6...",
  "report_type": "research",
  "report_url": "/report/a1b2c3d4e5f6..."
}
```

#### View Report

```bash
curl http://localhost:5001/report/a1b2c3d4e5f6...
```

Returns HTML content of the report.

#### List History (via home page)

The home page (`GET /`) includes all past reports in the response HTML.

### Programmatic Usage

```python
from pipeline import generate_full_report
import uuid

# Generate a report
run_id = uuid.uuid4().hex
result = generate_full_report("Your topic", run_id)

# Access files
html_path = result["html_path"]
meta_path = result["meta_path"]
```

## Testing

The project includes comprehensive unit and integration tests (110+ tests):

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_html_writer.py

# Run citation-related tests
pytest -k "citation"

# Verbose output
pytest -v
```

### Test Coverage

- **Unit Tests**: Individual module functionality
- **Integration Tests**: Component interactions
- **System Tests**: End-to-end workflows
- **Citation Tests**: Citation rendering and linking

### Test Files

- `test_llm_client.py`: API client and error handling
- `test_query_refiner.py`: Topic refinement
- `test_outline_builder.py`: Outline generation
- `test_section_researcher.py`: Section research
- `test_html_writer.py`: HTML rendering and citations
- `test_pipeline.py`: Pipeline orchestration
- `test_app.py`: Web interface
- `test_storage.py`: Storage utilities
- `test_system.py`: Integration tests

## Project Structure

```
research_agent/
├── app.py                    # Flask web application
├── pipeline.py               # Main orchestration
├── llm_client.py             # OpenRouter API client
├── query_refiner.py          # Topic refinement
├── outline_builder.py        # Section outline generation
├── section_researcher.py     # Section research
├── html_writer.py            # HTML rendering with citations
├── storage.py                # Session storage utilities
├── wsgi.py                   # Gunicorn entrypoint
├── run_tests.py              # Test runner script
├── pytest.ini                # Pytest configuration
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
├── .gitignore                # Git ignore rules
├── LICENSE                   # License file
├── README.md                 # This file
├── history/                  # Generated reports
│   ├── {run_id}.html        # HTML reports
│   └── {run_id}.json        # Metadata files
├── storage/                  # Alternative session storage
│   └── sessions/            # Session directories
└── tests/                    # Test suite
    ├── __init__.py
    ├── test_app.py
    ├── test_html_writer.py
    ├── test_llm_client.py
    ├── test_outline_builder.py
    ├── test_pipeline.py
    ├── test_query_refiner.py
    ├── test_section_researcher.py
    ├── test_storage.py
    ├── test_system.py
    └── README.md
```

## Troubleshooting

### Common Issues

#### "OPENROUTER_API_KEY is not set"

**Solution**:
1. Create `.env` file in project root
2. Add: `OPENROUTER_API_KEY=your-key-here`
3. Restart the application

#### Port Already in Use

**Solution**:
- Change port: `flask run --port=5002`
- On macOS, port 5000 is often used by AirPlay Receiver
- Kill existing process: `lsof -ti:5001 | xargs kill`

#### Report Generation Fails

**Possible Causes**:
- Invalid API key
- Network connectivity issues
- OpenRouter API downtime
- Rate limiting

**Solution**:
- Verify API key at https://openrouter.ai/keys
- Check internet connection
- Review server logs for error messages
- Wait and retry if rate limited

#### Citations Not Clickable

**Solution**:
- Clear browser cache
- Generate a new report (old reports may have old format)
- Check browser console for JavaScript errors

#### Empty History

**Solution**:
- Reports are stored in `history/` directory
- Check file permissions
- Verify directory exists and is writable

### Debugging

Enable Flask debug mode:
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
flask run
```

Check logs for detailed error messages.

## Development

### Setup Development Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies (if any)
pip install -r requirements-dev.txt  # If exists

# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to functions
- Keep functions focused and small

### Adding Features

1. **New Module**:
   - Create module file
   - Add unit tests
   - Update imports

2. **New Endpoint**:
   - Add route in `app.py`
   - Add tests in `test_app.py`
   - Update documentation

3. **New LLM Call**:
   - Use `call_llm()` from `llm_client.py`
   - Handle `LLMError` exceptions
   - Add fallback behavior

### Testing New Code

```bash
# Run specific test
pytest tests/test_your_module.py

# Run with verbose output
pytest -v tests/test_your_module.py::TestClass::test_method

# Run with coverage for specific file
pytest --cov=your_module tests/test_your_module.py
```

## 👤 Author

**Sareen Gogi**

- GitHub: [@sgogi1](https://github.com/sgogi1)
- LinkedIn: [Sareen Gogi](https://www.linkedin.com/in/sareengogi)
- Email: sareengogi@gmail.com

## License

See [LICENSE](LICENSE) file for details.

---

**Note**: This tool generates research reports automatically using AI. Always verify sources and citations before using in academic or professional contexts. The LLM may generate plausible but unverified information.
