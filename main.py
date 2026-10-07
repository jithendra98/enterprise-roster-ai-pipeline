import os
import sys
import json
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from pipeline.schema_mapper import DynamicSchemaMapper
from pipeline.compliance_validator import RosterComplianceValidator
from pipeline.webhook_dispatcher import WebhookAlertDispatcher

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(force_terminal=True)

def run_pipeline(input_file: str, webhook_url: str = None, dry_run: bool = True):
    console.print(Panel.fit(
        "[bold cyan]Enterprise Roster Ingestion & Shift Reconciliation Engine[/bold cyan]\n"
        "[dim]Forward Deployed Engineering Suite for Workplace Transit & Compliance[/dim]",
        border_style="cyan"
    ))

    if not os.path.exists(input_file):
        console.print(f"[bold red]Error:[/bold red] Input file '{input_file}' not found.")
        sys.exit(1)

    console.print(f"\n[bold green]-> Step 1:[/bold green] Ingesting raw enterprise roster from: [yellow]{input_file}[/yellow]")
    mapper = DynamicSchemaMapper()
    canonical_records, parse_errors = mapper.process_file(input_file)

    console.print(f"  ✓ Processed [bold green]{len(canonical_records)}[/bold green] valid records.")
    if parse_errors:
        console.print(f"  ⚠ Quarantined [bold yellow]{len(parse_errors)}[/bold yellow] unparseable rows.")

    # Display canonical mapped records
    table = Table(title="Canonical Normalized Records (Sample)", box=box.ROUNDED)
    table.add_column("Emp ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Gender", style="magenta")
    table.add_column("Shift", style="green")
    table.add_column("Pickup Loc", style="white")
    table.add_column("Drop Loc", style="white")
    table.add_column("Escort Req", style="yellow")

    for rec in canonical_records[:5]:
        table.add_row(
            rec.employee_id,
            rec.employee_name,
            rec.gender,
            rec.shift_time,
            rec.pickup_address[:18] + ("..." if len(rec.pickup_address) > 18 else ""),
            rec.drop_address[:18] + ("..." if len(rec.drop_address) > 18 else ""),
            "YES" if rec.requires_escort else "NO"
        )
    console.print(table)

    # Step 2: Safety & Compliance Validation
    console.print("\n[bold green]-> Step 2:[/bold green] Running Transit Safety & Regulatory Compliance Engine...")
    validator = RosterComplianceValidator()
    violations = validator.validate_batch(canonical_records)

    if violations:
        viol_table = Table(title="[bold red]Safety & Compliance Violations Detected[/bold red]", box=box.HEAVY_EDGE)
        viol_table.add_column("Severity", style="bold red")
        viol_table.add_column("Emp ID", style="cyan")
        viol_table.add_column("Policy Code", style="yellow")
        viol_table.add_column("Description", style="white")

        for v in violations:
            color = "red" if v.severity == "CRITICAL" else ("yellow" if v.severity == "WARNING" else "blue")
            viol_table.add_row(
                f"[{color}]{v.severity}[/{color}]",
                v.employee_id,
                v.policy_code,
                v.description
            )
        console.print(viol_table)
    else:
        console.print("  [bold green][OK] All records passed 100% of transit safety rules.[/bold green]")

    # Step 3: Automated Incident Dispatch & Escalations
    console.print("\n[bold green]-> Step 3:[/bold green] Generating Incident Payloads & Webhook Escalations...")
    dispatcher = WebhookAlertDispatcher(webhook_url=webhook_url)
    dispatches = dispatcher.dispatch_violations(violations, dry_run=dry_run)

    for item in dispatches:
        console.print(Panel(
            json.dumps(item["payload"], indent=2),
            title=f"[bold magenta]Webhook Payload (Status: {item['status']})[/bold magenta]",
            border_style="magenta"
        ))

    console.print("\n[bold green][OK] Pipeline execution completed successfully.[/bold green]\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enterprise Roster Ingestion & Shift Reconciliation Pipeline")
    parser.add_argument("--input", default="data/sample_raw_roster_workday.csv", help="Path to raw roster CSV")
    parser.add_argument("--webhook", default=None, help="Slack/Teams webhook URL for live alerts")
    parser.add_argument("--live", action="store_true", help="Send live webhook alerts (default is dry-run)")
    args = parser.parse_args()

    run_pipeline(input_file=args.input, webhook_url=args.webhook, dry_run=not args.live)
