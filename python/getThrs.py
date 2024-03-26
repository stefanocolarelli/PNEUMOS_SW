# code    
import requests
import numpy as np
from scipy.spatial.distance import euclidean
import schedule
import time
from pythonosc import udp_client
import json
import random
import sys 

client = udp_client.SimpleUDPClient("127.0.0.1", 12345)  # Indirizzo IP e porta OSC del destinatario

def send_osc_distances(distances):
    try:
        client = udp_client.SimpleUDPClient("127.0.0.1", 12345)  # Indirizzo IP e porta OSC del destinatario
        # Invia i valori come messaggio OSC
        for i, distance in enumerate(distances):
            client.send_message("/distance", (i + 1, distance))
    except ConnectionRefusedError:
        print("Errore: Connessione OSC rifiutata. Assicurati che il server OSC sia in esecuzione.")

def send_osc_breath(breath):
    try:
        client = udp_client.SimpleUDPClient("127.0.0.1", 12345)  # Indirizzo IP e porta OSC del destinatario
        # Invia i valori come messaggio OSC   
        client.send_message("/breath", breath)
    except ConnectionRefusedError:
        print("Errore: Connessione OSC rifiutata. Assicurati che il server OSC sia in esecuzione.")

def get_normalized_values():
    url = "https://apidare.comune.ravenna.it/dareairsamples/10"
    data = {}

    # Dati per la normalizzazione
    normalized_ranges = {
        'PM2.5': {'min': 0, 'max': 50},
        'PM10': {'min': 0, 'max': 100},
        'NO2': {'min': 0, 'max': 300},
        'SO2': {'min': 0, 'max': 500},
        'CO': {'min': 0, 'max': 100}
    }

    # Conversioni da ppm a μg/m3
    conversion_factors = {
        'SO2': 2620,
        'NO2': 1880,
        'CO': 1.145,
        'PM10': 1,
        'PM2.5': 1
    }
    
    with open('scpdump.json', 'r') as file:
        data = json.load(file)

    # Dizionari vuoti per ogni stazione
    station_dare1 = []
    station_dare2 = []
    station_dare3 = []

    for entry in data:
        if entry['StationName'] == 'MeteoStationDARE1':
            station_dare1.append(entry)
        elif entry['StationName'] == 'MeteoStationDARE2':
            station_dare2.append(entry)
        elif entry['StationName'] == 'MeteoStationDARE3':
            station_dare3.append(entry)

    # Seleziona un timestamp casuale per ogni stazione
    random_entry_dare1 = random.choice(station_dare1)
    random_entry_dare2 = random.choice(station_dare2)
    random_entry_dare3 = random.choice(station_dare3)
    
    # Calcola la media dei valori per ogni parametro
    average_values = {
        'PM2.5': (float(random_entry_dare1['PM2'].split()[0]) + float(random_entry_dare2['PM2'].split()[0]) + float(random_entry_dare3['PM2'].split()[0])) / 3,
        'PM10': (float(random_entry_dare1['PM10'].split()[0]) + float(random_entry_dare2['PM10'].split()[0]) + float(random_entry_dare3['PM10'].split()[0])) / 3,
        'NO2': (float(random_entry_dare1['NO2'].split()[0]) + float(random_entry_dare2['NO2'].split()[0]) + float(random_entry_dare3['NO2'].split()[0])) / 3,
        'SO2': (float(random_entry_dare1['SO2'].split()[0]) + float(random_entry_dare2['SO2'].split()[0]) + float(random_entry_dare3['SO2'].split()[0])) / 3,
        'CO': (float(random_entry_dare1['CO'].split()[0]) + float(random_entry_dare2['CO'].split()[0]) + float(random_entry_dare3['CO'].split()[0])) / 3
    }

    # Converte l'unità di misura
    converted_values = {}
    for key, values in average_values.items():
        converted_values[key] = values * conversion_factors[key]
    
    # Normalizza i valori
    normalized_values = {}
    for key, value in converted_values.items():
        min_value = normalized_ranges[key]['min']
        max_value = normalized_ranges[key]['max']
        normalized_value = (value - min_value) / (max_value - min_value)
        normalized_values[key] = normalized_value

    return normalized_values

def calculate_distances():
    normalized_values = get_normalized_values()
    
    # Punto soglie per ciascun inquinante
    soglie = {
        'PM2.5': [10, 15, 25, 37.5, 50],
        'PM10': [20, 45, 50, 75, 100],
        'NO2': [50, 120, 200, 240, 300],
        'SO2': [40, 50, 125, 350, 500],
        'CO': [4, 7, 10, 35, 100]
    }
    
    normalized_ranges = {
        'PM2.5': {'min': 0, 'max': 50},
        'PM10': {'min': 0, 'max': 100},
        'NO2': {'min': 0, 'max': 300},
        'SO2': {'min': 0, 'max': 500},
        'CO': {'min': 0, 'max': 100}
    }
    
    # Normalizza i valori
    normalized_soglie = {}
    for key, value in soglie.items():
        min_value = normalized_ranges[key]['min']
        max_value = normalized_ranges[key]['max']
        normalized_soglie[key] = []
        for i in value:
            normalized_value = (i - min_value) / (max_value - min_value)
            normalized_soglie[key].append(normalized_value)
        
    soglie_points = []
    for n in range(5):
        pn = [normalized_soglie['PM2.5'][n], normalized_soglie['PM10'][n], normalized_soglie['NO2'][n], normalized_soglie['SO2'][n], normalized_soglie['CO'][n]]
        soglie_points.append(pn)

    # Converte la lista di punti in un np.array
    array_punti = np.array(soglie_points)
    #print(soglie_points)
    # Punto di riferimento
    reference_point = np.array([
        normalized_values['PM2.5'],
        normalized_values['PM10'],
        normalized_values['NO2'],
        normalized_values['SO2'],
        normalized_values['CO'],
    ])
    #print(reference_point)
    # Calcola le distanze euclidee
    distances = []
    for point in soglie_points:
        distance = euclidean(reference_point, point)
        distances.append(distance)

    # Stampa le distanze euclidee
    print("Distanze euclidee tra i punti casuali e il punto di riferimento:")
    for i, distance in enumerate(distances):
        print(f"Punto {i + 1}: {distance:.4f}")
    

    min_value = min(distances)
    min_index = distances.index(min_value)
    if min_value > 7:
        min_index = 5
    print("Funzione di respiro arduino:", min_index)
    return(min_index)


# La funzione per l'uso da riga di comando
def main():
    soglia = 0
    cc = 0
    while soglia != 4:
        soglia = calculate_distances()  # Esegue il calcolo iniziale
        cc += 1
        if cc >= 6000:
            break

# Controlla se è stato passato un argomento da linea di comando
if __name__ == "__main__":
    main()
