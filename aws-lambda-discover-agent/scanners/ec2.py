def scan(session):
    ec2 = session.client("ec2")
    paginator = ec2.get_paginator("describe_instances")
    results = []
    for page in paginator.paginate():
        for reservation in page["Reservations"]:
            for inst in reservation["Instances"]:
                name_tag = next(
                    (t["Value"] for t in inst.get("Tags", [])
                     if t["Key"] == "Name"), ""
                )
                results.append({
                    "name":          inst["InstanceId"],
                    "display_name":  name_tag,
                    "type":          inst.get("InstanceType", ""),
                    "state":         inst["State"]["Name"],
                    "platform":      inst.get("Platform", "linux"),
                    "vpc_id":        inst.get("VpcId", ""),
                    "az":            inst.get("Placement",{}).get("AvailabilityZone",""),
                    "public_ip":     inst.get("PublicIpAddress", ""),
                    "private_ip":    inst.get("PrivateIpAddress", ""),
                    "architecture":  inst.get("Architecture", "x86_64"),
                    "tenancy":       inst.get("Placement",{}).get("Tenancy","default"),
                    "monitoring":    inst.get("Monitoring",{}).get("State","disabled"),
                    "launch_time":   str(inst.get("LaunchTime", "")),
                    "service":       "EC2",
                })
    return results