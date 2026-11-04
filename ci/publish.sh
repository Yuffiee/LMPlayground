#!/bin/sh
# Publish the built release APK to the `apk-out` branch so it can be downloaded.
set -e

APK=$(ls app/build/outputs/apk/release/app-arm64-v8a-release.apk 2>/dev/null || true)
if [ -z "$APK" ]; then
  APK=$(ls app/build/outputs/apk/release/*.apk 2>/dev/null | head -1)
fi
if [ -z "$APK" ]; then
  echo "no apk produced" >&2
  exit 1
fi

SIZE_MB=$(du -m "$APK" | cut -f1)
echo "publishing $APK (${SIZE_MB} MB)"

git config user.email "ci@example.invalid"
git config user.name "ci"
git checkout -B apk-out
mkdir -p ci-out
cp "$APK" ci-out/lmplayground.apk
rm -f CI-TEST.txt
git add -f ci-out/lmplayground.apk
git commit -m "ci: apk $(date -u +%Y%m%d-%H%M)"
git push -f origin apk-out
echo "pushed to apk-out"
