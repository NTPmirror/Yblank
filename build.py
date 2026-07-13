#!/usr/bin/env python3
import sys, os, subprocess, platform, shutil, time, threading, urllib.request, zipfile, json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IS_WIN = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
PATH_SEP = ";" if IS_WIN else ":"

ANDROID_DIR = os.path.join(SCRIPT_DIR, "for_android")
JDK_BASE = os.path.join(ANDROID_DIR, "jdk")
SDK_DIR = os.path.join(ANDROID_DIR, "android-sdk")

JDK_VERSION = "17.0.12+7"
JDK_BUILD = "7"

if IS_WIN:
    JDK_URL = f"https://github.com/adoptium/temurin17-binaries/releases/download/jdk-{JDK_VERSION.replace('+', '%2B')}/OpenJDK17U-jdk_x64_windows_hotspot_{JDK_VERSION.replace('+', '_')}.zip"
    JDK_FOLDER = f"jdk-{JDK_VERSION}"
    SDK_TOOLS_URL = "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip"
elif IS_LINUX:
    JDK_URL = f"https://github.com/adoptium/temurin17-binaries/releases/download/jdk-{JDK_VERSION.replace('+', '%2B')}/OpenJDK17U-jdk_x64_linux_hotspot_{JDK_VERSION.replace('+', '_')}.zip"
    JDK_FOLDER = f"jdk-{JDK_VERSION}"
    SDK_TOOLS_URL = "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"
else:
    JDK_URL = ""
    SDK_TOOLS_URL = ""

BAR_WIDTH = 36
CHAR_DONE = "\u2588"
CHAR_LEFT = "\u2591"


def progress_bar(label, pct):
    filled = int(BAR_WIDTH * min(pct, 100) / 100)
    bar = CHAR_DONE * filled + CHAR_LEFT * (BAR_WIDTH - filled)
    sys.stdout.write(f"\r  {label}  [{bar}] {min(pct, 100):5.1f}%")
    sys.stdout.flush()


def done_bar(label):
    sys.stdout.write(f"\r  {label}  [{CHAR_DONE * BAR_WIDTH}] DONE\n")
    sys.stdout.flush()


def animate(label, done_event):
    frames = ["   ", ".  ", ".. ", "..."]
    i = 0
    while not done_event.is_set():
        pct = int((i % 12) / 11 * 100)
        filled = int(BAR_WIDTH * pct / 100)
        bar = CHAR_DONE * filled + CHAR_LEFT * (BAR_WIDTH - filled)
        sys.stdout.write(f"\r  {label}  [{bar}] {frames[i % 4]}  ")
        sys.stdout.flush()
        time.sleep(0.12)
        i += 1


def run_animated(label, cmd, cwd=None, env=None):
    done = threading.Event()
    t = threading.Thread(target=animate, args=(label, done), daemon=True)
    t.start()
    subprocess.run(cmd, check=True, cwd=cwd, env=env)
    done.set()
    t.join()
    done_bar(label)


def run_silent(cmd, cwd=None, env=None):
    subprocess.run(cmd, check=True, cwd=cwd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def find_cmd(name):
    return shutil.which(name)


def run_cmd(cmd, cwd=None, env=None):
    subprocess.run(cmd, check=True, cwd=cwd, env=env)


def download_file(url, dest, label):
    def reporthook(block, block_size, total):
        if total > 0:
            pct = block * block_size * 100 // total
            progress_bar(label, pct)

    print(f"  Downloading {os.path.basename(dest)}...")
    urllib.request.urlretrieve(url, dest, reporthook=reporthook)
    done_bar(label)


def extract_zip(zip_path, dest_dir, label):
    print(f"  Extracting {os.path.basename(zip_path)}...")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        total = len(zf.namelist())
        for i, name in enumerate(zf.namelist()):
            zf.extract(name, dest_dir)
            progress_bar(label, (i + 1) * 100 // total)
    done_bar(label)


def check_go():
    go = find_cmd("go")
    if not go:
        print("ERROR: Go not found. Install from https://go.dev/dl/")
        sys.exit(1)
    print(f"  Go: {go}")
    return go


def ensure_gomobile(go):
    gomobile = find_cmd("gomobile")
    if not gomobile:
        print("  Installing gomobile...")
        run_cmd([go, "install", "golang.org/x/mobile/cmd/gomobile@latest"])
        gomobile = find_cmd("gomobile")
        if not gomobile:
            gopath = subprocess.check_output([go, "env", "GOPATH"]).decode().strip()
            ext = ".exe" if IS_WIN else ""
            gomobile = os.path.join(gopath, "bin", "gomobile" + ext)
        if not os.path.isfile(gomobile):
            print("ERROR: gomobile not found after install")
            sys.exit(1)
    print(f"  gomobile: {gomobile}")
    return gomobile


def ensure_wails(go):
    wails = find_cmd("wails")
    if not wails:
        print("  Installing Wails CLI...")
        run_cmd([go, "install", "github.com/wailsapp/wails/v2/cmd/wails@latest"])
        wails = find_cmd("wails")
        if not wails:
            gopath = subprocess.check_output([go, "env", "GOPATH"]).decode().strip()
            ext = ".exe" if IS_WIN else ""
            wails = os.path.join(gopath, "bin", "wails" + ext)
        if not os.path.isfile(wails):
            print("ERROR: Wails CLI not found after install")
            sys.exit(1)
    print(f"  Wails: {wails}")
    return wails


def download_deps():
    print()
    print("=== Downloading Project Dependencies ===")
    print()

    if not IS_WIN and not IS_LINUX:
        print("ERROR: Unsupported platform for -deps. Use Windows or Linux.")
        sys.exit(1)

    go = check_go()

    os.chdir(ANDROID_DIR)
    run_animated("[1/2] go mod download", [go, "mod", "download"])

    os.makedirs(ANDROID_DIR, exist_ok=True)

    # --- JDK 17 ---
    print()
    print("  [JDK 17]")
    if os.path.isdir(os.path.join(JDK_BASE, JDK_FOLDER)):
        print(f"  JDK already exists: {JDK_FOLDER}")
    else:
        os.makedirs(JDK_BASE, exist_ok=True)
        jdk_zip = os.path.join(JDK_BASE, "jdk17.zip")
        download_file(JDK_URL, jdk_zip, "  Download JDK")
        extract_zip(jdk_zip, JDK_BASE, "  Extract JDK")
        os.remove(jdk_zip)

    # --- Android SDK Command Line Tools ---
    print()
    print("  [Android SDK]")
    sdk_tools_dir = os.path.join(SDK_DIR, "cmdline-tools", "latest")
    if os.path.isdir(sdk_tools_dir):
        print(f"  SDK tools already exist")
    else:
        os.makedirs(SDK_DIR, exist_ok=True)
        sdk_zip = os.path.join(SDK_DIR, "sdk-tools.zip")
        download_file(SDK_TOOLS_URL, sdk_zip, "  Download SDK Tools")
        print("  Extracting SDK Tools...")
        tmp_dir = os.path.join(SDK_DIR, "tmp_extract")
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir)
        extract_zip(sdk_zip, tmp_dir, "  Extract SDK Tools")
        os.makedirs(sdk_tools_dir, exist_ok=True)
        src = os.path.join(tmp_dir, "cmdline-tools")
        for item in os.listdir(src):
            shutil.move(os.path.join(src, item), sdk_tools_dir)
        shutil.rmtree(tmp_dir)
        os.remove(sdk_zip)

    # --- sdkmanager: platform-tools, build-tools, platforms, NDK ---
    print()
    print("  [SDK Packages]")
    ext = ".bat" if IS_WIN else ""
    sdkmanager = os.path.join(SDK_DIR, "cmdline-tools", "latest", "bin", f"sdkmanager{ext}")
    if not os.path.isfile(sdkmanager):
        print("ERROR: sdkmanager not found")
        sys.exit(1)

    env = os.environ.copy()
    env["JAVA_HOME"] = os.path.join(JDK_BASE, JDK_FOLDER)
    env["ANDROID_HOME"] = SDK_DIR
    env["ANDROID_SDK_ROOT"] = SDK_DIR

    packages = [
        "platform-tools",
        "build-tools;34.0.0",
        "platforms;android-34",
        "ndk;26.1.10909125",
    ]
    for pkg in packages:
        run_cmd([sdkmanager, f"--sdk_root={SDK_DIR}", pkg], env=env)

    print()
    print("=== All Dependencies Downloaded ===\n")


def get_jdk_home():
    if os.path.isdir(JDK_BASE):
        jdk_list = [d for d in os.listdir(JDK_BASE) if d.startswith("jdk-")]
        if jdk_list:
            return os.path.join(JDK_BASE, sorted(jdk_list)[-1])
    return None


def get_android_env():
    env = os.environ.copy()
    jdk_home = get_jdk_home()
    if not jdk_home:
        print("ERROR: JDK not found. Run: python build.py -deps")
        sys.exit(1)
    if not os.path.isdir(SDK_DIR):
        print("ERROR: Android SDK not found. Run: python build.py -deps")
        sys.exit(1)

    env["JAVA_HOME"] = jdk_home
    env["ANDROID_HOME"] = SDK_DIR
    env["ANDROID_SDK_ROOT"] = SDK_DIR

    ext = ".exe" if IS_WIN else ""
    path_additions = [
        os.path.join(jdk_home, "bin"),
        os.path.join(SDK_DIR, "platform-tools"),
        os.path.join(SDK_DIR, "cmdline-tools", "latest", "bin"),
    ]
    env["PATH"] = PATH_SEP.join(path_additions) + PATH_SEP + env["PATH"]
    return env


def build_desktop():
    print()
    print("=== Building Desktop ===")
    go = check_go()
    wails = ensure_wails(go)
    os.chdir(SCRIPT_DIR)
    print("  go mod tidy...")
    run_cmd([go, "mod", "tidy"])
    print("  wails build...")
    run_cmd([wails, "build"])
    bin_dir = os.path.join(SCRIPT_DIR, "build", "bin")
    if os.path.isdir(bin_dir):
        for f in os.listdir(bin_dir):
            fp = os.path.join(bin_dir, f)
            if os.path.isfile(fp):
                print(f"  Binary: {fp}")
    print("=== Desktop build OK ===\n")


def build_android():
    print()
    print("=== Building Android APK ===")

    if not os.path.isdir(ANDROID_DIR):
        print("ERROR: for_android/ not found")
        sys.exit(1)

    env = get_android_env()

    go = check_go()
    gomobile = ensure_gomobile(go)

    os.chdir(ANDROID_DIR)
    print("[1/4] go mod tidy...")
    run_cmd([go, "mod", "tidy"], env=env)

    print("[2/4] Copying frontend to Android assets...")
    web_dir = os.path.join(ANDROID_DIR, "android", "ymusic", "app", "src", "main", "assets", "web")
    if os.path.isdir(web_dir):
        shutil.rmtree(web_dir)
    shutil.copytree(os.path.join(SCRIPT_DIR, "frontend"), web_dir)

    print("[3/4] gomobile bind...")
    aar_path = os.path.join(ANDROID_DIR, "android", "ymusic", "app", "libs", "ymobile.aar")
    os.makedirs(os.path.dirname(aar_path), exist_ok=True)
    run_cmd([gomobile, "bind", "-target=android", "-androidapi=24", "-o", aar_path, "ymusic/mobile"], env=env)

    print("[4/4] Gradle APK...")
    gradle_project = os.path.join(ANDROID_DIR, "android", "ymusic")
    gradlew = "gradlew.bat" if IS_WIN else "gradlew"
    gradlew_path = os.path.join(gradle_project, gradlew)
    if os.path.isfile(gradlew_path):
        if not IS_WIN:
            os.chmod(gradlew_path, 0o755)
        run_cmd([os.path.join(".", gradlew), "assembleRelease"], cwd=gradle_project, env=env)
    else:
        print(f"ERROR: {gradlew_path} not found")
        sys.exit(1)

    apk_path = os.path.join(gradle_project, "app", "build", "outputs", "apk", "release", "app-release.apk")
    if os.path.isfile(apk_path):
        size_mb = os.path.getsize(apk_path) / 1048576
        print(f"  APK: {apk_path} ({size_mb:.2f} MB)")
    print("=== Android build OK ===\n")


def help():
    print("YMusic Build Script")
    print()
    print("Usage: python build.py <argument>")
    print()
    print("Arguments:")
    print("  -deps       Download JDK 17, Android SDK, NDK, Go modules")
    print("  -Desktop    Build desktop app  (Wails, for Windows/Linux)")
    print("  -Android    Build Android APK  (requires for_android/ toolchain)")
    print("  -h, -help   Show this help")
    print()
    print("Run -deps first to set up the Android build toolchain.")


def main():
    args = [a.lower() for a in sys.argv[1:]]
    if not args or "-h" in args or "-help" in args:
        help()
        return
    if "-deps" in args:
        download_deps()
    elif "-desktop" in args:
        build_desktop()
    elif "-android" in args:
        build_android()
    else:
        print(f"Unknown argument: {sys.argv[1]}")
        help()
        sys.exit(1)


if __name__ == "__main__":
    main()
