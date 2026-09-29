#!/bin/sh
# Runs only inside converter_build.py's isolated userspace, without networking.
set -eu
cd /build
export PDF2HTMLEX_VERSION=0.18.8.rc2-tagger-cb7806a
ln -sfn /build/poppler /build/pdf2htmlEX/poppler
ln -sfn /build/fontforge /build/pdf2htmlEX/fontforge
cmake -S poppler -B poppler/build -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=/usr/local -DBUILD_SHARED_LIBS=OFF \
  -DENABLE_UNSTABLE_API_ABI_HEADERS=ON -DENABLE_LIBOPENJPEG=openjpeg2 \
  -DENABLE_DCTDECODER=libjpeg -DENABLE_CMS=lcms2 -DENABLE_LIBCURL=OFF \
  -DENABLE_GPGME=OFF -DENABLE_NSS3=OFF -DENABLE_QT5=OFF -DENABLE_QT6=OFF \
  -DENABLE_BOOST=OFF -DENABLE_LIBTIFF=OFF -DENABLE_CPP=OFF -DENABLE_GLIB=ON -DENABLE_GOBJECT_INTROSPECTION=OFF \
  -DENABLE_UTILS=OFF -DBUILD_GTK_TESTS=OFF -DBUILD_QT5_TESTS=OFF \
  -DBUILD_QT6_TESTS=OFF -DBUILD_CPP_TESTS=OFF -DBUILD_MANUAL_TESTS=OFF
cmake --build poppler/build --parallel 4
cmake --install poppler/build
cmake -S fontforge -B fontforge/build -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=/usr/local -DBUILD_SHARED_LIBS=OFF \
  -DENABLE_GUI=OFF -DENABLE_X11=OFF -DENABLE_NATIVE_SCRIPTING=ON \
  -DENABLE_PYTHON_SCRIPTING=OFF -DENABLE_PYTHON_EXTENSION=OFF \
  -DENABLE_LIBSPIRO=OFF -DENABLE_LIBUNINAMESLIST=OFF -DENABLE_LIBGIF=OFF \
  -DENABLE_LIBJPEG=ON -DENABLE_LIBPNG=ON -DENABLE_LIBREADLINE=OFF \
  -DENABLE_LIBTIFF=OFF -DENABLE_WOFF2=OFF -DENABLE_DOCS=OFF \
  -DENABLE_FONTFORGE_EXTRAS=OFF -DSPHINX_USE_VENV=OFF
cmake --build fontforge/build --parallel 4
cmake --install fontforge/build
make -C poppler-data install prefix=/usr/local datadir=/usr/local/share/pdf2htmlEX
cmake -S pdf2htmlEX/pdf2htmlEX -B pdf2htmlEX/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local -DCMAKE_CXX_STANDARD_LIBRARIES=-llcms2 -DCMAKE_C_FLAGS="$(pkg-config --cflags gio-2.0)"
cmake --build pdf2htmlEX/build --parallel 4
cmake --install pdf2htmlEX/build
dpkg-query -W -f='${binary:Package}\t${Version}\n' > /build/installed-packages.tsv
/usr/local/bin/pdf2htmlEX -v
