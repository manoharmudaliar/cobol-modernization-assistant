"""
cobol_parser.py
Rule-based COBOL analyzer — extracts structure, variables, logic, and complexity metrics.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class CobolVariable:
    level: str
    name: str
    pic_clause: Optional[str]
    value: Optional[str]
    data_type: str  # NUMERIC, ALPHANUMERIC, CONDITION, GROUP


@dataclass
class CobolParagraph:
    name: str
    line_start: int
    line_end: int
    statements: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)


@dataclass
class CobolFile:
    logical_name: str
    assign_to: str
    organization: str
    fd_name: str
    fields: List[CobolVariable] = field(default_factory=list)


@dataclass
class CobolAnalysis:
    program_id: str
    author: str
    divisions: List[str]
    files: List[CobolFile]
    working_storage: List[CobolVariable]
    paragraphs: List[CobolParagraph]
    complexity_score: int
    complexity_label: str
    metrics: Dict
    warnings: List[str]
    raw_lines: int


class CobolParser:

    DIVISION_PATTERNS = {
        'IDENTIFICATION': r'IDENTIFICATION\s+DIVISION',
        'ENVIRONMENT':    r'ENVIRONMENT\s+DIVISION',
        'DATA':           r'DATA\s+DIVISION',
        'PROCEDURE':      r'PROCEDURE\s+DIVISION',
    }

    STATEMENT_KEYWORDS = [
        'MOVE', 'COMPUTE', 'ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE',
        'IF', 'EVALUATE', 'PERFORM', 'READ', 'WRITE', 'OPEN', 'CLOSE',
        'STRING', 'UNSTRING', 'CALL', 'DISPLAY', 'ACCEPT', 'STOP',
        'GO TO', 'SET', 'INITIALIZE', 'INSPECT',
    ]

    def __init__(self, source: str):
        self.source = source
        self.lines = source.splitlines()
        self.clean_lines = self._clean_lines()

    def _clean_lines(self) -> List[str]:
        """Strip sequence numbers and continuation markers, remove pure comments."""
        cleaned = []
        for line in self.lines:
            if len(line) > 6 and line[6] == '*':
                continue  # comment line
            if len(line) > 7:
                cleaned.append(line[7:].rstrip())
            else:
                cleaned.append(line.rstrip())
        return cleaned

    def _join_source(self) -> str:
        return ' '.join(self.clean_lines)

    def parse(self) -> CobolAnalysis:
        source_upper = self._join_source().upper()

        program_id = self._extract_value(r'PROGRAM-ID\.\s+(\S+)', source_upper) or 'UNKNOWN'
        author     = self._extract_value(r'AUTHOR\.\s+(.+?)(?:\.|$)', source_upper) or 'UNKNOWN'

        divisions   = self._find_divisions(source_upper)
        files       = self._parse_file_control(source_upper)
        ws_vars     = self._parse_working_storage(source_upper)
        paragraphs  = self._parse_paragraphs()
        metrics     = self._compute_metrics(source_upper, paragraphs)
        warnings    = self._generate_warnings(source_upper, metrics)
        score, label = self._complexity_score(metrics)

        return CobolAnalysis(
            program_id=program_id,
            author=author,
            divisions=divisions,
            files=files,
            working_storage=ws_vars,
            paragraphs=paragraphs,
            complexity_score=score,
            complexity_label=label,
            metrics=metrics,
            warnings=warnings,
            raw_lines=len(self.lines),
        )

    def _extract_value(self, pattern: str, text: str) -> Optional[str]:
        m = re.search(pattern, text)
        return m.group(1).strip() if m else None

    def _find_divisions(self, text: str) -> List[str]:
        found = []
        for name, pattern in self.DIVISION_PATTERNS.items():
            if re.search(pattern, text):
                found.append(name)
        return found

    def _parse_file_control(self, text: str) -> List[CobolFile]:
        files = []
        select_blocks = re.findall(
            r'SELECT\s+(\S+)\s+ASSIGN\s+TO\s+[\'"]?(\S+?)[\'"]?(?:\s+ORGANIZATION\s+IS\s+(\S+(?:\s+\S+)?))?(?=SELECT|\Z)',
            text
        )
        for logical, assign, org in select_blocks:
            org = org.strip() if org else 'SEQUENTIAL'
            # find FD
            fd_match = re.search(rf'FD\s+{re.escape(logical)}', text)
            fd_name = logical if fd_match else logical
            files.append(CobolFile(
                logical_name=logical,
                assign_to=assign.strip("'."),
                organization=org,
                fd_name=fd_name,
                fields=[]
            ))
        return files

    def _parse_working_storage(self, text: str) -> List[CobolVariable]:
        variables = []
        ws_match = re.search(r'WORKING-STORAGE\s+SECTION\.(.*?)(?:PROCEDURE\s+DIVISION|LINKAGE\s+SECTION|\Z)', text, re.DOTALL)
        if not ws_match:
            return variables
        ws_text = ws_match.group(1)
        entries = re.findall(
            r'(\d{2})\s+([\w-]+)\s*(?:PIC\s+([\w9XSV()\.\-]+))?\s*(?:VALUE\s+([^.]+))?',
            ws_text
        )
        for level, name, pic, value in entries:
            if name in ('FILLER',):
                continue
            dtype = self._infer_type(pic, level)
            variables.append(CobolVariable(
                level=level, name=name,
                pic_clause=pic.strip() if pic else None,
                value=value.strip() if value else None,
                data_type=dtype
            ))
        return variables

    def _infer_type(self, pic: str, level: str) -> str:
        if not pic:
            return 'GROUP' if level in ('01', '05') else 'UNKNOWN'
        p = pic.upper()
        if 'X' in p:
            return 'ALPHANUMERIC'
        if any(c in p for c in ['9', 'S', 'V']):
            return 'NUMERIC'
        return 'UNKNOWN'

    def _parse_paragraphs(self) -> List[CobolParagraph]:
        paragraphs = []
        in_procedure = False
        current_para = None
        para_name_re = re.compile(r'^([A-Z0-9][A-Z0-9\-]*)\.$', re.IGNORECASE)
        perform_re   = re.compile(r'\bPERFORM\s+([\w-]+)', re.IGNORECASE)

        for i, line in enumerate(self.clean_lines):
            stripped = line.strip().upper()
            if 'PROCEDURE DIVISION' in stripped:
                in_procedure = True
                continue
            if not in_procedure:
                continue

            # Detect paragraph name (e.g. "2000-PROCESS.")
            para_match = para_name_re.match(stripped.rstrip('.') + '.')
            if para_match and not any(k in stripped for k in self.STATEMENT_KEYWORDS):
                if current_para:
                    current_para.line_end = i - 1
                    paragraphs.append(current_para)
                current_para = CobolParagraph(
                    name=para_match.group(1).rstrip('.'),
                    line_start=i,
                    line_end=i,
                )
            elif current_para:
                # Collect statements
                for kw in self.STATEMENT_KEYWORDS:
                    if stripped.startswith(kw):
                        current_para.statements.append(kw)
                        break
                # Track PERFORM calls
                for pm in perform_re.finditer(stripped):
                    target = pm.group(1)
                    if target not in ('UNTIL', 'VARYING', 'TIMES', 'THROUGH', 'THRU'):
                        current_para.calls.append(target)

        if current_para:
            current_para.line_end = len(self.clean_lines) - 1
            paragraphs.append(current_para)

        return paragraphs

    def _compute_metrics(self, text: str, paragraphs: List[CobolParagraph]) -> Dict:
        return {
            'total_lines':         len(self.lines),
            'code_lines':          len([l for l in self.clean_lines if l.strip()]),
            'paragraph_count':     len(paragraphs),
            'file_count':          len(re.findall(r'\bSELECT\b', text)),
            'if_count':            len(re.findall(r'\bIF\b', text)),
            'evaluate_count':      len(re.findall(r'\bEVALUATE\b', text)),
            'perform_count':       len(re.findall(r'\bPERFORM\b', text)),
            'compute_count':       len(re.findall(r'\bCOMPUTE\b', text)),
            'read_count':          len(re.findall(r'\bREAD\b', text)),
            'write_count':         len(re.findall(r'\bWRITE\b', text)),
            'goto_count':          len(re.findall(r'\bGO\s+TO\b', text)),
            'call_count':          len(re.findall(r'\bCALL\b', text)),
            'variable_count':      len(re.findall(r'^\s+\d{2}\s+\w', text, re.MULTILINE)),
            'condition_count':     len(re.findall(r'\b88\b', text)),
            'db2_sql':             'EXEC SQL' in text,
            'cics':                'EXEC CICS' in text,
            'ims':                 'EXEC DLI' in text or 'PCB' in text,
        }

    def _complexity_score(self, m: Dict):
        score = 0
        score += m['if_count'] * 2
        score += m['evaluate_count'] * 3
        score += m['perform_count'] * 1
        score += m['goto_count'] * 5       # GOTOs are high risk
        score += m['file_count'] * 3
        score += m['call_count'] * 4
        score += m['db2_sql'] * 10
        score += m['cics'] * 10
        score += m['ims'] * 8
        score += m['paragraph_count'] * 1

        if score <= 20:
            label = 'LOW'
        elif score <= 50:
            label = 'MEDIUM'
        elif score <= 100:
            label = 'HIGH'
        else:
            label = 'VERY HIGH'

        return score, label

    def _generate_warnings(self, text: str, metrics: Dict) -> List[str]:
        warnings = []
        if metrics['goto_count'] > 0:
            warnings.append(f"⚠️  {metrics['goto_count']} GO TO statement(s) detected — high migration risk, requires manual restructuring.")
        if metrics['db2_sql']:
            warnings.append("⚠️  DB2 SQL detected — SQL queries must be migrated to a modern ORM or database layer.")
        if metrics['cics']:
            warnings.append("⚠️  CICS commands detected — online transaction logic requires mapping to REST API or microservice.")
        if metrics['ims']:
            warnings.append("⚠️  IMS DLI calls detected — hierarchical database access must be re-architected for relational/NoSQL.")
        if metrics['call_count'] > 0:
            warnings.append(f"ℹ️  {metrics['call_count']} external CALL(s) detected — called programs must also be analyzed and migrated.")
        if metrics['total_lines'] > 500:
            warnings.append(f"ℹ️  Large program ({metrics['total_lines']} lines) — consider breaking into smaller modules during migration.")
        return warnings
