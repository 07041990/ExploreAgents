import boto3, sys, time
from scanners import lambda_scanner, ec2, rds, s3
from assessor import assess_all_services
from reporter import print_report, save_csv, save_json

SCANNERS = {
    "lambda": lambda_scanner.scan,
    "ec2":    ec2.scan,
    "rds":    rds.scan,
    "s3":     s3.scan,
}

def run(region="us-east-1", services=None):
    session  = boto3.Session(region_name=region)
    to_scan  = services or list(SCANNERS.keys())
    all_data = {}

    for svc in to_scan:
        if svc not in SCANNERS:
            print(f"[SKIP] Unknown service: {svc}")
            continue
        print(f"\n[SCAN] {svc.upper()} in {region}...")
        try:
            results = SCANNERS[svc](session)
            all_data[svc] = results
            print(f"       Found {len(results)} resource(s)")
        except Exception as e:
            print(f"[ERROR] {svc}: {e}")
            all_data[svc] = []

    return all_data

def main():
    args    = sys.argv[1:]
    region  = args[0] if args else "us-east-1"
    # Optional: pass service names as extra args e.g. python agent.py us-east-1 ec2 rds
    services = args[1:] if len(args) > 1 else None

    print(f"Starting multi-service scan | region: {region}")
    if services:
        print(f"Services: {', '.join(services)}")
    else:
        print("Services: all (lambda, ec2, rds, s3)")

    all_data = run(region, services)
    results  = assess_all_services(all_data)

    print_report(results)
    save_csv(results)
    save_json(results)
    print("\nDone. Open migration_report.csv for full details.")

if __name__ == "__main__":
    main()