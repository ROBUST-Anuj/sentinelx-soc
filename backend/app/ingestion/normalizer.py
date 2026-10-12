from typing import Tuple, List, Dict, Any
from app.models.schemas import CanonicalEvent, SourceType
from app.ingestion.parsers import LinuxAuthParser, SysmonParser, WebAccessParser, GenericJSONParser
import io
import csv

class NormalizationEngine:
    def __init__(self):
        self.parsers = {
            SourceType.LINUX_AUTH: LinuxAuthParser(),
            SourceType.SYSMON: SysmonParser(),
            SourceType.WEB_ACCESS: WebAccessParser(),
            SourceType.GENERIC_JSON: GenericJSONParser()
        }

    def process_content(self, content: str, source_type: SourceType, source_name: str, batch_id: str) -> Tuple[List[CanonicalEvent], int, int, List[str]]:
        """
        Takes raw string content (multiline log file), runs appropriate parser,
        validates CanonicalEvent, assigns batch_id, returns (events, valid_count, invalid_count, errors)
        """
        valid_events: List[CanonicalEvent] = []
        invalid_count = 0
        errors: List[str] = []

        if source_type == SourceType.GENERIC_CSV:
            # Handle CSV input
            reader = csv.DictReader(io.StringIO(content))
            for row_idx, row in enumerate(reader):
                try:
                    event = CanonicalEvent(
                        source_type=SourceType.GENERIC_CSV,
                        source_name=source_name,
                        host_id=row.get("host_id") or row.get("host"),
                        user_id=row.get("user_id") or row.get("user"),
                        src_ip=row.get("src_ip"),
                        src_port=int(row["src_port"]) if row.get("src_port") and row["src_port"].isdigit() else None,
                        dst_ip=row.get("dst_ip"),
                        dst_port=int(row["dst_port"]) if row.get("dst_port") and row["dst_port"].isdigit() else None,
                        protocol=row.get("protocol"),
                        event_type=row.get("event_type", "csv_network_flow"),
                        process_name=row.get("process_name"),
                        command_line=row.get("command_line"),
                        ingestion_batch_id=batch_id,
                        normalized_fields=row
                    )
                    valid_events.append(event)
                except Exception as e:
                    invalid_count += 1
                    errors.append(f"Row {row_idx}: {str(e)}")
            return valid_events, len(valid_events), invalid_count, errors

        parser = self.parsers.get(source_type, GenericJSONParser())
        lines = content.splitlines()

        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            success, event, err = parser.parse_line(line, source_name)
            if success and event:
                event.ingestion_batch_id = batch_id
                valid_events.append(event)
            else:
                invalid_count += 1
                if err and len(errors) < 20:
                    errors.append(f"Line {idx+1}: {err}")

        return valid_events, len(valid_events), invalid_count, errors

normalizer = NormalizationEngine()
