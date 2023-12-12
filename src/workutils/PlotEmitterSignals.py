from PyQt5.QtCore import pyqtSignal as Signal, QObject

# class to emit signals for showing figures in GUI
class EmittedPlotSignals(QObject):
     # emit a signal that provides figure 
    figure_plotted = Signal(object)
    # emit a signal that provides cell name plotted
    cell_plotted = Signal(str)
    figure_closed = Signal()