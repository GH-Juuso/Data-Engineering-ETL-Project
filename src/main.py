# Full ETL process : From Download to Dim-/Fact-tables
import main_ingest
import main_process

print("███████████████████████████████████████████████████████████████")
print("██ Full ETL process                        (15 - 25 minutes) ██")
print("███████████████████████████████████████████████████████████████")
print()
main_ingest.main()
print()
main_process.main()
