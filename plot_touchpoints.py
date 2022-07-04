import curses
import subprocess
import copy

MAX_HEIGHT = 1024
MAX_WIDTH = 768

def main():
    try:
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)

        window = curses.newwin(curses.LINES, curses.COLS, 0, 0)
        coordinates = {}
        oldcoordinateses = []
        slot = None
        with subprocess.Popen("evtest /dev/input/event3", shell=True, stdout=subprocess.PIPE, bufsize=1) as subproc:
            for line in subproc.stdout:
                words = line.split()
                if len(words) < 11:
                    window.erase()
                    for oldcoordinates in oldcoordinateses:
                        for i, (x, y) in oldcoordinates.items():
                            if x is not None and y is not None:
                                row = min((y * curses.LINES) // MAX_HEIGHT, curses.LINES-1)
                                col = min((x * curses.COLS) // MAX_WIDTH, curses.COLS-1)
                                window.addstr(row, col, f"{i}", curses.A_DIM)

                    for i, (x, y) in coordinates.items():
                        if x is not None and y is not None:
                            # window.addstr(i, 0, str(coord))
                            row = min((y * curses.LINES) // MAX_HEIGHT, curses.LINES-1)
                            col = min((x * curses.COLS) // MAX_WIDTH, curses.COLS-1)
                            window.addstr(row, col, f"{i}", curses.A_BOLD)
                    # window.addstr(12, 0, "hi")
                    window.refresh()
                    oldcoordinateses.append(coordinates)
                    oldcoordinateses = oldcoordinateses[-20:]
                    coordinates = copy.deepcopy(coordinates)
                else:
                    # window.addstr(14, 0, repr(words))
                    if words[4] == b"3":
                        # window.addstr(13, 0, line)
                        # window.addstr(13, 0, words[8])
                        if words[8] == b"(ABS_MT_SLOT),":
                            slot = int(words[10])
                            window.refresh()
                            # print(f"slot: {slot}")
                        if words[8] == b"(ABS_MT_POSITION_X),":
                            x = int(words[10])
                            if slot != None:
                                coordinates.setdefault(slot, [None, None])
                                coordinates[slot][0] = x
                                # window.addstr(10, 0, line)
                                window.refresh()
                        if words[8] == b"(ABS_MT_POSITION_Y),":
                            y = int(words[10])
                            if slot != None:
                                coordinates.setdefault(slot, [None, None])
                                coordinates[slot][1] = y
                                # window.addstr(11, 0, line)
                                window.refresh()
                        if words[8] == b"(ABS_MT_TRACKING_ID)," and words[10] == b"-1":
                            # seems to indicate finger up?
                            coordinates.pop(slot, None)


    finally:
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        curses.endwin()


if __name__ == '__main__':
    main()
