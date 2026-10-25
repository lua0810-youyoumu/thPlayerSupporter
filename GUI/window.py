import pyqtgraph as pg
import PySide6
from PySide6 import QtCore
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout, QComboBox
import os
import sys

VERSION = '0.00'

class MainWindow(QMainWindow):
    """
    """
    def __init__(self):
        """
        """
        super().__init__()
        self.setWindowTitle(f'東方サポートツール ver{VERSION}')
        
        # menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('ファイル')
        config_menu = menu_bar.addMenu('設定')
        
        # action
        exit_action = QAction('終了', self)
        exit_action.triggered.connect(self.close)
        
        file_menu.addAction(exit_action)
        
        # layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # UI
        combo = QComboBox(self)
        combo.addItems(["初クリア狙い", "通常プレイ", "NB", 'NM', 'スコアアタック'])
        
        # グラフウィジェット作成
        plot_widget = pg.PlotWidget()

        # データ
        x = [0, 1, 2, 3, 4, 5]
        y = [10, 15, 12, 18, 20, 17]

        # ライン描画
        plot_widget.plot(
            x,
            y,
            pen=pg.mkPen(color="r", width=2)
        )
        
        layout.addWidget(combo)
        layout.addWidget(plot_widget)
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())