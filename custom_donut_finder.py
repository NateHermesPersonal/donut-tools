import csv
from collections import Counter
from datetime import datetime
import time
import math
import bisect

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
            if not name:
                continue
            scores = ['Sweet Score', 'Spicy Score', 'Sour Score', 'Bitter Score', 'Fresh Score']
            flavor = sum(int(row[k]) for k in scores)
            levels = int(row['Levels'])
            calories = int(row['Calories'])
            count = int(row.get('Count', 0))          # NEW: read Count, default 0 if missing
            berries.append((name, flavor, levels, calories, count))
    # Sort descending by flavor score
    berries.sort(key=lambda x: x[1], reverse=True)
    return berries


# ----------------------------------------------------
# Backtracking with inventory check
# ----------------------------------------------------
def find_high_score_donuts(berries, target, num_berries=8, include_stars="all"):
    start_time = time.perf_counter()
    
    # Unpack for faster access
    names   = [b[0] for b in berries]
    scores  = [b[1] for b in berries]
    levels  = [b[2] for b in berries]
    cal     = [b[3] for b in berries]
    counts  = [b[4] for b in berries]          # NEW: available counts
    
    results = []
    best_min_found = target
    
    def search(pos, remaining, cur_flavor, cur_levels, cur_cal, path, remaining_counts):
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
                    
                    if include_stars == "all" or rating in include_stars:
                        results.append({
                            'name_counts': name_counts,
                            'flavor': cur_flavor,
                            'stars': rating,
                            'bonus_levels': bonus_levels,
                            'calories': total_cal,
                            'unique_berries': len(name_counts),
                            'inventory_sum': total_used_inventory
                        })
                    
                    if cur_flavor > best_min_found:
                        best_min_found = cur_flavor
            return  # ← always return here when pos is out of range
        
        if remaining == 0:
            return  # nothing more to assign, but we didn't reach the end → invalid path
        
        # Pruning
        max_possible = cur_flavor + scores[pos] * remaining
        if max_possible < best_min_found:
            return
        
        max_take = min(remaining, remaining_counts[pos])
        
        for take in range(max_take + 1):
            new_flavor = cur_flavor + take * scores[pos]
            new_levels = cur_levels + take * levels[pos]
            new_cal = cur_cal + take * cal[pos]
            
            # Early break if even max future won't help
            if take < max_take:
                future_max = new_flavor + scores[pos] * (remaining - take)
                if future_max < best_min_found:
                    break
            
            new_remaining = remaining_counts[:]
            new_remaining[pos] -= take
            
            new_path = path + [pos] * take
            search(pos + 1, remaining - take, new_flavor, new_levels, new_cal, new_path, new_remaining)
    
    # Start with initial counts
    initial_counts = counts[:]
    search(0, num_berries, 0, 0, 0, [], initial_counts)
    
    elapsed = time.perf_counter() - start_time
    print(f"Found {len(results):,} donuts ≥ {target} flavor in {elapsed:.2f} seconds "
          f"(respecting inventory)")
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
                f"using {num_berries} berries in {elapsed:.2f}s "
                f"(respecting current berry counts)\n\n")
        
        sorted_res = sorted(results, key=lambda x: x['inventory_sum'], reverse=True)
        
        for i, r in enumerate(sorted_res, 1):
            parts = [f"{cnt} {berry}" for berry, cnt in r['name_counts'].items()]
            line = (
                f"{i}. {r['stars']}★  ({', '.join(parts)})  "
                f"Flavor: {r['flavor']}  "
                f"Unique: {r['unique_berries']}  "
                f"Inv-sum: {r['inventory_sum']}  "           # ← added
                f"Bonus Levels: {r['bonus_levels']}  "
                f"Calories: {r['calories']}\n"
            )
            f.write(line)
    
    print(f"Saved to: {filename}")


# ----------------------------------------------------
# Main
# ----------------------------------------------------
if __name__ == "__main__":
    berries = load_berries('hyper_berries.csv')
    
    flavor_scores = [b[1] for b in berries]
    # max_possible = sum(sorted(flavor_scores, reverse=True)[:8])
    # print(f"Loaded {len(berries)} berries. Theoretical max flavor (8): {max_possible}")
    print(f"Loaded {len(berries)} berries.")
    
    TARGET = 400   # adjust as needed
    NUM_BERRIES = 8  # adjust as needed
    ONLY_STAR_RATING = [3,4]  # use "all" to include all star ratings
    results, elapsed = find_high_score_donuts(berries, TARGET, NUM_BERRIES, ONLY_STAR_RATING)
    
    if results:
        save_results(results, TARGET, NUM_BERRIES, elapsed)