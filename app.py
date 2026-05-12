"""
app.py
Flask web application for COBOL Modernization Assistant.
"""

from flask import Flask, render_template, request, jsonify
import os
import traceback
from cobol_parser import CobolParser
from ai_analyzer import generate_explanation, generate_python_conversion, generate_migration_plan

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1MB max

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), 'sample_cobol')


@app.route('/')
def index():
    samples = []
    if os.path.exists(SAMPLE_DIR):
        samples = [f for f in os.listdir(SAMPLE_DIR) if f.endswith('.cbl')]
    return render_template('index.html', samples=samples)


@app.route('/load_sample/<filename>')
def load_sample(filename):
    path = os.path.join(SAMPLE_DIR, filename)
    if not os.path.exists(path):
        return jsonify({'error': 'Sample not found'}), 404
    with open(path, 'r') as f:
        return jsonify({'source': f.read()})


@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        source = data.get('source', '').strip()
        use_ai = data.get('use_ai', True)

        if not source:
            return jsonify({'error': 'No COBOL source provided'}), 400

        # Rule-based parse
        parser = CobolParser(source)
        analysis = parser.parse()

        result = {
            'program_id':       analysis.program_id,
            'author':           analysis.author,
            'divisions':        analysis.divisions,
            'complexity_score': analysis.complexity_score,
            'complexity_label': analysis.complexity_label,
            'warnings':         analysis.warnings,
            'metrics': {
                'total_lines':      analysis.metrics['total_lines'],
                'code_lines':       analysis.metrics['code_lines'],
                'paragraph_count':  analysis.metrics['paragraph_count'],
                'file_count':       analysis.metrics['file_count'],
                'if_count':         analysis.metrics['if_count'],
                'evaluate_count':   analysis.metrics['evaluate_count'],
                'perform_count':    analysis.metrics['perform_count'],
                'compute_count':    analysis.metrics['compute_count'],
                'goto_count':       analysis.metrics['goto_count'],
                'call_count':       analysis.metrics['call_count'],
                'variable_count':   analysis.metrics['variable_count'],
                'condition_count':  analysis.metrics['condition_count'],
                'db2_sql':          analysis.metrics['db2_sql'],
                'cics':             analysis.metrics['cics'],
                'ims':              analysis.metrics['ims'],
            },
            'files': [
                {'name': f.logical_name, 'assign': f.assign_to, 'org': f.organization}
                for f in analysis.files
            ],
            'paragraphs': [
                {'name': p.name, 'calls': p.calls, 'statements': list(set(p.statements))}
                for p in analysis.paragraphs
            ],
            'working_storage_count': len(analysis.working_storage),
            'ai_explanation':   None,
            'python_code':      None,
            'migration_plan':   None,
        }

        if use_ai:
            result['ai_explanation'] = generate_explanation(source, analysis)
            result['python_code']    = generate_python_conversion(source, analysis)
            result['migration_plan'] = generate_migration_plan(analysis)

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
