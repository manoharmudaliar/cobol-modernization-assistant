"""
ai_analyzer.py
Uses Claude API to generate plain-English explanation and Python conversion of COBOL code.
Combines rule-based parse results with AI for richer output.
"""

import json
import requests
from cobol_parser import CobolAnalysis


CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"


def _call_claude(prompt: str, max_tokens: int = 2000) -> str:
    """Call Claude API and return text response."""
    payload = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(CLAUDE_API_URL, json=payload,
                             headers={"Content-Type": "application/json"})
    if response.status_code != 200:
        return f"[AI Error {response.status_code}: {response.text}]"
    data = response.json()
    return "".join(block.get("text", "") for block in data.get("content", []))


def generate_explanation(cobol_source: str, analysis: CobolAnalysis) -> str:
    """Generate plain-English explanation of what the COBOL program does."""
    prompt = f"""You are an expert mainframe developer and software architect.
Analyze the following COBOL program and provide a clear, concise plain-English explanation.

COBOL SOURCE:
```cobol
{cobol_source[:3000]}
```

PARSED METRICS:
- Program ID: {analysis.program_id}
- Paragraphs: {[p.name for p in analysis.paragraphs]}
- Files used: {[f.logical_name for f in analysis.files]}
- Complexity: {analysis.complexity_label} (score: {analysis.complexity_score})
- Uses DB2: {analysis.metrics['db2_sql']}
- Uses CICS: {analysis.metrics['cics']}
- Uses IMS: {analysis.metrics['ims']}

Provide your response in this exact JSON format (no markdown, just JSON):
{{
  "purpose": "One sentence summary of what this program does",
  "business_function": "2-3 sentences explaining the business purpose in non-technical language",
  "how_it_works": "Step by step explanation of the program flow (3-5 steps)",
  "inputs": "What data the program reads",
  "outputs": "What data the program produces",
  "key_logic": "The most important business rules or calculations in this program",
  "modernization_notes": "Key considerations for migrating this to a modern platform"
}}"""

    result = _call_claude(prompt, max_tokens=1500)
    try:
        # Strip any markdown fences if present
        clean = result.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(clean)
    except Exception:
        return {"purpose": result, "business_function": "", "how_it_works": "",
                "inputs": "", "outputs": "", "key_logic": "", "modernization_notes": ""}


def generate_python_conversion(cobol_source: str, analysis: CobolAnalysis) -> str:
    """Convert COBOL program to equivalent modern Python code."""
    prompt = f"""You are an expert in both COBOL mainframe development and modern Python.
Convert the following COBOL program to clean, modern Python 3 code.

COBOL SOURCE:
```cobol
{cobol_source[:3000]}
```

PROGRAM DETAILS:
- Program: {analysis.program_id}
- Paragraphs: {[p.name for p in analysis.paragraphs]}
- Complexity: {analysis.complexity_label}

Requirements for the Python conversion:
1. Use Python 3 with type hints
2. Convert COBOL paragraphs to Python functions
3. Convert COBOL file handling to Python file I/O with dataclasses
4. Convert COBOL COMPUTE statements to Python arithmetic
5. Convert EVALUATE TRUE to if/elif/else
6. Add docstrings explaining each function
7. Use pandas for data processing where appropriate
8. Include a main() function
9. Add logging instead of DISPLAY statements
10. Handle errors with try/except

Return ONLY the Python code with no explanation outside the code itself.
Use comments to explain non-obvious COBOL-to-Python translations."""

    return _call_claude(prompt, max_tokens=2000)


def generate_migration_plan(analysis: CobolAnalysis) -> dict:
    """Generate a structured modernization migration plan."""
    prompt = f"""You are a mainframe modernization architect.
Based on this COBOL program analysis, create a practical migration plan.

PROGRAM: {analysis.program_id}
COMPLEXITY: {analysis.complexity_label} (score: {analysis.complexity_score})
METRICS:
- Lines of code: {analysis.metrics['total_lines']}
- Paragraphs: {analysis.metrics['paragraph_count']}
- IF statements: {analysis.metrics['if_count']}
- EVALUATE blocks: {analysis.metrics['evaluate_count']}
- External files: {analysis.metrics['file_count']}
- GO TO statements: {analysis.metrics['goto_count']}
- DB2 SQL: {analysis.metrics['db2_sql']}
- CICS: {analysis.metrics['cics']}
- IMS: {analysis.metrics['ims']}
WARNINGS: {analysis.warnings}

Return ONLY this JSON (no markdown):
{{
  "effort_estimate": "X-Y weeks",
  "risk_level": "LOW/MEDIUM/HIGH",
  "recommended_target": "Python/Java/microservice/etc",
  "approach": "strangler fig / big bang / phased",
  "phases": [
    {{"phase": 1, "name": "Phase name", "tasks": ["task1", "task2"], "duration": "X weeks"}},
    {{"phase": 2, "name": "Phase name", "tasks": ["task1", "task2"], "duration": "X weeks"}}
  ],
  "dependencies": ["dep1", "dep2"],
  "testing_strategy": "How to validate the migration"
}}"""

    result = _call_claude(prompt, max_tokens=1000)
    try:
        clean = result.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(clean)
    except Exception:
        return {"effort_estimate": "TBD", "risk_level": "MEDIUM",
                "recommended_target": "Python", "approach": "phased",
                "phases": [], "dependencies": [], "testing_strategy": result}
