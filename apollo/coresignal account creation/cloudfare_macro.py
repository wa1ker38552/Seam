from ahk import AHK
import time


def dclick(x, y, delay):
    ahk.click(x, y)
    time.sleep(delay)

ahk = AHK(executable_path=r'C:\Program Files\AutoHotkey\AutoHotkey.exe')

ahk.add_hotkey('^x', callback=lambda: print(ahk.mouse_position, ahk.pixel_get_color(ahk.mouse_position[0], ahk.mouse_position[1])))
ahk.start_hotkeys()
# ahk.block_forever()

for window in ahk.list_windows():
    if 'email | email routing' in window.title.lower():
        win = window

win.activate()

for i in range(56):
    dclick(1313, 872, 0.5) # click create record
    dclick(1434, 500, 0.1) # click input field
    ahk.type(f'mailroute{16+i+1}')
    time.sleep(0.1)
    dclick(1494, 620, 2) # press add record and enable

ahk.block_forever()