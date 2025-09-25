# Digital Garden Android Controller (MIT App Inventor)

This directory contains an MIT App Inventor project that exposes the same commands handled by the `DigitalGarden.ino` firmware. Run `python scripts/generate_appinventor_project.py` from the repository root to build `app_inventor/DigitalGardenController/DigitalGardenController.aia`, then import the archive into [MIT App Inventor](https://ai2.appinventor.mit.edu/) to build or modify the Android companion app.

## Features

* **Bluetooth connection manager** – tap **Connect** to see nearby Bluetooth Classic devices and choose the `WIFILampV1` ESP32 controller. A notifier confirms success or failure and the status label is updated. Use **Disconnect** to close the connection and reset the manual color toggles.
* **Manual color toggles** – four checkboxes send the `RED/GREEN/BLUE/WHITE ON|OFF` commands expected by the sketch.
* **Mode shortcuts** – buttons issue `MODE MANUAL`, `MODE CHASE`, `MODE BLINK`, `MODE FADE`, and `MODE RAINBOW` commands.
* **Effect sliders** – each slider performs the same mapping as the built-in web UI:
  * Blink & chase: 0→2000 ms, 100→50 ms.
  * Fade step: 0→1, 100→20.
  * Rainbow speed: 0→200 ms, 100→10 ms.
  * Twinkle speed: 0→1, 100→100.
  The label beside each slider reflects the value that will be sent (using `SET <KEY> <value>` commands).

The app automatically appends a newline to each command so it is compatible with `SerialBT.readStringUntil('\n')` in the firmware.

## Building and regenerating

* **Edit / inspect** – once you generate and import the `.aia`, you can tweak the layout or logic in the MIT App Inventor designer/blocks editor.
* **Regenerate from source** – the checked-in `Screen1.scm` and `Screen1.bky` files, along with `scripts/generate_appinventor_project.py`, can recreate the project. Run the script from the repository root:

  ```bash
  python scripts/generate_appinventor_project.py
  ```

  The script refreshes the deterministic project metadata (such as `.nomedia` and `project.properties`) and places a fresh `DigitalGardenController.aia` alongside the sources (the binary is .gitignored so regenerate it whenever needed).

## Using the app

1. Flash `DigitalGarden.ino` to the ESP32 and reboot it so the Bluetooth name `WIFILampV1` is advertised.
2. Import the `.aia` into MIT App Inventor, build the APK or use the companion, and install the app on your Android device.
3. Open the app, tap **Connect**, and choose `WIFILampV1` from the picker. The status label will confirm the connection.
4. Use the color toggles, mode buttons, and sliders to drive the LEDs in real time.

If you adjust slider ranges or add new commands in the firmware, update the corresponding logic in `scripts/generate_appinventor_project.py` and regenerate the project.
