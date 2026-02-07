import csv
from datetime import datetime
import threading
import time
import math
import re
import bisect
import itertools
import random
from collections import Counter

starRatings = [0,120,240,400,700,960]
berryData = {}
scoreList = []
berryDict = {}
donutList = []


def readInData(file_path):
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
        scoreList.append((key, newBerry.flavorScore))
        berryDict[key] = newBerry
    # print(scoreList)
    # print(f"Created Berry Dictionary of size {len(berryDict)}")

def getStarRating(flavorScore): # put this calculation inside Donut init?
    rating = (bisect.bisect_right(starRatings, flavorScore)) - 1
    # print(f"{rating=}")
    multiplier = 1 + (.1 * rating)
    return rating, multiplier

def findDonuts(target, numBerries=8):
    start_time = time.perf_counter()
    # random.shuffle(scoreList) # shuffle to verify threads
    combinations = 0
    threads = []
    for combo in itertools.combinations_with_replacement(scoreList, numBerries):
        combinations += 1
        flavorScores = [item[1] for item in combo]
        if sum(flavorScores) >= target:
            berries = [item[0] for item in combo]
            t = threading.Thread(target=newDonut, args=[berries])
            t.start()
            threads.append(t)
    for thread in threads:
        thread.join()
            # donutList.append("1")
            # print(donut)
    # print(f"Looked through {count:,} combinations of {numBerries} berries and found {len(donutList)} suitable donuts (target Flavor Score of {target})")
    end_time = time.perf_counter()
    elapsedTime = f"{end_time - start_time:.2f}"
    createRecipeFile(combinations, numBerries, target, elapsedTime)
    # end_time = time.perf_counter()
    # print(f"Elapsed time: {end_time - start_time:.6f} seconds")

def newDonut(berries):
    global donutList
    # print("creating new Donut object")
    donut = Donut(berries)
    donutList.append(donut)

def createRecipeFile(combinations, numBerries, target, elapsedTime):
    dateString = datetime.now().strftime("%m%d%y_%H%M%S")
    # print(f"{dateString}")
    file_path = f"output/{dateString} donut recipes.txt"
    with open(file_path, mode='w') as file:
        file.write(f"Looked through {combinations:,} combinations of donuts with {numBerries} berries and found these {len(donutList):,} suitable donuts in {elapsedTime} seconds (targeting Flavor Score of {target})\n\n")
        for donut in donutList:
            file.write(str(donut))


class Donut:
    def __init__(self, berryList):
        length = len(berryList)
        if length < 2 or length > 8:
            print(f"The provided list of length {length} is outside the bounds of required berries (3-8)!")
        else:
            self.berries = []
            self.totalSweet = 0
            self.totalSpicy = 0
            self.totalSour = 0
            self.totalBitter = 0
            self.totalFresh = 0
            self.flavorScore = 0
            self.starRating = 0
            self.totalLevels = 0
            self.totalCalories = 0
            self.names = berryList
            for berryName in berryList:
                newBerry = Berry(berryName)
                self.berries.append(newBerry)
            for berry in self.berries:
                self.totalSweet += berry.sweet
                self.totalSpicy += berry.spicy
                self.totalSour += berry.sour
                self.totalBitter += berry.bitter
                self.totalFresh += berry.fresh
                self.flavorScore += berry.flavorScore
                self.totalLevels += berry.levels
                self.totalCalories += berry.calories
            self.starRating, multiplier = getStarRating(self.flavorScore)
            self.totalLevels = math.floor(self.totalLevels * multiplier) # rounds down
            self.totalCalories = int(self.totalCalories * multiplier)

    def __str__(self):
        list = []
        counts = Counter(self.names)
        for item, count in counts.items():
            list.append(f"{count} {item}")
        string = (
            f"__________\n"
            f"{self.starRating} Star Donut ({', '.join(list)})\n"
            # f"Flavor Score: {self.flavorScore}\n"
            f"Bonus Levels: {self.totalLevels}\n"
            f"Calories: {self.totalCalories}\n"
            f"__________\n"
        )
        return string

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


if __name__ == "__main__":
    readInData('hyper_berries.csv')
    createBerryDict()
    
    findDonuts(1200, 8)
    # findDonuts(960, 8)
    # findDonuts(700, 8)