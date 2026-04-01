import csv
import json

data = {}

with open("players.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        data[row["name"]] = {
            "runs": float(row["runs"]),
            "average": float(row["average"]),
            "strike_rate": float(row["strike_rate"])
        }

with open("players.json", "w") as f:
    json.dump(data, f, indent=4)

print("Done")