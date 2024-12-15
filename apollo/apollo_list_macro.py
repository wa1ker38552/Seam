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
    if 'companies - apollo' in window.title.lower():
        win = window

win.activate()

for i in range(13):
    print(i, 34)
    dclick(394, 320, 0.5) # click net new
    dclick(571, 250, 0.5) # click checkbox
    dclick(322, 356, 0.5) # click Select this page
    dclick(562, 403, 0.5) # click apply
    dclick(952, 205, 0.5) # click add to lists
    dclick(1601, 266, 0.5) # click input box
    dclick(1513, 351, 0.5) # select list from dropdown
    dclick(1465, 343, 3) # press apply
    dclick(92, 64, 3) # refresh the page'''

ahk.block_forever()