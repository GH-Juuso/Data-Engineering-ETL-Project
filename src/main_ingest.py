import time

import disruptions_download
import ingest_train_services
import ingest_weather_hourly

print("███████████████████████████████████████████████████████████████")
print("██ Running dataset ingestions...                             ██")
print("███████████████████████████████████████████████████████████████")

start = time.time()
print("██ Downloading disruptions dataset...", end=" ")
disruptions_download.main()
print(f"OK! ({time.time() - start:.2f}s)")

start = time.time()
print("██ Downloading train_services_asd dataset...", end=" ")
ingest_train_services.main()
print(f"OK! ({time.time() - start:.2f}s)")

start = time.time()
print("██ Downloading weather_hourly dataset...", end=" ")
ingest_weather_hourly.main()
print(f"OK! ({time.time() - start:.2f}s)")

print("█▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄█ ..Done! ██")

