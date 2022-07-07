# Raspberry Pi LED Matrix (BETA)

This is a collection of examples and an API wrapper to simplify driving a LED matrix of any size created with WS2812B LED strips.  To tinker locally without a LED matrix, the library will detect you are not in the live environment and render the matrix in a window on your local machine.
### Virtual Environment Example
https://user-images.githubusercontent.com/1588877/177685586-e4cb158d-c840-4b89-855e-5bfd087991b5.mp4


### Live LED Matrix Example
https://user-images.githubusercontent.com/1588877/177685583-cab5ac70-1f26-48f9-ab31-55bf0a61bf8d.mp4

## Virtual environment quick start

```bash
git clone git@github.com:natelewis/pi-led-matrix-playground.git
cd pi-led-matrix-playground
pip3 install opencv-python
pip3 install -U numpy
python3 test.py
# Red, blue, green... in a tiny 60x30 window
```

## Hardware

Here is the high level construction details of a LED matrix panel.

Shopping List:

* WS2812B LED strips
* 5V power supply
* Raspberry Pi 4
* Extra 3 pin wire @ 22AWG
* A few Male/Female JST SM 3 Pin Connectors to create an extension cable from where your panel is to your Pi/PSU
* Curtain rod
* Hobby wood/bamboo @ 3/8" wide to stick on the back of the LED strips to keep them straight
* A bit of patience -- Takes about 4-5 hours to put it all together

In this example I built a 60x30 array with 5V 300W 60A power supply:

1. Collect a 60 count of 30 LED per meter 1M strips
2. Build the matrix in a chain pattern:

```text
_   _   _   _ ...
 | | | | | |
 | | | | | |
 | | | | | |
 | | | | | |
 | | | | | |
 |_| |_| |_|
```

1. Attach power to every other strip in parallel

2. Connect GPIO 18 of the RPi4 to the green LED wire

3. Connect GND pin of the RPi4 to COM of the power supply

4. Hang the LED strips to the curtain rod with your adhesive of choice

5. Stick the wood to the back of the strips to keep them from bending around


## Raspberry Pi setup

1. Install RPi OS 32 bit

2. Get your Pi on your network, running headless and pull down this repo

3. Execute the following to globally install libraries and dependencies:

```bash
sudo apt update # you probably already did this
sudo apt install -y ffmpeg libatlas-base-dev

# libraries that are needed to communicate with the LED strips that Adafruit wrote for us
sudo pip3 install --upgrade adafruit-python-shell opencv-python rpi_ws281x adafruit-circuitpython-neopixel numpy adafruit_pixel_framebuf
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sudo python3 raspi-blinka.py
```

4. Update the `config.py` to adjust sizes if anything is different.

## Testing your LED matrix

Running the test script will cycle between R..., G..., B... (repeat)

```bash
./run.sh rgb_test
```

## Turning of your LEDs

LEDs will maintain their currently lit state when you cancel your script.  You can use the off effect to turn them off:

```bash
./run.sh off
```

## Effects

Custom effects are organized in the `effects` directory with the following structure:

```text
> effects > effect_name > effects.py
```

The effects.py have a `run()` function that will be executed by the `run.sh` script.

[View the effects list and usage details](effects/README.md)
# API

When emulating the LED array locally, it detects you do not have any of the adafruit modules installed and fails over to virtual mode.  To synchronously pause your event loop when animating use the `matrix.delay()` function.  This will ensure your rendering window stays open while waiting.

If you want use this outside of the effects directory import the `Matrix` class.

```python
from led_matrix import Matrix
matrix = Matrix()
```

If you building inside an [effect](effects/README.md) this is already been done for you and passed to your `run()` function.

```python
while True:
    matrix.fill(0,0,0) # black background
    matrix.show()
    matrix.delay(1000)
    matrix.line((0, 0), (60, 30), (255, 0, 0),  1) # diagonal red line
    matrix.show()
    matrix.delay(1000)
    matrix.rectangle((5, 5), (55, 25), (0, 255, 0),  1) # green rectangle
    matrix.show()
    matrix.delay(1000)
    matrix.circle((30, 15), 10, (0, 0, 255),  2) # blue circle
    matrix.show()
    matrix.delay(1000)

```

`matrix.circle((x,y), radius, (r, g, b), width)`

---

Draw a circle from its center point with a given radius.  A width of `-1` will fill in the circle.
```python
matrix.circle((30, 15), 10, (0, 0, 255),  3) # blue circle
matrix.show()
matrix.delay(5000)
```

<br/>

`matrix.delay(ms)`

---

Sleep x amount of milliseconds.

```python
matrix.delay(1000) # 1 second
matrix.delay(1000 * 60) # 1 minute
```

<br/>

`matrix.fill(r, g, b)`

---

Fill all the pixels with the RGB values given.

```python
matrix.fill(255, 0 , 0) # all LEDs red
matrix.show()
matrix.delay(5000)
matrix.fill(0, 0, 0) # turn off all LEDs
matrix.show()
```

<br/>

`matrix.image(Image)`

---

Display an image using the Python Imaging Library (PIL).

```python
from PIL import Image
image = Image.open(image_file)
matrix.image(image)
matrix.show()
matrix.delay(5000)
```

<br/>

`matrix.line((x,y), (x,y), (r, g, b), width)`

---

Draw a line from the start to then end coordinates.

```python
matrix.line((0, 0), (60, 30), (255, 0, 0),  1) # diagonal red line
matrix.show()
matrix.delay(5000)
```

<br/>

`matrix.pixel((x,y), (r, g, b), width)`

---

Draw a line from the start to then end coordinates.

```python
matrix.line((30, 15), (255, 0, 0),  1) # diagonal red line
matrix.show()
matrix.delay(5000)
```

<br/>

`matrix.rectangle((x,y), (x,y), (r, g, b), width)`

---

Draw a rectangle from the start to then end coordinates.

```python
matrix.rectangle((5, 5), (55, 25), (255, 0, 0),  1) # red rectangle
matrix.show()
matrix.delay(5000)
```

<br/>

`matrix.show()`

---

Paint the current image to the LEDs

```python
matrix.fill(0, 0, 255)
matrix.show() # turn all LEDs blue
matrix.delay(1000)
matrix.fill(0, 0, 0)
matrix.show() # turn off all LEDs

```

<br/>

`matrix.text(self, text, start, scale, color, thickness)`

---

Place text at the given location. ( font selection is currently disabled )

```python
matrix.text('hello', (10,20), 1, (255,0,0), 1)
matrix.show()
matrix.delay(5000)
```

<br/>

## Contributing

Checkout [CONTRIBUTING.md](CONTRIBUTING.md)

---

Created by [@natelewis](https://github.com/natelewis). Released under the MIT license.
