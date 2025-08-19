"""Report generation for Packster."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from jinja2 import Template
from ..types import Report, MappingResult, Decision
from ..config import REPORT_TEMPLATE

logger = logging.getLogger(__name__)


def write_reports(
    mapping_or_report,
    output_dir: Path,
    format_type: str = "json"
) -> Dict[str, Path]:
    """Write JSON and HTML reports.
    
    Args:
        report: Report object with mapping results
        output_dir: Output directory for reports
        format_type: Format type (json, yaml, both)
        
    Returns:
        Dictionary mapping report types to file paths
    """
    # Ensure directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    written_files = {}

    # Accept either Report or list of MappingResult
    if isinstance(mapping_or_report, Report):
        report = mapping_or_report
    else:
        # Build a minimal Report by treating all as AUTO
        try:
            from ..types import MappingResult, Decision
            items = list(mapping_or_report) if mapping_or_report else []
            report = Report(
                mapped_auto=[r for r in items if isinstance(r, MappingResult) and r.decision == Decision.AUTO],
                mapped_verify=[r for r in items if isinstance(r, MappingResult) and r.decision == Decision.VERIFY],
                manual=[r for r in items if isinstance(r, MappingResult) and r.decision == Decision.MANUAL],
                skipped=[r for r in items if isinstance(r, MappingResult) and r.decision == Decision.SKIP],
            )
        except Exception:
            report = Report()
    
    # Write JSON report
    if format_type in ["json", "both"]:
        json_path = output_dir / "report.json"
        write_json_report(report, json_path)
        written_files["json"] = json_path
    
    # Write HTML report
    html_path = output_dir / "report.html"
    write_html_report(report, html_path)
    written_files["html"] = html_path
    
    logger.info(f"Wrote {len(written_files)} report files")
    return written_files


def write_json_report(report: Report, output_path: Path) -> None:
    """Write a JSON report.
    
    Args:
        report: Report object to serialize
        output_path: Path to write the JSON report
    """
    # Convert report to dictionary
    report_dict = {
        "summary": {
            "total_items": report.total_items,
            "auto_percentage": report.auto_percentage,
            "mapped_auto": len(report.mapped_auto),
            "mapped_verify": len(report.mapped_verify),
            "manual": len(report.manual),
            "skipped": len(report.skipped),
        },
        "total_packages": report.total_items,
        "auto_mapped": len(report.mapped_auto),
        "verify_required": len(report.mapped_verify),
        "manual_review": len(report.manual),
        "skipped": len(report.skipped),
        "mapped_auto": [result.model_dump() for result in report.mapped_auto],
        "mapped_verify": [result.model_dump() for result in report.mapped_verify],
        "mapping_results": [
            *[result.model_dump() for result in report.mapped_auto],
            *[result.model_dump() for result in report.mapped_verify],
            *[result.model_dump() for result in report.manual],
            *[result.model_dump() for result in report.skipped],
        ],
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Wrote JSON report to {output_path}")


def write_html_report(report: Report, output_path: Path) -> None:
    """Write an HTML report.
    
    Args:
        report: Report object to render
        output_path: Path to write the HTML report
    """
    # Load template
    if not REPORT_TEMPLATE.exists():
        # Create default template if it doesn't exist
        template_content = create_default_html_template()
    else:
        with open(REPORT_TEMPLATE, 'r', encoding='utf-8') as f:
            template_content = f.read()
    
    # Create template context (use new MappingResult shape if available)
    context = {
        # Backwards compatibility: report MappingResult may have `source/candidate`
        # but templates in tests still reference `item` and `candidates[0]`.
        # To keep template simple, we pass the Report as-is and let MappingResult
        # model expose both old and new attributes (handled in types.py).
        "report": report,
        "summary": {
            "total_items": report.total_items,
            "auto_percentage": report.auto_percentage,
            "mapped_auto": len(report.mapped_auto),
            "mapped_verify": len(report.mapped_verify),
            "manual": len(report.manual),
            "skipped": len(report.skipped),
        },
        "header_total_text": f"Total Packages: {report.total_items}",
    }
    
    # Render template
    template = Template(template_content)
    html_content = template.render(**context)
    
    # Write HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Wrote HTML report to {output_path}")


def create_default_html_template() -> str:
    """Create the default HTML report template.
    
    Returns:
        Template content as string
    """
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Packster Migration Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .summary {
            padding: 30px;
            background-color: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .summary-card h3 {
            margin: 0 0 10px 0;
            color: #495057;
        }
        .summary-card .number {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .auto { color: #28a745; }
        .verify { color: #ffc107; }
        .manual { color: #dc3545; }
        .skipped { color: #6c757d; }
        .content {
            padding: 30px;
        }
        .section {
            margin-bottom: 40px;
        }
        .section h2 {
            color: #495057;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }
        th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }
        tr:hover {
            background-color: #f8f9fa;
        }
        .confidence {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.9em;
            font-weight: 500;
        }
        .confidence.high { background-color: #d4edda; color: #155724; }
        .confidence.medium { background-color: #fff3cd; color: #856404; }
        .confidence.low { background-color: #f8d7da; color: #721c24; }
        .decision {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.9em;
            font-weight: 500;
            text-transform: uppercase;
        }
        .decision.auto { background-color: #d4edda; color: #155724; }
        .decision.verify { background-color: #fff3cd; color: #856404; }
        .decision.manual { background-color: #f8d7da; color: #721c24; }
        .decision.skip { background-color: #e2e3e5; color: #383d41; }
        .empty-message {
            text-align: center;
            color: #6c757d;
            font-style: italic;
            padding: 40px;
        }
        .footer {
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            border-top: 1px solid #e9ecef;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Packster Migration Report</h1>
            <p>Cross-OS package migration helper</p>
        </div>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>Total Packages</h3>
                    <div class="number">{{ summary.total_items }}</div>
                </div>
                <div class="summary-card">
                    <h3>Auto-Mapped</h3>
                    <div class="number auto">{{ summary.mapped_auto }}</div>
                    <div>{{ "%.1f"|format(summary.auto_percentage) }}%</div>
                </div>
                <div class="summary-card">
                    <h3>Verify Required</h3>
                    <div class="number verify">{{ summary.mapped_verify }}</div>
                </div>
                <div class="summary-card">
                    <h3>Manual Review</h3>
                    <div class="number manual">{{ summary.manual }}</div>
                </div>
                <div class="summary-card">
                    <h3>Skipped</h3>
                    <div class="number skipped">{{ summary.skipped }}</div>
                </div>
            </div>
        </div>
        
        <div class="content">
            <!-- Auto-Mapped Packages -->
            <div class="section">
                <h2>Auto-Mapped Packages</h2>
                {% if report.mapped_auto %}
                <table>
                    <thead>
                        <tr>
                            <th>Source Package</th>
                            <th>Target Package</th>
                            <th>Confidence</th>
                            <th>Reason</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for result in report.mapped_auto %}
                        <tr>
                            <td><strong>{{ result.item.source_name }}</strong><br><small>{{ result.item.source_pm.value }}</small></td>
                            <td>
                                {% if result.candidates %}
                                {% set best = result.candidates[0] %}
                                <strong>{{ best.pm }}:{{ best.name }}</strong>
                                {% endif %}
                            </td>
                            <td>
                                {% if result.candidates %}
                                {% set best = result.candidates[0] %}
                                <span class="confidence {% if best.confidence >= 0.9 %}high{% elif best.confidence >= 0.6 %}medium{% else %}low{% endif %}">
                                    {{ "%.0f"|format(best.confidence * 100) }}%
                                </span>
                                {% endif %}
                            </td>
                            <td>
                                {% if result.candidates %}
                                {% set best = result.candidates[0] %}
                                {{ best.reason or "No reason provided" }}
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <div class="empty-message">No packages were auto-mapped.</div>
                {% endif %}
            </div>
            
            <!-- Verify Required Packages -->
            <div class="section">
                <h2>Verify Required Packages</h2>
                {% if report.mapped_verify %}
                <table>
                    <thead>
                        <tr>
                            <th>Source Package</th>
                            <th>Target Package</th>
                            <th>Confidence</th>
                            <th>Reason</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for result in report.mapped_verify %}
                        <tr>
                            <td><strong>{{ result.item.source_name }}</strong><br><small>{{ result.item.source_pm.value }}</small></td>
                            <td>
                                {% if result.candidates %}
                                {% set best = result.candidates[0] %}
                                <strong>{{ best.pm }}:{{ best.name }}</strong>
                                {% endif %}
                            </td>
                            <td>
                                {% if result.candidates %}
                                {% set best = result.candidates[0] %}
                                <span class="confidence {% if best.confidence >= 0.9 %}high{% elif best.confidence >= 0.6 %}medium{% else %}low{% endif %}">
                                    {{ "%.0f"|format(best.confidence * 100) }}%
                                </span>
                                {% endif %}
                            </td>
                            <td>
                                {% if result.candidates %}
                                {% set best = result.candidates[0] %}
                                {{ best.reason or "No reason provided" }}
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <div class="empty-message">No packages require verification.</div>
                {% endif %}
            </div>
            
            <!-- Manual Review Packages -->
            <div class="section">
                <h2>Manual Review Required</h2>
                {% if report.manual %}
                <table>
                    <thead>
                        <tr>
                            <th>Source Package</th>
                            <th>Package Manager</th>
                            <th>Category</th>
                            <th>Notes</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for result in report.manual %}
                        <tr>
                            <td><strong>{{ result.item.source_name }}</strong></td>
                            <td>{{ result.item.source_pm.value }}</td>
                            <td>{{ result.item.category or "Unknown" }}</td>
                            <td>{{ result.notes or "No mapping found" }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <div class="empty-message">No packages require manual review.</div>
                {% endif %}
            </div>
            
            <!-- Skipped Packages -->
            <div class="section">
                <h2>Skipped Packages</h2>
                {% if report.skipped %}
                <table>
                    <thead>
                        <tr>
                            <th>Source Package</th>
                            <th>Package Manager</th>
                            <th>Reason</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for result in report.skipped %}
                        <tr>
                            <td><strong>{{ result.item.source_name }}</strong></td>
                            <td>{{ result.item.source_pm.value }}</td>
                            <td>{{ result.notes or "Intentionally skipped" }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <div class="empty-message">No packages were skipped.</div>
                {% endif %}
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Packster - Cross-OS package migration helper</p>
        </div>
    </div>
</body>
</html>'''


def get_report_statistics(report: Report) -> Dict[str, Any]:
    """Get detailed statistics about the report.
    
    Args:
        report: Report object to analyze
        
    Returns:
        Dictionary with detailed statistics
    """
    stats = {
        "summary": {
            "total_items": report.total_items,
            "auto_percentage": report.auto_percentage,
            "mapped_auto": len(report.mapped_auto),
            "mapped_verify": len(report.mapped_verify),
            "manual": len(report.manual),
            "skipped": len(report.skipped),
        },
        "by_package_manager": {},
        "by_confidence": {
            "high": 0,    # 0.9-1.0
            "medium": 0,  # 0.6-0.89
            "low": 0,     # 0.0-0.59
        },
        "by_category": {},
    }
    
    # Process all results
    all_results = report.mapped_auto + report.mapped_verify + report.manual + report.skipped
    
    for result in all_results:
        # Count by package manager
        pm = result.item.source_pm.value
        stats["by_package_manager"][pm] = stats["by_package_manager"].get(pm, 0) + 1
        
        # Count by category
        category = result.item.category or "unknown"
        stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
        
        # Count by confidence
        if result.candidates:
            best_confidence = max(c.confidence for c in result.candidates)
            if best_confidence >= 0.9:
                stats["by_confidence"]["high"] += 1
            elif best_confidence >= 0.6:
                stats["by_confidence"]["medium"] += 1
            else:
                stats["by_confidence"]["low"] += 1
    
    return stats


def validate_report(report: Report) -> bool:
    """Validate a report object.
    
    Args:
        report: Report object to validate
        
    Returns:
        True if report is valid, False otherwise
    """
    try:
        # Check that total items matches sum of all sections
        total_calculated = (
            len(report.mapped_auto) + 
            len(report.mapped_verify) + 
            len(report.manual) + 
            len(report.skipped)
        )
        
        if total_calculated != report.total_items:
            return False
        
        # Check that auto percentage is reasonable
        if report.auto_percentage < 0 or report.auto_percentage > 100:
            return False
        
        # Check that all mapping results have valid decisions
        all_results = report.mapped_auto + report.mapped_verify + report.manual + report.skipped
        
        for result in all_results:
            if result.decision not in [Decision.AUTO, Decision.VERIFY, Decision.MANUAL, Decision.SKIP]:
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating report: {e}")
        return False
