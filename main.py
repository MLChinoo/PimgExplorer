import atexit
import io
import json
import sys
import traceback
from pathlib import Path
import shutil
import subprocess

from PIL import Image
from PySide6.QtCore import QByteArray, QBuffer, QIODeviceBase, QSize
from PySide6.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox, QGraphicsScene, QGraphicsPixmapItem, \
    QListWidgetItem
from PySide6.QtGui import QPixmap
from MainWindow import Ui_MainWindow
from event_filter import ResizeFilter
from json_model import PIMGJson, Layer

window = None
temp_path = Path("temp/")

class MyApp(QMainWindow):
    filepath: Path = None
    compose: bool = False
    images_by_name: dict[str, bytes] = None
    activated_image_name: str = None
    pixmap_item = None

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.openButton.clicked.connect(self.on_open_button_clicked)
        self.ui.composeCheckBox.clicked.connect(self.on_compose_check_box_clicked)
        self.ui.listWidget.itemActivated.connect(self.on_item_activated)
        self.ui.exportSingleButton.clicked.connect(self.on_export_single_button_clicked)
        self.ui.exportAllButton.clicked.connect(self.on_export_all_button_clicked)
        self.show()

    def on_open_button_clicked(self):
        filepath, _ = QFileDialog.getOpenFileName(
                window,
                "Open PIMG File...",
                "",
                "M2 Packaged Struct Binary (*.pimg);;All files (*.*)")
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

    def on_export_single_button_clicked(self):
        if self.activated_image_name is None:
            return
        filepath, _ = QFileDialog.getSaveFileName(
                window,
                "Save Single PNG File...",
                f"{self.activated_image_name}.png",
                "Portable Network Graphics (*.png);;All files (*.*)")
        if filepath != "":
            with Path(filepath).open(mode="wb") as single_f:
                single_f.write(self.images_by_name[self.activated_image_name])

    def on_export_all_button_clicked(self):
        if self.activated_image_name is None:
            return
        savedir = QFileDialog.getExistingDirectory(
            window,
            "Save All PNG Files..."
        )
        if savedir != "":
            for name, image in self.images_by_name.items():
                savepath = Path(savedir) / f"{name}.png"
                with savepath.open(mode="wb") as single_f:
                    single_f.write(image)

    def run(self):
        if self.filepath is None:
            return
        self.images_by_name = {}
        self.pixmap_item = None
        self.ui.listWidget.clear()
        self.ui.graphicsView.setScene(QGraphicsScene())
        assert temp_path.exists() and temp_path.is_dir()
        try:
            clean_temp()
            self.load_pimg(compose=self.compose)
        except Exception:
            traceback.print_exc()
            QMessageBox.critical(window, "Unexpected Exception", traceback.format_exc())

    def load_pimg(self, compose):
        filestem = self.filepath.stem
        temp_path_dir = temp_path / f"{filestem}/"
        temp_path_json = temp_path / f"{filestem}.json"
        temp_path_resx_json = temp_path / f"{filestem}.resx.json"

        subprocess.run(["psbdecompile/PsbDecompile.exe", str(self.filepath)], check=True)
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
        for layer in pimgjson.layers:
            if compose:
                assert len(layer.name) == 2 and str.isalpha(layer.name)
                layer.name = layer.name.lower()
            layers_by_name[layer.name] = layer
        layers_by_name = dict(sorted(layers_by_name.items()))

        if compose:
            head_name, head_layer = next(iter(layers_by_name.items()))
            assert head_layer.width == base_width and head_layer.height == base_height
            last_base_name = head_name
            for name, layer in layers_by_name.items():
                if name[1] == "a" and layer.width == base_width and layer.height == base_height:
                    # 需要更多样本来证实该规律
                    # base
                    image_filepath = temp_path / filestem / f"{layer.layer_id}.png"
                    with image_filepath.open(mode="rb") as image_f:
                        self.images_by_name[name] = image_f.read()
                    last_base_name = name
                else:
                    # diff
                    self.images_by_name[name] = self.compose_diff(layers_by_name[last_base_name], layer, filestem)
        else:
            for name, layer in layers_by_name.items():
                image_filepath = temp_path / filestem / f"{layer.layer_id}.png"
                with image_filepath.open(mode="rb") as image_f:
                    self.images_by_name[name] = image_f.read()

        for name in self.images_by_name.keys():
            item = QListWidgetItem(name)
            item.setSizeHint(QSize(0, 35))
            self.ui.listWidget.addItem(item)

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
