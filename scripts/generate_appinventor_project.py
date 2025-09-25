
import xml.etree.ElementTree as ET
from pathlib import Path
import zipfile

# Project structure
PROJECT_DIR = Path("app_inventor/DigitalGardenController")
SRC_DIR = PROJECT_DIR / "src" / "appinventor" / "ai_digitalgarden" / "DigitalGardenController"
ASSETS_DIR = PROJECT_DIR / "assets"
YOUNG_DIR = PROJECT_DIR / "youngandroidproject"

# -------------------------------------------------------------------
# Blockly/SCM builder functions
# -------------------------------------------------------------------

def text_literal(factory, value: str):
    block = ET.Element("block", type="text")
    field = ET.SubElement(block, "field", name="TEXT")
    field.text = value
    return block

def call_procedure(factory, name: str, args: list, values: list):
    block = ET.Element("block", type="procedures_callnoreturn")
    mutation = ET.SubElement(block, "mutation", name=name)
    for arg in args:
        ET.SubElement(mutation, "arg", name=arg)
    for arg, val in zip(args, values):
        value = ET.SubElement(block, "value", name=arg)
        value.append(val)
    return block

def lexical_get(factory, name: str, event_param=False):
    block = ET.Element("block", type="lexical_variable_get")
    field = ET.SubElement(block, "field", name="VAR")
    if event_param:
        field.set("eventparam", "true")
    field.text = name
    return block

def controls_if(factory, condition, then_block, else_block=None):
    block = ET.Element("block", type="controls_if")
    value = ET.SubElement(block, "value", name="IF0")
    value.append(condition)
    statement = ET.SubElement(block, "statement", name="DO0")
    statement.append(then_block)
    if else_block is not None:
        else_statement = ET.SubElement(block, "statement", name="ELSE")
        else_statement.append(else_block)
    return block

def component_event(factory, type_name, component, event_name, body, x=0, y=0):
    block = ET.Element("block",
        type="component_event",
        x=str(x),
        y=str(y))
    mutation = ET.SubElement(block, "mutation",
        component_type=type_name,
        component_id=component,
        event_name=event_name)
    statement = ET.SubElement(block, "statement", name="DO")
    statement.append(body)
    return block

def slider_event(factory, slider, label, key, base, delta, subtract, prefix, suffix, x=0, y=0):
    # When slider is moved, update label and send command
    block = ET.Element("block",
        type="component_event",
        x=str(x),
        y=str(y))
    mutation = ET.SubElement(block, "mutation",
        component_type="Slider",
        component_id=slider,
        event_name="PositionChanged")
    # Send command
    proc = call_procedure(factory, "SendCommand", ["cmd"],
        [text_literal(factory, f"{key} ")])
    # Append slider value
    append_val = lexical_get(factory, "thumbPosition", event_param=True)
    proc.find("value").append(append_val)
    statement = ET.SubElement(block, "statement", name="DO")
    statement.append(proc)
    return block

# -------------------------------------------------------------------
# Builders for SCM/BKY
# -------------------------------------------------------------------

def build_scm() -> str:
    return """#| Screen1.scm generated |#"""

def build_bky() -> str:
    root = ET.Element("xml")

    factory = None  # placeholder for uniform API

    # Example event: Disconnect button
    disconnect_first = call_procedure(factory, "SendCommand", ["cmd"], [text_literal(factory, "DISCONNECT")])
    disconnect_event = component_event(factory, "Button", "DisconnectButton", "Click", disconnect_first, x=40, y=420)
    root.append(disconnect_event)

    # Mode buttons
    modes = {
        "ManualButton": "MODE MANUAL",
        "ChaseButton": "MODE CHASE",
        "BlinkModeButton": "MODE BLINK",
        "FadeModeButton": "MODE FADE",
        "RainbowModeButton": "MODE RAINBOW",
    }
    offset = 640
    for name, command in modes.items():
        body = call_procedure(factory, "SendCommand", ["cmd"], [text_literal(factory, command)])
        event = component_event(factory, "Button", name, "Click", body, x=40, y=offset)
        root.append(event)
        offset += 120

    # CheckBox events
    colors = {
        "CheckBoxRed": ("RED ON", "RED OFF"),
        "CheckBoxGreen": ("GREEN ON", "GREEN OFF"),
        "CheckBoxBlue": ("BLUE ON", "BLUE OFF"),
        "CheckBoxWhite": ("WHITE ON", "WHITE OFF"),
    }
    offset = 40
    for name, (on_cmd, off_cmd) in colors.items():
        true_call = call_procedure(factory, "SendCommand", ["cmd"], [text_literal(factory, on_cmd)])
        false_call = call_procedure(factory, "SendCommand", ["cmd"], [text_literal(factory, off_cmd)])
        condition = lexical_get(factory, "value", event_param=True)
        body = controls_if(factory, condition, true_call, false_call)
        event = component_event(factory, "CheckBox", name, "Changed", body, x=600, y=offset)
        root.append(event)
        offset += 140

    # Slider events
    slider_specs = [
        ("BlinkSlider", "BlinkLabel", "BLINK", 2000, 1950, True, "Blink Interval: ", " ms"),
        ("ChaseSlider", "ChaseLabel", "CHASE", 2000, 1950, True, "Chase Interval: ", " ms"),
        ("FadeSlider", "FadeLabel", "FADE", 1, 19, False, "Fade Step: ", ""),
        ("RainbowSlider", "RainbowLabel", "RAINBOW", 200, 190, True, "Rainbow Speed: ", " ms"),
        ("TwinkleSlider", "TwinkleLabel", "TWINKLE", 1, 99, False, "Twinkle Speed: ", ""),
    ]
    offset = 40
    for slider, label, key, base, delta, subtract, prefix, suffix in slider_specs:
        event = slider_event(factory, slider, label, key, base, delta, subtract, prefix, suffix, x=900, y=offset)
        root.append(event)
        offset += 200

    return ET.tostring(root, encoding="utf-8").decode("utf-8")

def project_properties() -> str:
    return "\n".join([
        "main=appinventor.ai_digitalgarden.DigitalGardenController.Screen1",
        "name=DigitalGardenController",
        "assets=../assets",
        "source=../src",
        "build=../build",
        "versioncode=1",
        "versionname=1.0",
        "useslocation=False",
        "aname=DigitalGardenController",
        "sizing=Responsive",
        "showlistsasjson=True",
        "actionbar=True",
        "theme=AppTheme.Light.DarkActionBar",
        "color.primary=&HFF2196F3",
        "color.primary.dark=&HFF1565C0",
        "color.accent=&HFFFFC107",
    ]) + "\n"

# -------------------------------------------------------------------
# Main write function
# -------------------------------------------------------------------

def write_files():
    scm_text = build_scm()
    bky_text = build_bky()
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    YOUNG_DIR.mkdir(parents=True, exist_ok=True)

    (SRC_DIR / "Screen1.scm").write_text(scm_text)
    (SRC_DIR / "Screen1.bky").write_text(bky_text)
    (ASSETS_DIR / ".nomedia").write_text("")
    (YOUNG_DIR / "project.properties").write_text(project_properties())

    aia_path = PROJECT_DIR / "DigitalGardenController.aia"
    with zipfile.ZipFile(aia_path, "w") as zf:
        for path in sorted(PROJECT_DIR.rglob("*")):
            if path.is_file() and path.name != aia_path.name:
                arcname = path.relative_to(PROJECT_DIR)
                zf.write(path, arcname)

# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------

def main():
    write_files()

if __name__ == "__main__":
    main()
