"""Regenerate a screenshot from synthetic readings, without importing local state."""

import os
import logging
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["QT_QPA_PLATFORM"] = "offscreen"


def main():
    with tempfile.TemporaryDirectory() as directory:
        os.environ["WTT_DATA_DIR"] = directory
        from PyQt5.QtWidgets import QApplication
        import ui

        app = QApplication([])
        gui = ui.BottleTesterGUI()
        gui.show()
        gui.evaluate_results([60, 65, 70, 75], False, "main")
        for index, reading in enumerate((60, 65, 70, 75)):
            gui._set_sensor_card("main", index, reading, "pass")
        app.processEvents()
        target = ROOT / "docs" / "demo.png"
        target.parent.mkdir(exist_ok=True)
        if not gui.grab().save(str(target)):
            raise RuntimeError("Screenshot could not be saved")
        gui.close()
        logging.shutdown()
        print("Saved synthetic screenshot: docs/demo.png")


if __name__ == "__main__":
    main()
