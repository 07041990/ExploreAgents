# AWS → Azure Migration Agent

A command-line agent that scans your AWS account for Lambda functions, EC2 instances, RDS databases, and S3 buckets — then scores each resource for Azure migration feasibility. Outputs a ranked report as both a CSV (open in Excel) and JSON.

---

## What it does

- Scans **Lambda**, **EC2**, **RDS**, and **S3** across any AWS region
- Enriches each resource with metadata beyond what the basic AWS API returns
- Scores each resource from 0–100 for Azure migration complexity
- Groups output by service and flags specific blockers (unsupported runtimes, VPC configs, unencrypted storage, etc.)
- Saves results to `migration_report.csv` and `migration_report.json`

---

## Score labels

| Score | Label | What it means |
|---|---|---|
| 80–100 | Easy | Minimal changes needed — near drop-in migration |
| 55–79 | Moderate | Trigger, networking, or config changes required |
| 30–54 | Hard | Runtime or service refactor required |
| 0–29 | Rewrite needed | Significant rewrite; reconsider architecture |

---

## Project structure

```
aws-migration-agent/
├── agent.py                  # Entry point — run this
├── assessor.py               # Scores each resource for Azure migration
├── reporter.py               # Formats and saves the report
├── requirements.txt          # Python dependencies
└── scanners/
    ├── __init__.py
    ├── lambda_scanner.py     # Scans Lambda functions (paginated)
    ├── ec2.py                # Scans EC2 instances
    ├── rds.py                # Scans RDS instances and Aurora clusters
    └── s3.py                 # Scans S3 buckets with security checks
```

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.8+ | [python.org](https://python.org/downloads) or `brew install python3` |
| AWS CLI | v2 | [AWS docs](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) or `brew install awscli` |
| boto3 | latest | installed via `pip` (see below) |

---

## Setup — first time only

### 1. Clone or unzip the project

```bash
cd aws-migration-agent
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv

# macOS / Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

> Your terminal prompt will show `(venv)` when the environment is active.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure AWS credentials

The agent needs read-only access to your AWS account. Create an IAM user with the `ReadOnlyAccess` managed policy, generate access keys, then run:

```bash
aws configure
```

Enter your Access Key ID, Secret Access Key, default region (e.g. `us-east-1`), and output format (`json`).

Verify the connection:

```bash
aws sts get-caller-identity
```

You should see your AWS account ID and username.

---

## Running the agent

### Scan all services in a region

```bash
python3 agent.py us-east-1
```

### Scan a specific service only

```bash
python3 agent.py us-east-1 lambda
python3 agent.py us-east-1 ec2
python3 agent.py us-east-1 rds
python3 agent.py us-east-1 s3
```

### Scan multiple services

```bash
python3 agent.py us-east-1 ec2 rds
```

### Scan a different region

```bash
python3 agent.py ap-south-1        # Mumbai
python3 agent.py eu-west-1         # Ireland
python3 agent.py us-west-2         # Oregon
```

---

## Output files

After the scan completes, two files are created in the project folder:

**`migration_report.csv`** — open in Excel or Google Sheets. Columns:

| Column | Description |
|---|---|
| service | AWS service (Lambda, EC2, RDS, S3) |
| function | Resource name or ID |
| runtime | Engine, runtime, or encryption type |
| score | 0–100 migration score (higher = easier) |
| label | Easy / Moderate / Hard / Rewrite needed |
| issues | Pipe-separated list of migration blockers |

**`migration_report.json`** — full structured output for use in dashboards or scripts.

---

## IAM permissions required

The agent only reads — it never modifies any resource. The minimum IAM policy needed:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:ListFunctions",
        "lambda:ListEventSourceMappings",
        "lambda:GetPolicy",
        "lambda:GetFunctionUrlConfig",
        "lambda:GetFunctionConcurrency",
        "ec2:DescribeInstances",
        "ec2:DescribeRegions",
        "rds:DescribeDBInstances",
        "rds:DescribeDBClusters",
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation",
        "s3:GetBucketVersioning",
        "s3:GetEncryptionConfiguration",
        "s3:GetBucketPublicAccessBlock",
        "s3:GetLifecycleConfiguration",
        "s3:GetReplicationConfiguration"
      ],
      "Resource": "*"
    }
  ]
}
```

> Alternatively, attach the AWS-managed `ReadOnlyAccess` policy which covers all of the above.

---

## Using multiple AWS accounts

Add a named profile for each account:

```bash
aws configure --profile client-prod
aws configure --profile client-staging
```

Then update the session line in `agent.py`:

```python
session = boto3.Session(region_name=region, profile_name="client-prod")
```

---

## Extending the agent

Every scanner follows the same contract: **accept a boto3 session, return a list of dicts**. To add a new service (e.g. EKS):

1. Create `scanners/eks.py` with a `scan(session)` function
2. Add it to the `SCANNERS` dict in `agent.py`
3. Add an `assess_eks()` function in `assessor.py`
4. Add routing for `"eks"` in `assess_all_services()` in `assessor.py`

---

## Troubleshooting

| Error | Fix |
|---|---|
| `zsh: command not found: python` | Use `python3` instead, or add `alias python=python3` to `~/.zshrc` |
| `Unable to locate credentials` | Run `aws configure` and enter your access keys |
| `AccessDenied` on a service | Add the missing permission to your IAM user/role |
| `EndpointResolutionError` | The service is not available in your selected region — try another region |
| Rate limit / throttling errors | Increase the `time.sleep()` delay in the scanner file |

---

## Dependencies

```
boto3>=1.28.0
pandas>=2.0.0
tabulate>=0.9.0
```

---

## License

MIT — free to use, modify, and distribute.
