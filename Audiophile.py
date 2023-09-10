import os
import sys
import threading
import ffmpeg
import youtube_dl
import yt_dlp
import urllib.parse
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QComboBox, QDialog, QFormLayout, QColorDialog, QFontDialog, QSpinBox, QCheckBox, QTextEdit, QPlainTextEdit, QTextBrowser
from PyQt5.QtGui import QIcon, QTextCursor, QColor
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from pytube import YouTube
from pydub import AudioSegment

FFMPEG_PATH = r"PATH_TO_FFMPEG.EXE"
preferred_conversion_method = 'ffmpeg'

def download_youtube_audio(youtube_url, output_dir='output', format='aac', bitrate='320k', sampling_rate=48000, bit_depth='24-bit', conversion_method='ffmpeg', library_source='pytube'):
    os.makedirs(output_dir, exist_ok=True)

    try:
        if library_source == 'pytube':
            yt = YouTube(youtube_url)
            audio_stream = yt.streams.filter(only_audio=True).first()
            audio_file = audio_stream.download(output_path=output_dir)

            audio_output_file = os.path.splitext(os.path.basename(audio_file))[0]
            if format == 'aac':
                audio_output_file += '.m4a'
                codec = 'aac'
            elif format == 'mp3':
                audio_output_file += '.mp3'
                codec = 'libmp3lame'
            elif format == 'flac':
                audio_output_file += '.flac'
                codec = 'flac'
                bitrate = None
                sampling_rate = None
                bit_depth = None
            elif format == 'wav':
                audio_output_file += '.wav'
                codec = 'pcm_s16le'
                bitrate = None
                sampling_rate = None
                bit_depth = None
            else:
                print("Invalid audio format selected.")
                return

            audio_output_path = os.path.join(output_dir, audio_output_file)

            if conversion_method == 'ffmpeg':
                if bitrate is not None and sampling_rate is not None:
                    ffmpeg.input(audio_file).output(audio_output_path, loglevel='error', **{
                        'b:a': bitrate,
                        'ar': sampling_rate,
                        'codec:a': codec
                    }).run(cmd=FFMPEG_PATH, overwrite_output=True)
                else:
                    ffmpeg.input(audio_file).output(audio_output_path, loglevel='error', **{
                        'codec:a': codec
                    }).run(cmd=FFMPEG_PATH, overwrite_output=True)
            elif conversion_method == 'pydub':
                audio = AudioSegment.from_file(audio_file, format='mp4')
                if format == 'aac':
                    audio.export(audio_output_path, format='m4a', codec='aac')
                elif format == 'mp3':
                    audio.export(audio_output_path, format='mp3', codec='libmp3lame')
                elif format == 'flac':
                    audio.export(audio_output_path, format='flac')
                elif format == 'wav':
                    audio.export(audio_output_path, format='wav')

            os.remove(audio_file)

            print(f"Conversion for {youtube_url} to {format} completed successfully.")

        elif library_source == 'youtube_dl':
            ydl_opts = {
                'format': f'bestaudio/best',
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'postprocessors': [],
            }

            if conversion_method == 'Default':
                ydl_opts['postprocessors'].append({'key': 'FFmpegExtractAudio'})
            elif conversion_method == 'ffmpeg':
                ydl_opts['postprocessors'].append({'key': 'FFmpegExtractAudio'})
            elif conversion_method == 'pydub':
                ydl_opts['postprocessors'].append({'key': 'pydubPP'})

            ydl_opts['postprocessors'].append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format,
                'preferredquality': '320',
            })

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])

            print(f"Conversion for {youtube_url} using youtube_dl completed successfully.")

        elif library_source == 'yt_dlp':
            ydl_opts = {
                'format': f'bestaudio/best',
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'postprocessors': [],
            }

            if conversion_method == 'Default':
                ydl_opts['postprocessors'].append({'key': 'FFmpegExtractAudio'})
            elif conversion_method == 'ffmpeg':
                ydl_opts['postprocessors'].append({'key': 'FFmpegExtractAudio'})
            elif conversion_method == 'pydub':
                ydl_opts['postprocessors'].append({'key': 'FFmpegExtractAudioPP'})

            ydl_opts['postprocessors'].append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format,
                'preferredquality': '320',
            })

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])

            print(f"Conversion for {youtube_url} using yt_dlp completed successfully.")

        else:
            print("Invalid library source selected.")
            return
    except Exception as e:
        print(f"An error occurred for {youtube_url}: {e}")
        print(f"An error occurred for {youtube_url}: {e}")
        self.conversion_status_label.setText(f"Conversion Status: Error - {str(e)}")

class DownloadWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, youtube_url, output_dir, audio_format, bitrate, sampling_rate, bit_depth, conversion_method, library_source):
        super().__init__()
        self.youtube_url = youtube_url
        self.output_dir = output_dir
        self.audio_format = audio_format
        self.bitrate = bitrate
        self.sampling_rate = sampling_rate
        self.bit_depth = bit_depth
        self.conversion_method = conversion_method
        self.library_source = library_source

    def download_and_convert(self):
        try:
            download_youtube_audio(
                self.youtube_url,
                self.output_dir,
                self.audio_format,
                self.bitrate,
                self.sampling_rate,
                self.bit_depth,
                self.conversion_method,
                self.library_source
            )
            print(f"Conversion for {self.youtube_url} to {self.audio_format} completed successfully.")
            self.finished.emit(f"Conversion for {self.youtube_url} to {self.audio_format} completed successfully.")
        except Exception as e:
            error_message = f"An error occurred for {self.youtube_url}: {e}"
            print(error_message)
            self.error.emit(error_message)

class Console(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: black; color: lightgreen;")
        self.setReadOnly(True)

    def append_message(self, message, color=QColor(0, 255, 0)):
        self.setTextColor(color)
        self.append(message)

    def append_error(self, error_message):
        self.append_message(error_message, color=QColor(255, 0, 0))

class UrlConversionWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.url_entries = []
        self.convert_buttons = []
        self.start_conversion_buttons = []

        self.layout = QVBoxLayout()

        url_label = QLabel("Enter YouTube URL:")
        self.layout.addWidget(url_label)

        self.add_url_field()
        
        add_urls_button = QPushButton("Add")
        add_urls_button.clicked.connect(self.add_url_field)
        self.layout.addWidget(add_urls_button)
        
        parse_button = QPushButton("Parse")
        parse_button.clicked.connect(self.parse_urls_metadata)
        self.layout.addWidget(parse_button)

        self.download_all_button = QPushButton("Download All")

        self.download_all_button.clicked.connect(self.download_all)
        self.layout.addWidget(self.download_all_button)

        self.download_all_button.setEnabled(False)

        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset_defaults)
        self.layout.addWidget(reset_button)

        self.parsed_info_browser = QTextBrowser()
        self.parsed_info_browser.setStyleSheet("background-color: black; color: lightgreen;")
        self.layout.addWidget(self.parsed_info_browser)

        self.layout.addSpacing(10)

        library_label = QLabel("Select Library Source:")
        self.library_combo_box = QComboBox()
        self.library_combo_box.addItems(['pytube', 'youtube_dl', 'yt_dlp'])
        self.library_combo_box.currentIndexChanged.connect(self.handle_library_change)
        self.layout.addWidget(library_label)
        self.layout.addWidget(self.library_combo_box)

        format_label = QLabel("Select Audio Format:")
        self.layout.addWidget(format_label)

        self.format_combo_box = QComboBox()
        self.format_combo_box.addItems(['aac', 'mp3', 'flac', 'wav'])
        self.format_combo_box.currentIndexChanged.connect(self.handle_format_change)
        self.layout.addWidget(format_label)
        self.layout.addWidget(self.format_combo_box)
        
        bitrate_label = QLabel("Select Bitrate:")
        self.layout.addWidget(bitrate_label)

        self.bitrate_combo_box = QComboBox()
        self.bitrate_combo_box.addItems(['320k', '640k', '1411k', '1920k', '2560k', '3200k', '3840k', '4599k'])
        self.layout.addWidget(self.bitrate_combo_box)

        bit_depth_label = QLabel("Select Bit Depth:")
        self.layout.addWidget(bit_depth_label)

        self.bit_depth_combo_box = QComboBox()
        self.bit_depth_combo_box.addItems(['16-bit', '24-bit', '32-bit'])
        self.layout.addWidget(self.bit_depth_combo_box)

        sampling_rate_label = QLabel("Select Sampling Rate:")
        self.layout.addWidget(sampling_rate_label)

        self.sampling_rate_combo_box = QComboBox()
        self.sampling_rate_combo_box.addItems(['44100', '48000', '88200', '96000', '176400', '192000'])
        self.layout.addWidget(self.sampling_rate_combo_box)

        conversion_method_label = QLabel("Select Conversion Method:")
        self.layout.addWidget(conversion_method_label)

        self.conversion_method_combo_box = QComboBox()
        self.conversion_method_combo_box.addItems(['Default', 'ffmpeg', 'pydub'])
        self.conversion_method_combo_box.currentIndexChanged.connect(self.handle_conversion_change)
        self.layout.addWidget(self.conversion_method_combo_box)
        
        folder_label = QLabel("Select Output Folder:")
        self.layout.addWidget(folder_label)

        self.folder_entry = QLineEdit()
        self.layout.addWidget(self.folder_entry)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_folder_path)
        self.layout.addWidget(browse_button)

        library_info_label = QLabel("Library Information:\n"
                                    "- pytube: Simple library for downloading YouTube videos. Supports MP3, AAC, FLAC and WAV.\n"
                                    "- youtube_dl: Robust library for downloading YouTube videos with many options. "
                                    "Supports MP3, AAC, FLAC and WAV formats.\n"
                                    "- yt_dlp: Improved version of youtube_dl with additional features and improvements. "
                                    "Supports MP3, AAC, FLAC and WAV formats.")
        self.layout.addWidget(library_info_label)

        self.conversion_status_label = QLabel("Conversion Status: Idle")
        self.layout.addWidget(self.conversion_status_label)

        self.setLayout(self.layout)
    
    def download_all(self):
        for url_entry in self.url_entries:
            self.start_conversion(url_entry)
    
    def reset_defaults(self):
        for url_entry in self.url_entries:
            url_entry.deleteLater()
        self.url_entries.clear()
        for button in self.start_conversion_buttons:
            button.deleteLater()
        self.start_conversion_buttons.clear()

        self.download_all_button.setEnabled(False)
        self.add_url_field()

        self.library_combo_box.setCurrentIndex(0)
        self.handle_library_change()
        self.format_combo_box.setCurrentIndex(0)
        self.handle_format_change()
        self.bitrate_combo_box.setCurrentIndex(0)
        self.sampling_rate_combo_box.setCurrentIndex(0)
        self.bit_depth_combo_box.setCurrentIndex(0)
        self.conversion_method_combo_box.setCurrentIndex(0)
        self.folder_entry.clear()
        self.parsed_info_browser.clear()
        self.conversion_status_label.setText("Conversion Status: Idle")

    def fetch_video_details(self, url):
        try:
            yt = YouTube(url)
            title = yt.title
            author = yt.author

            details = {
                "Name": title,
                "Artist": author
            }
            return details
        except Exception as e:
            return {"Error": str(e)}

    def parse_urls_metadata(self):
        parsed_info = ""

        for url_entry in self.url_entries:
            url = url_entry.text()
            if url:
                video_details = self.fetch_video_details(url)

                if "Error" in video_details:
                    parsed_info += f"Error fetching metadata for {url}: {video_details['Error']}\n\n"
                else:
                    parsed_info += f"Name: {video_details['Name']}\n"
                    parsed_info += f"Artist: {video_details['Artist']}\n\n"

        self.parsed_info_browser.setPlainText(parsed_info)

    def add_url_field(self):
        url_entry = QLineEdit()
        self.url_entries.append(url_entry)

        convert_button = QPushButton("Start Conversion")
        convert_button.clicked.connect(lambda: self.start_conversion(url_entry))
        self.convert_buttons.append(convert_button)

        layout = self.layout

        index = layout.indexOf(self.sender())
        layout.insertWidget(index, url_entry)

        if len(self.url_entries) > 1:
            self.download_all_button.setEnabled(True)
        
            for button in self.start_conversion_buttons:
                button.hide()
        else:
            self.start_conversion_buttons.append(convert_button)
            convert_button.setEnabled(True)
            layout.insertWidget(index, convert_button)

    def handle_library_change(self):
        library_source = self.library_combo_box.currentText()

        disable_bitrate_sampling_bitdepth = library_source in ['flac', 'wav']
        self.bitrate_combo_box.setEnabled(not disable_bitrate_sampling_bitdepth)
        self.sampling_rate_combo_box.setEnabled(not disable_bitrate_sampling_bitdepth)
        self.bit_depth_combo_box.setEnabled(not disable_bitrate_sampling_bitdepth)

        if library_source == 'youtube_dl':
            self.format_combo_box.clear()
            self.format_combo_box.addItems(['aac', 'mp3'])
        else:
            self.format_combo_box.clear()
            self.format_combo_box.addItems(['aac', 'mp3', 'flac', 'wav'])

        self.handle_format_change()

    def browse_folder_path(self):
        folder_selected = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        self.folder_entry.setText(folder_selected)

    def start_conversion(self, url_entry):
        url = url_entry.text()

        self.conversion_status_label.setText(f"Conversion Status: Converting {url}")

        try:
            parsed_url = urllib.parse.urlparse(url)
            url_sanitized = urllib.parse.urlunparse(parsed_url._replace(query=''))
            url_encoded = urllib.parse.quote(url_sanitized, safe=':/')

            output_folder = self.folder_entry.text()
            audio_format = self.format_combo_box.currentText()
            bitrate = self.bitrate_combo_box.currentText()
            sampling_rate = int(self.sampling_rate_combo_box.currentText())
            bit_depth = self.bit_depth_combo_box.currentText()
            conversion_method = self.conversion_method_combo_box.currentText()
            library_source = self.library_combo_box.currentText()

            t = threading.Thread(target=download_youtube_audio,
                                 args=(url_encoded, output_folder, audio_format, bitrate, sampling_rate, bit_depth, conversion_method, library_source))
            t.start()
        except Exception as e:
            error_message = f"An error occurred for {url}: {e}"
            print(error_message)
            self.conversion_status_label.setText(f"Conversion Status: Error - {str(e)}")

    def download_and_convert(self, youtube_url, output_dir, audio_format, bitrate, sampling_rate, bit_depth, conversion_method, library_source):
        worker = DownloadWorker(youtube_url, output_dir, audio_format, bitrate, sampling_rate, bit_depth, conversion_method, library_source)
        worker.finished.connect(self.on_conversion_finished)
        worker.error.connect(self.on_conversion_error)
        worker.download_and_convert()

    def on_conversion_finished(self, message):
        self.conversion_status_label.setText(f"Conversion Status: {message}")

    def on_conversion_error(self, error_message):
        self.conversion_status_label.setText(f"Conversion Status: Error - {error_message}")

    def handle_format_change(self):
        audio_format = self.format_combo_box.currentText()

        disable_bitrate_sampling_bitdepth = audio_format in ['flac', 'wav']
        self.bitrate_combo_box.setEnabled(not disable_bitrate_sampling_bitdepth)
        self.sampling_rate_combo_box.setEnabled(not disable_bitrate_sampling_bitdepth)
        self.bit_depth_combo_box.setEnabled(not disable_bitrate_sampling_bitdepth)

        if audio_format == 'aac':
            self.sampling_rate_combo_box.clear()
            self.sampling_rate_combo_box.addItems(['44100', '48000', '88200', '96000'])
        elif audio_format == 'mp3':
            self.sampling_rate_combo_box.clear()
            self.sampling_rate_combo_box.addItems(['44100', '48000'])
        else:
            self.sampling_rate_combo_box.clear()
            self.sampling_rate_combo_box.addItems(['44100', '48000', '88200', '96000', '176400', '192000'])

        selected_sampling_rate = int(self.sampling_rate_combo_box.currentText())
        if audio_format == 'aac' and selected_sampling_rate > 96000:
            self.sampling_rate_combo_box.setCurrentText('96000')
        elif audio_format == 'mp3' and selected_sampling_rate > 48000:
            self.sampling_rate_combo_box.setCurrentText('48000')

    def handle_conversion_change(self):
        conversion_method = self.conversion_method_combo_box.currentText()

        hide_bitrate_sampling_bitdepth = conversion_method == 'Default'
        self.bitrate_combo_box.setEnabled(not hide_bitrate_sampling_bitdepth)
        self.sampling_rate_combo_box.setEnabled(not hide_bitrate_sampling_bitdepth)
        self.bit_depth_combo_box.setEnabled(not hide_bitrate_sampling_bitdepth)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Audiophile")
        self.setGeometry(100, 100, 800, 500)
        self.setStyleSheet("background-color: lightgray;")

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        layout = QHBoxLayout()

        self.console = Console()
        layout.addWidget(self.console, 1) 

        url_conversion_widget = UrlConversionWidget()
        layout.addWidget(url_conversion_widget, 2) 

        main_widget.setLayout(layout)

        sys.stdout = EmittingStream(text_written=self.console.append_message)

        sys.stderr = EmittingStream(text_written=lambda message: self.console.append_error(message))
    
class EmittingStream(QObject):
    text_written = pyqtSignal(str)

    def write(self, text):
        self.text_written.emit(str(text))

    def flush(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
