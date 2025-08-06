from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QCursor
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class TimeDomainPlot(QWidget):
    truncation_changed = pyqtSignal()

    def __init__(self, model):
        super().__init__()
        self.model = model
        layout = QVBoxLayout(self)

        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        self.trunc_line = None
        self._dragging = False
        self._drag_threshold = 1 # ps
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def update_plot(self):
        t, E_ref, E_sam = self.model.time, self.model.E_ref, self.model.E_sam
        if t is None: return

        self.ax.clear()
        self.ax.plot(t, E_ref, color='blue', label='Reference', linewidth=1)
        self.ax.plot(t, E_sam, color='red', label='Sample', linewidth=1)

        self.trunc_line = self.ax.axvline(self.model.trunc_time_ps, color='k')
        self.ax.set_xlabel("Time (ps)")
        self.ax.set_ylabel("E-field (V)")
        self.ax.legend()
        self.ax.grid(True)
        self.fig.tight_layout()
        self.canvas.draw()

    def on_press(self, event):
        if event.inaxes != self.ax:
            return
        if self.trunc_line is None:
            return

        x_line = self.trunc_line.get_xdata()[0]
        if abs(event.xdata - x_line) < self._drag_threshold:
            self._dragging = True

    def on_release(self, event):
        if self._dragging:
            self._dragging = False
            self.model.update_truncation(self.trunc_line.get_xdata()[0])
            self.truncation_changed.emit()

    def on_motion(self, event):
        if event.inaxes != self.ax:
            return

        # Handle dragging
        if self._dragging:
            self.trunc_line.set_xdata([event.xdata])
            self.model.update_truncation(event.xdata)
            self.truncation_changed.emit()
            self.canvas.draw_idle()
            return

        # Handle cursor style when hovering
        x_line = self.trunc_line.get_xdata()[0] if self.trunc_line else None
        if x_line is not None and abs(event.xdata - x_line) < self._drag_threshold:
            self.canvas.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))  # resize icon
        else:
            self.canvas.setCursor(QCursor(Qt.CursorShape.ArrowCursor))  # normal pointer

