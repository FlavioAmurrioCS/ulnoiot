# lcd display
# author: ulno
# created: 2017-04-08
#

import time
from machine import I2C
import ssd1306
from uiot.device import Device


class Display(Device):

    # Handle display
    def __init__(self, name, sda=None, scl=None,
                 width=128, height=64,
                 addr=0x3c):
        self.present = False
        self._y = 0
        self._x = 0
        self.last_text = ""
        self.char_width = width // 8
        self.char_height = height // 8

        if type(sda) is I2C:
            i2c = sda
        else:
            i2c = I2C(sda=sda, scl=scl)
        # test if lcd is responding
        try:
            self.dp = ssd1306.SSD1306_I2C(width, height, i2c, addr=addr)
            self.clear(show=False)
            self.println("  iot.ulno.net\n", show=True)

        except OSError:
            print("lcd not found")
        else:
            self.present = True
            Device.__init__(self, name, i2c, setters={"set": self.evaluate},
                            report_change=False)
            self.getters[""] = self.value

    def fill(self, c):
        self.dp.fill(c)

    def text(self, t, x, y):
        self.dp.text(t, x, y)

    def show(self):
        self.dp.show()

    def scroll(self, y0, y1):
        self.dp.scroll(y0, y1)

    def pixel(self, x, y, fill):
        self.dp.pixel(x, y, fill)

    def set_cursor(self, x, y):
        if x < 0: x = 0
        if y < 0: y = 0
        if x >= self.char_width: x = self.char_width - 1
        if y >= self.char_height: y = self.char_height - 1
        self._x = x
        self._y = y

    def get_cursor(self):
        return (self._x, self._y)

    # clear display immediately
    def clear(self, show=True):
        self.set_cursor(0, 0)
        self.dp.fill(0)
        if show:
            self.dp.show()

    # move cursor down and scroll the text area by one line if at screen end
    def line_feed(self, show=True):
        if self._y < self.char_height - 1:
            self._y += 1
        else:
            self.scroll(0, -8)
            # TODO: check if line really needs to be cleared (seems to happen sometimes that it does not clear)
            self.clear_line()
            if show:
                self.dp.show()
        self._x = 0

    # move just to start of line and clear the whole line
    def clear_line(self, show=True):
        self._x = 0
        # clear line
        for y in range(self._y * 8, (self._y + 1) * 8):
            for x in range(0, self.char_width * 8):
                self.dp.pixel(x, y, False)
        if show:
            self.dp.show()

    # print some text in the text area and linebreak and wrap if necessary
    def print(self, text="", newline=False, show=True):
        text = str(text)
        linefeed_last = text.endswith("\n")
        if linefeed_last:
            text = text[:-1]
        l_first = True
        for l in text.split("\n"):
            if not l_first:  # scroll if it's not the first line
                self.line_feed(show=False)
            l_first = False
            while len(l) > 0:
                sub = l[0:self.char_width - self._x]
                self.dp.text(sub, self._x * 8, self._y * 8)
                self._x += len(sub)
                if self._x >= self.char_width:
                    self.line_feed(show=False)
                l = l[len(sub):]
        if linefeed_last:
            self.line_feed(show=False)
        if newline:
            self.line_feed(show=False)
        if show:
            self.dp.show()

    def println(self, text="", show=True):
        self.print(text, newline=True, show=show)

    def evaluate(self, msg):
        if msg.startswith("&&clear"):
            self.clear()
            if len(msg) > 8:
                self.evaluate(msg[8:])
        elif msg.startswith("&&linefeed"):
            self.line_feed()
            if len(msg) > 11:
                self.evaluate(msg[11:])
        elif msg.startswith("&&newline"):
            self.line_feed()
            if len(msg) > 11:
                self.evaluate(msg[11:])
        elif msg.startswith("&&lf"):
            self.line_feed()
            if len(msg) > 5:
                self.evaluate(msg[5:])
        elif msg.startswith("&&nl"):
            self.line_feed()
            if len(msg) > 5:
                self.evaluate(msg[5:])
        elif msg.startswith("&&cursor"):
            csplit = msg[9:].strip().split()
            self.set_cursor(int(csplit[0]), int(csplit[1]))
            inlen = 11 + len(csplit[0]) + len(csplit[1])
            if len(msg) > inlen:
                self.evaluate(msg[inlen:])
        elif msg.startswith("&&plot"):
            msg = msg[6:].strip().split()
            for i in range(0, len(msg), 2):
                self.pixel(int(msg[i]), int(msg[i + 1]), 1)
            self.show()
        else:
            self.print(msg)
            self.last_text = msg

    def value(self):
        return self.last_text
