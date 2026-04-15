Pre Requisites
pip install boto3 pandas tabulate


Inside your project folder, run:

python -m venv venv

Make sure you are in the project folder and your venv is active, then run:

# Default region (us-east-1):
python agent.py

# Specific region:
python agent.py ap-south-1

# Multiple regions (run separately):
python agent.py us-east-1
python agent.py eu-west-1


You will see live progress as each Lambda function is scanned. When done, two files are created in the same folder:

migration_report.csv
— open in Excel or Google Sheets
migration_report.json
— for programmatic use or dashboards
For 100 functions the scan takes roughly 2-4 minutes due to rate-limit throttling between API calls.
