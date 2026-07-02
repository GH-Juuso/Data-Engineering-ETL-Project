import time

import disruptions_download
import ingest_train_services
import ingest_weather_hourly

def main(verbose:bool = False):
    print("███████████████████████████████████████████████████████████████")
    print("██ Running dataset ingestions...                             ██")
    print("███████████████████████████████████████████████████████████████")

    verbose = False

    total_start = time.time()
    start = time.time()
    print("██ Downloading disruptions dataset...", end=" ")
    disruptions_download.main(verbose)
    print(f"OK! ({time.time() - start:.2f}s)")

    start = time.time()
    print("██ Downloading train_services_asd dataset...", end=" ")
    ingest_train_services.main(verbose)
    print(f"OK! ({time.time() - start:.2f}s)")

    start = time.time()
    print("██ Downloading weather_hourly dataset...", end=" ")
    ingest_weather_hourly.main(verbose)
    print(f"OK! ({time.time() - start:.2f}s)")

    print("██▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀██ ..Done! ██")
    print(f"██ Dataset ingestion - Total Time {time.time() - total_start:.2f}s")
    print(f"██                     Total Time {(time.time() - total_start)/60:.2f}min")
    print("███████████████████████████████████████████████████████████████")

if __name__ == "__main__":
    main()
