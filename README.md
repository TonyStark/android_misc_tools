system.img
=
Adapted from: http://forum.xda-developers.com/showthread.php?t=2501219

The following sections outline the necessary steps to build a Moto X (ghost) SafeStrap compatible OTA from a carrier OTA

System image mounting as a loopback under linux
==

1. dd if=system.img of=simg bs=131072 skip=1  # Strip the custom Motorola header from the image
1. simg2img.py simg raw.img # Convert from sparse filesystem to full filesystem
1. mount -o loop raw.img /mnt/system.img # Mount the image as a loopback

Patching files
==

1. Build imgdiff/imgpatch/bsdiff/bspatch from aosp/bootable/recovery/applypatch
1. Install sha1sum
1. Run process_updater-script.py with the necessary arguments. NOTE: This is a Python 3 application, it will NOT run under Python 2

Building diff/patch apps
=
You really don't want to do this.  Use the pre-compiled packages in this repo

1. Install libbz2-dev, libbz2-1.0, zlib-dev packages
1. Copy libmincrypt, mincrypt, minelf, mtdutils from bootable/recovery and system/core to the local source dir
1. Compile applypatch: gcc -lbz2 -lz -o imgpatch utils.c imgpatch.c bsdiff.c libmincrypt/sha.c libmincrypt/sha256.c libmincrypt/rsa.c minelf/Retouch.c edify/expr.c applypatch.c mtdutils/mtdutils.c freecache.c bspatch.c main.c
1. 


Misc Notes
=

Suggested folder layout
==
xxx_sbf
xx_img
logs
ota
tools

updater-script Commands
==

* apply_patch_check(File to patch, Patched file sha1sum, Pre-patched file sha1sum) 
* apply_patch(original file path relative to booted android root, 
       ??? likely non-patched file size,
       patched file sha1sum, 
       patched file size,
       original file sha1sum, 
       patch path relative to ota root);

imagepatch Usage
==
applypatch source_file target_file target_sha1 target_size source_file_sha1:patch_file
Example: ./tools_notes/applypatch/applypatch ./44_repack/system/app/Books.apk ./44_repack/system/app/Books.apk aec0e4c42c51d2bc7860f018245bed5325cb53cb 5519762 a03d64e4db2a1ffa9eb5e9d53716f06c47984134:./patch/system/app/Books.apk.p
