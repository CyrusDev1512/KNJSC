"""Chạy tuần tự các phép đo cô lập; không dùng Compose/database đang sử dụng."""
import json
import hashlib
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "storage/grid-flags-20260916"
NETWORK = "knjsc-gridflags-test"
DB = "test_knjsc_gridflags_load"
NODE = Path("C:/Users/PC/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe")


def run(*args, **kw):
    return subprocess.run(args, check=True, **kw)


def container_exists(name):
    return subprocess.run(["docker", "inspect", name], capture_output=True).returncode == 0


def assert_owned(name):
    info = json.loads(subprocess.check_output(["docker", "inspect", name], text=True))[0]
    assert list(info["NetworkSettings"]["Networks"]) == [NETWORK], "Sai network test"


def common():
    return ["--network", NETWORK, "--env-file", str(ROOT / "runtime.env"),
            "-v", str(ROOT) + ":/runtime", "-v", str(ROOT / "harness") + ":/harness:ro"]


def setup():
    assert not container_exists("knjsc-gridflags-db"), "Môi trường đã tồn tại"
    env = dict(line.split("=", 1) for line in (ROOT / "runtime.env").read_text().splitlines())
    run("docker", "network", "create", NETWORK)
    run("docker", "run", "-d", "--name", "knjsc-gridflags-db", "--network", NETWORK,
        "--env-file", str(ROOT / "runtime.env"), "--memory", "1280m", "postgres:16-alpine",
        "postgres", "-c", "shared_buffers=512MB", "-c", "work_mem=4MB", "-c", "max_connections=40")
    run("docker", "run", "-d", "--name", "knjsc-gridflags-redis", "--network", NETWORK,
        "--memory", "256m", "redis:7-alpine")
    for _ in range(60):
        if subprocess.run(["docker", "exec", "knjsc-gridflags-db", "pg_isready", "-U", env["POSTGRES_USER"]], capture_output=True).returncode == 0:
            break
        time.sleep(1)
    run("docker", "run", "--rm", "--name", "knjsc-gridflags-seed", *common(),
        "-v", str(ROOT / "after/app") + ":/app:ro", "knjsc-web", "python", "/harness/setup.py")
    run("docker", "exec", "knjsc-gridflags-db", "createdb", "-U", "gridflags_test", "-T", DB, "test_knjsc_gridflags_pristine")


def start(variant):
    assert variant in {"before", "after", "render", "read", "sync"}
    for name in ["knjsc-gridflags-db", "knjsc-gridflags-redis"]:
        assert_owned(name)
    database = json.loads(subprocess.check_output(["docker", "inspect", "knjsc-gridflags-db"], text=True))[0]
    assert database["HostConfig"]["NanoCpus"] == 0, "Cấu hình nghiệm thu không có CPU quota"
    if container_exists("knjsc-gridflags-app"):
        assert_owned("knjsc-gridflags-app")
        run("docker", "rm", "-f", "knjsc-gridflags-app", stdout=subprocess.DEVNULL)
    run("docker", "exec", "knjsc-gridflags-db", "dropdb", "-U", "gridflags_test", DB)
    run("docker", "exec", "knjsc-gridflags-db", "createdb", "-U", "gridflags_test", "-T", "test_knjsc_gridflags_pristine", DB)
    run("docker", "exec", "knjsc-gridflags-redis", "redis-cli", "FLUSHALL", stdout=subprocess.DEVNULL)
    source = ROOT / ("before" if variant == "before" else "after") / "app"
    args = ["docker", "run", "-d", "--name", "knjsc-gridflags-app", *common(),
            "--memory", "640m", "-p", "127.0.0.1:18641:8000", "-v", str(source) + ":/app:ro"]
    for flag in ["READ", "SYNC", "RECEIPTS", "RENDER", "STATS", "EXPORT", "QUEUES"]:
        active = (flag == "READ" and variant in {"read", "sync"}) or (flag == "SYNC" and variant == "sync") or (flag == "RENDER" and variant == "render")
        args += ["-e", "CRM_OPT_" + flag + "=" + str(int(active))]
    run(*args, "knjsc-web", "gunicorn", "mixed_wsgi:application", "--bind", "0.0.0.0:8000",
        "--workers", "1", "--threads", "4", "--worker-class", "gthread", "--timeout", "60", "--keep-alive", "5", stdout=subprocess.DEVNULL)
    for _ in range(60):
        try:
            with urllib.request.urlopen("http://127.0.0.1:18641/dang-nhap/", timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(1)
    raise RuntimeError("App test chưa sẵn sàng")


def phase(name, variant, mixed=False, seconds=362, width=1440):
    assert not (ROOT / "results" / (name + ".json")).exists(), "Không ghi đè bằng chứng"
    warm = 60 if seconds >= 360 else 0
    runtime = {"variant": variant, "mixed": mixed, "seconds": seconds, "warmup": warm,
               "width": width, "containers": {}}
    for container in ["knjsc-gridflags-app", "knjsc-gridflags-db", "knjsc-gridflags-redis"]:
        inspected = json.loads(subprocess.check_output(["docker", "inspect", container], text=True))[0]
        runtime["containers"][container] = {
            "image": inspected["Image"], "memory": inspected["HostConfig"]["Memory"],
            "nano_cpus": inspected["HostConfig"]["NanoCpus"], "command": inspected["Config"]["Cmd"],
            "flags": [value for value in inspected["Config"]["Env"] if value.startswith("CRM_OPT_")],
        }
    source = ROOT / ("before" if variant == "before" else "after") / "app"
    runtime["source"] = {relative: hashlib.sha256((source / relative).read_bytes()).hexdigest()
                         for relative in ["static/js/master-grid.js", "crm/services/optimization.py"]}
    (ROOT / "results" / (name + "-runtime.json")).write_text(json.dumps(runtime, indent=2))
    env = {**os.environ, "NODE_PATH": str(NODE.parent.parent / "node_modules"), "PHASE": name,
           "DURATION": str(seconds + 10), "WARMUP": str(warm), "WIDTH": str(width)}
    files = []

    def launch(suffix, args):
        f = (ROOT / "results" / f"{name}-{suffix}.log").open("w", encoding="utf-8")
        files.append(f)
        return subprocess.Popen(args, stdout=f, stderr=subprocess.STDOUT, env=env)

    browser = launch("chrome", [str(NODE), str(ROOT / "harness/browser.cjs")])
    resources = launch("resources", [sys.executable, str(ROOT / "harness/resources.py"), name])
    args = ["docker", "run", "--rm", "--name", "knjsc-gridflags-load", *common(),
            "-e", "PHASE=" + name, "-e", "WARMUP=" + str(warm), "-e", "DELIVERY_USERS=9",
            "-e", "MEASURE_SECONDS=" + str(seconds - warm - 2 if warm else seconds),
            "-e", "MIXED=" + str(int(mixed)), "-e", "PROTOCOL=" + ("2" if variant in {"read", "sync"} else "1"),
            "-e", "SYNC=" + str(int(variant == "sync")), "knjsc-web", "locust", "-f", "/harness/locust_mixed.py",
            "--headless", "--host", "http://knjsc-gridflags-app:8000", "-u", str(39 if mixed else 9),
            "-r", "4", "-t", str(seconds) + "s", "--stop-timeout", "45", "--only-summary"]
    load = launch("locust", args)
    while load.poll() is None:
        if browser.poll() is not None and browser.returncode != 0:
            # Giữ đủ mười người dùng đã cam kết; browser hỏng thì lượt đo dừng.
            run("docker", "stop", "--timeout", "45", "knjsc-gridflags-load", stdout=subprocess.DEVNULL)
            break
        time.sleep(.5)
    rc = load.wait()
    browser_rc = browser.wait(timeout=75)
    resources.wait(timeout=20)
    for f in files:
        f.close()
    run("docker", "exec", "-e", "PHASE=" + name, "knjsc-gridflags-app", "python", "/harness/verify.py")
    report = json.loads((ROOT / "results" / (name + ".json")).read_text())
    integrity = json.loads((ROOT / "results" / (name + "-integrity.json")).read_text())
    result = {"phase": name, "exit": rc, "browser_exit": browser_rc, "measured_seconds": report["measured_seconds"],
              "abort": report["abort"], "server_errors": report["unexpected_server_errors"], "operations": report["operations"],
              "integrity": integrity}
    print(json.dumps(result), flush=True)
    assert rc == browser_rc == 0 and not report["abort"] and not report["unexpected_server_errors"] and not integrity["errors"], "Không đạt correctness; dừng lượt sau"
    if warm:
        assert report["measured_seconds"] >= seconds - warm - 2, "Lượt đo chưa đủ thời gian"
    return result


if __name__ == "__main__":
    if sys.argv[1] == "setup":
        setup()
    elif sys.argv[1] == "start":
        start(sys.argv[2])
    elif sys.argv[1] == "phase":
        phase(sys.argv[2], sys.argv[3], sys.argv[4] == "mixed", int(sys.argv[5]), int(sys.argv[6]) if len(sys.argv) > 6 else 1440)
