[app]

# O'yin nomi va sozlamalari
title = Ilon O'yini
package.name = snakegame
package.domain = uz.ilon

# Kodlar joylashgan manzil
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

# Versiya
version = 1.0.0

# Kerakli kutubxonalar (Barqaror versiyalar majburlab qo'yildi)
requirements = python3,kivy==2.3.0,pillow

# Ekran sozlamalari
orientation = portrait
fullscreen = 0

# Android tizim sozlamalari (Litsenziya va barqaror NDK versiyalari)
android.api = 34
android.minapi = 24
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
