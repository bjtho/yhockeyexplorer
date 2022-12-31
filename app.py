import pandas as pd
import streamlit as st
import plotly.express as px

st.title("The Yahoo UI we deserve")

# URL = "https://hockey.fantasysports.yahoo.com/hockey/87862/4"

LEAGUE = 87862
TEAM = 4
DATE = "2022-12-31"
STAT_1 = "S"
ALL_STAT_2 = ["D","L7","L14","L30","S_2022"]
# ALL_STAT_2 = ["L7", "L14"]

adjectives = ["current", "last_7", "last_14", "last_30", "s_2022"]

permanent = ["Pos", "Forwards/Defensemen", "Opp", "Status", 'Pre-Season']
variable = ["Current", "% Started","TOI/G", "G", "A", "+/-", "PPP", "SOG", "HIT"]

league = st.text_input("Input League ID", value="87862")
team = st.text_input("Input Team ID", value="4")
dt = st.date_input("Choose Date")


def get_table(league, team, date, stat_1, stat_2, adjective, table_index=0):
    local_variable = variable[:]
    if adjective == 'current':
        local_variable.remove('TOI/G')
    
    
    URL = f"https://hockey.fantasysports.yahoo.com/hockey/{league}/{team}/team?&date={date}&stat1={stat_1}&stat2={stat_2}"
    
    df_tables = pd.read_html(URL)
    
    current_table = df_tables[table_index]
    current_table.drop('Action', axis=1, level=1, inplace=True)
    current_table.drop(current_table.columns[-1], axis=1, inplace=True)
    headers = []
    headers.extend(permanent)
    headers.extend(local_variable)

    



    current_table.set_axis(headers, axis=1, inplace=True)
    current_table = current_table[current_table["Forwards/Defensemen"] != "Starting Lineup Totals"]
    return current_table[permanent], current_table[local_variable]

def clean_base(base):
    
    base["Forwards/Defensemen"] = base["Forwards/Defensemen"].str.replace("New Player Note", "")
    base["Forwards/Defensemen"] = base["Forwards/Defensemen"].str.replace("No new player Notes", "")
    base["Forwards/Defensemen"] = base["Forwards/Defensemen"].str.replace("Player Note", "")
    return base

@st.cache
def get_all_tables(league, team, dt):
    base = None
    tables = {}

    for idx, stat_2 in enumerate(ALL_STAT_2):
        if base is None:
            base, tables[adjectives[idx]] = get_table(league, team, dt, STAT_1,stat_2, adjectives[idx], table_index=0)

        else:
            _, tables[adjectives[idx]] = get_table(league, team, dt, STAT_1, stat_2, adjectives[idx], table_index=0)

    
    base = clean_base(base)
    return base, tables


loading_state = st.text("Loading Data from Y!")

base, tables = get_all_tables(league, team, dt)

loading_state.text("Done")

stat_filter_columns = variable[:]
time_series_filter_columns = adjectives[:]

stats = st.multiselect(label='stats', options=stat_filter_columns)
options = st.multiselect(label='options', options=time_series_filter_columns)


if not stats:
    stats = stat_filter_columns

if not options:
    options = time_series_filter_columns
    

table_render = base
print(stats, options)
if options:
    for o in options:
        table_render = table_render.join(tables[o][tables[o].columns.intersection(stats)], rsuffix="_"+o)
        


st.dataframe(table_render)

def rating_trend(base, tables):
    
    selection = st.selectbox(label="Choose player", options=base['Forwards/Defensemen'])
    s_idx = base.index[base['Forwards/Defensemen'] == selection]
    results = []
    for a in adjectives[1:]:
        rating = tables[a].loc[s_idx, 'Current'].values[0]
        results.append(rating)

    df_display = pd.DataFrame.from_dict({'period': reversed(adjectives[1:]), 'ratings':reversed(results)})
    print(df_display)
    fig = px.line(df_display,x='period', y='ratings', title=f"Rating Trend for {selection} (lower=better)")
    st.plotly_chart(fig)



    
graph_options = {"Yahoo Rating Trend": rating_trend}

graph_selection = st.selectbox(label="Select a graph", options=graph_options)

if graph_selection:
    graph_options[graph_selection](base, tables)

    