# Installation

## Setup:

1. Create ssd image with Raspberry Pi Imager
1. put `ssd` file into boot partition
1. put `wpa_supplicant.conf` from this project into boot partition 

## Connect

1. Boot up PI
1. Connect as pi@ip and `raspberry` as password
1. setup camera:
    1. `sudo raspi-config`
    1. Interface options 
    1. camera -> on
    1. reboot `sudo reboot`
    1. test: `raspistill -v -o test.jpg && python3 -m http.server 8080`
    1. access url and see image, e.g. <http://192.168.178.60:8080/test.jpg>
1. Create app folder:

```sh
sudo mkdir /opt/app
sudo chown pi /opt/app
```

1. Copy code from this folder to the remote folder, e.g. via VS code ssh

1. make python3 default:
see https://raspberry-valley.azurewebsites.net/Python-Default-Version/
```sh
sudo update-alternatives --list python
sudo update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.7 2
python --version
```

1. install necessary libs:
```sh
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
cd /opt/app
export POETRY_VIRTUALENVS_CREATE="false"
source $HOME/.poetry/env
poetry install --no-dev --no-root

```

1. setup tesseract:
we need 4.1.x  not 4.0.0
See https://notesalexp.org/tesseract-ocr/
additionally
```sh
sudo apt-get install tesseract-ocr-eng
or if this does not work:
cd /usr/share/tesseract-ocr/5/tessdata
sudo wget https://github.com/tesseract-ocr/tessdata/raw/master/eng.traineddata
```

1. TODO setup code and autostart 
1. todo fix scipy? e.g. see https://stackoverflow.com/questions/59994060/cant-install-scipy-to-raspberry-pi-4-raspbian
1. todo tesseract install


For RavenDb:
1. Async?
1. tutorial should probably include @dataclass
1. Error message weird if no hashable object
1. Type the public api
1. Especially the cert param, add that to docs, too