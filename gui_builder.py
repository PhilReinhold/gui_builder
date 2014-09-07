from inspect import getsource
from PyQt4.QtGui import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QDoubleSpinBox, QLineEdit, \
    QPushButton, QApplication
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
            if isinstance(node, ast.Call):
                if node.func.id.startswith('get_'):
                    segs = node.func.id.split('_')
                    caster = __builtins__[segs[1]]
                    name = "_".join(segs[2:])
                    if name in seen_form_items:
                        continue
                    seen_form_items.append(name)
                    editor = QLineEdit()
                    if node.args:
                        if isinstance(node.args[0], ast.Num):
                            init = node.args[0].n
                        else:
                            init = node.args[0].s
                        editor.setText(str(caster(init)))
                    __builtins__[node.func.id] = lambda init, e=editor, c=caster: c(e.text())
                    self.form_layout.addRow(prettify(name), editor)

                if node.func.id.startswith('plot_xy_'):
                    segs = node.func.id.split("_")
                    plot_type = segs[1]
                    plot_name = segs[2]
                    data_item_name = "_".join(segs[3:])

                    if (plot_name, data_item_name) in seen_plot_items:
                        continue
                    seen_plot_items.append((plot_name, data_item_name))

                    if plot_name not in self.plot_widgets:
                        pw = PlotWidget()
                        self.plot_widgets[plot_name] = pw
                        self.plot_color_generators[plot_name] = itertools.cycle('rgb')
                        pw.addLegend()
                        dock = Dock(name=prettify(plot_name), widget=pw)
                        self.plots_layout.addDock(dock, 'above')

                    self.add_plot_item(node.func.id, plot_name, data_item_name)

            if isinstance(node, ast.FunctionDef):
                if node.name.endswith("_button"):
                    name = "_".join(node.name.split("_")[:-1])
                    button = QPushButton(prettify(name))
                    button.clicked.connect(getattr(instance, node.name))
                    self.buttons_layout.addWidget(button)


    def add_plot_item(self, fn_name, plot_name, data_item_name):
        plot_widget = self.plot_widgets[plot_name]
        color_generator = self.plot_color_generators[plot_name]
        def plot_fn(x, y):
            if data_item_name in self.plot_data_items:
                self.plot_data_items[data_item_name].setData(x, y)
            else:
                self.plot_data_items[data_item_name] = plot_widget.plot(
                    x, y, name=prettify(data_item_name), pen=color_generator.next()
                )

        __builtins__[fn_name] = plot_fn




def make_gui(cls):
    def wrapper(*args, **kwargs):
        app = QApplication([])
        win = GUIBuilder(cls(*args, **kwargs))
        win.show()
        sys.exit(app.exec_())
    return wrapper

