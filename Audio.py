import socket
import pyaudio
import struct
import tkinter as tk
import tkinter.ttk as ttk
import threading

PORT = 12345

class AudioStreamingApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("Audio Streaming App")
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.ip_label = ttk.Label(self, text="Destination IP:")
        self.ip_label.pack()

        self.ip_entry = ttk.Entry(self)
        self.ip_entry.pack()

        self.get_ip_button = ttk.Button(self, text="Get IP", command=self.get_ip)
        self.get_ip_button.pack()

        self.start_button = ttk.Button(self, text="Start Streaming", command=self.start_streaming, state=tk.DISABLED)
        self.start_button.pack()

        self.stop_button = ttk.Button(self, text="Stop Streaming", command=self.stop_streaming, state=tk.DISABLED)
        self.stop_button.pack()

        self.start_receiving_button = ttk.Button(self, text="Start Receiving", command=self.start_receiving_audio, state=tk.DISABLED)
        self.start_receiving_button.pack()

        self.stop_receiving_button = ttk.Button(self, text="Stop Receiving", command=self.stop_receiving, state=tk.DISABLED)
        self.stop_receiving_button.pack()

        self.streaming = False
        self.receiving = False
        self.p = None
        self.stream = None
        self.sock = None
        self.receive_sock = None

    def get_ip(self):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        self.ip_entry.delete(0, tk.END)
        self.ip_entry.insert(0, ip_address)
        self.start_button.config(state=tk.NORMAL)
        self.start_receiving_button.config(state=tk.NORMAL)

    def start_streaming(self):
        self.streaming = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        ip_address = self.ip_entry.get()

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16,
                                   channels=1,
                                   rate=44100,
                                   input=True,
                                   frames_per_buffer=4096)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.record_and_send_audio_thread = threading.Thread(target=self.record_and_send_audio, args=(ip_address, PORT))
        self.record_and_send_audio_thread.start()

    def stop_streaming(self):
        self.streaming = False

        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

        self.sock.close()

        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def start_receiving_audio(self):
        self.receiving = True
        self.start_receiving_button.config(state=tk.DISABLED)
        self.stop_receiving_button.config(state=tk.NORMAL)

        self.receive_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.receive_sock.bind(('', PORT))

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16,
                               channels=2,
                               rate=44100,
                               output=True,
                               frames_per_buffer=4096)

        self.play_audio_thread = threading.Thread(target=self.play_audio)
        self.play_audio_thread.start()


    def stop_receiving(self):
        self.receiving = False

        self.receive_sock.close()

        self.start_receiving_button.config(state=tk.NORMAL)
        self.stop_receiving_button.config(state=tk.DISABLED)

    def record_and_send_audio(self, ip_address, port):
        while self.streaming:
            audio_data = self.stream.read(4096)
            data = struct.pack('h' * len(audio_data), *audio_data)
            self.sock.sendto(data, (ip_address, port))

    def play_audio(self):
        while self.receiving:
            data, address = self.receive_sock.recvfrom(4096 * 8)
            audio_data = struct.unpack('h' * (len(data) // 2), data)
            self.stream.start_stream()
            self.stream.write(audio_data)


if __name__ == "__main__":
    app = AudioStreamingApp()
    app.mainloop()

