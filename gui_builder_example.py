from gui_builder import make_gui
from PyQt4.QtCore import QTimer
from numpy import linspace, sin, cos, tan

@make_gui
class Window(object):
    def make_plot_gb_button(self):
        f = gb_get_float_frequency(3)
        start = gb_get_float_start(0)
        stop = gb_get_float_stop(10)
        steps = gb_get_int_step(100)
        x = linspace(start, stop, steps)
        y = sin(f * x)
        gb_plot_xy_sinusoid_sin(x, sin(f*x))
        gb_plot_xy_sinusoid_cos(x, cos(f*x))
        gb_plot_xy_trig_tan(x, tan(f*x))

    def recurring_plot_gb_button(self):
        self.timer = QTimer()
        self.recurring_plot()

    def recurring_plot(self):
        f = gb_get_float_frequency()
        gb_set_float_frequency(f+1)
        self.make_plot_gb_button()
        if gb_get_bool_halt(False):
            gb_set_bool_halt(False)
        else:
            self.timer.singleShot(1000, self.recurring_plot)

if __name__ == '__main__':
    Window()
