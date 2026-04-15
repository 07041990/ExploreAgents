def scan(session):
    s3 = session.client("s3")
    buckets = s3.list_buckets().get("Buckets", [])
    results = []

    for bucket in buckets:
        name = bucket["Name"]
        info = {
            "name":              name,
            "created":           str(bucket.get("CreationDate", "")),
            "region":            _get_region(s3, name),
            "versioning":        _get_versioning(s3, name),
            "encryption":        _get_encryption(s3, name),
            "public_access_blocked": _get_public_block(s3, name),
            "lifecycle_rules":   _get_lifecycle(s3, name),
            "replication":       _get_replication(s3, name),
            "service":           "S3",
        }
        results.append(info)

    return results

def _get_region(s3, name):
    try:
        loc = s3.get_bucket_location(Bucket=name)
        return loc.get("LocationConstraint") or "us-east-1"
    except Exception:
        return "unknown"

def _get_versioning(s3, name):
    try:
        v = s3.get_bucket_versioning(Bucket=name)
        return v.get("Status", "Disabled")
    except Exception:
        return "unknown"

def _get_encryption(s3, name):
    try:
        enc = s3.get_bucket_encryption(Bucket=name)
        rules = enc["ServerSideEncryptionConfiguration"]["Rules"]
        return rules[0]["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"]
    except Exception:
        return "None"

def _get_public_block(s3, name):
    try:
        cfg = s3.get_public_access_block(Bucket=name)
        blk = cfg["PublicAccessBlockConfiguration"]
        return all([
            blk.get("BlockPublicAcls", False),
            blk.get("IgnorePublicAcls", False),
            blk.get("BlockPublicPolicy", False),
            blk.get("RestrictPublicBuckets", False),
        ])
    except Exception:
        return False

def _get_lifecycle(s3, name):
    try:
        lc = s3.get_bucket_lifecycle_configuration(Bucket=name)
        return len(lc.get("Rules", []))
    except Exception:
        return 0

def _get_replication(s3, name):
    try:
        s3.get_bucket_replication(Bucket=name)
        return True
    except Exception:
        return False