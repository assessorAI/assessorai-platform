import csv
import io
from typing import List, Dict, Any
from fastapi.responses import StreamingResponse


def generate_csv_response(
    data: List[Dict[str, Any]],
    filename: str,
) -> StreamingResponse:
    """
    Convert list of dicts to CSV and return as streaming response.
    
    Args:
        data: List of dictionaries with flat structure
        filename: Name for downloaded file
    
    Returns:
        StreamingResponse with CSV content
    """
    if not data:
        # Empty CSV with just headers
        output = io.StringIO()
        output.write("# No data available\n")
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    # Flatten nested dicts for CSV
    flat_data = []
    for row in data:
        flat_row = flatten_dict(row)
        flat_data.append(flat_row)
    
    # Write CSV
    output = io.StringIO()
    if flat_data:
        writer = csv.DictWriter(output, fieldnames=flat_data[0].keys())
        writer.writeheader()
        writer.writerows(flat_data)
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """
    Flatten nested dictionary for CSV export.
    
    Example:
        {"metrics": {"logs_7d": 10}} -> {"metrics_logs_7d": 10}
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Convert lists to comma-separated strings
            items.append((new_key, ','.join(str(x) for x in v)))
        else:
            items.append((new_key, v))
    return dict(items)
