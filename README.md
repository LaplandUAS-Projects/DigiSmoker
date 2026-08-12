# Raspberry Pi Savustin Pro

Tämä projekti toteuttaa Raspberry Pi -pohjaisen savustimen lämpötilanohjausjärjestelmän, joka mittaa reaaliaikaisesti sekä savustuskammion että paistettavan tuotteen lämpötilaa ja säätää lämmitysvastuksen tehoa automaattisesti.

Järjestelmä hyödyntää termoparianturia savustimen lämpötilan mittaamiseen, NTC-pohjaista paistomittaria lihan lämpötilan seurantaan sekä SSR-relettä lämmityksen ohjaamiseen. Käyttäjä voi seurata lämpötiloja ja lämmitystehoa graafisesta käyttöliittymästä reaaliajassa.

## Käyttöprosessi

1. Kytke lämpötila-anturit Raspberry Pi -laitteeseen.

   - Savustimen lämpötila mitataan MAX6675- tai MAX31855-termoparimuuntimella.
   - Lihan lämpötila mitataan ADS1115-muuntimeen kytketyllä NTC-paistomittarilla.

2. Kytke SSR-rele savustimen lämmitysvastuksen ohjaukseen.

3. Ota Raspberry Pi:n SPI- ja I2C-väylät käyttöön.

4. Käynnistä sovellus.

5. Aseta haluttu tavoitelämpötila käyttöliittymästä.

6. Järjestelmä:

   - mittaa savustimen lämpötilaa
   - mittaa lihan sisälämpötilaa
   - laskee lämpötilan nousunopeuden
   - säätää lämmitystehoa automaattisesti
   - näyttää lämpötilat ja tehon trendikäyrinä

7. Seuraa savustusprosessia reaaliaikaisesti käyttöliittymästä.

## Vaadittava laitteisto

- Raspberry Pi 3, 4 tai 5
- SSR-rele
- MAX6675 tai MAX31855
- K-tyypin termopari
- ADS1115 ADC-muunnin
- NTC-paistomittari
- Savustimen lämmitysvastus

> [!NOTE]
> SSR-releen tulee olla mitoitettu käytettävän lämmitysvastuksen tehon mukaisesti. Verkkosähköasennukset tulee suorittaa voimassa olevien sähkömääräysten mukaisesti.

## Vaadittava ohjelmisto

### Pakolliset

- Raspberry Pi OS
- Python 3
- Tkinter
- Matplotlib
- gpiozero
- spidev
- adafruit-circuitpython-ads1x15

### Python-kirjastojen asennus

```bash
sudo apt update
sudo apt install python3-pip python3-tk -y

pip3 install gpiozero
pip3 install spidev
pip3 install matplotlib
pip3 install adafruit-circuitpython-ads1x15
```

## Raspberry Pi -asetukset

SPI- ja I2C-väylät tulee ottaa käyttöön:

```bash
sudo raspi-config
```

Valitse:

```text
Interface Options
 ├─ SPI -> Enable
 └─ I2C -> Enable
```

Käynnistä Raspberry Pi uudelleen asetusten jälkeen.

## Projektin toimintaperiaate

Ratkaisu hyödyntää ennakoivaa lämpötilansäätöä perinteisen ON/OFF-ohjauksen sijaan.

Järjestelmä mittaa jatkuvasti savustimen lämpötilaa ja arvioi samalla lämpötilan nousunopeutta. Kun tavoitelämpötilaa lähestytään, lämmitystehoa pienennetään asteittain, jolloin lämpötilan ylitys vähenee ja lämpötila pysyy vakaampana.

Lämmitystehoa ohjataan PWM-jaksotuksella SSR-releen kautta. Tehon laskennassa huomioidaan:

- tavoitelämpötila
- nykyinen lämpötila
- lämpötilan nousunopeus

Tämän ansiosta savustin reagoi kuormituksen muutoksiin ja saavuttaa tavoitelämpötilan hallitummin.

## Käyttöliittymä

Sovellus tarjoaa reaaliaikaisen käyttöliittymän, josta käyttäjä voi seurata:

### Lämpötilat

- Savustimen lämpötila
- Lihan lämpötila
- Tavoitelämpötila

### Ohjaustiedot

- Lämmitysteho (%)
- Anturin offset-korjaus

### Trendiseuranta

Ylempi kuvaaja näyttää:

- Savustimen lämpötilan
- Lihan lämpötilan
- Tavoitelämpötilan

Alempi kuvaaja näyttää:

- Lämmitystehon prosentteina

## Käynnistys

```bash
python3 savustin.py
```

## Konfigurointi

Sovelluksen keskeiset asetukset löytyvät ohjelman alusta:

```python
RELE_PIN = 18
PWM_JAKSO = 3.0
TEHO_ALUE = 30.0
```

### PWM_JAKSO

Määrittää SSR-ohjauksen PWM-jakson pituuden sekunteina.

### TEHO_ALUE

Määrittää lämpötila-alueen, jonka sisällä tehoa aletaan pienentää ennen tavoitelämpötilan saavuttamista.

### Offset-korjaus

Käyttöliittymästä voidaan kompensoida anturin mahdollinen mittausvirhe ilman ohjelmakoodin muokkaamista.

## Turvatoiminnot

Järjestelmä sisältää useita suojaavia toimintoja:

- SSR sammutetaan ohjelman sulkeutuessa.
- Virheelliset anturilukemat hylätään.
- I2C-virheet käsitellään hallitusti.
- Irrotettu tai viallinen paistomittari tunnistetaan automaattisesti.

## Kehitysideat

- PID-säädin
- MQTT-etäseuranta
- Web-käyttöliittymä
- Tietojen tallennus SQLite-tietokantaan
- Lämpötilahälytykset
- Mobiilikäyttöliittymä
- Node-RED-integraatio
- Pilvipohjainen seuranta

---

<picture>
  /logot/license.png">
  <source media="(prefers-color-scheme: light)" srcset="/img/logot/licenseot/license.png