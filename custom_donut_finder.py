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
            berries.append((name, flavor, levels, calories))
    # Sort descending by flavor score → enables good pruning
    berries.sort(key=lambda x: x[1], reverse=True)
    return berries


# ----------------------------------------------------
# Backtracking to find combinations
# ----------------------------------------------------
def find_high_score_donuts(berries, target, num_berries=8):
    start_time = time.perf_counter()
    
    # Unpack for faster access
    names   = [b[0] for b in berries]
    scores  = [b[1] for b in berries]
    levels  = [b[2] for b in berries]
    cal     = [b[3] for b in berries]
    
    results = []
    best_min_found = target  # we raise this when we find better donuts
    
    def search(pos, remaining, cur_flavor, cur_levels, cur_cal, path):
        nonlocal best_min_found
        
        if remaining == 0:
            if cur_flavor >= best_min_found:
                # Convert index counts → name counts right away
                counts = Counter(path)
                name_counts = {names[idx]: count for idx, count in counts.items()}
                
                rating, mult = get_star_rating(cur_flavor)
                bonus_levels = math.floor(cur_levels * mult)
                total_cal = int(cur_cal * mult)
                
                results.append({
                    'name_counts': name_counts,
                    'flavor': cur_flavor,
                    'stars': rating,
                    'bonus_levels': bonus_levels,
                    'calories': total_cal
                })
                
                # Track the best flavor found so far (optional tightening)
                if cur_flavor > best_min_found:
                    best_min_found = cur_flavor
            return
        
        # Pruning: even taking the best remaining berries isn't enough
        max_possible = cur_flavor + scores[pos] * remaining
        if max_possible < best_min_found:
            return
        
        # Try taking 0 or more of this berry
        for take in range(remaining + 1):
            new_flavor = cur_flavor + take * scores[pos]
            new_levels = cur_levels + take * levels[pos]
            new_cal = cur_cal + take * cal[pos]
            
            # Early stop if adding more of this won't help
            if take > 0 and new_flavor + scores[pos] * (remaining - take) < best_min_found:
                break
            
            new_path = path + [pos] * take
            search(pos + 1, remaining - take, new_flavor, new_levels, new_cal, new_path)
    
    search(0, num_berries, 0, 0, 0, [])
    
    elapsed = time.perf_counter() - start_time
    print(f"Found {len(results):,} donuts ≥ {target} flavor in {elapsed:.2f} seconds")
    if results:
        print(f"Best flavor found: {max(r['flavor'] for r in results)}")
    
    return results, elapsed


# ----------------------------------------------------
# Output formatting
# ----------------------------------------------------
def save_results(results, target, num_berries, elapsed):
    timestamp = datetime.now().strftime("%m%d%y_%H%M%S")
    filename = f"output/donut_recipes_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Found {len(results):,} donuts with ≥ {target} flavor "
                f"using {num_berries} berries in {elapsed:.2f}s\n\n")
        
        # Sort by flavor descending
        sorted_res = sorted(results, key=lambda x: x['flavor'], reverse=True)
        
        for i, r in enumerate(sorted_res, 1):
            parts = [f"{cnt} {berry}" for berry, cnt in r['name_counts'].items()]
            line = (
                f"{i}. {r['stars']}★  ({', '.join(parts)})  "
                f"Flavor: {r['flavor']}  "
                f"Bonus Levels: {r['bonus_levels']}  "
                f"Calories: {r['calories']}\n"
            )
            f.write(line)
    
    print(f"Saved to: {filename}")

# ----------------------------------------------------
# Main
# ----------------------------------------------------
if __name__ == "__main__":
    berries = load_berries('hyper_berries.csv')  # change path if needed
    print(f"Loaded {len(berries)} berries. Max flavor (8): {sum(b[1] for b in berries[:8])}")
    
    TARGET = 700   # change as desired: 700, 960, 1000, 1050, etc.
    results, elapsed = find_high_score_donuts(berries, target=TARGET, num_berries=8)
    
    if results:
        save_results(results, TARGET, 8, elapsed)