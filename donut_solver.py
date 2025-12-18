import pandas as pd
import numpy as np
import itertools
from collections import Counter
import os
import time
from scipy.special import comb as combinations_with_replacement

# --- CONFIGURATION ---
INPUT_FILE = '4star_berries.csv'          # File in the same directory
SELECTION_SIZE = 8                  # Number of items to pick (r)
MIN_THRESHOLD = 400                  # Threshold ONLY applies to the value(s) that match
TARGET_MATCH_COUNT = 2              # E.g., 2 means we need at least 2 identical scores
REPORT_INTERVAL = 10000             # Report progress every N combinations checked
MAX_RESULTS = 50                 # Maximum number of results to find before stopping

# New Parameter: The match MUST involve a score from this list.
# 1. Use a list of one or more scores: e.g., ["Sweet Score"]
#    - The solver finds a match (e.g., Spicy=60, Sour=60). It only PASSES if 
#      the Sweet Score is ALSO 60, OR if Sweet Score was listed here.
# 2. Use "All" to not restrict which scores can be part of the match.
TARGET_SCORE_NAMES = ["Sour Score"] 
# ---------------------

def solve_recipes():
    # 1. Load and Prepare Data
    if not os.path.exists(INPUT_FILE):
        print(f"Error: '{INPUT_FILE}' not found. Please verify the file path.")
        return

    df = pd.read_csv(INPUT_FILE)
    score_columns = ["Sweet Score", "Spicy Score", "Sour Score", "Bitter Score", "Fresh Score"]
    
    # 1a. Validate and Set up Target Scores
    global TARGET_SCORE_NAMES
    if isinstance(TARGET_SCORE_NAMES, str) and TARGET_SCORE_NAMES.lower() == "all":
        # If "all" is set, the filter is effectively off.
        target_score_indices = list(range(len(score_columns)))
        target_score_names_display = "ALL"
    elif isinstance(TARGET_SCORE_NAMES, list):
        if not all(name in score_columns for name in TARGET_SCORE_NAMES):
            print(f"Error: TARGET_SCORE_NAMES contains invalid column names.")
            print(f"Valid options are: {score_columns}")
            return
        target_score_indices = [score_columns.index(name) for name in TARGET_SCORE_NAMES]
        target_score_names_display = TARGET_SCORE_NAMES
    else:
        print("Error: TARGET_SCORE_NAMES must be a list of score names or the string 'All'.")
        return

    # Extract data
    items = []
    for _, row in df.iterrows():
        items.append({
            "name": row["Berry Name"],
            "scores": row[score_columns].to_numpy(dtype=int)
        })

    N = len(items) 
    R = SELECTION_SIZE 
    total_combinations = int(combinations_with_replacement(N + R - 1, R))
    
    print("-" * 50)
    print(f"Data: {N} entries | Selection Size: {R}")
    print(f"Total Combinations to check: {total_combinations:,}")
    print(f"Goal: Find {TARGET_MATCH_COUNT} identical scores (>= {MIN_THRESHOLD})")
    print(f"Filter: The match MUST involve one of these scores: {target_score_names_display}")
    print("-" * 50)


    # 2. Setup Generator and Timer
    comb_gen = itertools.combinations_with_replacement(items, R)
    matches_found = 0
    combinations_checked = 0
    start_time = time.time()
    
    # Time formatting helper (simplified)
    def format_time(seconds):
        if seconds == float('inf'):
            return "Calculating..."
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}h {m:02d}m {s:02d}s"

    
    for combo in comb_gen:
        combinations_checked += 1
        
        # --- PROGRESS REPORTING ---
        if combinations_checked % REPORT_INTERVAL == 0:
            elapsed_time = time.time() - start_time
            progress_percent = (combinations_checked / total_combinations) * 100
            
            if progress_percent > 0:
                estimated_total_time = elapsed_time / (combinations_checked / total_combinations)
                time_remaining = estimated_total_time - elapsed_time
            else:
                time_remaining = float('inf')

            print(f"| Progress: {progress_percent:6.2f}% | Checked: {combinations_checked:,} | Time Remaining: {format_time(time_remaining)}", end='\r')


        # 3. Solver Logic (Check ALL 5 scores for a match)
        vectors = np.array([item['scores'] for item in combo])
        total_scores = np.sum(vectors, axis=0)
        
        # We now check all 5 scores for duplicates
        score_counts = Counter(total_scores)
        
        # Find all values that meet the criteria (MATCH COUNT & THRESHOLD)
        all_potential_match_values = [
            val for val, count in score_counts.items() 
            if count >= TARGET_MATCH_COUNT and val >= MIN_THRESHOLD
        ]
        
        if not all_potential_match_values:
            continue # No match was found anywhere, skip to next combination

        # 4. Filter Logic (Does the match include a target score?)
        
        # Get the actual scores in the combination that are targeted (Sweet, Spicy, etc.)
        target_score_values = total_scores[target_score_indices]
        
        # Check if ANY of the potential match values is present in the target score values
        valid_match_values = [
            match_val for match_val in all_potential_match_values
            if match_val in target_score_values
        ]
        
        # If valid_match_values is not empty, it means we found a match AND the value
        # is present in one of the required target scores.
        if valid_match_values:
            matches_found += 1
            
            # Print the final result
            print("\n" + "=" * 50)
            print(f"✨ RECIPE #{matches_found} FOUND!")
            
            names = [item['name'] for item in combo]
            ingredient_counts = Counter(names)
            quantity_str = ", ".join([f"{qty}x {name}" for name, qty in ingredient_counts.items()])
            
            # Full score map for clarity
            full_score_map = dict(zip(score_columns, total_scores))

            print(f"Ingredients: {quantity_str}")
            print(f"Final Scores: {full_score_map}")
            print(f"Success Logic: The value(s) {valid_match_values} appeared {TARGET_MATCH_COUNT}+ times (incl. a targeted score) and met the threshold.")
            print("=" * 50)
            
            # Optional: Stop after hitting max results
            if matches_found >= MAX_RESULTS:
                print(f"\n(Stopping after {MAX_RESULTS} results.)")
                break

    # Final Summary
    print("\n" + "#" * 50)
    print(f"Scan complete. Total time taken: {format_time(time.time() - start_time)}")
    print(f"Total combinations checked: {combinations_checked:,}")
    print(f"Total recipes found: {matches_found}")
    print("#" * 50)

if __name__ == "__main__":
    try:
        solve_recipes()
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please ensure you have installed the necessary libraries: pip install pandas numpy scipy")