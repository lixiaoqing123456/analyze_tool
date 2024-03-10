import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import numpy as np
from matplotlib.figure import Figure
import matplotlib

matplotlib.use('Qt5Agg')


class SnappingCursor:
    def __init__(self):
        self.axes = []
        self.x_datas = []
        self.y_datas = []
        self.vertical_lines = []
        self.texts = []
        self.last_indexes = []
        self.xlims = []
        self.canvas = {}

        self.last_xdata = None
        self.last_ax = None

    def add_canvas(self, canvas):
        ax = canvas.get_ax()
        self.canvas[ax] = canvas
        line = canvas.get_line()
        self.axes.append(ax)
        x, y = line.get_data()
        self.x_datas.append(x)
        self.y_datas.append(y)
        self.vertical_lines.append(ax.axvline(color='k', lw=0.8, ls='--'))
        self.texts.append(ax.text(0.72, 0.9, '', transform=ax.transAxes))
        self.last_indexes.append(None)
        self.xlims.append(ax.get_xlim())
        ax.figure.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        ax.figure.canvas.mpl_connect('button_press_event', self.on_click)
        ax.figure.canvas.mpl_connect('button_release_event', self.on_release)

    def remove_canvas(self, canvas):
        pass

    def set_cross_hair_visible(self, idx, visible):
        self.vertical_lines[idx].set_visible(visible)
        self.texts[idx].set_visible(visible)

    def set_cross_hair_off(self, idx):
        need_redraw = not self.vertical_lines[idx].get_visible()
        self.set_cross_hair_visible(idx, False)
        if need_redraw:
            self.axes[idx].figure.canvas.draw()

    def on_mouse_move(self, event):
        if not event.inaxes:
            for i in range(len(self.axes)):
                self.last_indexes[i] = None
                self.set_cross_hair_off(i)
        else:
            x, _ = event.xdata, event.ydata
            for i in range(len(self.axes)):
                index = min(np.searchsorted(self.x_datas[i], x), len(self.x_datas[i]) - 1)
                if index == self.last_indexes[i]:
                    continue
                else:
                    x = self.x_datas[i][index]
                    y = self.y_datas[i][index]
                    self.last_indexes[i] = index
                    self.vertical_lines[i].set_xdata([x])
                    self.texts[i].set_text(f'x={x:1.2f}, y={y:1.2f}')
                    self.set_cross_hair_visible(i, True)
                    self.axes[i].figure.canvas.draw()

            if self.last_ax:
                if self.last_ax != event.inaxes:
                    self.last_ax = None
                    self.last_xdata = None
                else:
                    return
                    rect = matplotlib.patches.Rectangle((0, 0), 1, 1, alpha=0.8, fc='yellow')
                    self.canvas[event.inaxes].get_line().set_clip_path(rect)
                    return
                    event.inaxes.fill_betweenx([-1, 1], self.last_xdata, event.xdata, color='b')
                    event.inaxes.figure.canvas.draw()

    def on_click(self, event):
        if not event.inaxes:
            return
        if event.dblclick:
            self.double_click(event)
            return
        if event.button == 3:
            self.last_ax = event.inaxes
            self.last_xdata = event.xdata

    def on_release(self, event):
        if not event.inaxes or event.inaxes != self.last_ax:
            self.last_ax = None
            self.last_xdata = None
            return

        if event.button == 3:
            if self.last_xdata >= event.xdata:
                return
            for ax in self.axes:
                ax.set_xlim(self.last_xdata, event.xdata)
                ax.figure.canvas.draw()
        self.last_ax = None
        self.last_xdata = None

    def double_click(self, event):
        index = self.axes.index(event.inaxes)
        if not (0 <= index < len(self.axes)):
            return
        for i, ax in enumerate(self.axes):
            ax.set_xlim(self.xlims[i][0], self.xlims[i][1])
            ax.figure.canvas.draw()

    def remove_ax(self, ax):
        index = self.axes.index(ax)
        if not (0 <= index < len(self.axes)):
            return
        self.axes.pop(index)
        self.x_datas.pop(index)
        self.y_datas.pop(index)
        self.vertical_lines.pop(index)
        self.texts.pop(index)
        self.last_indexes.pop(index)
        self.xlims.pop(index)


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, title="", width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        super(MplCanvas, self).__init__(fig)
        self.parent = parent
        self.axes = fig.add_subplot(111)
        self.setParent(parent)
        self.axes.set_title(title)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.updateGeometry()
        self.close_button = QToolButton(self)
        self.close_button.setIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton))
        self.close_button.setGeometry(self.width() - 25, 5, 20, 20)
        self.close_button.setStyleSheet('background-color:transparent')
        self.close_button.clicked.connect(self.on_close)

        x = np.arange(0, 1, 0.01)
        y = np.sin(2 * 2 * np.pi * x)
        self.line, = self.axes.plot(x, y, 'o')

    def resizeEvent(self, event):
        self.close_button.setGeometry(event.size().width() - 25, 5, 20, 20)
        FigureCanvasQTAgg.resizeEvent(self, event)

    def get_ax(self):
        return self.axes

    def get_line(self):
        return self.line

    def on_close(self):
        self.parent.remove_ax(self.axes)
        self.deleteLater()


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        sc1 = MplCanvas(self, title='title1', width=5, height=4, dpi=100)
        sc2 = MplCanvas(self, title='title2', width=5, height=4, dpi=100)
        sc3 = MplCanvas(self, title='title3', width=5, height=4, dpi=100)
        sc4 = MplCanvas(self, title='title4', width=5, height=4, dpi=100)
        self.snap_cursor = SnappingCursor()
        self.snap_cursor.add_canvas(sc1)
        self.snap_cursor.add_canvas(sc2)
        self.snap_cursor.add_canvas(sc3)
        self.snap_cursor.add_canvas(sc4)

        self.list_layout = QVBoxLayout()
        self.list_layout.addWidget(sc1)
        self.list_layout.addWidget(sc2)
        self.list_layout.addWidget(sc3)
        self.list_layout.addWidget(sc4)
        widget = QWidget()
        widget.setLayout(self.list_layout)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidget(widget)
        self.scroll_area.setAlignment(Qt.AlignHCenter)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setBaseSize(400, 500)
        self.setCentralWidget(self.scroll_area)

    def remove_ax(self, ax):
        self.snap_cursor.remove_ax(ax)


app = QApplication(sys.argv)
w = MainWindow()
w.setMinimumSize(1200, 800)
w.show()
app.exec_()
