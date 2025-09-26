import requests
import pandas as pd
import schedule
import schedule
import time
from sqlalchemy import create_engine
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'database': 'cricbuzz2',
    'password': 'Root',
    'port': 3306
}
def extract_score(score_dict):
    """Extract score information from score dictionary"""
    # Get the latest innings (highest inningsId)
    if not score_dict:
        return "N/A"
    innings = list(score_dict.values())
    if not innings:
        return "N/A"
    # Pick the last innings (usually latest)
    latest = innings[-1]
    runs = latest.get('runs', 'N/A')
    wickets = latest.get('wickets', 'N/A')
    overs = latest.get('overs', 'N/A')
    return f"{runs}/{wickets} ({overs} ov)"

def fetch_and_store():
    url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
    headers = {
        "x-rapidapi-key": "f493d43d51mshd2b86741565d751p1ef6a6jsn5103eba1f487",
        "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        return
    
    type_matches = data.get('typeMatches', [])
    rows = []
    
    for type_match in type_matches:
        match_type = type_match.get('matchType', 'N/A')
        for series in type_match.get('seriesMatches', []):
            series_wrapper = series.get('seriesAdWrapper')
            if not series_wrapper:
                continue
            series_name = series_wrapper.get('seriesName', 'N/A')
            for match in series_wrapper.get('matches', []):
                info = match.get('matchInfo', {})
                score = match.get('matchScore', {})
                team1 = info.get('team1', {}).get('teamName', 'N/A')
                team2 = info.get('team2', {}).get('teamName', 'N/A')
                status = info.get('status', 'N/A')
                
                # Extract scores using the helper function
                team1_score = extract_score(score.get('team1Score', {}))
                team2_score = extract_score(score.get('team2Score', {}))
                
                rows.append({
                    'match_type': match_type,
                    'series_name': series_name,
                    'team1': team1,
                    'team2': team2,
                    'status': status,
                    'team1_score': str(team1_score),
                    'team2_score': str(team2_score)
                })
    
    df = pd.DataFrame(rows)
    if df.empty:
        print("No live matches found. DataFrame is empty. Skipping database update.")
        return
    
    try:
        engine = create_engine(
            f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
        df.to_sql('live_matches', con=engine, if_exists='replace', index=False)
        print(f"Data updated in database. {len(df)} matches stored.")
    except Exception as e:
        print(f"Error storing data to database: {e}")
        
schedule.every(6).hours.do(fetch_and_store)
if __name__ == "__main__":
    fetch_and_store()  # Initial run
    while True:
        schedule.run_pending()
        time.sleep(1)