
# ============================================================
#  IPL DATA ANALYSIS — Complete EDA Script
#  Dataset: matches.csv + deliveries.csv (1095 matches, 17 seasons)
#  Tools: Pandas, Matplotlib, Seaborn
# ============================================================
 
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')
 
# ── Global chart style ───────────────────────────────────────
sns.set_theme(style="whitegrid", palette="Set2")
plt.rcParams.update({
    "figure.facecolor": "#FAFAFA",
    "axes.facecolor":   "#FAFAFA",
    "font.family":      "DejaVu Sans",
    "axes.titlesize":   14,
    "axes.titleweight": "bold",
    "axes.labelsize":   11,
})
 
# ============================================================
# SECTION 1 — LOAD DATA
# ============================================================
print("Loading data...")
 
matches    = pd.read_csv('matches.csv')
deliveries = pd.read_csv('deliveries.csv')
 
print(f"  matches    : {matches.shape[0]:,} rows × {matches.shape[1]} columns")
print(f"  deliveries : {deliveries.shape[0]:,} rows × {deliveries.shape[1]} columns")
 
# ============================================================
# SECTION 2 — CLEAN DATA
# ============================================================
print("\nCleaning data...")
 
# --- matches.csv ---
# Drop rows where winner is unknown (abandoned / no result matches)
matches.dropna(subset=['winner'], inplace=True)
 
# Fill missing city with 'Unknown'
matches['city'].fillna('Unknown', inplace=True)
 
# The 'method' column is mostly null (Duckworth-Lewis matches only) — drop it
matches.drop(columns=['method'], inplace=True)
 
# Normalise season labels: '2007/08' → 2008, '2020/21' → 2021, etc.
def parse_season(s):
    s = str(s)
    if '/' in s:
        return int(s.split('/')[1])   # take the later year
    return int(s)
 
matches['year'] = matches['season'].apply(parse_season)
 
# --- deliveries.csv ---
# Replace 'NA' string placeholders with proper NaN
deliveries.replace('NA', pd.NA, inplace=True)
 
# is_wicket should be integer (0 or 1)
deliveries['is_wicket'] = pd.to_numeric(deliveries['is_wicket'], errors='coerce').fillna(0).astype(int)
 
# batsman_runs and total_runs should be numeric
deliveries['batsman_runs'] = pd.to_numeric(deliveries['batsman_runs'], errors='coerce').fillna(0)
deliveries['total_runs']   = pd.to_numeric(deliveries['total_runs'],   errors='coerce').fillna(0)
 
print("  Cleaning complete.")
print(f"  Valid matches after cleaning: {len(matches):,}")
 
# ============================================================
# SECTION 3 — TOP 10 RUN SCORERS
# ============================================================
print("\nAnalysing top run scorers...")
 
top_batsmen = (
    deliveries
    .groupby('batter')['batsman_runs']
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
    .rename(columns={'batter': 'Player', 'batsman_runs': 'Total Runs'})
)
 
print(top_batsmen.to_string(index=False))
 
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(
    top_batsmen['Player'][::-1],
    top_batsmen['Total Runs'][::-1],
    color=sns.color_palette("Blues_d", 10)
)
 
# Add run labels on bars
for bar, val in zip(bars, top_batsmen['Total Runs'][::-1]):
    ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height() / 2,
            f'{int(val):,}', va='center', fontsize=9)
 
ax.set_title('Top 10 Run Scorers in IPL History')
ax.set_xlabel('Total Runs')
ax.set_xlim(0, top_batsmen['Total Runs'].max() * 1.12)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
plt.tight_layout()
plt.savefig('top_run_scorers.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: top_run_scorers.png")
 
# ============================================================
# SECTION 4 — TOP 10 WICKET TAKERS
# ============================================================
print("\nAnalysing top wicket takers...")
 
# Only count actual dismissals (not run-outs attributed to the fielder)
actual_wickets = deliveries[
    (deliveries['is_wicket'] == 1) &
    (deliveries['dismissal_kind'].notna()) &
    (~deliveries['dismissal_kind'].isin(['run out', 'retired hurt', 'obstructing the field']))
]
 
top_bowlers = (
    actual_wickets
    .groupby('bowler')['is_wicket']
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
    .rename(columns={'bowler': 'Player', 'is_wicket': 'Wickets'})
)
 
print(top_bowlers.to_string(index=False))
 
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(
    top_bowlers['Player'][::-1],
    top_bowlers['Wickets'][::-1],
    color=sns.color_palette("Greens_d", 10)
)
 
for bar, val in zip(bars, top_bowlers['Wickets'][::-1]):
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
            str(int(val)), va='center', fontsize=9)
 
ax.set_title('Top 10 Wicket Takers in IPL History')
ax.set_xlabel('Total Wickets')
ax.set_xlim(0, top_bowlers['Wickets'].max() * 1.12)
plt.tight_layout()
plt.savefig('top_wicket_takers.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: top_wicket_takers.png")
 
# ============================================================
# SECTION 5 — TOSS WIN VS MATCH WIN
# ============================================================
print("\nAnalysing toss impact...")
 
matches['toss_win_match_win'] = matches['toss_winner'] == matches['winner']
 
toss_rate = matches['toss_win_match_win'].mean() * 100
print(f"  Toss winner goes on to win the match: {toss_rate:.1f}%")
 
# Breakdown: does the toss decision (bat/field) affect win rate?
toss_decision = (
    matches
    .groupby('toss_decision')['toss_win_match_win']
    .agg(['sum', 'count'])
    .assign(win_pct=lambda df: df['sum'] / df['count'] * 100)
    .reset_index()
    .rename(columns={'toss_decision': 'Decision', 'sum': 'Wins', 'count': 'Total', 'win_pct': 'Win %'})
)
 
print(toss_decision.to_string(index=False))
 
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
 
# Pie: overall toss win → match win
overall = [toss_rate, 100 - toss_rate]
axes[0].pie(
    overall,
    labels=['Toss winner\nalso won', 'Toss winner\nlost'],
    autopct='%1.1f%%',
    colors=['#4CAF50', '#EF5350'],
    startangle=90,
    textprops={'fontsize': 11}
)
axes[0].set_title('Does Winning the Toss Help?')
 
# Bar: win % by toss decision
axes[1].bar(
    toss_decision['Decision'],
    toss_decision['Win %'],
    color=['#42A5F5', '#FF7043'],
    width=0.4
)
for i, row in toss_decision.iterrows():
    axes[1].text(i, row['Win %'] + 0.5, f"{row['Win %']:.1f}%", ha='center', fontsize=10)
axes[1].set_title('Win % by Toss Decision')
axes[1].set_ylabel('Win %')
axes[1].set_ylim(0, 65)
 
plt.suptitle('Toss Analysis', fontsize=15, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('toss_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: toss_analysis.png")
 
# ============================================================
# SECTION 6 — SEASON-WISE TOTAL RUNS
# ============================================================
print("\nAnalysing season-wise runs...")
 
# Merge deliveries with matches to get the year column
season_runs = (
    deliveries
    .merge(matches[['id', 'year']], left_on='match_id', right_on='id', how='left')
    .groupby('year')['total_runs']
    .sum()
    .reset_index()
    .rename(columns={'year': 'Season', 'total_runs': 'Total Runs'})
    .sort_values('Season')
)
 
fig, ax = plt.subplots(figsize=(13, 6))
ax.plot(
    season_runs['Season'],
    season_runs['Total Runs'],
    marker='o', linewidth=2.5, markersize=7,
    color='#1565C0'
)
 
# Shade area under line
ax.fill_between(season_runs['Season'], season_runs['Total Runs'], alpha=0.12, color='#1565C0')
 
# Annotate each point
for _, row in season_runs.iterrows():
    ax.annotate(
        f"{int(row['Total Runs']):,}",
        xy=(row['Season'], row['Total Runs']),
        xytext=(0, 10), textcoords='offset points',
        ha='center', fontsize=7.5, color='#333'
    )
 
ax.set_title('Season-wise Total Runs Scored in IPL')
ax.set_xlabel('Season')
ax.set_ylabel('Total Runs')
ax.set_xticks(season_runs['Season'])
ax.set_xticklabels(season_runs['Season'], rotation=45)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
plt.tight_layout()
plt.savefig('season_wise_runs.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: season_wise_runs.png")
 
# ============================================================
# SECTION 7 — EXPORT CLEANED DATA
# ============================================================
print("\nExporting cleaned data...")
 
matches.to_csv('matches_clean.csv', index=False)
print("  Saved: matches_clean.csv")
 
# ============================================================
# SUMMARY
# ============================================================
print("\n" + "="*50)
print("ANALYSIS COMPLETE — FILES GENERATED:")
print("  top_run_scorers.png")
print("  top_wicket_takers.png")
print("  toss_analysis.png")
print("  season_wise_runs.png")
print("  matches_clean.csv")
print("="*50)
print(f"\nQuick stats:")
print(f"  Total seasons analysed : {matches['year'].nunique()}")
print(f"  Total matches          : {len(matches):,}")
print(f"  Total balls bowled     : {len(deliveries):,}")
print(f"  Total runs scored      : {deliveries['total_runs'].sum():,}")
print(f"  Most successful team   : {matches['winner'].value_counts().index[0]}")
print(f"  Top run scorer         : {top_batsmen.iloc[0]['Player']} ({int(top_batsmen.iloc[0]['Total Runs']):,} runs)")
print(f"  Top wicket taker       : {top_bowlers.iloc[0]['Player']} ({int(top_bowlers.iloc[0]['Wickets'])} wickets)")
print(f"  Toss → match win rate  : {toss_rate:.1f}%")
