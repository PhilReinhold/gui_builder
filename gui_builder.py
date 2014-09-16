from inspect import getsource
from PyQt4.QtGui import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,\
    QFormLayout, QLineEdit, QPushButton, QApplication, QCheckBox
import ast
import itertools
from pyqtgraph import PlotWidget
import sys
from pyqtgraph.dockarea import DockArea, Dock

def prettify(s):
    return ' '.join(w.capitalize() for w in s.split('_'))

class GUIBuilder(QMainWindow):
    def __init__(self, instance):
        super(GUIBuilder, self).__init__()
        self.setCentralWidget(QWidget())
        layout = QVBoxLayout(self.centralWidget())
        self.plots_layout = DockArea()
        layout.addWidget(self.plots_layout)
        self.form_layout = QFormLayout()
        self.form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        layout.addLayout(self.form_layout)
        self.buttons_layout = QHBoxLayout()
        layout.addLayout(self.buttons_layout)

        self.instance = instance
        self.plot_widgets = {}
        self.plot_data_items = {}
        self.plot_color_generators = {}

        seen_form_items = []
        seen_plot_items = []

        for node in ast.walk(ast.parse(getsource(type(instance)))):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id.startswith('gb_get_') or node.func.id.startswith('gb_set_'):
                    segs = node.func.id.split('_')
                    caster = __builtins__[segs[2]]
                    name = "_".join(segs[3:])

                    if name in seen_form_items:
                        continue
                    seen_form_items.append(name)

                    if caster is bool:
                        editor = QCheckBox()
                        if node.func.id.startswith('gb_get_') and node.args:
                            editor.setChecked(node.args[0].id == 'True')
                        get_fn = lambda e=editor: e.isChecked()
                        set_fn = lambda v, e=editor: e.setChecked(v)
                    else:
                        editor = QLineEdit()
                        if node.func.id.startswith('gb_get_') and node.args:
                            if isinstance(node.args[0], ast.Num):
                                init = node.args[0].n
                            else:
                                init = node.args[0].s
                            editor.setText(str(caster(init)))
                        get_fn = lambda e=editor, c=caster: c(e.text())
                        set_fn = lambda val, e=editor: e.setText(str(val))

                    base_name = "_".join(segs[2:])
                    get_name = "gb_get_" + base_name
                    set_name = "gb_set_" + base_name
                    __builtins__[get_name] = lambda init=0, get_fn=get_fn: get_fn()
                    __builtins__[set_name] = lambda val, set_fn=set_fn: set_fn(val)

                    self.form_layout.addRow(prettify(name), editor)

                if node.func.id.startswith('gb_plot_'):
                    segs = node.func.id.split("_")
                    plot_type = segs[2]
                    plot_name = segs[3]
                    if len(segs) >= 5:
                        data_item_name = "_".join(segs[4:])
                    else:
                        data_item_name = ""

                    if (plot_name, data_item_name) in seen_plot_items:
                        continue
                    seen_plot_items.append((plot_name, data_item_name))

                    if plot_name not in self.plot_widgets:
                        if plot_type in ['y', 'xy']:
                            pw = PlotWidget()
                            self.plot_widgets[plot_name] = pw
                            self.plot_color_generators[plot_name] = itertools.cycle('rgb')
                            pw.addLegend()
                        else:
                            raise ValueError("Unknown plot type in {}: {}".format(node.func.id, plot_type))
                        dock = Dock(name=prettify(plot_name), widget=pw)
                        self.plots_layout.addDock(dock, 'above')

                    self.add_plot_item(node.func.id, plot_name, data_item_name)

            if isinstance(node, ast.FunctionDef):
                if node.name.endswith("_gb_button"):
                    name = "_".join(node.name.split("_")[:-2])
                    button = QPushButton(prettify(name))
                    button.clicked.connect(getattr(instance, node.name))
                    self.buttons_layout.addWidget(button)


    def add_plot_item(self, fn_name, plot_name, data_item_name):
        plot_widget = self.plot_widgets[plot_name]
        color_generator = self.plot_color_generators[plot_name]
        plot_type = fn_name.split("_")[2]
        if plot_type == "xy":
            def plot_fn(x, y):
                if data_item_name in self.plot_data_items:
                    self.plot_data_items[data_item_name].setData(x, y)
                else:
                    self.plot_data_items[data_item_name] = plot_widget.plot(
                        x, y, name=prettify(data_item_name), pen=color_generator.next()
                    )
        elif plot_type == "y":
            def plot_fn(y):
                if data_item_name in self.plot_data_items:
                    self.plot_data_items[data_item_name].setData(y)
                else:
                    self.plot_data_items[data_item_name] = plot_widget.plot(
                        y, name=prettify(data_item_name), pen=color_generator.next()
                    )
        else:
            raise ValueError("Unknown plot type in {}: {}".format(fn_name, plot_type))


        __builtins__[fn_name] = plot_fn


def make_gui(cls):
    def wrapper(*args, **kwargs):
        app = QApplication([])
        win = GUIBuilder(cls(*args, **kwargs))
        win.show()
        sys.exit(app.exec_())
    return wrapper

