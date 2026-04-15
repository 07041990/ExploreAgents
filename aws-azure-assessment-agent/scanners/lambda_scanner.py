import time

def scan_all(session):
    lmb = session.client("lambda")
    paginator = lmb.get_paginator("list_functions")
    all_fns = []
    for page in paginator.paginate():
        all_fns.extend(page["Functions"])
    return all_fns

def enrich(session, fn):
    lmb = session.client("lambda")
    name = fn["FunctionName"]
    result = {
        "name": name,
        "runtime": fn.get("Runtime", "unknown"),
        "memory_mb": fn.get("MemorySize", 128),
        "timeout_sec": fn.get("Timeout", 3),
        "code_size_bytes": fn.get("CodeSize", 0),
        "last_modified": fn.get("LastModified", ""),
        "architecture": fn.get("Architectures", ["x86_64"]),
        "vpc": bool(fn.get("VpcConfig", {}).get("VpcId")),
        "layers": [l["Arn"] for l in fn.get("Layers", [])],
        "env_vars": list(fn.get("Environment",{})
                         .get("Variables",{}).keys()),
    }
    try:
        t = lmb.list_event_source_mappings(FunctionName=name)
        result["triggers"] = [m["EventSourceArn"]
                               for m in t.get("EventSourceMappings",[])]
    except Exception:
        result["triggers"] = []
    try:
        lmb.get_function_url_config(FunctionName=name)
        result["has_url"] = True
    except Exception:
        result["has_url"] = False
    return result

def scan(session):
    print("Fetching all Lambda functions (paginated)...")
    fns = scan_all(session)
    print(f"Found {len(fns)} functions. Enriching metadata...")
    enriched = []
    for i, fn in enumerate(fns):
        print(f"  [{i+1}/{len(fns)}] {fn['FunctionName']}")
        enriched.append(enrich(session, fn))
        time.sleep(0.08)
    return enriched
