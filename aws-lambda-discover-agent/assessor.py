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
