def scan(session):
    rds = session.client("rds")
    results = []

    # Scan DB instances (MySQL, Postgres, Oracle, SQL Server, etc.)
    paginator = rds.get_paginator("describe_db_instances")
    for page in paginator.paginate():
        for db in page["DBInstances"]:
            results.append({
                "name":           db["DBInstanceIdentifier"],
                "engine":         db["Engine"],
                "engine_version": db.get("EngineVersion", ""),
                "instance_class": db.get("DBInstanceClass", ""),
                "status":         db.get("DBInstanceStatus", ""),
                "multi_az":       db.get("MultiAZ", False),
                "storage_gb":     db.get("AllocatedStorage", 0),
                "storage_type":   db.get("StorageType", ""),
                "encrypted":      db.get("StorageEncrypted", False),
                "vpc_id":         db.get("DBSubnetGroup",{}).get("VpcId",""),
                "publicly_accessible": db.get("PubliclyAccessible", False),
                "deletion_protection": db.get("DeletionProtection", False),
                "backup_retention": db.get("BackupRetentionPeriod", 0),
                "resource_type":  "instance",
                "service":        "RDS",
            })

    # Scan Aurora clusters separately
    try:
        cpag = rds.get_paginator("describe_db_clusters")
        for page in cpag.paginate():
            for cluster in page["DBClusters"]:
                results.append({
                    "name":           cluster["DBClusterIdentifier"],
                    "engine":         cluster["Engine"],
                    "engine_version": cluster.get("EngineVersion",""),
                    "instance_class": "cluster",
                    "status":         cluster.get("Status",""),
                    "multi_az":       cluster.get("MultiAZ", False),
                    "storage_gb":     0,
                    "storage_type":   "aurora",
                    "encrypted":      cluster.get("StorageEncrypted", False),
                    "vpc_id":         cluster.get("VpcId",""),
                    "publicly_accessible": False,
                    "deletion_protection": cluster.get("DeletionProtection", False),
                    "backup_retention": cluster.get("BackupRetentionPeriod", 0),
                    "resource_type":  "cluster",
                    "service":        "RDS",
                })
    except Exception:
        pass

    return results