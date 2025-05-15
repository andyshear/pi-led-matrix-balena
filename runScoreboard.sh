# only supports mac/linux and pi
ENV_TYPE=$(uname -m)
if [ $ENV_TYPE = "armv7l" ] || [ $ENV_TYPE = "armv6l" ]; then
    echo Running on Raspberry Pi
    sudo python3 /pi-led-matrix-balena/load_effect2.py "$@"
else
    echo Running on $ENV_TYPE
    python3 /pi-led-matrix-balena/load_effect2.py "$@"
fi
