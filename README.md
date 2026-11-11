# Agentic Research Assistant

An AI-powered academic research assistant built with **Google Agent Development Kit (ADK)** and **Cerebras LLM**. It automates literature discovery, abstract extraction, DOI verification, research comparison, identification of research gaps, and bibliography generation through browser-based research.

## Features

- **Academic Literature Search:** Searches Google Scholar using Playwright browser automation.
- **Abstract Extraction:** Retrieves abstracts and publication metadata directly from publisher websites.
- **DOI Verification:** Checks DOI resolution and compares publication titles.
- **Research Analysis:** Extracts research objectives, datasets, model architectures, methodologies, and reported performance.
- **Research Gap Identification:** Identifies potential gaps based on the retrieved literature.
- **Bibliography Generation:** Generates APA-style reference drafts.
- **Multi-Agent Ready:** Supports integration with multiple Google ADK agents.
- **Request Management:** Shared concurrency control and retry handling for Cerebras API rate limits.

## Technology Stack

| Component | Technology |
|---|---|
| Agent Framework | Google ADK 2.11.0 |
| LLM Provider | Cerebras Cloud |
| Language | Python |
| Browser Automation | Playwright |
| Research Discovery | Google Scholar |
| DOI Verification | DOI Resolver |
| Bibliography | Python |
| Interface | Google ADK Web UI |

## Architecture

```text
                 User Query
                     |
                     v
          Google ADK Research Agent
                     |
                     v
          Cerebras LLM (GPT-OSS 120B)
                     |
                     v
          Research Workflow / Tools
                     |
       +-------------+-------------+
       |             |             |
       v             v             v
 Google Scholar  Abstract       DOI Verification
 Search          Extraction     (doi.org)
       |             |             |
       +-------------+-------------+
                     |
                     v
             Research Analysis
                     |
                     v
             Research Gap Analysis
                     |
                     v
           APA Bibliography Generator
                     |
                     v
              Final Research Report
```

## Project Structure

```text
R/
│
├── agent.py          # Main agent, Cerebras adapter and research tools
├── __init__.py       # ADK package initialization
├── .env              # API credentials
└── .adk/             # ADK local configuration
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows**
```bash
venv\Scripts\activate
```

**Linux/macOS**
```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install --upgrade google-adk cerebras_cloud_sdk python-dotenv playwright
```

Install the Playwright Chromium browser:

```bash
python -m playwright install chromium
```

## Configuration

Create a `.env` file in the project directory:

```env
CEREBRAS_API_KEY=your_cerebras_api_key
```

Obtain your API key from:

https://cloud.cerebras.ai/

**Security:** Never commit your `.env` file or expose your API key publicly.

Add the following to `.gitignore`:

```gitignore
.env
venv/
__pycache__/
*.pyc
.adk/
```

## Running the Application

Run the following command from the parent directory containing the `R` package:

```bash
adk web
```

Open the local ADK Web interface and select the `R` agent.

## Research Workflow

The assistant uses four primary tools:

| Tool | Function |
|---|---|
| `search_academic` | Searches Google Scholar for relevant publications |
| `retrieve_abstract` | Extracts abstracts and DOI metadata from publisher pages |
| `verify_source` | Checks DOI resolution and publication-title similarity |
| `generate_bibliography` | Generates APA-style bibliography entries |

### Example Research Query

```text
Conduct a literature review on Deep Learning Techniques
for Brain Tumor Classification Using MRI Images.

Find five research papers published between 2020 and 2025.

1. Search Google Scholar.
2. Retrieve abstracts from publisher websites.
3. Extract datasets, model architectures and reported accuracy.
4. Verify available DOIs.
5. Compare research methodologies.
6. Identify at least three research gaps.
7. Generate an APA-style bibliography.

Do not fabricate missing information.
```

## Rate Limit Management

The Cerebras integration includes:

- Shared asynchronous request management.
- Configurable concurrent request limits.
- Exponential backoff for HTTP 429 responses.
- Retry handling for temporary rate-limit errors.

The default configuration allows two concurrent requests. Actual throughput depends on the Cerebras account's model-specific limits.

## Limitations

- Google Scholar may restrict automated browser access through CAPTCHA or traffic controls.
- Some publishers restrict access to abstracts and publication metadata.
- DOI resolution confirms that a DOI resolves; it does not establish the scientific validity or peer-review status of a paper.
- APA references may require manual metadata verification.
- API availability and rate limits depend on the Cerebras account and selected model.

The assistant is designed to report unavailable information rather than generate fabricated research findings.

## Future Enhancements

- Dedicated multi-agent research architecture.
- Research paper PDF retrieval and parsing.
- Citation network analysis.
- Research methodology comparison dashboards.
- Export research reports to PDF and DOCX.
- Interactive Streamlit research interface.
- Improved bibliography validation.

## Contributing

Contributions, bug reports, and feature suggestions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Submit a pull request.

## License

This project is available under the MIT License. Add a `LICENSE` file to the repository if you intend to distribute it under that license.

---

**Built with Google ADK, Cerebras and Playwright.**
