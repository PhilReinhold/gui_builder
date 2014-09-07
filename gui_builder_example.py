from gui_builder import make_gui
from numpy import linspace, sin, cos, tan

@make_gui
class Window(object):
    def make_plot_button(self):
        f = get_float_frequency(3)
        start = get_float_start(0)
        stop = get_float_stop(10)
        steps = get_int_step(100)
        x = linspace(start, stop, steps)
        y = sin(f * x)
        plot_xy_sinusoid_sin(x, sin(f*x))
        plot_xy_sinusoid_cos(x, cos(f*x))
        plot_xy_trig_tan(x, tan(f*x))

if __name__ == '__main__':
    Window()
