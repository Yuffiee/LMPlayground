import pathlib, sys

p = pathlib.Path("app/build.gradle.kts")
s = p.read_text()

def sub(old, new, label):
    global s
    assert old in s, f"anchor not found: {label}"
    s = s.replace(old, new, 1)
    print(f"patched: {label}")

# 1. Always sign with the bundled debug.keystore — CI has no release secrets.
sub(
    '''        named("debug") {
            storeFile = if (hasKeyInfo) userKeystore else localKeystore
            storePassword = if (hasKeyInfo) System.getenv("STORE_PASSWORD") else "android"
            keyAlias = if (hasKeyInfo) System.getenv("LM_PLAYGROUND_KEY_ALIAS") else "androiddebugkey"
            keyPassword = if (hasKeyInfo) System.getenv("LM_PLAYGROUND_KEY_PASSWORD") else "android"
        }''',
    '''        named("debug") {
            storeFile = localKeystore
            storePassword = "android"
            keyAlias = "androiddebugkey"
            keyPassword = "android"
        }''',
    "signing uses bundled keystore",
)

# 2. arm64 only — halves native compile time and APK size.
sub('abiFilters += setOf("arm64-v8a", "x86_64")', 'abiFilters += setOf("arm64-v8a")', "abiFilters arm64")
sub('include("arm64-v8a", "x86_64")', 'include("arm64-v8a")', "splits arm64")

# 3. Drop the native symbol table — it bloats the APK; we only want to install it.
sub(
    '''            ndk {
                debugSymbolLevel = "SYMBOL_TABLE"
            }''',
    '''            // debugSymbolLevel removed for the sideload build (APK size)''',
    "no debug symbols",
)

# 4. Attach the APK publisher to the CI build command.
s += '''
// --- sideload build: expose the release APK on the `apk-out` branch ---
tasks.register<Exec>("publishApkToBranch") {
    dependsOn("assembleRelease")
    workingDir = rootProject.projectDir
    commandLine("sh", "ci/publish.sh")
}

tasks.named("bundleRelease") {
    finalizedBy("publishApkToBranch")
}
'''
p.write_text(s)
print("build.gradle.kts patched")
