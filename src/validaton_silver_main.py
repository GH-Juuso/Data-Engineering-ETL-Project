import validation_silver_disruptions
import validation_silver_train_services_asd
import validation_silver_weather

def main(verbose:bool = False):
    if verbose: print("█████████████████████████████████████████████")
    if verbose: print("██ Running validations of silver tables... ██")
    if verbose: print("█████████████████████████████████████████████")
    if verbose: print("██ Running validation_silver_disruptions...")
    validation_silver_disruptions.main()
    if verbose: print("██ Running validation_silver_train_services_asd...")
    validation_silver_train_services_asd.main()
    if verbose: print("██ Running validation_silver_weather...")
    validation_silver_weather.main()
    if verbose: print("██")
    if verbose: print("██ ..Done! █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ ██")

if __name__ == "__main__":
    main()
