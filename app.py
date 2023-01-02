import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_elements import elements, dashboard, mui, html
st.set_page_config(layout="wide")
st.title("The Yahoo UI we deserve")

# URL = "https://hockey.fantasysports.yahoo.com/hockey/87862/4"

LEAGUE = 87862
TEAM = 4
DATE = "2022-12-31"
STAT_1 = "S"
ALL_STAT_2 = ["D","L7","L14","L30","S_2022"]
# ALL_STAT_2 = ["L7", "L14"]

adjectives = ["current", "last_7", "last_14", "last_30", "s_2022"]

permanent = ["Roster Pos","Forwards/Defensemen", "Opp", "Status", 'Pre-Season']
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


def extract_positions(row):
    return row.split("-")[-1].strip().split(",")

def clean_base(base):
    
    base["Forwards/Defensemen"] = base["Forwards/Defensemen"].str.replace("New Player Note", "")
    base["Forwards/Defensemen"] = base["Forwards/Defensemen"].str.replace("No new player Notes", "")
    base["Forwards/Defensemen"] = base["Forwards/Defensemen"].str.replace("Player Note", "")
    
    base.insert(1, "Player Pos", base["Forwards/Defensemen"])
    base["Player Pos"] = base["Player Pos"].map(extract_positions)
    return base



@st.cache(allow_output_mutation=True)
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
permanent.insert(2, "Test")
loading_state.text("Done")

stat_filter_columns = variable[:]
time_series_filter_columns = adjectives[:]
players_filter_columns = base['Forwards/Defensemen']
positions_filter_columns = ['C', 'LW', 'RW', 'D']

stats = st.multiselect(label='stats', options=stat_filter_columns)
options = st.multiselect(label='options', options=time_series_filter_columns)
players = st.multiselect(label='players', options=players_filter_columns)
positions = st.multiselect(label='positions', options=positions_filter_columns)
if not stats:
    stats = stat_filter_columns

if not options:
    options = time_series_filter_columns
    

table_render = base

if options:
    for o in options:
        table_render = table_render.join(tables[o][tables[o].columns.intersection(stats)], rsuffix="_"+ o)
    
    if players:
        table_render = table_render[table_render['Forwards/Defensemen'].isin(players)]

    if positions:
        table_render = table_render[table_render['Player Pos'].items().isin(positions)]

st.dataframe(table_render)


def rating_trend(base, tables):
    
    selection = st.selectbox(label="Choose player", options=players_filter_columns)
    s_idx = base.index[base['Forwards/Defensemen'] == selection]
    results = []
    for a in adjectives[1:]:
        rating = tables[a].loc[s_idx, 'Current'].values[0]
        results.append(rating)

    df_display = pd.DataFrame.from_dict({'period': reversed(adjectives[1:]), 'ratings':reversed(results)})
    fig = px.line(df_display,x='period', y='ratings', title=f"Rating Trend for {selection} (lower=better)")
    st.plotly_chart(fig)



    
graph_options = {"Yahoo Rating Trend": rating_trend}

graph_selection = st.selectbox(label="Select a graph", options=graph_options)

if graph_selection:
    graph_options[graph_selection](base, tables)

st.title("Depth Chart")

layout_count = [0.25,0.25,0.25,0.25]
layout_pos = {"LW": 0,"C": 1, "RW":2, "D":3}



layout = [
        # Parameters: element_identifier, x_pos, y_pos, width, height, [item properties...]
        dashboard.Item("LW", 0, 0, 1, 1, static=True, isDraggable=False, isResizable=False),
        dashboard.Item("C", 1, 0, 1, 1, static=True, isDraggable=False, isResizable=False),
        dashboard.Item("RW", 2, 0, 1, 1, static=True, isDraggable=False, isResizable=False),
        dashboard.Item("D", 3, 0, 1, 1, static=True, isDraggable=False, isResizable=False),
        # dashboard.Item(i="0", x=0, y=2, w=1, h=1)
    ]

for index, row in base.iterrows():
    ctr = layout_count[layout_pos[row["Player Pos"][0]]]
    layout_count[layout_pos[row["Player Pos"][0]]] +=1

    item = dashboard.Item(i=str(index), x=layout_pos[row["Player Pos"][0]], y=ctr, w=1, h=1, isDraggable=True, isResizable=True) #
    layout.append(item)
print(layout)

paper_sx = {"textAlign":"center", "line-height": "40px", 'height': "40px" }
with elements("dashboard"):
    with dashboard.Grid(layout, cols={"lg":4}, allowOverlap=False, rowHeight=40):
            mui.Paper("LW", key="LW", elevation=10, sx=paper_sx) 
            mui.Paper("C", key="C", elevation=10, sx=paper_sx)
            mui.Paper("RW", key="RW", elevation=10, sx=paper_sx)
            mui.Paper("D", key="D", elevation=10, sx=paper_sx)
            mui.Paper("0", key="0", elevation=0, sx=paper_sx)

            for index, row in base.iterrows():
                mui.Paper(row['Forwards/Defensemen'], key=str(index), elevation=0, sx=paper_sx)


# st.markdown("[![Foo](http://www.google.com.au/images/nav_logo7.png)](http://google.com.au/)") 

# txt = "View Project on GitHub"
# c1, _ , c2 = st.columns([1, 1, 10])
# with c1:
#     st.image("static/github-mark.png", use_column_width=True)
# with c2:
#     st.write(txt)
with elements("new_element"):
    mui.Button("View on GitHub", variant="outlined", href="https://github.com/bjtho/yhockeyexplorer",target="_blank", startIcon=mui.icon.GitHub(color='inherit'))
        # mui.icon.GitHub(color='inherit')
        # mui.Typography("View on GitHub")
    
        