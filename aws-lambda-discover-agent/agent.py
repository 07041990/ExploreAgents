import boto3, sys
from scanners import lambda_scanner
from assessor import assess_all
from reporter import print_report, save_csv, save_json

def main():
    region = sys.argv[1] if len(sys.argv) > 1 else "us-east-1"
    print(f"Starting scan in region: {region}")
    session = boto3.Session(region_name=region)

    functions = lambda_scanner.scan(session)
    results   = assess_all(functions)

    print_report(results)
    save_csv(results)
    save_json(results)
    print("\nDone. Open migration_report.csv to view results in Excel.")

if __name__ == "__main__":
    main()