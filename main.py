import wx
import tkinter as tk
from tkinter import filedialog
import json
import wave
import shutil

# Dictionary for localization
localization = {
    "English": {
        "decode_tab": "Decode",
        "encode_tab": "Encode",
        "info_tab": "Info",
        "settings_tab": "Settings",
        "asrc_file": "ASRC File:",
        "output_file": "Output File:",
        "audio_file": "Audio File:",
        "asrc_output_file": "ASRC Output File:",
        "info_file": "Info File:",
        "convert": "Convert",
        "format": "Format:",
        "info_text": "File Information:",
        "export_json": "Export to JSON",
        "language": "Language:",
        "about": "About",
        "about_text": "Apollo Justice Sound Tool\n\n"
                      "This program allows you to decode, encode, and get information about ASRC files.\n\n"
                      "Developer: FILLDOR\n"
                      "Team: Translation Bureau \"Phoenix & Co\"\n"
                      "License: Apache 2.0",
        "conversion_completed": "Conversion completed!"
    },
    "Russian": {
        "decode_tab": "Декодирование",
        "encode_tab": "Кодирование",
        "info_tab": "Информация",
        "settings_tab": "Настройки",
        "asrc_file": "ASRC Файл:",
        "output_file": "Выходной Файл:",
        "audio_file": "Аудио Файл:",
        "asrc_output_file": "ASRC Выходной Файл:",
        "info_file": "Файл Информации:",
        "convert": "Конвертировать",
        "format": "Формат:",
        "info_text": "Информация о Файле:",
        "export_json": "Экспорт в JSON",
        "language": "Язык:",
        "about": "О Программе",
        "about_text": "Apollo Justice Sound Tool\n\n"
                      "Эта программа позволяет декодировать, кодировать и получать информацию о ASRC файлах.\n\n"
                      "Разработчик: FILLDOR\n"
                      "Команда: Бюро переводов \"Феникс & Ко\"\n"
                      "Лицензия: Apache 2.0",
        "conversion_completed": "Конвертация завершена!"
    },
    "Ukrainian": {
        "decode_tab": "Декодування",
        "encode_tab": "Кодування",
        "info_tab": "Інформація",
        "settings_tab": "Налаштування",
        "asrc_file": "ASRC Файл:",
        "output_file": "Вихідний Файл:",
        "audio_file": "Аудіо Файл:",
        "asrc_output_file": "ASRC Вихідний Файл:",
        "info_file": "Файл Інформації:",
        "convert": "Конвертувати",
        "format": "Формат:",
        "info_text": "Інформація про Файл:",
        "export_json": "Експорт в JSON",
        "language": "Мова:",
        "about": "Про Програму",
        "about_text": "Apollo Justice Sound Tool\n\n"
                      "Ця програма дозволяє декодувати, кодувати та отримувати інформацію про ASRC файли.\n\n"
                      "Розробник: FILLDOR\n"
                      "Команда: Бюро перекладів \"Фенікс & Ко\"\n"
                      "Ліцензія: Apache 2.0",
        "conversion_completed": "Конвертація завершена!"
    },
    "Japanese": {
        "decode_tab": "デコード",
        "encode_tab": "エンコード",
        "info_tab": "情報",
        "settings_tab": "設定",
        "asrc_file": "ASRC ファイル:",
        "output_file": "出力ファイル:",
        "audio_file": "オーディオファイル:",
        "asrc_output_file": "ASRC 出力ファイル:",
        "info_file": "情報ファイル:",
        "convert": "変換",
        "format": "フォーマット:",
        "info_text": "ファイル情報:",
        "export_json": "JSONにエクスポート",
        "language": "言語:",
        "about": "このプログラムについて",
        "about_text": "Apollo Justice Sound Tool\n\n"
                      "このプログラムを使用すると、ASRC ファイルをデコード、エンコードし、情報を取得できます。\n\n"
                      "開発者: FILLDOR\n"
                      "チーム: 翻訳局「フェニックス＆コー」\n"
                      "ライセンス: Apache 2.0",
        "conversion_completed": "変換が完了しました!"
    }
}

# Custom info function
def get_file_info(file_path):
    with open(file_path, 'rb') as f:
        magic = f.read(4)
        if magic == b'srch':
            sid = read_u32(f)
            return {"type": "srch", "id": sid}
        elif magic != b'srcd':
            raise ValueError("not a valid asrc file")

        assert read_u32(f) == 0  # always 0
        file_size = read_u32(f)
        assert f.read(4) == b'wav '

        strm = read_u32(f)
        assert strm <= 1
        strm = bool(strm)
        id = read_u32(f)
        unk0 = read_u32(f)

        channels = read_u32(f)
        samples = read_u32(f)
        urate = read_u32(f)
        rate = read_u32(f)
        depth = read_u32(f)

        assert read_u32(f) == 1  # always 1

        loop = ord(f.read(1))
        assert loop <= 1
        loop = bool(loop)
        lps = read_u32(f)
        lpe = read_u32(f)

        mark_count = read_u32(f)
        if mark_count > 0:
            mark = []
            for _ in range(mark_count):
                mark.append((read_u32(f), read_u32(f)))
        else:
            mark = None

        assert f.read(9) == b'\0' * 9  # always 0
        unk1 = read_u32(f)

        header_size = read_u32(f)
        data_offset = read_u32(f)

        assert header_size == f.tell()

        f.seek(0, 2)
        assert file_size == f.tell() - header_size
        f.seek(header_size)

        with wave.open(f) as w:
            params = w.getparams()
        assert data_offset == f.tell() - header_size
        f.seek(header_size)

        soff = samples % channels != 0
        if soff:
            samples -= 1

        assert channels == params.nchannels
        assert samples == params.nframes * params.nchannels
        assert rate == params.framerate
        assert depth == params.sampwidth * 8

        return {
            "type": "srcd",
            "id": id,
            "unk0": unk0,
            "unk1": unk1,
            "urate": urate,
            "soff": soff,
            "strm": strm,
            "loop": loop,
            "lps": lps,
            "lpe": lpe,
            "mark": mark,
            "channels": channels,
            "samples": samples,
            "rate": rate,
            "depth": depth
        }

def read_u32(f):
    return int.from_bytes(f.read(4), 'little')

def decode_file(asrc_file, output_file):
    with open(asrc_file, 'rb') as f:
        # Validate and seek to end of header
        magic = f.read(4)
        if magic == b'srch':
            raise ValueError("srch files contain no audio data")

        if magic != b'srcd':
            raise ValueError("not a valid asrc file")

        assert read_u32(f) == 0  # always 0
        file_size = read_u32(f)
        assert f.read(4) == b'wav '

        strm = read_u32(f)
        assert strm <= 1
        id = read_u32(f)
        unk0 = read_u32(f)

        channels = read_u32(f)
        samples = read_u32(f)
        urate = read_u32(f)
        rate = read_u32(f)
        depth = read_u32(f)

        assert read_u32(f) == 1  # always 1

        loop = ord(f.read(1))
        assert loop <= 1
        lps = read_u32(f)
        lpe = read_u32(f)

        mark_count = read_u32(f)
        if mark_count > 0:
            for _ in range(mark_count):
                read_u32(f)
                read_u32(f)

        assert f.read(9) == b'\0' * 9  # always 0
        unk1 = read_u32(f)

        header_size = read_u32(f)
        data_offset = read_u32(f)

        assert header_size == f.tell()

        f.seek(0, 2)
        assert file_size == f.tell() - header_size
        f.seek(header_size)

        with open(output_file, 'wb') as of:
            shutil.copyfileobj(f, of)

def encode_file(audio_file, asrc_output_file, info_file):
    with wave.open(audio_file, 'rb') as w:
        params = w.getparams()
    data_offset = w.getnframes()

    with open(audio_file, 'rb') as f:
        f.seek(0, 2)
        file_size = f.tell()
        f.seek(0)

        with open(asrc_output_file, 'wb') as of:
            of.write(b'srcd')
            write_u32(of, 0)  # always 0
            write_u32(of, file_size)
            of.write(b'wav ')

            write_u32(of, 0)  # strm
            write_u32(of, 0)  # id
            write_u32(of, 0)  # unk0

            write_u32(of, params.nchannels)
            write_u32(of, params.nframes * params.nchannels)
            write_u32(of, 44100)  # urate
            write_u32(of, params.framerate)
            write_u32(of, params.sampwidth * 8)

            write_u32(of, 1)  # always 1

            of.write(b'\x00')  # loop
            write_u32(of, 0)  # lps
            write_u32(of, params.nframes - 1)  # lpe

            write_u32(of, 0)  # mark_count

            of.write(b'\0' * 9)  # always 0
            write_u32(of, 0)  # unk1

            write_u32(of, of.tell() + 8)
            write_u32(of, data_offset)

            shutil.copyfileobj(f, of)

def write_u32(f, x):
    f.write(x.to_bytes(4, 'little'))

class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Apollo Justice Sound Tool", size=(600, 400))
        icon = wx.Icon("_internal/1.ico", wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        self.panel = wx.Panel(self)
        self.notebook = wx.Notebook(self.panel)

        # Create tabs
        self.tab_decode = wx.Panel(self.notebook)
        self.tab_encode = wx.Panel(self.notebook)
        self.tab_info = wx.Panel(self.notebook)
        self.tab_settings = wx.Panel(self.notebook)

        self.notebook.AddPage(self.tab_decode, localization["English"]["decode_tab"])
        self.notebook.AddPage(self.tab_encode, localization["English"]["encode_tab"])
        self.notebook.AddPage(self.tab_info, localization["English"]["info_tab"])
        self.notebook.AddPage(self.tab_settings, localization["English"]["settings_tab"])

        self.current_language = "English"
        self.setup_decode_tab()
        self.setup_encode_tab()
        self.setup_info_tab()
        self.setup_settings_tab()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.EXPAND)
        self.panel.SetSizer(sizer)

        self.Centre()
        self.Show()

    def setup_decode_tab(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        # ASRC file input
        asrc_label = wx.StaticText(self.tab_decode, label=localization[self.current_language]["asrc_file"])
        sizer.Add(asrc_label, 0, wx.ALL, 5)

        asrc_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.asrc_input = wx.TextCtrl(self.tab_decode)
        asrc_button = wx.Button(self.tab_decode, label="...")
        asrc_button.Bind(wx.EVT_BUTTON, self.on_asrc_file_decode)
        asrc_sizer.Add(self.asrc_input, 1, wx.EXPAND)
        asrc_sizer.Add(asrc_button, 0, wx.LEFT, 5)
        sizer.Add(asrc_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Output file input
        output_label = wx.StaticText(self.tab_decode, label=localization[self.current_language]["output_file"])
        sizer.Add(output_label, 0, wx.ALL, 5)

        self.output_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.output_input = wx.TextCtrl(self.tab_decode)
        output_button = wx.Button(self.tab_decode, label="...")
        output_button.Bind(wx.EVT_BUTTON, self.on_output_file_decode)
        self.output_sizer.Add(self.output_input, 1, wx.EXPAND)
        self.output_sizer.Add(output_button, 0, wx.LEFT, 5)
        sizer.Add(self.output_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Convert button
        convert_button = wx.Button(self.tab_decode, label=localization[self.current_language]["convert"])
        convert_button.Bind(wx.EVT_BUTTON, self.on_convert_decode)
        sizer.Add(convert_button, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.tab_decode.SetSizer(sizer)

    def setup_encode_tab(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Audio file input
        audio_label = wx.StaticText(self.tab_encode, label=localization[self.current_language]["audio_file"])
        sizer.Add(audio_label, 0, wx.ALL, 5)

        audio_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.audio_input = wx.TextCtrl(self.tab_encode)
        audio_button = wx.Button(self.tab_encode, label="...")
        audio_button.Bind(wx.EVT_BUTTON, self.on_audio_file_encode)
        audio_sizer.Add(self.audio_input, 1, wx.EXPAND)
        audio_sizer.Add(audio_button, 0, wx.LEFT, 5)
        sizer.Add(audio_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # ASRC output file input
        asrc_output_label = wx.StaticText(self.tab_encode, label=localization[self.current_language]["asrc_output_file"])
        sizer.Add(asrc_output_label, 0, wx.ALL, 5)

        asrc_output_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.asrc_output_input = wx.TextCtrl(self.tab_encode)
        asrc_output_button = wx.Button(self.tab_encode, label="...")
        asrc_output_button.Bind(wx.EVT_BUTTON, self.on_asrc_output_file_encode)
        asrc_output_sizer.Add(self.asrc_output_input, 1, wx.EXPAND)
        asrc_output_sizer.Add(asrc_output_button, 0, wx.LEFT, 5)
        sizer.Add(asrc_output_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Info file input
        info_label = wx.StaticText(self.tab_encode, label=localization[self.current_language]["info_file"])
        sizer.Add(info_label, 0, wx.ALL, 5)

        info_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.info_input = wx.TextCtrl(self.tab_encode)
        info_button = wx.Button(self.tab_encode, label="...")
        info_button.Bind(wx.EVT_BUTTON, self.on_info_file_encode)
        info_sizer.Add(self.info_input, 1, wx.EXPAND)
        info_sizer.Add(info_button, 0, wx.LEFT, 5)
        sizer.Add(info_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Convert button
        convert_button = wx.Button(self.tab_encode, label=localization[self.current_language]["convert"])
        convert_button.Bind(wx.EVT_BUTTON, self.on_convert_encode)
        sizer.Add(convert_button, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.tab_encode.SetSizer(sizer)

    def setup_info_tab(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        # ASRC file input
        asrc_label = wx.StaticText(self.tab_info, label=localization[self.current_language]["asrc_file"])
        sizer.Add(asrc_label, 0, wx.ALL, 5)

        asrc_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.asrc_info_input = wx.TextCtrl(self.tab_info)
        asrc_button = wx.Button(self.tab_info, label="...")
        asrc_button.Bind(wx.EVT_BUTTON, self.on_asrc_file_info)
        asrc_sizer.Add(self.asrc_info_input, 1, wx.EXPAND)
        asrc_sizer.Add(asrc_button, 0, wx.LEFT, 5)
        sizer.Add(asrc_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Info text box
        info_text_label = wx.StaticText(self.tab_info, label=localization[self.current_language]["info_text"])
        sizer.Add(info_text_label, 0, wx.ALL, 5)

        self.info_text = wx.TextCtrl(self.tab_info, style=wx.TE_MULTILINE | wx.TE_READONLY)
        sizer.Add(self.info_text, 1, wx.EXPAND | wx.ALL, 5)

        # Export to JSON button
        export_button = wx.Button(self.tab_info, label=localization[self.current_language]["export_json"])
        export_button.Bind(wx.EVT_BUTTON, self.on_export_json)
        sizer.Add(export_button, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.tab_info.SetSizer(sizer)

    def setup_settings_tab(self):
        self.notebook_settings = wx.Notebook(self.tab_settings)

        # Settings tab
        settings_panel = wx.Panel(self.notebook_settings)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Language selection
        language_label = wx.StaticText(settings_panel, label=localization[self.current_language]["language"])
        sizer.Add(language_label, 0, wx.ALL, 5)

        language_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.language_choice = wx.Choice(settings_panel, choices=list(localization.keys()))
        self.language_choice.Bind(wx.EVT_CHOICE, self.on_language_change)
        language_sizer.Add(self.language_choice, 0, wx.LEFT, 5)
        sizer.Add(language_sizer, 0, wx.ALL, 5)

        settings_panel.SetSizer(sizer)
        self.notebook_settings.AddPage(settings_panel, localization[self.current_language]["settings_tab"])

        # About tab
        about_panel = wx.Panel(self.notebook_settings)
        sizer = wx.BoxSizer(wx.VERTICAL)

        about_text = wx.StaticText(about_panel, label=localization[self.current_language]["about_text"])
        sizer.Add(about_text, 0, wx.ALL, 5)

        about_panel.SetSizer(sizer)
        self.notebook_settings.AddPage(about_panel, localization[self.current_language]["about"])

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook_settings, 1, wx.EXPAND)
        self.tab_settings.SetSizer(sizer)

    def on_language_change(self, event):
        self.current_language = self.language_choice.GetString(self.language_choice.GetSelection())
        self.update_ui_language()

    def update_ui_language(self):
        self.notebook.SetPageText(0, localization[self.current_language]["decode_tab"])
        self.notebook.SetPageText(1, localization[self.current_language]["encode_tab"])
        self.notebook.SetPageText(2, localization[self.current_language]["info_tab"])
        self.notebook.SetPageText(3, localization[self.current_language]["settings_tab"])

        # Update decode tab
        self.tab_decode.GetSizer().GetItem(0).GetWindow().SetLabel(localization[self.current_language]["asrc_file"])
        self.tab_decode.GetSizer().GetItem(2).GetWindow().SetLabel(localization[self.current_language]["output_file"])
        self.tab_decode.GetSizer().GetItem(4).GetWindow().SetLabel(localization[self.current_language]["convert"])

        # Update encode tab
        self.tab_encode.GetSizer().GetItem(0).GetWindow().SetLabel(localization[self.current_language]["audio_file"])
        self.tab_encode.GetSizer().GetItem(2).GetWindow().SetLabel(localization[self.current_language]["asrc_output_file"])
        self.tab_encode.GetSizer().GetItem(4).GetWindow().SetLabel(localization[self.current_language]["info_file"])
        self.tab_encode.GetSizer().GetItem(6).GetWindow().SetLabel(localization[self.current_language]["convert"])

        # Update info tab
        self.tab_info.GetSizer().GetItem(0).GetWindow().SetLabel(localization[self.current_language]["asrc_file"])
        self.tab_info.GetSizer().GetItem(2).GetWindow().SetLabel(localization[self.current_language]["info_text"])
        self.tab_info.GetSizer().GetItem(4).GetWindow().SetLabel(localization[self.current_language]["export_json"])

        # Update settings tab
        self.notebook_settings.GetPage(0).GetSizer().GetItem(0).GetWindow().SetLabel(localization[self.current_language]["language"])
        self.notebook_settings.SetPageText(0, localization[self.current_language]["settings_tab"])
        self.notebook_settings.SetPageText(1, localization[self.current_language]["about"])
        self.notebook_settings.GetPage(1).GetSizer().GetItem(0).GetWindow().SetLabel(localization[self.current_language]["about_text"])

        self.tab_decode.Layout()
        self.tab_encode.Layout()
        self.tab_info.Layout()
        self.tab_settings.Layout()

    def on_asrc_file_decode(self, event):
        root = tk.Tk()
        root.withdraw()
        file_paths = filedialog.askopenfilenames(filetypes=[("ASRC files", "*.asrc.*")])
        if file_paths:
            self.asrc_input.SetValue(";".join(file_paths))
            if len(file_paths) > 1:
                self.output_sizer.Hide(self.output_input)
                self.output_sizer.Hide(self.output_sizer.GetItem(1).GetWindow())
                format_sizer = wx.BoxSizer(wx.HORIZONTAL)
                format_label = wx.StaticText(self.tab_decode, label=localization[self.current_language]["format"])
                self.format_choice = wx.Choice(self.tab_decode, choices=["wav", "mp3", "ogg"])
                format_sizer.Add(format_label, 0, wx.ALIGN_CENTER_VERTICAL)
                format_sizer.Add(self.format_choice, 0, wx.LEFT, 5)
                self.output_sizer.Add(format_sizer, 0, wx.EXPAND | wx.ALL, 5)
            else:
                self.output_sizer.Show(self.output_input)
                self.output_sizer.Show(self.output_sizer.GetItem(1).GetWindow())
                if hasattr(self, 'format_choice'):
                    self.output_sizer.Remove(2)
                    self.format_choice.Destroy()
                    del self.format_choice
            self.tab_decode.Layout()

    def on_output_file_decode(self, event):
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV files", "*.wav"), ("MP3 files", "*.mp3"), ("OGG files", "*.ogg")])
        if file_path:
            self.output_input.SetValue(file_path)

    def on_convert_decode(self, event):
        asrc_files = self.asrc_input.GetValue().split(";")
        if len(asrc_files) > 1:
            format = self.format_choice.GetString(self.format_choice.GetSelection())
            for asrc_file in asrc_files:
                output_file = asrc_file.rsplit('.', 1)[0] + f".{format}"
                decode_file(asrc_file, output_file)
        else:
            asrc_file = asrc_files[0]
            output_file = self.output_input.GetValue()
            decode_file(asrc_file, output_file)
        wx.MessageBox(localization[self.current_language]["conversion_completed"], "Info", wx.OK | wx.ICON_INFORMATION)

    def on_audio_file_encode(self, event):
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(filetypes=[("Audio files", "*.mp3;*.wav;*.ogg")])
        if file_path:
            self.audio_input.SetValue(file_path)

    def on_asrc_output_file_encode(self, event):
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.asksaveasfilename(defaultextension=".asrc", filetypes=[("ASRC files", "*.asrc.*")])
        if file_path:
            # Remove any existing .asrc extension before adding the new one
            if file_path.endswith('.asrc'):
                file_path = file_path[:-5]  # Remove .asrc
            self.asrc_output_input.SetValue(file_path) # ВОТ ТУТ БЫЛ БАГ! (я в конце делал + ".asrc")

    def on_info_file_encode(self, event):
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            self.info_input.SetValue(file_path)

    def on_convert_encode(self, event):
        audio_file = self.audio_input.GetValue()
        asrc_output_file = self.asrc_output_input.GetValue()
        info_file = self.info_input.GetValue()
        encode_file(audio_file, asrc_output_file, info_file)
        wx.MessageBox(localization[self.current_language]["conversion_completed"], "Info", wx.OK | wx.ICON_INFORMATION)

    def on_asrc_file_info(self, event):
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(filetypes=[("ASRC files", "*.asrc.*")])
        if file_path:
            self.asrc_info_input.SetValue(file_path)
            info = get_file_info(file_path)
            self.info_text.SetValue(str(info))

    def on_export_json(self, event):
        asrc_file = self.asrc_info_input.GetValue()
        info = get_file_info(asrc_file)
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(info, f, indent=4)

if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    app.MainLoop()
