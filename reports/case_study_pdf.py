from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _stable_name(trade_date: str, filters: list[Any]) -> str:
    key = json.dumps(filters, sort_keys=True, default=str)
    suffix = hashlib.sha256(key.encode('utf-8')).hexdigest()[:10]
    safe_date = str(trade_date).replace(':', '-').replace('/', '-')
    return f"case_study_{safe_date}_{suffix}.pdf"


def _fallback_minimal_pdf(path: Path, lines: list[str], metadata: dict[str, Any]) -> None:
    def esc(s: str) -> str:
        return s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

    y = 780
    content_ops: list[str] = []
    for line in lines[:45]:
        content_ops.append(f"BT /F1 10 Tf 40 {y} Td ({esc(line[:120])}) Tj ET")
        y -= 14
    stream = ('\n'.join(content_ops)).encode('latin-1', errors='replace')

    chunks: list[bytes] = [b'%PDF-1.4\n']
    offsets: list[int] = []

    def add_obj(obj_no: int, body: bytes) -> None:
        offsets.append(sum(len(c) for c in chunks))
        chunks.append(f'{obj_no} 0 obj\n'.encode('ascii') + body + b'\nendobj\n')

    add_obj(1, b'<< /Type /Catalog /Pages 2 0 R >>')
    add_obj(2, b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>')
    add_obj(3, b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>')
    add_obj(4, b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>')
    add_obj(5, f'<< /Length {len(stream)} >>\nstream\n'.encode('ascii') + stream + b'\nendstream')
    title = esc(str(metadata.get('title', 'Case Study')))
    subject = esc(str(metadata.get('subject', 'SA2 CAD')))
    add_obj(6, f'<< /Title ({title}) /Subject ({subject}) >>'.encode('latin-1', errors='replace'))

    startxref = sum(len(c) for c in chunks)
    xref = [b'xref\n0 7\n', b'0000000000 65535 f \n']
    for off in offsets[:6]:
        xref.append(f'{off:010d} 00000 n \n'.encode('ascii'))
    trailer = (
        b'trailer\n<< /Size 7 /Root 1 0 R /Info 6 0 R >>\nstartxref\n'
        + str(startxref).encode('ascii')
        + b'\n%%EOF\n'
    )
    path.write_bytes(b''.join(chunks + xref + [trailer]))


def export_case_study_pdf(
    summary: dict[str, Any],
    stats_rows: list[dict[str, Any]],
    chart_image_path: str | Path | None,
    output_dir: str | Path,
    trade_date: str,
    filters: list[Any],
    metadata: dict[str, Any] | None = None,
    takeaways: list[str] | None = None,
) -> Path:
    """Export deterministic PDF including summary stats, chart image (if available), and key takeaways."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / _stable_name(trade_date, filters)
    md = {'title': f'Case Study {trade_date}', 'subject': 'SA2Academy CAD'}
    if metadata:
        md.update(metadata)

    takeaways = takeaways or [
        'Review target lift and timing concentration before operational use.',
        'Validate on out-of-sample dates before promoting the setup.',
    ]

    try:
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages

        with PdfPages(out_path) as pdf:
            fig = plt.figure(figsize=(8.5, 11))
            ax = fig.add_subplot(111)
            ax.axis('off')
            y = 0.98
            ax.text(0.01, y, f'Case Study Report - {trade_date}', va='top', fontsize=14, fontweight='bold')
            y -= 0.04
            ax.text(0.01, y, 'Summary', va='top', fontsize=11, fontweight='bold')
            y -= 0.03
            for k, v in summary.items():
                ax.text(0.02, y, f'{k}: {v}', va='top', fontsize=8)
                y -= 0.02
            y -= 0.01
            ax.text(0.01, y, 'Stats (top rows)', va='top', fontsize=11, fontweight='bold')
            y -= 0.03
            for row in stats_rows[:10]:
                ax.text(
                    0.02,
                    y,
                    f"{row.get('label')} | n={row.get('n')} hits={row.get('hits')} p={row.get('p')} lift={row.get('lift')}",
                    va='top',
                    fontsize=8,
                )
                y -= 0.018
                if y < 0.25:
                    break
            ax.text(0.01, 0.22, 'Key Takeaways', fontsize=11, fontweight='bold')
            yy = 0.20
            for item in takeaways:
                ax.text(0.02, yy, f'- {item}', fontsize=8)
                yy -= 0.02
            if chart_image_path and Path(chart_image_path).exists():
                try:
                    img = plt.imread(str(chart_image_path))
                    ax2 = fig.add_axes([0.08, 0.02, 0.84, 0.15])
                    ax2.imshow(img)
                    ax2.axis('off')
                    ax2.set_title('Replay Chart', fontsize=9)
                except Exception:
                    ax.text(0.02, 0.03, f'Chart image render failed: {chart_image_path}', fontsize=8)
            else:
                ax.text(0.02, 0.03, f'Chart image unavailable: {chart_image_path}', fontsize=8)
            pdf.savefig(fig, metadata=md)
            plt.close(fig)
        return out_path
    except Exception:
        lines = [
            f'Case Study Report - {trade_date}',
            f'Summary: {json.dumps(summary, default=str)}',
            f'Chart: {chart_image_path}',
            'Stats:',
        ]
        lines.extend([f"- {r.get('label')}: n={r.get('n')} hits={r.get('hits')} p={r.get('p')}" for r in stats_rows[:20]])
        lines.append('Key Takeaways:')
        lines.extend([f'- {t}' for t in takeaways])
        _fallback_minimal_pdf(out_path, lines, md)
        return out_path
