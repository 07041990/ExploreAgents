AZURE_RUNTIMES = [
    "python3.9","python3.10","python3.11","python3.12",
    "nodejs18.x","nodejs20.x","dotnet6","dotnet8",
    "java11","java17","powershell7.2"
]
BAD_RUNTIMES = ["ruby","go1.x","provided","provided.al2"]

def assess(fn):
    issues, score = [], 100
    rt = fn.get("runtime","")

    if any(b in rt for b in BAD_RUNTIMES):
        issues.append(f"Runtime '{rt}' not supported on Azure — full rewrite needed")
        score -= 35
    elif rt not in AZURE_RUNTIMES:
        issues.append(f"Runtime '{rt}' — verify Azure Functions compatibility")
        score -= 10

    if fn.get("vpc"):
        issues.append("VPC-attached — needs Azure VNet integration (extra config)")
        score -= 15

    timeout = fn.get("timeout_sec", 3)
    if timeout > 230:
        issues.append(f"Timeout {timeout}s exceeds Azure Consumption plan (230s max)")
        score -= 20
    elif timeout > 60:
        issues.append(f"Timeout {timeout}s — may need Azure Premium plan")
        score -= 5

    if fn.get("memory_mb", 128) > 1536:
        issues.append("Memory >1536MB — requires Azure Premium plan")
        score -= 15

    layers = fn.get("layers", [])
    if layers:
        issues.append(f"{len(layers)} Lambda layer(s) — must bundle into deployment package for Azure")
        score -= 8 * len(layers)

    trigger_map = {
        "sqs":      ("Azure Service Bus", -5),
        "sns":      ("Azure Event Grid", -10),
        "s3":       ("Azure Blob trigger", -3),
        "kinesis":  ("Azure Event Hubs (API refactor needed)", -20),
        "dynamodb": ("Cosmos DB change feed (significant refactor)", -25),
        "kafka":    ("Azure Event Hubs for Kafka (mostly compatible)", -8),
    }
    for src in fn.get("triggers", []):
        for key, (note, penalty) in trigger_map.items():
            if key in src.lower():
                issues.append(f"Trigger {key.upper()} -> {note}")
                score += penalty

    aws_keys = [k for k in fn.get("env_vars", [])
                if any(x in k.upper() for x in
                       ["AWS","DYNAMO","SQS","SNS","KINESIS","COGNITO"])]
    if aws_keys:
        issues.append(f"AWS-specific env vars: {aws_keys} — need remapping")
        score -= 4 * len(aws_keys)

    if "arm64" in fn.get("architecture", []):
        issues.append("ARM64 — verify custom binaries work on Azure")
        score -= 5

    score = max(0, score)
    if score >= 80: label = "Easy"
    elif score >= 55: label = "Moderate"
    elif score >= 30: label = "Hard"
    else: label = "Rewrite needed"

    return {"function": fn["name"], "runtime": fn.get("runtime"),
            "score": score, "label": label, "issues": issues}

def assess_all(functions):
    return sorted([assess(fn) for fn in functions],
                  key=lambda x: x["score"])

# ---- ADD THESE BELOW assess_all() ----

def assess_ec2(fn):
    issues, score = [], 100

    # Windows instances need Azure Windows VMs (higher cost)
    if str(fn.get("platform","")).lower() == "windows":
        issues.append("Windows platform — maps to Azure Windows VM (higher licensing cost)")
        score -= 15

    # Dedicated tenancy has no direct Azure equivalent
    if fn.get("tenancy") == "dedicated":
        issues.append("Dedicated tenancy — no direct Azure equivalent; needs Azure Dedicated Host")
        score -= 20

    # VPC-attached instances need VNet setup in Azure
    if fn.get("vpc_id"):
        issues.append("VPC-attached — requires Azure VNet + subnet configuration")
        score -= 10

    # ARM architecture
    if fn.get("architecture") == "arm64":
        issues.append("ARM64 — verify workload runs on Azure Ampere/ARM VMs")
        score -= 5

    score = max(0, score)
    if score >= 80:   label = "Easy"
    elif score >= 55: label = "Moderate"
    elif score >= 30: label = "Hard"
    else:             label = "Rewrite needed"

    return {
        "function": fn["name"], "service": "EC2",
        "runtime": fn.get("type",""), "score": score,
        "label": label, "issues": issues,
    }


def assess_rds(fn):
    issues, score = [], 100

    engine = fn.get("engine","").lower()

    # Engine mapping
    engine_map = {
        "mysql":       ("Azure Database for MySQL", -5),
        "postgres":    ("Azure Database for PostgreSQL", -5),
        "mariadb":     ("Azure Database for MariaDB", -8),
        "aurora-mysql":("Azure Database for MySQL Flexible Server", -10),
        "aurora-postgresql": ("Azure Database for PostgreSQL Flexible", -10),
        "sqlserver":   ("Azure SQL Database (mostly compatible)", -5),
        "oracle":      ("No managed Oracle on Azure — needs Oracle VM or license migration", -40),
    }
    matched = False
    for key,(note,penalty) in engine_map.items():
        if key in engine:
            issues.append(f"Engine {engine} -> {note}")
            score += penalty
            matched = True
            break
    if not matched:
        issues.append(f"Unknown engine '{engine}' — manual review needed")
        score -= 20

    if not fn.get("encrypted"):
        issues.append("Storage not encrypted — enable before migration")
        score -= 10

    if fn.get("publicly_accessible"):
        issues.append("Publicly accessible — review network exposure on Azure")
        score -= 10

    if fn.get("backup_retention", 0) == 0:
        issues.append("No automated backups configured")
        score -= 5

    score = max(0, score)
    if score >= 80:   label = "Easy"
    elif score >= 55: label = "Moderate"
    elif score >= 30: label = "Hard"
    else:             label = "Rewrite needed"

    return {
        "function": fn["name"], "service": "RDS",
        "runtime": fn.get("engine",""), "score": score,
        "label": label, "issues": issues,
    }


def assess_s3(fn):
    issues, score = [], 100

    if fn.get("encryption") == "None":
        issues.append("No server-side encryption — enable SSE before migration")
        score -= 15

    if not fn.get("public_access_blocked"):
        issues.append("Public access not fully blocked — review ACLs/bucket policy")
        score -= 20

    if fn.get("versioning") not in ("Enabled",):
        issues.append("Versioning disabled — Azure Blob versioning needs to be enabled manually")
        score -= 5

    if fn.get("replication"):
        issues.append("Replication configured — re-create cross-region replication in Azure Blob")
        score -= 10

    if fn.get("lifecycle_rules", 0) > 0:
        issues.append(f"{fn['lifecycle_rules']} lifecycle rule(s) — re-create as Azure Blob lifecycle policies")
        score -= 5 * fn["lifecycle_rules"]

    score = max(0, score)
    if score >= 80:   label = "Easy"
    elif score >= 55: label = "Moderate"
    elif score >= 30: label = "Hard"
    else:             label = "Rewrite needed"

    return {
        "function": fn["name"], "service": "S3",
        "runtime": fn.get("encryption",""), "score": score,
        "label": label, "issues": issues,
    }


def assess_all_services(all_resources):
    results = []
    for svc, items in all_resources.items():
        for item in items:
            if svc == "lambda":  results.append(assess(item))
            elif svc == "ec2":   results.append(assess_ec2(item))
            elif svc == "rds":   results.append(assess_rds(item))
            elif svc == "s3":    results.append(assess_s3(item))
    return sorted(results, key=lambda x: x["score"])
