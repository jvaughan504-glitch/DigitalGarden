# Digital Garden

An art project using a ESP32 and a bunnch of LEDs.

## Android controller

A companion Android app built with MIT App Inventor is available under [`app_inventor/`](app_inventor/). Run `python scripts/generate_appinventor_project.py` to produce `app_inventor/DigitalGardenController/DigitalGardenController.aia`, then import it into MIT App Inventor (or install the generated APK) to control the lamp over Bluetooth. The app exposes manual color toggles, effect mode buttons, and the same tunable sliders as the built-in web interface.
