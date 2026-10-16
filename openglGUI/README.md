# Necessary Installs
on linux run
```bash
sudo apt install libfreetype-dev libassimp-dev libx11-dev build-essential libxi-dev libxrandr-dev zlib1g-dev libbz2-dev libpng-dev libbrotli-dev python3-dev g++
```
To install qt
```bash
curl -OL https://download.qt.io/official_releases/online_installers/qt-online-installer-linux-x64-online.run
chmod +x qt-online-installer-linux-x64-online.run
./qt-online-installer-linux-x64-online.run --accept-licenses --default-answer --confirm-command install qt6.12.0-sdk
```
