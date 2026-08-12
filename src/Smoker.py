import spidev
import time
import threading
import tkinter as tk
from tkinter import ttk
from gpiozero import OutputDevice
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import math

# --- I2C ja ADS1115 KIRJASTOT ---
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# --- ASETUKSET: UUNI ---
RELE_PIN = 18
PWM_JAKSO = 3.0  # Hieman pidempi jakso antaa tasaisemman vasteen
TEHO_ALUE = 30.0 # Aloitetaan jarrutus jo 30 astetta ennen

# --- ASETUKSET: LIHALÄMPÖ (ADS1115) ---
R_FIXED = 11000.0        # Mitattu vastus 11k
R_NOMINAL = 28000.0      # Säädä tarvittaessa kalibrointia varten
B_COEFFICIENT = 3950.0   # Paistomittarien perus-Beta
TEMP_NOMINAL = 25.0      
V_IN = 3.3               

# --- LAITTEISTON ALUSTUS ---
ssr = OutputDevice(RELE_PIN)

# SPI (Uunin anturi MAX6675/MAX31855)
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 50000
spi.mode = 0b00

# I2C (Lihalämpö ADS1115)
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c)
    liha_chan = AnalogIn(ads, 0) # Kanava A0
    print("I2C ja ADS1115 alustettu onnistuneesti.")
except Exception as e:
    print(f"Virhe I2C-yhteydessä (Lihalämpö ei toimi): {e}")
    liha_chan = None

class SavustinApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Savustin Pro - Trendi & Ohjaus")
        self.root.geometry("850x650")
        
        # Datamuuttujat uuni
        self.tavoite = tk.DoubleVar(value=100.0)
        self.offset = tk.DoubleVar(value=0.0)
        self.nykyinen_temp = 0.0
        self.teho_nyt = 0.0
        
        # Historiatiedot graafia varten (viimeiset 100 pistettä)
        self.aika_data = deque(maxlen=100)
        self.temp_data = deque(maxlen=100)
        self.teho_data = deque(maxlen=100)
        self.liha_temp_data = deque(maxlen=100) # Lihalämmön historia
        
        self.alkuaika = time.time()

        # --- GUI ASETTELU ---
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Vasen puoli: Säädöt ja näytöt
        control_frame = tk.Frame(main_frame, width=250, padx=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Uunin lämpö
        tk.Label(control_frame, text="Uunin Lämpö", font=("Arial", 14)).pack(pady=(10,0))
        self.temp_label = tk.Label(control_frame, text="0.0°C", font=("Arial", 28, "bold"), fg="red")
        self.temp_label.pack()

        # Lihan lämpö
        tk.Label(control_frame, text="Lihan Lämpö", font=("Arial", 14)).pack(pady=(20,0))
        self.liha_temp_label = tk.Label(control_frame, text="--.-°C", font=("Arial", 28, "bold"), fg="blue")
        self.liha_temp_label.pack()

        # Säädöt
        tk.Label(control_frame, text="Tavoite (°C)").pack(pady=(20,0))
        tk.Spinbox(control_frame, from_=0, to_=250, textvariable=self.tavoite, font=("Arial", 14), width=5).pack()

        tk.Label(control_frame, text="Offset korjaus").pack(pady=(10,0))
        tk.Scale(control_frame, from_=-15, to=15, variable=self.offset, orient="horizontal", resolution=0.1).pack()

        self.teho_label = tk.Label(control_frame, text="Teho: 0%", font=("Arial", 14, "bold"))
        self.teho_label.pack(pady=30)

        # Oikea puoli: Graafit
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(6, 5), sharex=True)
        self.fig.tight_layout(pad=3.0)
        self.canvas = FigureCanvasTkAgg(self.fig, master=main_frame)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Käynnistys
        self.running = True
        self.thread = threading.Thread(target=self.paasilmukka, daemon=True)
        self.thread.start()
        self.paivita_graafi()

    def lue_suodatettu_temp(self):
        try:
            resp = spi.readbytes(2)
            val = (resp[0] << 8) | resp[1]
            if val & 0x4: return None
            return ((val >> 3) * 0.25) + self.offset.get()
        except: return None

    def lue_liha_temp(self):
        if liha_chan is None:
            return None
        try:
            voltage = liha_chan.voltage
            # Estetään virhetilanteet (jos anturi irti tai oikosulussa)
            if voltage >= 3.25 or voltage <= 0.05:
                return None
            
            # Steinhart-Hart / Beta yhtälö
            resistance = R_FIXED * (voltage / (V_IN - voltage))
            steinhart = math.log(resistance / R_NOMINAL)
            steinhart /= B_COEFFICIENT
            steinhart += 1.0 / (TEMP_NOMINAL + 273.15)
            steinhart = 1.0 / steinhart
            return steinhart - 273.15
        except:
            return None

    def paasilmukka(self):
        viime_temp = 0
        while self.running:
            temp = self.lue_suodatettu_temp()
            liha_temp = self.lue_liha_temp()
            nyky_aika = time.time() - self.alkuaika
            
            if temp is not None:
                self.nykyinen_temp = temp
                tavoite = self.tavoite.get()
                
                # Uunin nopeuden ennakointi (vaimennus)
                nousunopeus = temp - viime_temp 
                viime_temp = temp
                ero = tavoite - temp
                
                # Lasketaan uunin teho
                teho = (ero / TEHO_ALUE) - (nousunopeus * 2.0)
                teho = max(0.0, min(1.0, teho))
                if temp >= tavoite: teho = 0.0

                self.teho_nyt = teho
                
                # Päivitetään GUI-tekstit
                self.temp_label.config(text=f"{temp:.1f}°C")
                self.teho_label.config(text=f"Teho: {int(teho*100)}%")
                
                if liha_temp is not None:
                    self.liha_temp_label.config(text=f"{liha_temp:.1f}°C")
                else:
                    self.liha_temp_label.config(text="--.-°C")

                # Tallennetaan dataa graafiin (lisätään float('nan') jos liha_temp puuttuu, jotta graafi ei sekoita linjoja)
                self.aika_data.append(nyky_aika)
                self.temp_data.append(temp)
                self.teho_data.append(teho * 100)
                self.liha_temp_data.append(liha_temp if liha_temp is not None else float('nan'))
                
                self.aja_pwm(teho)
            else:
                time.sleep(1)

    def aja_pwm(self, teho):
        if teho <= 0:
            ssr.off()
            time.sleep(PWM_JAKSO)
        elif teho >= 1:
            ssr.on()
            time.sleep(PWM_JAKSO)
        else:
            paalla = PWM_JAKSO * teho
            ssr.on()
            time.sleep(paalla)
            ssr.off()
            time.sleep(PWM_JAKSO - paalla)

    def paivita_graafi(self):
        if not self.running: return
        
        self.ax1.clear()
        # Piirretään uunin ja lihan lämmöt
        self.ax1.plot(list(self.aika_data), list(self.temp_data), 'r-', label="Uuni")
        self.ax1.plot(list(self.aika_data), list(self.liha_temp_data), 'b-', linewidth=2, label="Liha")
        self.ax1.axhline(y=self.tavoite.get(), color='g', linestyle='--', label="Tavoite")
        
        self.ax1.set_ylabel("Lämpö °C")
        self.ax1.set_title("Lämpötilat ja Teho")
        self.ax1.legend(loc="upper left", fontsize=8)

        self.ax2.clear()
        self.ax2.fill_between(list(self.aika_data), list(self.teho_data), color='red', alpha=0.3)
        self.ax2.set_ylabel("Teho %")
        self.ax2.set_ylim(0, 110)
        self.ax2.set_xlabel("Aika (s)")

        self.canvas.draw()
        self.root.after(3000, self.paivita_graafi) # Päivitä graafi 3s välein

if __name__ == "__main__":
    root = tk.Tk()
    app = SavustinApp(root)
    try:
        root.mainloop()
    finally:
        app.running = False
        ssr.off()
        spi.close()