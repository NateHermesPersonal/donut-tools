import csv
from collections import Counter
from datetime import datetime
from tabulate import tabulate # pip install tabulate
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
            original_index = int(row['Index'])
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
                    original_index,  # 0: original CSV index
                    name,            # 1: berry name
                    flavor_total,    # 2: total flavor
                    levels,          # 3: levels
                    calories,        # 4: calories
                    count,           # 5: inventory count
                    sweet,           # 6: sweet
                    spicy,           # 7: spicy
                    sour,            # 8: sour
                    bitter,          # 9: bitter
                    fresh            # 10: fresh
                ))
            except (ValueError, KeyError) as e:
                print(f"Skipping invalid row for '{name}': {e}")
                continue

    # Sort descending by total flavor score FOR SEARCH PERFORMANCE (but we'll re-sort for display)
    berries.sort(key=lambda x: x[2], reverse=True)
    return berries


# ----------------------------------------------------
# Backtracking with inventory check
# ----------------------------------------------------
def find_high_score_donuts(berries, target, num_berries=8, include_stars="all", include_flavors="all"):
    start_time = time.perf_counter()

    # Unpack for faster access
    names = [b[1] for b in berries]
    scores = [b[2] for b in berries]          # total flavor
    levels_list = [b[3] for b in berries]
    cal_list = [b[4] for b in berries]
    counts = [b[5] for b in berries]
    sweets = [b[6] for b in berries]
    spicies = [b[7] for b in berries]
    sours = [b[8] for b in berries]
    bitters = [b[9] for b in berries]
    freshes = [b[10] for b in berries]
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
                        total_used_inventory += counts[idx] # inventory of each unique berry

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
def save_results(results, target, berry_count_str, elapsed, berries):
    timestamp = datetime.now().strftime("%m%d%y_%H%M%S")
    filename = f"output/donut_recipes_{timestamp}.txt"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Found {len(results):,} donuts with ≥ {target} flavor\n")
        f.write(f"using {berry_count_str} berries in {elapsed:.2f}s "
                f"(respecting current inventory)\n\n")

        if not results:
            f.write("No matching recipes found.\n")
            print("No results to save.")
            return

        # Prepare data for tabulate
        table_data = []

        # Sort berries by original_index ASCENDING for recipe display
        sorted_berries = sorted(berries, key=lambda x: x[0])

        for r in results:
            # Build recipe string in ascending CSV index order (only include used berries)
            parts = []
            for berry_tuple in sorted_berries:
                berry_name = berry_tuple[1]
                cnt = r['name_counts'].get(berry_name, 0)
                if cnt > 0:
                    parts.append(f"{cnt} {berry_name}")

            composition = ", ".join(parts)

            # Optional: truncate very long lines
            if len(composition) > 120:
                composition = composition[:117] + "..."

            total_berries = sum(r['name_counts'].values())

            table_data.append([
                f"{total_berries} ({r['unique_berries']})",
                f"{r['stars']}★",
                f"{r['max_flavor_type']} ({r['max_flavor_value']})",
                r['flavor'],
                r['calories'],
                f"{math.floor(r['calories']/10)}s", # 5 star calorie burn rate
                r['inventory_sum'],
                r['bonus_levels'],
                composition
            ])

        # You can change sorting here if desired
        # Current: most inventory → highest calories
        table_data.sort(key=lambda row: (-row[6], -row[4]))

        headers = [
            "Count",
            "★",
            "Dominant",
            "Flavor",
            "Calories",
            "Time (5★)",
            "Inventory",
            "Levels",
            "Recipe"
        ]

        # Create beautiful table
        table_str = tabulate(
            table_data,
            headers=headers,
            tablefmt="github",
            colalign=("right", "center", "left", "right", "right", "right", "right", "right", "left"),
            stralign="left",
            numalign="right",
        )

        f.write(table_str + "\n\n")

    print(f"Saved formatted table to: {filename}")


# ----------------------------------------------------
# Main
# ----------------------------------------------------
if __name__ == "__main__":
    berries = load_berries('hyper_berries.csv')
    print(f"Loaded {len(berries)} berries.\n")

    TARGET_FLAVOR = 400
    MIN_BERRIES   = 3
    MAX_BERRIES   = 8
    ONLY_STAR_RATING = [3, 4]           # or "all"
    ONLY_FLAVORS     = "all"
    # ONLY_FLAVORS     = ["Spicy", "Bitter", "Fresh"]   # or "all"

    all_results = []
    total_time = 0

    for num in range(MIN_BERRIES, MAX_BERRIES + 1):
        print(f"\nSearching for {num}-berry donuts ≥ {TARGET_FLAVOR} flavor ...")
        results, elapsed = find_high_score_donuts(
            berries,
            TARGET_FLAVOR,
            num_berries = num,
            include_stars = ONLY_STAR_RATING,
            include_flavors = ONLY_FLAVORS
        )
        total_time += elapsed
        all_results.extend(results)
        print(f"  → found {len(results)} recipes in {elapsed:.2f}s")

    print(f"\nTotal recipes found: {len(all_results)}")
    print(f"Total search time: {total_time:.2f}s")

    if all_results:
        # Pass berries here so save_results can use original order
        save_results(all_results, TARGET_FLAVOR, f"{MIN_BERRIES}–{MAX_BERRIES}", total_time, berries)