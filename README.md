<br/>
<div align="center">
<a href="https://github.com/https://github.com/com-name-here/megalauncher">
<img src="https://github.com/com-name-here/megalauncher/blob/main/icon.png" alt="Logo" width="80" height="80">
</a>
<h3 align="center">MegaLauncher</h3>
<p align="center">
A basic GUI for launching and updating MegaAntiCheat, made with Qt.
<br/>
</p>
</div>

## Installation

### Windows
_Not yet available due to the whole application being stopped when trying to stop MAC._ If you're fine with this, try building it yourself.

### Linux
- For more recent distros (Arch, Fedora 40, etc.) and theming on KDE, download the standard [MegaLauncher](https://github.com/com-name-here/megalauncher/releases/download/v0.1.0/MegaLauncher) binary. _(Built on Arch Linux)_
- For distros with a glibc version older than 2.39, download [MegaLauncher-compat](https://github.com/com-name-here/megalauncher/releases/download/v0.1.0/MegaLauncher-compat) instead. _(Built on Ubuntu 22.04)_

## Building
If no release binary works for you, try building manually instead:

### Downloading The Code
- Either clone the repo with git:
```sh
git clone https://github.com/com-name-here/megalauncher.git
```
- Or download an archive [directly](https://github.com/com-name-here/megalauncher/archive/refs/heads/main.zip)

### Windows
1. Install [Python 3.12](https://python.org). **Make sure to add it to PATH in the installer!**
2. Install requirements (Replace `path\to\` with actual path)
```sh
pip install -r path\to\requirements.txt
```
3. Build the executable with PyInstaller (Replace `path\to\` with actual path)
```sh
pyinstaller --name="MegaLauncher" --windowed --onefile --icon=path\to\icon.ico path\to\main.py
```

4. Profit! (You'll find the executable in a folder called `dist`, which is located in the folder you ran the command from. You should probably look in your user folder.)

### Linux
1. Install Python 3.12 from your distro's package manager
2. Install requirements (Replace `path/to/` with actual path)
```sh
pip install -r path/to/requirements.txt
```
3. Build the executable with PyInstaller (Replace `path/to/` with actual path)
```sh
pyinstaller --name="MegaLauncher" --windowed --onefile path/to/main.py
```

4. And we're done! (Hopefully)
