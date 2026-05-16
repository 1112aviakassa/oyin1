# Ilon o'yini — Android APK uchun Buildozer sozlamalari
# Qurish (Linux / WSL2): buildozer android debug

[app]

title = Ilon O'yini
package.name = snakegame
package.domain = uz.ilon

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.0.0

# Faqat Kivy — internet ruxsati shart emas
requirements = python3,kivy

# Ikonka qo'shsangiz, quyidagi qatorlarni oching:
# icon.filename = %(source.dir)s/assets/icon.png
# presplash.filename = %(source.dir)s/assets/presplash.png

orientation = portrait
fullscreen = 0

# O'yin foniga mos (main.py dagi to'q fon)
android.presplash_color = #121724

#
# Android
#

# Qo'shimcha ruxsatlar kerak emas (offline o'yin)
# android.permissions =

android.api = 34
android.minapi = 24

android.archs = arm64-v8a, armeabi-v7a

# Play Store uchun keyin: buildozer android release
# android.release_artifact = aab

[buildozer]

log_level = 2
warn_on_root = 1
