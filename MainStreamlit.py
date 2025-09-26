import streamlit as st
import pymysql
import pandas as pd

# ------------------ DATABASE CONFIG ------------------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Root',
    'database': 'cricbuzz2',
    'port': 3306
}

def get_mysql_conn():
    """Establishes and returns a MySQL database connection."""
    return pymysql.connect(**DB_CONFIG)

def get_table_data(table_name):
    """Fetches all data from a specified table."""
    conn = get_mysql_conn()
    try:
        df = pd.read_sql(f"SELECT * FROM `{table_name}`", conn)
    except Exception as e:
        st.error(f"Error reading from table '{table_name}': {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

def run_query(query, params=None):
    """Executes a SELECT query and returns the results as a DataFrame."""
    conn = get_mysql_conn()
    try:
        df = pd.read_sql(query, conn, params=params)
    except Exception as e:
        st.error(f"Query failed: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

def modify_query(query, params=None):
    """Executes a DDL or DML query (e.g., INSERT, UPDATE, DELETE)."""
    conn = get_mysql_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="Cricbuzz Live Match Dashboard", layout="wide")
st.markdown("<h1>🏏 Cricbuzz Live Match Dashboard</h1>", unsafe_allow_html=True)

# Sidebar Navigation
pages = [
    "Live Scores",
    "Player Stats",
    "SQL Analytics",
    "CRUD Operations"
]
page = st.sidebar.selectbox("Choose a page:", pages)

st.sidebar.markdown("---")
st.sidebar.markdown("#### 📊 Detailed scorecards")
st.sidebar.markdown("#### 🏆 Series information")
st.sidebar.markdown("#### 🎯 Interactive match selection")

# ------------------ LIVE SCORES ------------------
if page == "Live Scores":
    st.header("🏏 Live Cricket Dashboard")
    matches_df = get_table_data("live_matches")
    recent_matches = get_table_data("recent_matches")
    schedules = get_table_data("schedules")

    # Top Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("📊 Total Matches", len(matches_df) + len(recent_matches) + len(schedules))
    col2.metric("🟢 Live Now", matches_df.shape[0])
    col3.metric("📅 Upcoming", schedules.shape[0])

    # Tabs
    tab1, tab2, tab3 = st.tabs(["🟢 Live Matches", "📜 Recent Matches", "📅 Schedules"])

    with tab1:
        if matches_df.empty:
            st.info("No live matches found in the database.")
        else:
            matches_df["match_label"] = matches_df.apply(
                lambda row: f"{row['team1']} vs {row['team2']} - {row['series_name']} ({row['status']})", axis=1
            )
            match_choice = st.selectbox("Available Matches:", matches_df["match_label"])
            match_row = matches_df[matches_df["match_label"] == match_choice].iloc[0]

            st.markdown(f"""
    <div style="
        background-color: var(--background-color);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        margin-bottom: 15px;
        color: var(--text-color);
    ">
        <h3 style="color: var(--primary-color);">
            {match_row['team1']} vs {match_row['team2']}
        </h3>
        <p>🏆 <b>Series:</b> {match_row['series_name']}</p>
        <p>📌 <b>Match Type:</b> {match_row['match_type']}</p>
        <p>⏱ <b>Status:</b> {match_row['status']}</p>
        <hr>
        <h4>📊 Current Score</h4>
        <p><b>{match_row['team1']}:</b> {match_row['team1_score']}</p>
        <p><b>{match_row['team2']}:</b> {match_row['team2_score']}</p>
    </div>
""", unsafe_allow_html=True)
    with tab2:
        if recent_matches.empty:
            st.info("No recent matches found in the database.")
        else:
            st.subheader("📜 Recent Matches")
            team_filter = st.selectbox("Filter by Team", ["All"] + recent_matches["Team_1"].unique().tolist())
            if team_filter != "All":
                recent_matches = recent_matches[(recent_matches["Team_1"] == team_filter) | (recent_matches["Team_2"] == team_filter)]
            st.dataframe(recent_matches)

    with tab3:
        if schedules.empty:
            st.info("No schedules found in the database.")
        else:
            st.subheader("📅 Upcoming Matches")
            st.dataframe(schedules)

# ------------------ PLAYER STATS ------------------
elif page == "Player Stats":
    st.header("🌟 Player & Team Statistics")

    icc_ranks = get_table_data("icc_ranks")
    player_stats = get_table_data("player_stats")
    team_results = get_table_data("team_results")

    col1, col2, col3 = st.columns(3)
    col1.metric("🏆 Ranked Players", icc_ranks.shape[0])
    col2.metric("📊 Player Records", player_stats.shape[0])
    col3.metric("📌 Team Results", team_results.shape[0])

    tab1, tab2, tab3 = st.tabs(["🏆 ICC Ranks", "🧑‍💻 Player Stats", "👥 Team Results"])

    with tab1:
        if icc_ranks.empty:
            st.info("No ICC ranks found in the database.")
        else:
            st.subheader("🏆 ICC Player Rankings")
            st.dataframe(icc_ranks)

    with tab2:
        if player_stats.empty:
            st.info("No player stats found in the database.")
        else:
            st.subheader("📊 Player Batting & Bowling Stats")
            format_filter = st.selectbox("Filter by Format", ["All"] + player_stats["format_type"].unique().tolist())
            if format_filter != "All":
                player_stats = player_stats[player_stats["format_type"] == format_filter]
            st.dataframe(player_stats)
            if "runs" in player_stats.columns:
                st.bar_chart(player_stats.groupby("player_name")["runs"].sum().sort_values(ascending=False).head(10))

    with tab3:
        if team_results.empty:
            st.info("No team results found in the database.")
        else:
            st.subheader("👥 Team Match Results")
            st.dataframe(team_results)

# ------------------ SQL ANALYTICS ------------------
elif page == "SQL Analytics":
    st.header("📊 SQL Analytics & Insights")

    # Intro Row with Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("📝 Total Queries", 25)
    col2.metric("🔎 Beginner Queries", 8)
    col3.metric("⚡ Advanced Queries", 10)
    st.markdown("---")

    queries = {
        # Beginner Level
        "1. Players representing India": """
            SELECT player_name, playing_role, batting_style, bowling_style
            FROM player_info
            WHERE country = 'India';
        """,
        "2. Recent cricket matches": """
            SELECT CONCAT(Team_1, ' vs ', Team_2) AS match_desc, Team_1, Team_2, Venue, Start_Time
            FROM recent_matches
            WHERE Start_Time >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            ORDER BY Start_Time DESC;
        """,
        "3. Top 10 ODI run scorers": """
            SELECT player_id, player_name, matches, innings, runs, average, strike_rate, hundreds, fifties
            FROM player_stats
            WHERE format_type = 'ODI'
            ORDER BY runs DESC
            LIMIT 10;
        """,
        "4. Venues with capacity > 50,000": """
            SELECT venue_name, city, country, capacity
            FROM venues
            WHERE capacity > 50000
            ORDER BY capacity DESC;
        """,
        "5. Matches won by team": """
            SELECT team_name,
            COUNT(*) as total_wins
            FROM (
            SELECT Team_1 as team_name
            FROM recent_matches 
            WHERE Status LIKE '%won by%' AND Status LIKE CONCAT(Team_1, '%')
            UNION ALL
            SELECT Team_2 as team_name
            FROM recent_matches 
            WHERE Status LIKE '%won by%' AND Status LIKE CONCAT(Team_2, '%')
            ) as wins
            GROUP BY team_name
            ORDER BY total_wins DESC;
        """,
        "6. Player count by role": """
            SELECT playing_role, COUNT(*) AS player_count
            FROM player_info
            GROUP BY playing_role;
        """,
        "7. Highest individual score by format": """
            SELECT format_type, MAX(runs) AS highest
            FROM player_stats
            GROUP BY format_type;
        """,
        "8. Series started in 2024": """
            SELECT Series_ID, Series_Name, Start_Date, End_Date, Year
            FROM series_list
        """,

        # Intermediate Level
        "9. All-rounders with 1000+ runs & 50+ wickets": """
            SELECT player_name, runs, wickets, format_type
            FROM player_stats
            WHERE runs > 1000 AND wickets > 50;
        """,
        "10. Last 20 completed matches": """
            SELECT CONCAT(Team_1, ' vs ', Team_2) AS match_desc, Team_1, Team_2, Status, Venue, Start_Time
            FROM recent_matches
            ORDER BY Start_Time DESC
            LIMIT 20;
        """,
        "11. Player performance across formats": """
            SELECT player_name, 
                SUM(CASE WHEN format_type='Test' THEN runs ELSE 0 END) AS test_runs,
                SUM(CASE WHEN format_type='ODI' THEN runs ELSE 0 END) AS odi_runs,
                SUM(CASE WHEN format_type='T20I' THEN runs ELSE 0 END) AS t20i_runs,
                AVG(average) AS overall_avg
            FROM player_stats
            GROUP BY player_name
            HAVING COUNT(DISTINCT format_type) >= 2;
        """,
        "12. Team home vs away wins": """
            SELECT t.team_name,
            SUM(CASE WHEN t.team_name = rm.Team_1 AND rm.Status LIKE CONCAT(t.team_name, '%') THEN 1 ELSE 0 END) AS home_wins,
            SUM(CASE WHEN t.team_name = rm.Team_2 AND rm.Status LIKE CONCAT(t.team_name, '%') THEN 1 ELSE 0 END) AS away_wins
            FROM recent_matches rm
            JOIN (
            SELECT Team_1 AS team_name FROM recent_matches
            UNION
            SELECT Team_2 FROM recent_matches
            ) t ON t.team_name IN (rm.Team_1, rm.Team_2)
            GROUP BY t.team_name
            ORDER BY t.team_name;
        """,
        "13. 100+ run partnerships (adjacent batsmen)": """
            SELECT 
            player_name AS batsman1, 
            bat_partner_name AS batsman2, 
            total_runs AS partnership_runs
            FROM partnership_scorecard
            WHERE total_runs >= 100
            ORDER BY total_runs DESC;
        """,
        "14. Bowling performance by venue": """
        SELECT 
            ps.player_name,
            vm.venue_name,
            AVG(ps.economy_rate) AS avg_economy,
            SUM(ps.wickets) AS total_wickets,
            COUNT(*) AS matches
        FROM player_stats ps
        JOIN venue_matches vm 
            ON ps.format_type = vm.match_format
        WHERE ps.overs_bowled >= 4
        GROUP BY ps.player_name, vm.venue_name
        HAVING matches >= 3
        ORDER BY total_wickets DESC;
        """,
        "15. Player performance in close matches": """
            SELECT series_name, match_type, team_1, team_2, status, start_time
            FROM recent_matches
            WHERE status LIKE '%won by % run%'
                AND CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(status, ' ', -2), ' ', 1) AS UNSIGNED) < 50
                OR status LIKE '%won by % wkt%'
                AND CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(status, ' ', -2), ' ', 1) AS UNSIGNED) < 5
            ORDER BY start_time DESC;
        """,
        "16. Batting performance by year (since 2020)": """
            SELECT 
                player_name,
                format_type,
                AVG(runs) AS avg_runs,
                AVG(strike_rate) AS avg_sr,
                COUNT(*) AS records
            FROM player_stats
            GROUP BY player_name, format_type
            HAVING records >= 5;
        """,
        # Advanced Level
        "17. Toss win advantage analysis": """
            SELECT toss_decision, 
                ROUND(100 * SUM(CASE WHEN toss_winner = match_winner THEN 1 ELSE 0 END)/COUNT(*),2) AS win_pct
            FROM live_matches
            GROUP BY toss_decision;
        """,
        "18. Most economical bowlers (ODI & T20)": """
            SELECT bowler_name, AVG(economy_rate) AS avg_economy, SUM(wickets) AS total_wickets, COUNT(*) AS matches
            FROM player_bowling_stats
            WHERE format IN ('ODI', 'T20I')
            GROUP BY bowler_name
            HAVING matches >= 10 AND AVG(overs_bowled) >= 2
            ORDER BY avg_economy ASC;
        """,
        "19. Most consistent batsmen (since 2022)": """
            SELECT player_name, AVG(runs) AS avg_runs, STDDEV(runs) AS run_stddev
            FROM player_batting_stats
            WHERE balls_faced >= 10 AND match_date >= '2022-01-01'
            GROUP BY player_name
            HAVING COUNT(*) >= 5
            ORDER BY run_stddev ASC;
        """,
        "20. Player matches & averages by format": """
            SELECT player_name, 
                SUM(CASE WHEN format='Test' THEN 1 ELSE 0 END) AS test_matches,
                SUM(CASE WHEN format='ODI' THEN 1 ELSE 0 END) AS odi_matches,
                SUM(CASE WHEN format='T20I' THEN 1 ELSE 0 END) AS t20_matches,
                AVG(CASE WHEN format='Test' THEN batting_average END) AS test_avg,
                AVG(CASE WHEN format='ODI' THEN batting_average END) AS odi_avg,
                AVG(CASE WHEN format='T20I' THEN batting_average END) AS t20_avg
            FROM player_batting_stats
            GROUP BY player_name
            HAVING (test_matches + odi_matches + t20_matches) >= 20;
        """,
        "21. Player performance ranking": """
            SELECT player_name,
                (runs * 0.01 + batting_average * 0.5 + strike_rate * 0.3) +
                (wickets * 2 + (50-bowling_average)*0.5 + (6-economy_rate)*2) +
                (catches + stumpings) AS total_points
            FROM player_stats
            ORDER BY total_points DESC
            LIMIT 20;
        """,
        "22. Head-to-head team analysis (last 3 years)": """
            SELECT team1, team2, COUNT(*) AS matches_played,
                SUM(CASE WHEN winner = team1 THEN 1 ELSE 0 END) AS team1_wins,
                SUM(CASE WHEN winner = team2 THEN 1 ELSE 0 END) AS team2_wins,
                AVG(CASE WHEN winner = team1 THEN victory_margin END) AS team1_avg_margin,
                AVG(CASE WHEN winner = team2 THEN victory_margin END) AS team2_avg_margin
            FROM matches
            WHERE match_date >= DATE_SUB(CURDATE(), INTERVAL 3 YEAR)
            GROUP BY team1, team2
            HAVING matches_played >= 5;
        """,
        "23. Recent player form & momentum": """
            SELECT player_name,
                AVG(CASE WHEN match_num > 5 THEN runs END) AS avg_last_10,
                AVG(CASE WHEN match_num <= 5 THEN runs END) AS avg_last_5,
                SUM(CASE WHEN runs >= 50 THEN 1 ELSE 0 END) AS scores_50plus,
                STDDEV(runs) AS consistency_score
            FROM (
                SELECT player_name, runs, ROW_NUMBER() OVER (PARTITION BY player_name ORDER BY match_date DESC) AS match_num
                FROM player_batting_stats
            ) AS recent
            WHERE match_num <= 10
            GROUP BY player_name;
        """,
        "24. Best batting partnerships": """
            SELECT p1.player_name AS batsman1, p2.player_name AS batsman2,
                AVG(partnership_runs) AS avg_runs,
                SUM(CASE WHEN partnership_runs > 50 THEN 1 ELSE 0 END) AS fifty_plus,
                MAX(partnership_runs) AS highest,
                COUNT(*) AS total_partnerships
            FROM partnerships
            JOIN player_info p1 ON partnerships.batsman1_id = p1.id
            JOIN player_info p2 ON partnerships.batsman2_id = p2.id
            WHERE ABS(partnerships.batsman1_pos - partnerships.batsman2_pos) = 1
            GROUP BY batsman1, batsman2
            HAVING total_partnerships >= 5
            ORDER BY avg_runs DESC;
        """,
        "25. Player performance time-series analysis": """
            SELECT player_name, 
                CONCAT(YEAR(match_date), '-Q', QUARTER(match_date)) AS quarter,
                AVG(runs) AS avg_runs, AVG(strike_rate) AS avg_sr, COUNT(*) AS matches
            FROM player_batting_stats
            GROUP BY player_name, quarter
            HAVING COUNT(*) >= 3
            ORDER BY player_name, quarter;
        """
    }
    query_choice = st.selectbox("🔍 Choose a query to run:", list(queries.keys()))
    if st.button("▶ Run Query"):
        df = run_query(queries[query_choice])
        if df.empty:
            st.warning("No results found for this query.")
        else:
            st.markdown("""
            <div style="background:#ffffff;
                        padding:15px;
                        border-radius:12px;
                        box-shadow:0 2px 10px rgba(0,0,0,0.1);
                        margin-bottom:15px;">
                <h4 style="color:#0B6623;">📊 Query Results</h4>
            </div>
            """, unsafe_allow_html=True)
            st.dataframe(df)
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            if len(numeric_cols) >= 1:
                st.subheader("📈 Quick Visualization")
                st.bar_chart(df.set_index(df.columns[0])[numeric_cols[0]])

# ------------------ CRUD OPERATIONS ------------------
elif page == "CRUD Operations":
    st.header("⚙️ CRUD Operations (Admin Panel)")
    tables = [
        "icc_ranks",
        "live_matches",
        "player_info",
        "player_stats",
        "recent_matches",
        "schedules",
        "series_list",
        "team_results",
        "team_standings",
        "venues"
    ]
    crud_table = st.selectbox("Select Table", tables)
    action = st.radio("Action", ["Create", "Read", "Update", "Delete"], key="crud_action")

    # READ
    if action == "Read":
        st.subheader(f"📖 Data from `{crud_table}`")
        df = get_table_data(crud_table)
        st.dataframe(df)

    # CREATE
    elif action == "Create":
        with st.expander("➕ Insert New Row"):
            st.write(f"Insert new row into `{crud_table}`")
            new_values = st.text_area("Enter comma-separated values:")
            if st.button("Insert Row"):
                conn = get_mysql_conn()
                cursor = conn.cursor()
                cursor.execute(f"DESCRIBE {crud_table};")
                col_count = len(cursor.fetchall())
                conn.close()
                placeholders = ",".join(["%s"] * col_count)
                try:
                    modify_query(f"INSERT INTO `{crud_table}` VALUES ({placeholders})", tuple(new_values.split(",")))
                    st.success("✅ Row inserted successfully!")
                except Exception as e:
                    st.error(f"❌ Insert failed: {e}")

    # UPDATE
    elif action == "Update":
        with st.expander("✏️ Update Existing Row"):
            conn = get_mysql_conn()
            cursor = conn.cursor()
            cursor.execute(f"DESCRIBE {crud_table};")
            valid_columns = [col[0] for col in cursor.fetchall()]
            conn.close()

            row_id = st.number_input("Row ID:", min_value=1, step=1)
            column = st.selectbox("Column name:", valid_columns)
            new_value = st.text_input("New value:")

            if st.button("Update Row"):
                try:
                    modify_query(f"UPDATE `{crud_table}` SET `{column}`=%s WHERE id=%s", (new_value, row_id))
                    st.success("✅ Row updated successfully!")
                except Exception as e:
                    st.error(f"❌ Update failed: {e}")

    # DELETE
    elif action == "Delete":
        with st.expander("🗑️ Delete Row"):
            row_id = st.number_input("Row ID to delete:", min_value=1, step=1)
            if st.button("Delete Row"):
                try:
                    modify_query(f"DELETE FROM `{crud_table}` WHERE id=%s", (row_id,))
                    st.success("✅ Row deleted successfully!")
                except Exception as e:
                    st.error(f"❌ Delete failed: {e}")
