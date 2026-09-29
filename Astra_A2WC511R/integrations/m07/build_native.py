"""Build isolated native-codec endpoint and pin its minimal runtime inputs."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOLS = Path("C:/Renesas/e2_studio/eclipse/plugins/org.eclipse.justj.openjdk.hotspot.jre.full.win32.x86_64_21.0.11.v20260515-1531/jre/bin")
JAVA = Path("C:/Program Files/RomRaider/jdk-11.0.14.1+1-jre/bin/java.exe")
LIBS = [Path("C:/Program Files/RomRaider/RomRaider.jar"), ROOT / "integrations/romraider/dist/romraider-bridge.jar"]
OUT = ROOT / "work/m07_host/native"


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    classes = OUT / "classes"
    classes.mkdir(exist_ok=True)
    log = []
    jar = OUT / "m07-native-virtual.jar"
    commands = [[str(TOOLS/"javac.exe"), "--release", "8", "-cp", ";".join(map(str,LIBS)), "-d", str(classes), str(HERE/"NativeVirtualEndpoint.java")],
                [str(TOOLS/"jar.exe"), "--create", "--file", str(jar), "-C", str(classes), "NativeVirtualEndpoint.class", "-C", str(classes), "NativeVirtualEndpoint$TranscriptConnection.class"]]
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True)
        log.append({"command": command, "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode:
            (OUT/"build_log.json").write_text(json.dumps(log,indent=2))
            raise RuntimeError("Native endpoint build failed")
    (OUT/"build_log.json").write_text(json.dumps(log,indent=2))
    fixture = ROOT/"reports/local/m07_residency/host/stock_six_a8_fixtures.json"
    data=json.loads(fixture.read_text())
    classpath=[jar,*LIBS]
    profile={"schema":1,"mode":"OFFLINE_ONLY_NO_PHYSICAL_BACKEND","fixture":{"path":str(fixture),"sha256":digest(fixture)},
             "stock_rom":data["stock_rom"],"java":{"path":str(JAVA),"sha256":digest(JAVA)},
             "classpath":[{"path":str(p),"sha256":digest(p)} for p in classpath],
             "endpoint_source_sha256":digest(HERE/"NativeVirtualEndpoint.java"),
             "build_log":{"path":str(OUT/"build_log.json"),"sha256":digest(OUT/"build_log.json")},
             "no_JNA_or_provider_library_on_classpath":True}
    (HERE/"profile.json").write_text(json.dumps(profile,indent=2))
    print(json.dumps({"status":"BUILT_OFFLINE_ENDPOINT","profile":str(HERE/"profile.json"),"jar_sha256":digest(jar)}))


if __name__=="__main__":main()
