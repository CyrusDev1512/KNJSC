"""Dọn đúng môi trường grid-flags sau khi lưu bằng chứng; không prune Docker."""
import json
import subprocess
from run import ROOT, NETWORK, DB


def inspect(name):
    result = subprocess.run(["docker", "inspect", name], capture_output=True, text=True)
    return json.loads(result.stdout)[0] if result.returncode == 0 else None


names = ["knjsc-gridflags-load", "knjsc-gridflags-app", "knjsc-gridflags-redis", "knjsc-gridflags-db"]
containers = {name: data for name in names if (data := inspect(name))}
if "knjsc-gridflags-load" in containers:
    assert not containers["knjsc-gridflags-load"]["State"]["Running"], "Kiểm tải còn chạy"
for name, data in containers.items():
    assert list(data["NetworkSettings"]["Networks"]) == [NETWORK], f"Sai network: {name}"
database = containers.get("knjsc-gridflags-db")
volumes = []
if database:
    assert "POSTGRES_DB=" + DB in database["Config"]["Env"], "Sai database test"
    volumes = [m["Name"] for m in database["Mounts"] if m["Type"] == "volume"]
    all_ids = subprocess.check_output(["docker", "ps", "-aq"], text=True).split()
    for identity in all_ids:
        other = inspect(identity)
        if other["Id"] != database["Id"]:
            assert not any(m.get("Name") in volumes for m in other["Mounts"]), "Volume còn được container khác dùng"
for name in containers:
    subprocess.run(["docker", "rm", "-f", name], check=True)
for volume in volumes:
    subprocess.run(["docker", "volume", "rm", volume], check=True)
network = subprocess.run(["docker", "network", "inspect", NETWORK], capture_output=True, text=True)
if network.returncode == 0:
    assert not json.loads(network.stdout)[0]["Containers"], "Network còn container khác"
    subprocess.run(["docker", "network", "rm", NETWORK], check=True)
root = ROOT.resolve()
for filename in ["runtime.env", "ready.json"]:
    path = (root / filename).resolve()
    assert path.parent == root
    path.unlink(missing_ok=True)
print("Test containers/database and credentials removed; evidence retained.")
