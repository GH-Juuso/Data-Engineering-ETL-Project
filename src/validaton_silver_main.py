import validation_silver_disruptions
import validation_silver_train_services_asd
import validation_silver_weather

print("█████████████████████████████████████████████")
print("██ Running validations of silver tables... ██")
print("█████████████████████████████████████████████")
print("██ Running validation_silver_disruptions...")
validation_silver_disruptions.main()
print("██ Running validation_silver_train_services_asd...")
validation_silver_train_services_asd.main()
print("██ Running validation_silver_weather...")
validation_silver_weather.main()
print("██")
print("██ ..Done! █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ █ ██")
