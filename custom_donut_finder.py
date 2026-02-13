import csv
from collections import Counter
from datetime import datetime
import time
import math
import bisect
import re

# Star thresholds and multipliers
starRatings = [0, 120, 240, 400, 700, 960]


def get_star_rating(flavor_score):
    rating = bisect.bisect_right(starRatings, flavor_score) - 1
    return rating, 1 + 0.1 * rating


# ----------------------------------------------------
# Data loading
# ----------------------------------------------------
def load_berries(file_path='hyper_berries.csv'):
    berries = []
    with open(file_path, mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['Berry Name'].strip()
            nameMatch = re.search(r"Hyper (\w+) Berry", name)
            if nameMatch:
                name = f"H-{nameMatch.group(1)}"
            if not name:
                continue
            try:
                sweet = int(row['Sweet Score'])
                spicy = int(row['Spicy Score'])
                sour = int(row['Sour Score'])
                bitter = int(row['Bitter Score'])
                fresh = int(row['Fresh Score'])
                flavor_total = sweet + spicy + sour + bitter + fresh

                levels = int(row['Levels'])
                calories = int(row['Calories'])
                count = int(row.get('Count', 0))  # available inventory

                berries.append((
                    name,
                    flavor_total,
                    levels,
                    calories,
                    count,
                    sweet,
                    spicy,
                    sour,
                    bitter,
                    fresh
                ))
            except (ValueError, KeyError) as e:
                print(f"Skipping invalid row for '{name}': {e}")
                continue

    # Sort descending by total flavor score
    berries.sort(key=lambda x: x[1], reverse=True)
    return berries


# ----------------------------------------------------
# Backtracking with inventory check
# ----------------------------------------------------
def find_high_score_donuts(berries, target, num_berries=8, include_stars="all", include_flavors="all"):
    start_time = time.perf_counter()

    # Unpack for faster access
    names = [b[0] for b in berries]
    scores = [b[1] for b in berries]          # total flavor
    levels_list = [b[2] for b in berries]
    cal_list = [b[3] for b in berries]
    counts = [b[4] for b in berries]
    sweets = [b[5] for b in berries]
    spicies = [b[6] for b in berries]
    sours = [b[7] for b in berries]
    bitters = [b[8] for b in berries]
    freshes = [b[9] for b in berries]
    results = []
    best_min_found = target

    def search(pos, remaining, cur_flavor, cur_levels, cur_cal,
               cur_sweet, cur_spicy, cur_sour, cur_bitter, cur_fresh,
               path, remaining_counts):
        nonlocal best_min_found

        if pos == len(scores):
            if remaining == 0:
                if cur_flavor >= best_min_found:
                    name_counts = Counter()
                    for idx, cnt in Counter(path).items():
                        name_counts[names[idx]] = cnt

                    total_used_inventory = 0
                    for berry_name in name_counts:
                        idx = names.index(berry_name)
                        total_used_inventory += counts[idx]

                    rating, mult = get_star_rating(cur_flavor)
                    bonus_levels = math.floor(cur_levels * mult)
                    total_cal = int(cur_cal * mult)
                    max_single = max(cur_sweet, cur_spicy, cur_sour, cur_bitter, cur_fresh)
                    max_flavor_name = ["Sweet", "Spicy", "Sour", "Bitter", "Fresh"][
                        [cur_sweet, cur_spicy, cur_sour, cur_bitter, cur_fresh].index(max_single)
                    ]

                    if (include_stars == "all" or rating in include_stars) and (include_flavors == "all" or max_flavor_name in include_flavors):
                        results.append({
                            'name_counts': name_counts,
                            'flavor': cur_flavor,
                            'stars': rating,
                            'bonus_levels': bonus_levels,
                            'calories': total_cal,
                            'unique_berries': len(name_counts),
                            'inventory_sum': total_used_inventory,
                            # Individual flavor scores
                            'sweet': cur_sweet,
                            'spicy': cur_spicy,
                            'sour': cur_sour,
                            'bitter': cur_bitter,
                            'fresh': cur_fresh,
                            'max_flavor_value': max_single,
                            'max_flavor_type': max_flavor_name,
                        })

                    if cur_flavor > best_min_found:
                        best_min_found = cur_flavor
            return

        if remaining == 0:
            return

        # Pruning: can't reach target even if we take max of everything left
        max_possible = cur_flavor + scores[pos] * remaining
        if max_possible < best_min_found:
            return

        max_take = min(remaining, remaining_counts[pos])

        for take in range(max_take + 1):
            new_flavor = cur_flavor + take * scores[pos]
            new_levels = cur_levels + take * levels_list[pos]
            new_cal = cur_cal + take * cal_list[pos]

            new_sweet = cur_sweet + take * sweets[pos]
            new_spicy = cur_spicy + take * spicies[pos]
            new_sour = cur_sour + take * sours[pos]
            new_bitter = cur_bitter + take * bitters[pos]
            new_fresh = cur_fresh + take * freshes[pos]

            # Early break if even taking max future won't help
            if take < max_take:
                future_max = new_flavor + scores[pos] * (remaining - take)
                if future_max < best_min_found:
                    break

            new_remaining = remaining_counts[:]
            new_remaining[pos] -= take

            new_path = path + [pos] * take
            search(pos + 1, remaining - take,
                   new_flavor, new_levels, new_cal,
                   new_sweet, new_spicy, new_sour, new_bitter, new_fresh,
                   new_path, new_remaining)

    initial_counts = counts[:]
    search(0, num_berries, 0, 0, 0, 0, 0, 0, 0, 0, [], initial_counts)

    elapsed = time.perf_counter() - start_time
    print(f"Found {len(results):,} donuts ≥ {target} flavor in {elapsed:.2f} seconds")
    if results:
        print(f"Best flavor found: {max(r['flavor'] for r in results)}")

    return results, elapsed


# ----------------------------------------------------
# Output
# ----------------------------------------------------
def save_results(results, target, num_berries, elapsed):
    timestamp = datetime.now().strftime("%m%d%y_%H%M%S")
    filename = f"output/donut_recipes_{timestamp}.txt"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Found {len(results):,} donuts with ≥ {target} flavor "
                f"using {num_berries} berries in {elapsed:.2f}s\n\n")

        # Sort: highest inventory sum first, then highest calories
        sorted_res = sorted(results, key=lambda x: (x['inventory_sum'], x['calories']), reverse=True)
        
        # Sort: highest calories first, then highest inventory sum
        # sorted_res = sorted(results, key=lambda x: (x['calories'], x['inventory_sum']), reverse=True)

        for i, r in enumerate(sorted_res, 1):
            parts = [f"{cnt} {berry}" for berry, cnt in r['name_counts'].items()]
            calories = r['calories']
            duration = math.floor(calories / 10)  # assuming 5★ portal
            # 1-Star Portal: 1 calorie per second (60 cal/min)
            # 2-Star Portal: 1.6 calories per second (96 cal/min)
            # 3-Star Portal: 3.5 calories per second (210 cal/min)
            # 4-Star Portal: 7.5 calories per second (450 cal/min)
            # 5-Star Portal: 10 calories per second (600 cal/min)

            flavor_breakdown = (
                f"Sweet:{r['sweet']} Spicy:{r['spicy']} Sour:{r['sour']} "
                f"Bitter:{r['bitter']} Fresh:{r['fresh']}"
            )

            line = (
                f"{i}. {r['stars']}★ ({r['max_flavor_type']}) ({', '.join(parts)})→"
                f"In Stock:{r['inventory_sum']} "
                f"Calories:{calories} ({duration:.1f}s) "
                f"Bonus Lvl:{r['bonus_levels']} "
                f"Flavor:{r['flavor']}  "
                f"[{flavor_breakdown}] "
                f"Unique:{r['unique_berries']}\n"
            )
            f.write(line)

    print(f"Saved to: {filename}")


# ----------------------------------------------------
# Main
# ----------------------------------------------------
if __name__ == "__main__":
    berries = load_berries('hyper_berries.csv')

    print(f"Loaded {len(berries)} berries.")

    TARGET = 400          # adjust as needed
    NUM_BERRIES = 8       # adjust as needed
    ONLY_STAR_RATING = [3,4]   # or "all"
    ONLY_FLAVORS = ["Spicy","Bitter","Fresh"]   # or "all"

    results, elapsed = find_high_score_donuts(
        berries,
        TARGET,
        NUM_BERRIES,
        ONLY_STAR_RATING,
        ONLY_FLAVORS
    )

    if results:
        save_results(results, TARGET, NUM_BERRIES, elapsed)