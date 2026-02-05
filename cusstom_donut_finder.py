import csv
import re
import bisect

starRatings = [0,120,240,400,700,960]
berryData = {}
berryDict = {}


def readData(file_path):
    global berryData
    with open(file_path, mode='r') as file:
        berryData = {}
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            name = ""
            for key in row.keys():
                if re.search("Name", key):
                    name = row[key]
                    berryData[name] = {}
                else:
                    berryData[name][key] = row[key]
            # print(f"{row['Berry Name']} has Flavor Score {row['Flavor Score']}")
        # print(f"Read in {file_path} and created data Dictionary with {len(berryData)} entries")

def createBerryDict():
    for key in berryData:
        newBerry = Berry(key)
        berryDict[key] = newBerry
    # print(f"Created Berry Dictionary of size {len(berryDict)}")

def getStarRating(flavorScore): # put this calculation inside Donut init?
    rating = (bisect.bisect_right(starRatings, flavorScore)) - 1
    # print(f"{rating=}")
    multiplier = 1 + (.1 * rating)
    return rating , multiplier

def getFullBerryName():
    pass


class Donut:
    def __init__(self, berryList):
        print(berryData["Hyper Yache Berry"])

class Berry():
    def __init__(self, name):
        self.name = name
        entry = berryData[self.name]
        self.sweet = int(entry['Sweet Score'])
        self.spicy = int(entry['Spicy Score'])
        self.sour = int(entry['Sour Score'])
        self.bitter = int(entry['Bitter Score'])
        self.fresh = int(entry['Fresh Score'])
        self.flavorScore = self.sweet + self.spicy + self.sour + self.bitter + self.fresh
        self.levels = int(entry['Levels'])
        self.calories = int(entry['Calories'])

        # print(self.flavorScore)


if __name__ == "__main__":
    readData('hyper_berries.csv')
    createBerryDict()

    # for key in berryDict:
    #     entry = berryDict[key]
    #     print(f"{entry.name} has Flavor Score {entry.flavorScore}")

    target = 1050
    starRating, multiplier = getStarRating(target)
    print(f"A Flavor Score of {target} means the donut is {starRating} star(s), with a multiplier of {multiplier}")

    # newDonut = Donut([])
    # newBerry = Berry("Hyper Colbur Berry")
    
    # for key in berryData:
    #     print(f"{key}: {berryData[key]}")