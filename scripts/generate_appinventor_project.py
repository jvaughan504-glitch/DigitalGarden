
#!/usr/bin/env python3
"""Package the MIT App Inventor project into an AIA archive.

This helper rewrites the small bits of metadata that are deterministic and then
zips the checked-in source tree under ``app_inventor/DigitalGardenController``.
The generated ``DigitalGardenController.aia`` can be imported directly into MIT
App Inventor.  Running the script repeatedly is safe.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
import zipfile

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = REPO_ROOT / "app_inventor" / "DigitalGardenController"
SRC_DIR = PROJECT_DIR / "src" / "appinventor" / "ai_digitalgarden" / "DigitalGardenController"
ASSETS_DIR = PROJECT_DIR / "assets"
YOUNG_DIR = PROJECT_DIR / "youngandroidproject"
AIA_PATH = PROJECT_DIR / "DigitalGardenController.aia"

REQUIRED_FILES = (
    SRC_DIR / "Screen1.scm",
    SRC_DIR / "Screen1.bky",
)

PROJECT_PROPERTIES = """main=appinventor.ai_digitalgarden.DigitalGardenController.Screen1
name=DigitalGardenController
assets=../assets
source=../src
build=../build
versioncode=1
versionname=1.0
useslocation=False
aname=DigitalGardenController
sizing=Responsive
showlistsasjson=True
actionbar=True
theme=AppTheme.Light.DarkActionBar
color.primary=&HFF2196F3
color.primary.dark=&HFF1565C0
color.accent=&HFFFFC107
"""


class ConflictError(RuntimeError):
    """Raised when Git reports unresolved merge conflicts."""


def ensure_required_files() -> None:
    missing = [str(path) for path in REQUIRED_FILES if not path.exists()]
    if missing:
        missing_text = "\n".join(f"  - {item}" for item in missing)
        raise FileNotFoundError(
            "The MIT App Inventor sources are incomplete. Make sure the following files exist:\n"
            f"{missing_text}\n"
            "If they were deleted, restore them with `git checkout -- app_inventor`."
        )


def list_git_conflicts() -> list[Path]:
    """Return the set of files that Git still considers conflicted."""

    try:
        result = subprocess.run(
            ["git", "ls-files", "-u"],
            check=True,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - defensive
        raise RuntimeError("Failed to query git for conflicts") from exc

    conflicts = set()
    for line in result.stdout.splitlines():
        # The format is: <mode> <hash> <stage>\t<path>
        try:
            _metadata, path_str = line.split("\t", 1)
        except ValueError:  # pragma: no cover - defensive
            continue
        conflicts.add(REPO_ROOT / path_str)

    return sorted(conflicts)


def ensure_no_conflicts() -> None:
    conflicts = [path for path in list_git_conflicts() if path != AIA_PATH]
    if conflicts:
        file_list = "\n".join(f"  - {path.relative_to(REPO_ROOT)}" for path in conflicts)
        raise ConflictError(
            "Resolve the Git merge conflicts below before packaging the MIT App Inventor project:\n"
            f"{file_list}\n"
            "Open each file, remove the `<<<<<<<`, `=======`, and `>>>>>>>` markers, choose the correct blocks of text, then run:\n"
            "  git add <each resolved file>\n"
            "  python scripts/generate_appinventor_project.py\n"
            "Once the helper succeeds you can commit and continue your merge or rebase."
        )


def ensure_assets() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / ".nomedia").write_text("")


def ensure_project_properties() -> None:
    YOUNG_DIR.mkdir(parents=True, exist_ok=True)
    (YOUNG_DIR / "project.properties").write_text(PROJECT_PROPERTIES)


def write_aia() -> None:
    with zipfile.ZipFile(AIA_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PROJECT_DIR.rglob("*")):
            if path.is_file() and path != AIA_PATH:
                archive.write(path, path.relative_to(PROJECT_DIR))


def main() -> None:
    ensure_required_files()
    ensure_no_conflicts()
    ensure_assets()
    ensure_project_properties()
    write_aia()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate the MIT App Inventor project files for the Digital Garden controller."""


import json
import xml.etree.ElementTree as ET
from pathlib import Path
import zipfile

PROJECT_DIR = Path('app_inventor/DigitalGardenController')
SRC_DIR = PROJECT_DIR / 'src/appinventor/ai_digitalgarden/DigitalGardenController'
ASSETS_DIR = PROJECT_DIR / 'assets'
YOUNG_DIR = PROJECT_DIR / 'youngandroidproject'

SLIDER_DEFAULT = 50

class ComponentBuilder:
    """Helper for building the Screen1.scm component tree."""

    def __init__(self):
        self._uuid = 1000

    def _next_uuid(self) -> str:
        self._uuid += 1
        return str(self._uuid)

    def component(self, name: str, type_: str, version: int, props: dict | None = None, children: list | None = None) -> dict:
        data: dict[str, object] = {
            '$Name': name,
            '$Type': type_,
            '$Version': str(version),
            'Uuid': self._next_uuid(),
        }
        if props:
            for key, value in props.items():
                data[key] = str(value)
        if children:
            data['$Components'] = children
        return data


def build_scm() -> str:
    builder = ComponentBuilder()

    def slider_block(name: str, label_text: str) -> list[dict]:
        label = builder.component(f'{name}Label', 'Label', 5, {'Text': label_text})
        slider = builder.component(name, 'Slider', 3, {
            'MaxValue': '100',
            'MinValue': '0',
            'ThumbPosition': str(SLIDER_DEFAULT),
            'Width': '-2'
        })
        layout = builder.component(f'{name}Layout', 'VerticalArrangement', 4, {'Width': '-2'}, [label, slider])
        return layout

    blink_default = round(2000 - (1950 * SLIDER_DEFAULT) / 100)
    chase_default = round(2000 - (1950 * SLIDER_DEFAULT) / 100)
    fade_default = round(1 + (19 * SLIDER_DEFAULT) / 100)
    rainbow_default = round(200 - (190 * SLIDER_DEFAULT) / 100)
    twinkle_default = round(1 + (99 * SLIDER_DEFAULT) / 100)

    title = builder.component('TitleLabel', 'Label', 5, {
        'Text': 'Digital Garden Controller',
        'FontSize': '20',
        'TextAlignment': '1'
    })

    connect_picker = builder.component('ConnectPicker', 'ListPicker', 9, {
        'Text': 'Connect',
        'Width': '-2'
    })
    disconnect_button = builder.component('DisconnectButton', 'Button', 7, {
        'Text': 'Disconnect',
        'Width': '-2'
    })
    connection_row = builder.component('ConnectionRow', 'HorizontalArrangement', 4, {
        'AlignHorizontal': '3',
        'Width': '-2'
    }, [connect_picker, disconnect_button])

    status_label = builder.component('StatusLabel', 'Label', 5, {
        'Text': 'Not connected',
        'Width': '-2'
    })

    mode_label = builder.component('ModeLabel', 'Label', 5, {'Text': 'Modes', 'FontBold': 'True'})
    manual_button = builder.component('ManualButton', 'Button', 7, {'Text': 'Manual'})
    chase_button = builder.component('ChaseButton', 'Button', 7, {'Text': 'Chase'})
    mode_row1 = builder.component('ModeRow1', 'HorizontalArrangement', 4, {'Width': '-2'}, [manual_button, chase_button])

    blink_button = builder.component('BlinkModeButton', 'Button', 7, {'Text': 'Blink'})
    fade_button = builder.component('FadeModeButton', 'Button', 7, {'Text': 'Fade'})
    mode_row2 = builder.component('ModeRow2', 'HorizontalArrangement', 4, {'Width': '-2'}, [blink_button, fade_button])

    rainbow_button = builder.component('RainbowModeButton', 'Button', 7, {'Text': 'Rainbow'})
    mode_row3 = builder.component('ModeRow3', 'HorizontalArrangement', 4, {'Width': '-2'}, [rainbow_button])

    manual_label = builder.component('ManualLabel', 'Label', 5, {'Text': 'Manual Colors', 'FontBold': 'True'})

    color_layout = builder.component('ColorLayout', 'VerticalArrangement', 4, {'Width': '-2'}, [
        builder.component('CheckBoxRed', 'CheckBox', 2, {'Text': 'Red', 'Checked': 'False'}),
        builder.component('CheckBoxGreen', 'CheckBox', 2, {'Text': 'Green', 'Checked': 'False'}),
        builder.component('CheckBoxBlue', 'CheckBox', 2, {'Text': 'Blue', 'Checked': 'False'}),
        builder.component('CheckBoxWhite', 'CheckBox', 2, {'Text': 'White', 'Checked': 'False'})
    ])

    settings_label = builder.component('SettingsLabel', 'Label', 5, {'Text': 'Effect Settings', 'FontBold': 'True'})

    blink_layout = slider_block('BlinkSlider', f'Blink Interval: {blink_default} ms')
    chase_layout = slider_block('ChaseSlider', f'Chase Interval: {chase_default} ms')
    fade_layout = slider_block('FadeSlider', f'Fade Step: {fade_default}')
    rainbow_layout = slider_block('RainbowSlider', f'Rainbow Speed: {rainbow_default} ms')
    twinkle_layout = slider_block('TwinkleSlider', f'Twinkle Speed: {twinkle_default}')

    main_layout = builder.component('MainLayout', 'VerticalArrangement', 4, {
        'AlignHorizontal': '3',
        'Width': '-2'
    }, [
        title,
        connection_row,
        status_label,
        mode_label,
        mode_row1,
        mode_row2,
        mode_row3,
        manual_label,
        color_layout,
        settings_label,
        blink_layout,
        chase_layout,
        fade_layout,
        rainbow_layout,
        twinkle_layout
    ])

    notifier = builder.component('Notifier1', 'Notifier', 6)
    bluetooth = builder.component('BluetoothClient1', 'BluetoothClient', 8, {'Enabled': 'True'})

    properties = {
        '$Name': 'Screen1',
        '$Type': 'Form',
        '$Version': '31',
        'AppName': 'DigitalGardenController',
        'Title': 'Digital Garden Controller',
        'Scrollable': 'True',
        'Sizing': 'Responsive',
        'Theme': 'AppTheme.Light.DarkActionBar',
        'ShowListsAsJson': 'True',
        'Uuid': '0',
        '$Components': [main_layout, notifier, bluetooth]
    }

    scm_obj = {
        'authURL': ['*UNKNOWN*', 'digitalgarden'],
        'YaVersion': '213',
        'Source': 'Form',
        'Properties': properties
    }

    return "#|\n$JSON\n" + json.dumps(scm_obj, separators=(',', ':')) + "\n|#"


class BlockFactory:
    def __init__(self):
        self.counter = 0

    def new_block(self, type_: str, **attrs) -> ET.Element:
        block = ET.Element('block')
        block.set('type', type_)
        self.counter += 1
        block.set('id', attrs.pop('id', f"b{self.counter}"))
        for key, value in attrs.items():
            block.set(key, str(value))
        return block


def mutation(parent: ET.Element, **attrs) -> ET.Element:
    m = ET.SubElement(parent, 'mutation')
    for key, value in attrs.items():
        m.set(key, str(value))
    return m


def field(parent: ET.Element, name: str, text: str) -> ET.Element:
    node = ET.SubElement(parent, 'field', {'name': name})
    node.text = text
    return node


def value(parent: ET.Element, name: str, child: ET.Element) -> ET.Element:
    wrapper = ET.SubElement(parent, 'value', {'name': name})
    wrapper.append(child)
    return wrapper


def statement(parent: ET.Element, name: str, child: ET.Element | None = None) -> ET.Element:
    wrapper = ET.SubElement(parent, 'statement', {'name': name})
    if child is not None:
        wrapper.append(child)
    return wrapper


def nxt(parent: ET.Element, child: ET.Element) -> ET.Element:
    wrapper = ET.SubElement(parent, 'next')
    wrapper.append(child)
    return wrapper


def text_literal(factory: BlockFactory, text: str) -> ET.Element:
    block = factory.new_block('text')
    field(block, 'TEXT', text)
    return block


def math_number(factory: BlockFactory, number: float | int) -> ET.Element:
    block = factory.new_block('math_number')
    field(block, 'NUM', str(number))
    return block


def math_arithmetic(factory: BlockFactory, op: str, left: ET.Element, right: ET.Element) -> ET.Element:
    block = factory.new_block('math_arithmetic')
    field(block, 'OP', op)
    value(block, 'A', left)
    value(block, 'B', right)
    return block


def math_round(factory: BlockFactory, child: ET.Element) -> ET.Element:
    block = factory.new_block('math_round')
    field(block, 'OP', 'ROUND')
    value(block, 'NUM', child)
    return block


def lexical_get(factory: BlockFactory, name: str, event_param: bool = False) -> ET.Element:
    block = factory.new_block('lexical_variable_get')
    if event_param:
        mut = mutation(block)
        ET.SubElement(mut, 'eventparam', {'name': name})
    field(block, 'VAR', name)
    return block


def local_declaration(factory: BlockFactory, name: str, initial: ET.Element, body: ET.Element) -> ET.Element:
    block = factory.new_block('local_declaration_statement', inline='false')
    mut = mutation(block)
    ET.SubElement(mut, 'localname', {'name': name})
    field(block, 'VAR0', name)
    value(block, 'DECL0', initial)
    statement(block, 'STACK', body)
    return block


def set_property(factory: BlockFactory, component: str, component_type: str, prop: str, child: ET.Element) -> ET.Element:
    block = factory.new_block('component_set_get', inline='false')
    mutation(block, component_type=component_type, set_or_get='set', property_name=prop, is_generic='false', instance_name=component)
    field(block, 'COMPONENT_SELECTOR', component)
    field(block, 'PROP', prop)
    value(block, 'VALUE', child)
    return block


def get_property(factory: BlockFactory, component: str, component_type: str, prop: str) -> ET.Element:
    block = factory.new_block('component_set_get', inline='false')
    mutation(block, component_type=component_type, set_or_get='get', property_name=prop, is_generic='false', instance_name=component)
    field(block, 'COMPONENT_SELECTOR', component)
    field(block, 'PROP', prop)
    return block


def call_method(factory: BlockFactory, component: str, component_type: str, method: str, args: list[ET.Element]) -> ET.Element:
    block = factory.new_block('component_method', inline='false')
    mutation(block, component_type=component_type, method_name=method, is_generic='false', instance_name=component)
    field(block, 'COMPONENT_SELECTOR', component)
    for index, arg in enumerate(args):
        value(block, f'ARG{index}', arg)
    return block


def text_join(factory: BlockFactory, *items: ET.Element) -> ET.Element:
    block = factory.new_block('text_join', inline='false')
    mutation(block, items=str(len(items)))
    for index, item in enumerate(items):
        value(block, f'ADD{index}', item)
    return block


def call_procedure(factory: BlockFactory, name: str, arg_names: list[str], arg_blocks: list[ET.Element]) -> ET.Element:
    block = factory.new_block('procedures_callnoreturn', inline='false')
    mut = mutation(block, name=name)
    for arg in arg_names:
        ET.SubElement(mut, 'arg', {'name': arg})
    field(block, 'PROCNAME', name)
    for index, arg in enumerate(arg_blocks):
        value(block, f'ARG{index}', arg)
    return block


def component_event(factory: BlockFactory, component_type: str, instance: str, event: str, body: ET.Element, x: int | None = None, y: int | None = None) -> ET.Element:
    attrs = {}
    if x is not None:
        attrs['x'] = str(x)
    if y is not None:
        attrs['y'] = str(y)
    block = factory.new_block('component_event', **attrs)
    mutation(block, component_type=component_type, is_generic='false', instance_name=instance, event_name=event)
    field(block, 'COMPONENT_SELECTOR', instance)
    statement(block, 'DO', body)
    return block


def text_split(factory: BlockFactory, text_block: ET.Element, delimiter: ET.Element) -> ET.Element:
    block = factory.new_block('text_split', inline='false')
    mutation(block, mode='SPLIT')
    field(block, 'OP', 'SPLIT')
    value(block, 'TEXT', text_block)
    value(block, 'AT', delimiter)
    return block


def select_list_item(factory: BlockFactory, list_block: ET.Element, index: int) -> ET.Element:
    block = factory.new_block('lists_select_item')
    value(block, 'LIST', list_block)
    value(block, 'NUM', math_number(factory, index))
    return block


def logic_compare(factory: BlockFactory, op: str, left: ET.Element, right: ET.Element) -> ET.Element:
    block = factory.new_block('logic_compare')
    field(block, 'OP', op)
    value(block, 'A', left)
    value(block, 'B', right)
    return block


def controls_if(factory: BlockFactory, condition: ET.Element, then_block: ET.Element, else_block: ET.Element | None = None) -> ET.Element:
    block = factory.new_block('controls_if', inline='false')
    if else_block is not None:
        mutation(block, **{'else': '1'})
    value(block, 'IF0', condition)
    statement(block, 'DO0', then_block)
    if else_block is not None:
        statement(block, 'ELSE', else_block)
    return block


def logic_boolean(factory: BlockFactory, value_bool: bool) -> ET.Element:
    block = factory.new_block('logic_boolean')
    field(block, 'BOOL', 'TRUE' if value_bool else 'FALSE')
    return block


def slider_expression(factory: BlockFactory, base: int, delta: int, subtract: bool) -> ET.Element:
    param = lexical_get(factory, 'thumbPosition', event_param=True)
    mult = math_arithmetic(factory, 'MULTIPLY', math_number(factory, delta), param)
    div = math_arithmetic(factory, 'DIVIDE', mult, math_number(factory, 100))
    if subtract:
        expr = math_arithmetic(factory, 'MINUS', math_number(factory, base), div)
    else:
        expr = math_arithmetic(factory, 'ADD', math_number(factory, base), div)
    return math_round(factory, expr)


def slider_event(
    factory: BlockFactory,
    slider: str,
    label: str,
    command_key: str,
    base: int,
    delta: int,
    subtract: bool,
    prefix: str,
    suffix: str,
    x: int,
    y: int,
) -> ET.Element:
    value_expr = slider_expression(factory, base, delta, subtract)
    text_parts = [text_literal(factory, prefix), lexical_get(factory, 'sliderValue')]
    if suffix:
        text_parts.append(text_literal(factory, suffix))
    label_text = text_join(factory, *text_parts)
    label_block = set_property(factory, label, 'Label', 'Text', label_text)
    send_block = call_procedure(
        factory,
        'SendCommand',
        ['cmd'],
        [text_join(factory, text_literal(factory, f'SET {command_key} '), lexical_get(factory, 'sliderValue'))]
    )
    nxt(label_block, send_block)
    local_body = local_declaration(factory, 'sliderValue', value_expr, label_block)
    return component_event(factory, 'Slider', slider, 'PositionChanged', local_body, x=x, y=y)


def build_bky() -> str:
    factory = BlockFactory()
    root = ET.Element('xml', {'xmlns': 'http://www.w3.org/1999/xhtml'})

    # Procedure SendCommand
    proc = factory.new_block('procedures_defnoreturn', x='40', y='20')
    mut = mutation(proc)
    ET.SubElement(mut, 'arg', {'name': 'cmd'})
    field(proc, 'NAME', 'SendCommand')
    field(proc, 'VAR0', 'cmd')
    stack = statement(proc, 'STACK')

    cond = get_property(factory, 'BluetoothClient1', 'BluetoothClient', 'IsConnected')
    send_text = call_method(
        factory,
        'BluetoothClient1',
        'BluetoothClient',
        'SendText',
        [text_join(factory, lexical_get(factory, 'cmd'), text_literal(factory, '\\n'))]
    )
    alert = call_method(
        factory,
        'Notifier1',
        'Notifier',
        'ShowAlert',
        [text_literal(factory, 'Connect to the ESP32 over Bluetooth first.')]
    )
    stack.append(controls_if(factory, cond, send_text, alert))
    root.append(proc)

    # Screen1.Initialize
    init_body_first = set_property(
        factory,
        'StatusLabel',
        'Label',
        'Text',
        text_literal(factory, 'Tap Connect to pair with WIFILampV1.')
    )

    # helper to set initial slider labels
    def init_slider_text(label: str, text_value: str) -> ET.Element:
        return set_property(factory, label, 'Label', 'Text', text_literal(factory, text_value))

    blink_default = round(2000 - (1950 * SLIDER_DEFAULT) / 100)
    chase_default = round(2000 - (1950 * SLIDER_DEFAULT) / 100)
    fade_default = round(1 + (19 * SLIDER_DEFAULT) / 100)
    rainbow_default = round(200 - (190 * SLIDER_DEFAULT) / 100)
    twinkle_default = round(1 + (99 * SLIDER_DEFAULT) / 100)

    current_block = init_body_first
    for label_name, text in [
        ('BlinkLabel', f'Blink Interval: {blink_default} ms'),
        ('ChaseLabel', f'Chase Interval: {chase_default} ms'),
        ('FadeLabel', f'Fade Step: {fade_default}'),
        ('RainbowLabel', f'Rainbow Speed: {rainbow_default} ms'),
        ('TwinkleLabel', f'Twinkle Speed: {twinkle_default}')
    ]:
        next_block = init_slider_text(label_name, text)
        nxt(current_block, next_block)
        current_block = next_block

    init_block = component_event(factory, 'Form', 'Screen1', 'Initialize', init_body_first, x=40, y=220)
    root.append(init_block)

    # ConnectPicker.BeforePicking
    before_body = set_property(
        factory,
        'ConnectPicker',
        'ListPicker',
        'Elements',
        get_property(factory, 'BluetoothClient1', 'BluetoothClient', 'AddressesAndNames')
    )
    before_event = component_event(factory, 'ListPicker', 'ConnectPicker', 'BeforePicking', before_body, x=320, y=20)
    root.append(before_event)

    # ConnectPicker.AfterPicking
    selection = get_property(factory, 'ConnectPicker', 'ListPicker', 'Selection')
    empty_text = text_literal(factory, '')
    condition = logic_compare(factory, 'NEQ', selection, empty_text)

    parts = text_split(factory, get_property(factory, 'ConnectPicker', 'ListPicker', 'Selection'), text_literal(factory, '\\n'))
    device_name = select_list_item(factory, parts, 1)
    device_address = select_list_item(factory, text_split(factory, get_property(factory, 'ConnectPicker', 'ListPicker', 'Selection'), text_literal(factory, '\\n')), 2)

    connect_call = call_method(factory, 'BluetoothClient1', 'BluetoothClient', 'Connect', [device_address])

    success_text = text_join(factory, text_literal(factory, 'Connected to '), device_name)
    success_body = set_property(factory, 'StatusLabel', 'Label', 'Text', success_text)
    nxt(success_body, call_method(factory, 'Notifier1', 'Notifier', 'ShowAlert', [success_text]))

    failure_text = text_literal(factory, 'Connection failed. Make sure the lamp is discoverable.')
    failure_body = set_property(factory, 'StatusLabel', 'Label', 'Text', failure_text)
    nxt(failure_body, call_method(factory, 'Notifier1', 'Notifier', 'ShowAlert', [failure_text]))

    connect_if = controls_if(factory, connect_call, success_body, failure_body)
    after_body = controls_if(factory, condition, connect_if)
    after_event = component_event(factory, 'ListPicker', 'ConnectPicker', 'AfterPicking', after_body, x=320, y=200)
    root.append(after_event)

    # Disconnect button
    disconnect_first = call_method(factory, 'BluetoothClient1', 'BluetoothClient', 'Disconnect', [])
    current = disconnect_first
    status_reset = set_property(factory, 'StatusLabel', 'Label', 'Text', text_literal(factory, 'Disconnected.'))
    current = nxt(current, status_reset)
    for checkbox in ['CheckBoxRed', 'CheckBoxGreen', 'CheckBoxBlue', 'CheckBoxWhite']:
        checkbox_block = set_property(factory, checkbox, 'CheckBox', 'Checked', logic_boolean(factory, False))
        current = nxt(current, checkbox_block)
    alert_block = call_method(factory, 'Notifier1', 'Notifier', 'ShowAlert', [text_literal(factory, 'Disconnected.')])
    nxt(current, alert_block)
    disconnect_event = component_event(factory, 'Button', 'DisconnectButton', 'Click', disconnect_first, x=40, y=420)
    root.append(disconnect_event)

    # Mode buttons
    modes = {
        'ManualButton': 'MODE MANUAL',
        'ChaseButton': 'MODE CHASE',
        'BlinkModeButton': 'MODE BLINK',
        'FadeModeButton': 'MODE FADE',
        'RainbowModeButton': 'MODE RAINBOW',
    }
    offset = 640
    for name, command in modes.items():
        body = call_procedure(factory, 'SendCommand', ['cmd'], [text_literal(factory, command)])
        event = component_event(factory, 'Button', name, 'Click', body, x=40, y=offset)
        root.append(event)
        offset += 120

    # CheckBox events
    colors = {
        'CheckBoxRed': ('RED ON', 'RED OFF'),
        'CheckBoxGreen': ('GREEN ON', 'GREEN OFF'),
        'CheckBoxBlue': ('BLUE ON', 'BLUE OFF'),
        'CheckBoxWhite': ('WHITE ON', 'WHITE OFF'),
    }
    offset = 40
    for name, (on_cmd, off_cmd) in colors.items():
        true_call = call_procedure(factory, 'SendCommand', ['cmd'], [text_literal(factory, on_cmd)])
        false_call = call_procedure(factory, 'SendCommand', ['cmd'], [text_literal(factory, off_cmd)])
        condition = lexical_get(factory, 'value', event_param=True)
        body = controls_if(factory, condition, true_call, false_call)
        event = component_event(factory, 'CheckBox', name, 'Changed', body, x=600, y=offset)
        root.append(event)
        offset += 140

    # Slider events (manual label text handled separately)
    slider_specs = [
        ('BlinkSlider', 'BlinkLabel', 'BLINK', 2000, 1950, True, 'Blink Interval: ', ' ms'),
        ('ChaseSlider', 'ChaseLabel', 'CHASE', 2000, 1950, True, 'Chase Interval: ', ' ms'),
        ('FadeSlider', 'FadeLabel', 'FADE', 1, 19, False, 'Fade Step: ', ''),
        ('RainbowSlider', 'RainbowLabel', 'RAINBOW', 200, 190, True, 'Rainbow Speed: ', ' ms'),
        ('TwinkleSlider', 'TwinkleLabel', 'TWINKLE', 1, 99, False, 'Twinkle Speed: ', '')
    ]
    offset = 40
    for slider, label, key, base, delta, subtract, prefix, suffix in slider_specs:
        event = slider_event(factory, slider, label, key, base, delta, subtract, prefix, suffix, x=900, y=offset)
        root.append(event)
        offset += 200

    return ET.tostring(root, encoding='utf-8').decode('utf-8')


def project_properties() -> str:
    return "\n".join([
        'main=appinventor.ai_digitalgarden.DigitalGardenController.Screen1',
        'name=DigitalGardenController',
        'assets=../assets',
        'source=../src',
        'build=../build',
        'versioncode=1',
        'versionname=1.0',
        'useslocation=False',
        'aname=DigitalGardenController',
        'sizing=Responsive',
        'showlistsasjson=True',
        'actionbar=True',
        'theme=AppTheme.Light.DarkActionBar',
        'color.primary=&HFF2196F3',
        'color.primary.dark=&HFF1565C0',
        'color.accent=&HFFFFC107',
    ]) + "\n"


def write_files():
    scm_text = build_scm()
    bky_text = build_bky()
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    YOUNG_DIR.mkdir(parents=True, exist_ok=True)

    (SRC_DIR / 'Screen1.scm').write_text(scm_text)
    (SRC_DIR / 'Screen1.bky').write_text(bky_text)
    (ASSETS_DIR / '.nomedia').write_text('')
    (YOUNG_DIR / 'project.properties').write_text(project_properties())

    aia_path = PROJECT_DIR / 'DigitalGardenController.aia'
    with zipfile.ZipFile(aia_path, 'w') as zf:
        for path in sorted(PROJECT_DIR.rglob('*')):
            if path.is_file() and path.name != aia_path.name:
                arcname = path.relative_to(PROJECT_DIR)
                zf.write(path, arcname)


def main():
    write_files()


if __name__ == '__main__':
    main()


