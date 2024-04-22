# code    
import requests
import numpy as np
from scipy.spatial.distance import euclidean
import schedule
import time
from pythonosc import udp_client
import json

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
    url = "https://apidare.comune.ravenna.it/dareairsamples/60"
    data = {}

    # Dati per la normalizzazione
    normalized_ranges = {
        'PM2': {'min': 0, 'max': 75},
        'PM10': {'min': 0, 'max': 150},
        'NO2': {'min': 0, 'max': 340},
        'SO2': {'min': 0, 'max': 750},
        'CO': {'min': 0, 'max': 100}
    }

    # Conversioni da ppm a μg/m3
    conversion_factors = {
        'SO2': 2620,
        'NO2': 1880,
        'CO': 1.145,
        'PM10': 1,
        'PM2': 1
    }
    
    try:
        response = requests.get(url)
        data = response.json()  # Converti la risposta in formato JSON
        # Writing to sample.json
        with open("lastworking.json", "w") as outfile:
            outfile.write(json.dumps(data, indent = 4))

    except requests.exceptions.RequestException as e:
        print("Errore durante la richiesta API:", e)
        print('Verrano utilizzati gli ultimi dati rilevati validi')
        with open('lastworking.json', 'r') as file:
            data = json.load(file)

    # Dizionari vuoti per ogni stazione
    station_dare1 = {}
    station_dare2 = {}
    station_dare3 = {}

    for entry in data:
        if entry['StationName'] == 'MeteoStationDARE1':
            if 'latest_timestamp' not in station_dare1 or entry['TimeStamp'] > station_dare1['latest_timestamp']:
                station_dare1 = entry
                station_dare1['latest_timestamp'] = entry['TimeStamp']
        elif entry['StationName'] == 'MeteoStationDARE2':
            if 'latest_timestamp' not in station_dare2 or entry['TimeStamp'] > station_dare2['latest_timestamp']:
                station_dare2 = entry
                station_dare2['latest_timestamp'] = entry['TimeStamp']
        elif entry['StationName'] == 'MeteoStationDARE3':
            if 'latest_timestamp' not in station_dare3 or entry['TimeStamp'] > station_dare3['latest_timestamp']:
                station_dare3 = entry
                station_dare3['latest_timestamp'] = entry['TimeStamp']

    average_values = {'PM2':0, 'PM10':0, 'NO2':0, 'SO2':0, 'CO':0}
    stationdatas = [station_dare1, station_dare2, station_dare3]
    error = True

    idx = 0
    # Calcola la media dei valori per ogni parametro
    for i in stationdatas:
        idx += 1
        for key in average_values.keys():
            if i != {}:
                average_values[key] += float(i[key].split()[0])/3
                error = False
            else:
                print(f"MeteoStationDARE{idx} is missing")
                break
    
    if error:
        print('Connesso ma con nessun dato ricevuto, verrano utilizzati gli ultimi dati rilevati validi')
        with open('lastworking.json', 'r') as file:
            data = json.load(file)
        for entry in data:
            if entry['StationName'] == 'MeteoStationDARE1':
                if 'latest_timestamp' not in station_dare1 or entry['TimeStamp'] > station_dare1['latest_timestamp']:
                    station_dare1 = entry
                    station_dare1['latest_timestamp'] = entry['TimeStamp']
            elif entry['StationName'] == 'MeteoStationDARE2':
                if 'latest_timestamp' not in station_dare2 or entry['TimeStamp'] > station_dare2['latest_timestamp']:
                    station_dare2 = entry
                    station_dare2['latest_timestamp'] = entry['TimeStamp']
            elif entry['StationName'] == 'MeteoStationDARE3':
                if 'latest_timestamp' not in station_dare3 or entry['TimeStamp'] > station_dare3['latest_timestamp']:
                    station_dare3 = entry
                    station_dare3['latest_timestamp'] = entry['TimeStamp']
        stationdatas = [station_dare1, station_dare2, station_dare3]
        for i in stationdatas:
            for key in average_values.keys():
                if i != {}:
                    average_values[key] += float(i[key].split()[0])/3

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
        'PM2': [10, 20, 25, 50, 75],
        'PM10': [20, 40, 50, 100, 150],
        'NO2': [40, 90, 120, 230, 340],
        'SO2': [100, 200, 350, 500, 750],
        'CO': [4, 7, 10, 35, 100]
    }
    
    normalized_ranges = {
        'PM2': {'min': 0, 'max': 75},
        'PM10': {'min': 0, 'max': 150},
        'NO2': {'min': 0, 'max': 340},
        'SO2': {'min': 0, 'max': 750},
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
        pn = [normalized_soglie['PM2'][n], normalized_soglie['PM10'][n], normalized_soglie['NO2'][n], normalized_soglie['SO2'][n], normalized_soglie['CO'][n]]
        soglie_points.append(pn)

    # Converte la lista di punti in un np.array
    array_punti = np.array(soglie_points)
    #print(soglie_points)
    # Punto di riferimento
    reference_point = np.array([
        normalized_values['PM2'],
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
    print("Distanze euclidee tra le soglie e il punto di riferimento:")
    for i, distance in enumerate(distances):
        print(f"Punto {i + 1}: {distance:.4f}")
    
    send_osc_distances(distances)
    min_value = min(distances)
    min_index = distances.index(min_value)
    if min_value > 2:
        min_index = 5
    print("Funzione di respiro arduino:", min_index)
    send_osc_breath(min_index)

    # Serializing json
    json_object = json.dumps(distances, indent=4)
    
    # Writing to sample.json
    with open("sample.json", "w") as outfile:
        outfile.write(json_object)
        
# Pianifica l'esecuzione della funzione ogni 10 minuti
calculate_distances()
schedule.every(30).minutes.do(calculate_distances)

while True:
    schedule.run_pending()
    time.sleep(1)
