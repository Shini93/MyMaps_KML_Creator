#!/usr/bin/env python3
"""
Dieses Skript liest alle CSV-Dateien im aktuellen Verzeichnis (oder angegebenen Verzeichnis) im Format
Titel,Notiz,URL,Tags,Kommentar ein und erzeugt für jede CSV eine KML-Datei mit demselben Basisnamen.

Abhängigkeiten:
  pip install geopy simplekml
"""
import csv
import sys
import os
import time

# Externe Bibliotheken
try:
    import simplekml
except ImportError:
    print("Fehler: Modul 'simplekml' nicht gefunden. Installiere mit:\n  pip install simplekml", file=sys.stderr)
    sys.exit(1)

try:
    from geopy.geocoders import Nominatim
    from geopy.extra.rate_limiter import RateLimiter
except ImportError:
    print("Fehler: Modul 'geopy' nicht gefunden. Installiere mit:\n  pip install geopy", file=sys.stderr)
    sys.exit(1)


def process_csv(csv_path, kml_path, user_agent="csv2kml_app"):
    """
    Liest eine einzelne CSV und schreibt eine KML-Datei.
    """
    # Nominatim-Geocoder einrichten
    geolocator = Nominatim(user_agent=user_agent)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    kml = simplekml.Kml()
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get('Titel') or row.get('Title') or ''
            note = row.get('Notiz') or row.get('Note') or ''
            url = row.get('URL') or ''
            tags = row.get('Tags') or ''
            comment = row.get('Kommentar') or ''

            if not title:
                print(f"Warnung: Kein Titel in '{csv_path}' Zeile {reader.line_num}, übersprungen.", file=sys.stderr)
                continue

            # Geokodieren
            try:
                location = geocode(title)
                if location is None:
                    print(f"Kein Ergebnis für '{title}' aus '{csv_path}'", file=sys.stderr)
                    continue
                lat, lng = location.latitude, location.longitude
            except Exception as e:
                print(f"Fehler bei Geokodierung '{title}' aus '{csv_path}': {e}", file=sys.stderr)
                continue

            # Placemark erstellen
            p = kml.newpoint(name=title, coords=[(lng, lat)])
            desc = []
            if note:
                desc.append(f"<b>Notiz:</b> {note}")
            if tags:
                desc.append(f"<b>Tags:</b> {tags}")
            if comment:
                desc.append(f"<b>Kommentar:</b> {comment}")
            if url:
                desc.append(f"<a href=\"{url}\">Link</a>")
            p.description = '<br/>'.join(desc)

    kml.save(kml_path)
    print(f"KML-Datei geschrieben: {kml_path}")


def process_all(directory):
    """
    Sucht alle .csv-Dateien im angegebenen Verzeichnis und verarbeitet sie.
    """
    for entry in os.listdir(directory):
        if entry.lower().endswith('.csv'):
            csv_path = os.path.join(directory, entry)
            basename = os.path.splitext(entry)[0]
            kml_path = os.path.join(directory, basename + '.kml')
            print(f"Verarbeite {csv_path} → {kml_path}")
            process_csv(csv_path, kml_path)
            time.sleep(1)  # Sicherheitsspanne zwischen Dateien


if __name__ == '__main__':
    # Optionales Verzeichnis-Argument
    if len(sys.argv) > 2:
        print(f"Usage: {sys.argv[0]} [verzeichnis]", file=sys.stderr)
        sys.exit(1)
    target_dir = sys.argv[1] if len(sys.argv) == 2 else os.getcwd()
    if not os.path.isdir(target_dir):
        print(f"Fehler: '{target_dir}' ist kein Verzeichnis.", file=sys.stderr)
        sys.exit(1)
    process_all(target_dir)
