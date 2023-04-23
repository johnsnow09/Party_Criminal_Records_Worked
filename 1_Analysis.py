import streamlit as st
import polars as pl
import pandas as pd
import numpy as np
import datetime as dt
import plotly.express as px


# from: https://youtu.be/lWxN-n6L7Zc
# StreamlitAPIException: set_page_config() can only be called once per app, and must be called as the first Streamlit command in your script.


st.set_page_config(page_title="Election Party Candidate Analysis",
                    layout='wide',
                    initial_sidebar_state="expanded")


############################## GET DATA ##############################
# @st.cache
# @st.cache_data
def get_data():
    df = pl.scan_parquet('Elections_Data_Compiled.parquet')
    
    return df

df = get_data()
############################## DATA DONE ##############################





############################## CREATING HEADER ##############################

header_left,header_mid,header_right = st.columns([1,6,1],gap = "large")

with header_mid:
    # https://docs.streamlit.io/library/get-started/create-an-app
    st.title("Party Criminal Records Analysis")

############################## HEADER DONE ##############################





############################## FIRST FILTER STATE ##############################

with st.sidebar:

    st.write("This is Selection Control Panel")

    # State_List = df.lazy().select(pl.col('State')).unique().collect().to_series().to_list()
    State_List = df.collect().to_pandas()["State"].unique().tolist()

    # State_Selected = st.selectbox(label="Select State",
    #                               options = State_List)

    State_Selected = st.multiselect(label="Select State",
                                    options = State_List,
                                    default = ["Uttar Pradesh"], # Delhi West Bengal  
                                    # default = State_List[-1],
                                    max_selections=1
                                       )
    
############################## FIRST FILTER STATE DONE ##############################





############################## SECOND FILTER YEAR ##############################

    Year_List = df.lazy().filter(pl.col('State').is_in(State_Selected)).select(
                                                pl.col('Year')).unique().collect().to_series().sort().to_list()

    Year_Selected = st.multiselect(label="Select Election Year",
                                     options=Year_List,
                                     default=Year_List[-1])
    
############################## SECOND FILTER YEAR DONE ##############################
    




############################## FILTERED DATA ##############################

df_selected = df.lazy().filter(pl.col('State').is_in(State_Selected) &
                    (pl.col('Year').is_in(Year_Selected))
                    ).collect()
    
############################## FILTERED DATA DONE ##############################    





############################## FIRST PLOT ##############################

fig_party_crime_sum = px.bar(df_selected.groupby(['Party']
                            ).agg(pl.col('Criminal_Case').sum()
                            ).sort(by='Criminal_Case',descending=True
                            ).head(18).to_pandas(),
                            orientation='h',
                            x='Criminal_Case',y='Party', color="Party",
                            labels={
                                    "Criminal_Case": "Total Criminal Cases",
                                    "Party": "Election Parties"
                                },
                        
                        title=f'<b>{State_Selected} - Top 18 Election Parties with Total Criminal Records in {Year_Selected} Elections</b>')

# fig_party_crime_sum.update_yaxes(autorange="reversed")
fig_party_crime_sum.update_layout(title_font_size=26, height = 600, 
                                    showlegend=False
                                    )
fig_party_crime_sum.add_annotation(
                                    showarrow=False,
                                    text='Data Source: https://myneta.info/',
                                    xanchor='right',
                                    x=2,
                                    xshift=675,
                                    yanchor='bottom',
                                    y=0.01 #,
                                    # font=dict(
                                    #     family="Courier New, monospace",
                                    #     size=22,
                                    #     color="#0000FF"
                                )

st.plotly_chart(fig_party_crime_sum,use_container_width=True)

############################## FIRST PLOT DONE ##############################





############################## SECOND PLOT ##############################

cases_agg_2022 = df_selected.groupby(['Party']).agg(
    [
    (pl.col('Party').count().alias('candidates_count')),
    (pl.col('Criminal_Case').sum().alias('total_criminal_cases'))
    ]
).with_columns(
    (pl.col('total_criminal_cases') / pl.col('candidates_count') ).alias('avg_cases')
).sort(by = 'total_criminal_cases', descending = True)

fig_party_cand_count = px.bar(cases_agg_2022.sort(by='candidates_count',descending=True
                                ).head(18).to_pandas(),
                                orientation='h',
                                x='candidates_count',y='Party', color="Party",
                                labels={
                                        "candidates_count": "Total Candidates",
                                        "Party": "Election Parties"
                                    },
                            
                            title=f'<b>Highest Total Candidates in {Year_Selected} Elections</b>'
                            )
fig_party_cand_count.update_layout(title_font_size=16, height = 600, 
                                    showlegend=False
                                    )

fig_party_crime_sum2 = fig_party_crime_sum

fig_party_crime_sum2.update_layout(title_font_size=16, height = 600, 
                                    showlegend=False,
                                    title_text = f'<b>Highest Total Criminal Cases in {Year_Selected} Elections</b>'
                                    )

fig_party_avg_cases = px.bar(cases_agg_2022.sort(by='avg_cases',descending=True
                                ).head(18).to_pandas(),
                                orientation='h',
                                x='avg_cases',y='Party', color="Party",
                                labels={
                                        "avg_cases": "Average Case (Cases/Candidates) ",
                                        "Party": "Election Parties"
                                    },
                            
                            title=f'<b>Highest Average Criminal Cases in {Year_Selected} Elections</b>'
                            )
fig_party_avg_cases.update_layout(title_font_size=16, height = 600, 
                                    showlegend=False
                                    )

plt1_left,plt1_mid,plt1_right = st.columns([1,1,1],gap = "small")

with plt1_left:
    st.plotly_chart(fig_party_cand_count,use_container_width=True)

with plt1_mid:
    st.plotly_chart(fig_party_crime_sum2,use_container_width=True)

with plt1_right:
    st.plotly_chart(fig_party_avg_cases,use_container_width=True)


Major_Parties = (
    cases_agg_2022
    .filter(pl.col('total_criminal_cases')>0)
    # .groupby('Party')
    # .count()
    # .sort('count',descending = True)
    .sort('total_criminal_cases',descending = True)
    .head(6)
    .select(pl.col('Party'))
    .to_series()
    .to_list()
)

fig_cases_count_party_facet = px.bar(df_selected.filter(pl.col('Party').is_in(Major_Parties) & 
                                    (pl.col('Criminal_Case') > 3)).sort(
                                    by='Criminal_Case', descending=True
                                    ).groupby(
                                    ['Party','Criminal_Case'], maintain_order=True).count().to_pandas(),
                                    orientation='h',
                                    x='count',y='Criminal_Case', facet_col="Party", facet_col_wrap=3,
                                    labels={
                                            "Criminal_Case": "Criminal Cases on a Candidate",
                                            "count": "Count of candidates with Cases #"
                                        },
                                    
                                    title=f'<b>{State_Selected} - Top 6 Parties with Highest number of Criminal Records in {Year_Selected} Elections</b>'
                        )

fig_cases_count_party_facet.update_layout(title_font_size=16, height = 600, 
                                    showlegend=False
                                    )

st.plotly_chart(fig_cases_count_party_facet,use_container_width=True)