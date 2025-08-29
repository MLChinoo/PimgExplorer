import atexit
import io
import json
import sys
import threading
import traceback
from pathlib import Path
import shutil
import subprocess

from PIL import Image
from PySide6.QtCore import QByteArray, QBuffer, QIODeviceBase, QSize, Signal
from PySide6.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox, QGraphicsScene, QGraphicsPixmapItem, \
    QListWidgetItem
from PySide6.QtGui import QPixmap
from MainWindow import Ui_MainWindow
from event_filter import ResizeFilter
from image_process import has_transparency
from json_model import PIMGJson, Layer

window = None
temp_path = Path("temp/")

class MyApp(QMainWindow):
    filepath: Path = None
    compose: bool = False
    images_by_name: dict[str, bytes] = None
    resolutions_by_name: dict[str, tuple[int, int]] = None
    activated_image_name: str = None
    pixmap_item = None
    exception_signal = Signal(str)

    def __init__(self):
        super().__init__()
        threading.excepthook = lambda args: self.show_exception()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.exception_signal.connect(self.show_exception_gui)
        self.ui.openButton.clicked.connect(self.on_open_button_clicked)
        self.ui.composeCheckBox.clicked.connect(self.on_compose_check_box_clicked)
        self.ui.listWidget.itemActivated.connect(self.on_item_activated)
        self.ui.exportSingleButton.clicked.connect(self.on_export_single_button_clicked)
        self.ui.exportAllButton.clicked.connect(self.on_export_all_button_clicked)
        self.show()

    def show_exception(self):
        traceback.print_exc()
        self.exception_signal.emit(traceback.format_exc())

    def show_exception_gui(self, message: str):
        self.ui.statusbar.showMessage("An unexpected exception occurred.")
        QMessageBox.critical(window, "Unexpected Exception", message)

    def on_open_button_clicked(self):
        filepath, _ = QFileDialog.getOpenFileName(
                window,
                "Open PIMG File...",
                "",
                "M2 Packaged Struct Binary (*.pimg);;All Files (*.*)")
        if filepath != "":
            self.filepath = Path(filepath)
            self.ui.lineEdit.setText(str(self.filepath))
            self.ui.lineEdit.setCursorPosition(len(self.ui.lineEdit.text()))
            self.run()

    def on_compose_check_box_clicked(self):
        self.compose = self.ui.composeCheckBox.isChecked()
        self.run()

    def on_item_activated(self, item: QListWidgetItem):
        self.activated_image_name = item.text()
        activated_image_width, activated_image_height = self.resolutions_by_name.get(self.activated_image_name)
        data = self.images_by_name.get(self.activated_image_name)
        byte_array = QByteArray(data)
        buffer = QBuffer(byte_array)
        buffer.open(QIODeviceBase.OpenModeFlag.ReadOnly)

        pixmap = QPixmap()
        pixmap.loadFromData(buffer.data())

        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        scene = QGraphicsScene()
        scene.addItem(self.pixmap_item)

        self.ui.graphicsView.setScene(scene)
        self.ui.graphicsView.installEventFilter(ResizeFilter(self.pixmap_item))

        self.ui.statusbar.showMessage(f"{self.activated_image_name} ( {activated_image_width} x {activated_image_height} pixels )")

    def on_export_single_button_clicked(self):
        if self.activated_image_name is None:
            return
        self.ui.statusbar.showMessage(f"Exporting {self.activated_image_name}...")
        filepath, _ = QFileDialog.getSaveFileName(
                window,
                "Save Single PNG File...",
                f"{self.activated_image_name}.png",
                "Portable Network Graphics (*.png);;All Files (*.*)")
        if filepath != "":
            with Path(filepath).open(mode="wb") as single_f:
                single_f.write(self.images_by_name[self.activated_image_name])
            self.ui.statusbar.showMessage(f"Export {self.activated_image_name} to {filepath} successfully.")
        else:
            self.ui.statusbar.showMessage("Exporting aborted.")

    def on_export_all_button_clicked(self):
        self.ui.statusbar.showMessage("Exporting all images...")
        savedir = QFileDialog.getExistingDirectory(
            window,
            "Save All PNG Files..."
        )
        if savedir != "":
            for name, image in self.images_by_name.items():
                savepath = Path(savedir) / f"{name}.png"
                with savepath.open(mode="wb") as single_f:
                    single_f.write(image)
            self.ui.statusbar.showMessage(f"Export all images to {savedir} successfully.")
        else:
            self.ui.statusbar.showMessage("Exporting aborted.")

    def run(self):
        if self.filepath is None:
            return
        self.images_by_name = {}
        self.resolutions_by_name = {}
        self.pixmap_item = None
        self.ui.listWidget.clear()
        self.ui.graphicsView.setScene(QGraphicsScene())
        self.ui.statusbar.showMessage("")
        assert temp_path.exists() and temp_path.is_dir()

        clean_temp()
        self.ui.statusbar.showMessage(f"Loading {self.filepath}...")
        threading.Thread(target=self.load_pimg, args=(self.compose,)).start()

    def load_pimg(self, compose):
        filestem = self.filepath.stem
        temp_path_dir = temp_path / f"{filestem}/"
        temp_path_json = temp_path / f"{filestem}.json"
        temp_path_resx_json = temp_path / f"{filestem}.resx.json"

        process = subprocess.Popen(
            [Path("psbdecompile/PsbDecompile.exe"), self.filepath],
            creationflags=subprocess.CREATE_NO_WINDOW,
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)
        shutil.move(self.filepath.parent / f"{filestem}/", temp_path_dir)
        shutil.move(self.filepath.parent / f"{filestem}.json", temp_path_json)
        shutil.move(self.filepath.parent / f"{filestem}.resx.json", temp_path_resx_json)

        with temp_path_resx_json.open(mode="r", encoding="UTF-8") as resx_json_f:
            resx_json_loaded: dict = json.load(resx_json_f)
            if resx_json_loaded.get("PsbType") != "Pimg":
                QMessageBox.critical(window, "Invalid File", "This is not a valid PIMG file.")
                return

        with temp_path_json.open(mode="r", encoding="UTF-8") as json_f:
            pimgjson: PIMGJson = PIMGJson.model_validate_json(json_f.read())
        base_width, base_height = pimgjson.width, pimgjson.height
        layers_by_name: dict[str, Layer] = {}
        layers_by_id: dict[int, Layer] = {}
        for layer in pimgjson.layers:
            if compose:
                assert len(layer.name) == 2 and str.isalpha(layer.name)
                layer.name = layer.name.lower()
            layers_by_name[layer.name] = layer
            layers_by_id[layer.layer_id] = layer
        layers_by_name = dict(sorted(layers_by_name.items()))

        if compose:
            group_base_names = {}  # a: ad
            for name, layer in layers_by_name.items():
                group_layer_name, single_layer_name = name  # a, d
                image_filepath = temp_path / filestem / f"{layer.layer_id}.png"
                if layer.width == base_width and layer.height == base_height and not has_transparency(image_filepath):
                    # base
                    assert group_layer_name not in group_base_names.keys()
                    group_base_names[group_layer_name] = name

            for name, layer in layers_by_name.items():
                group_layer_name, single_layer_name = name  # a, d
                image_filepath = temp_path / filestem / f"{layer.layer_id}.png"
                if layer.width == base_width and layer.height == base_height and not has_transparency(image_filepath):
                    # base
                    image_filepath = temp_path / filestem / f"{layer.layer_id}.png"
                    with image_filepath.open(mode="rb") as image_f:
                        self.images_by_name[name] = image_f.read()
                else:
                    # diff
                    if layer.diff_id is not None:
                        assert layers_by_id[layer.diff_id].name in group_base_names.values()
                        self.images_by_name[name] = self.compose_diff(layers_by_id[layer.diff_id], layer, filestem)
                    else:
                        if group_layer_name not in group_base_names.keys():
                            group_layer_name = next(reversed(group_base_names))
                        self.images_by_name[name] = self.compose_diff(layers_by_name[group_base_names[group_layer_name]], layer, filestem)
                self.resolutions_by_name[name] = (base_width, base_height)
        else:
            for name, layer in layers_by_name.items():
                image_filepath = temp_path / filestem / f"{layer.layer_id}.png"
                with image_filepath.open(mode="rb") as image_f:
                    self.images_by_name[name] = image_f.read()
                    self.resolutions_by_name[name] = (layer.width, layer.height)

        for name in self.images_by_name.keys():
            item = QListWidgetItem(name)
            item.setSizeHint(QSize(0, 35))
            self.ui.listWidget.addItem(item)
        self.ui.statusbar.showMessage(f"{self.filepath} loaded.")

    def compose_diff(self, base_layer: Layer, diff_layer: Layer, filestem: str) -> bytes:
        base_filepath = temp_path / filestem / f"{base_layer.layer_id}.png"
        diff_filepath = temp_path / filestem / f"{diff_layer.layer_id}.png"
        assert all((base_filepath.exists(), diff_filepath.exists()))
        base = Image.open(base_filepath).convert("RGBA")
        diff = Image.open(diff_filepath).convert("RGBA")
        # TODO: visible, opacity
        self.paste_with_clip(base, diff, diff_layer.left, diff_layer.top)
        byte_io = io.BytesIO()
        base.save(byte_io, format="PNG")
        return byte_io.getvalue()

    def paste_with_clip(self, bg: Image.Image, fg: Image.Image, left: int, top: int):
        bg_w, bg_h = bg.size
        fg_w, fg_h = fg.size
        src_left = max(0, -left)
        src_top = max(0, -top)
        src_right = min(fg_w, bg_w - left)
        src_bottom = min(fg_h, bg_h - top)
        if src_right <= src_left or src_bottom <= src_top:
            return
        fg_cropped = fg.crop((src_left, src_top, src_right, src_bottom))
        dest_x = max(0, left)
        dest_y = max(0, top)
        bg.paste(fg_cropped, (dest_x, dest_y), fg_cropped)


def clean_temp():
    for item in Path(temp_path).iterdir():
        if item.is_file() or item.is_symlink():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    dependencies: list[Path] = [
        Path("psbdecompile/PsbDecompile.exe"),
    ]
    missing_dependencies: list[str] = []
    for dependency in dependencies:
        if not dependency.exists():
            missing_dependencies.append(str(dependency.absolute()))
    if len(missing_dependencies) > 0:
        QMessageBox.warning(None,
                            "Can’t Find Required Files",
                            f"The following files are missing, please download the app again:"
                            f"\n\n"
                            f"{"\n".join(missing_dependencies)}")
        sys.exit(0)

    Path(temp_path).mkdir(exist_ok=True)
    atexit.register(clean_temp)

    window = MyApp()
    sys.exit(app.exec())
