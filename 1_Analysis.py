import streamlit as st
import polars as pl
import pandas as pd
import numpy as np
import datetime as dt
import plotly.express as px
import geopandas as gp


# from: https://youtu.be/lWxN-n6L7Zc
# StreamlitAPIException: set_page_config() can only be called once per app, and must be called as the first Streamlit command in your script.


############### Custom Functions ###############

# from: https://discuss.streamlit.io/t/how-to-add-extra-lines-space/2220/7
def v_spacer(height, sb=False) -> None:
    for _ in range(height):
        if sb:
            st.sidebar.write('\n')
        else:
            st.write('\n')

############### Custom Functions Ends ###############


st.set_page_config(page_title="Political Parties Crime Record Analysis",
                    layout='wide',
                    initial_sidebar_state="expanded")


############################## GET DATA ##############################
# @st.cache
# @st.cache_data
@st.cache_resource
def get_data():
    df = pl.scan_parquet('Elections_Data_Compiled.parquet')
    
    return df

df = get_data()

@st.cache_resource
def get_shape_data():
    final_shp_export = gp.read_file('shape_file_exported/final_shp_export.shp').rename(
                                                                            columns = {'Criminal_C':'Criminal_Case',
                                                                           'Total_Asse':'Total_Assets'})
    
    return final_shp_export

final_shp_export = get_shape_data()
############################## DATA DONE ##############################





############################## CREATING HEADER ##############################

header_left,header_mid,header_right = st.columns([1,8,1],gap = "small")

with header_mid:
    # https://docs.streamlit.io/library/get-started/create-an-app
    st.title("Political Parties Criminal Records Analysis")

############################## HEADER DONE ##############################





############################## FIRST FILTER STATE ##############################

with st.sidebar:

    st.write("This is Selection Control Panel")

    # State_List = df.lazy().select(pl.col('State')).unique().collect().to_series().to_list()
    # State_List = df.collect().to_pandas()["State"].unique().tolist()

    @st.cache_data
    def get_state_list():
        # return get_data().select('State').unique().collect().to_series().to_list()
        return df.select('State').unique().collect().to_series().to_list()
    
    State_List = get_state_list()
    State_index = State_List.index('Delhi')
    # st.write(State_index)

    State_Selected = st.selectbox(label="Select State",
                                  options = State_List,
                                  index=State_index)
    
    # Converting State_Selected to list 
    # State_Selected = [State_Selected]

    # State_Selected = st.multiselect(label="Select State",
    #                                 options = State_List,
    #                                 default = ["Delhi"], # Uttar Pradesh West Bengal  
    #                                 # default = State_List[-1],
    #                                 max_selections=1
    #                                    )
    
############################## FIRST FILTER STATE DONE ##############################





############################## SECOND FILTER YEAR ##############################

    @st.cache_data
    def get_year_list(State_Selected):
        
        return df.filter(pl.col('State') == State_Selected
                              ).select(pl.col('Year')
                                       ).unique().collect().to_series().sort().to_list()
    
    Year_List = get_year_list(State_Selected)

    Year_Selected = st.multiselect(label="Select Election Year (Latest by default)",
                                     options=Year_List,
                                     default=Year_List[-1])
    
############################## SECOND FILTER YEAR DONE ##############################
    




############################## SIDEBAR DISCAILMER ##############################
    # v_spacer(1)

    st.write("*Disclaimer:* - This app is for **educational** Purpose only and to demonstrate the use of **Python & Polars**  \n   \
             \n We do not guarantee for Authenticity of the data and would request you to do your own research.  \
             \n It uses very small portion of data from https://myneta.info/ and aggregates using **Polars Python** to handle **data processing** efficiently.   \n \
             \n Data used in this **Web App** is from https://myneta.info/ which is maintained by **ADR**. \
               \n Would request the viewers to visit https://myneta.info/ for more details and original content.")
############################## SIDEBAR DISCAILMER END ##############################





############################## FILTERED DATA ##############################

df_selected = df.filter((pl.col('State') == State_Selected) &
                    (pl.col('Year').is_in(Year_Selected))
                    )


final_shp_trimmed = final_shp_export[(final_shp_export.State == State_Selected) & (final_shp_export.Year.isin(Year_Selected))]
Top_constituency_df =  final_shp_trimmed[['AC_NAME','Criminal_Case']].nlargest(n = 1, columns='Criminal_Case')
Top_constituency_name = Top_constituency_df['AC_NAME'].item()
Top_constituency_crime = Top_constituency_df['Criminal_Case'].item()
############################## FILTERED DATA DONE ##############################    





############################## USEFUL AGGREGATIONS & LIST ##############################

cases_agg_2022 = df_selected.groupby(['Party']).agg(
    [
    (pl.col('Party').count().alias('candidates_count')),
    (pl.col('Criminal_Case').sum().alias('total_criminal_cases'))
    ]
).with_columns(
    (pl.col('total_criminal_cases') / pl.col('candidates_count') ).alias('avg_cases')
).sort(by = 'total_criminal_cases', descending = True)



Major_Parties = (
    cases_agg_2022
    .filter(pl.col('total_criminal_cases')>0)
    .sort('total_criminal_cases',descending = True)
    .head(6)
    .select(pl.col('Party'))
    .collect()
    .to_series()
    .to_list()
)


############################## USEFUL AGGREGATIONS & LIST DONE ##############################




# By Constituency Text
st.markdown("""---""")    

Const_1,Const_2,Const_3 = st.columns([1,8,1],gap = "large")

with Const_2:
    st.markdown("""
    <style>.big-font {
    font-size:10px !important;}
    </style>
    """, unsafe_allow_html=True)
    st.markdown(f'<p class="big-font">Criminal Cases by Constituency of {State_Selected}</p>', unsafe_allow_html=True)
    # st.markdown(f'<center><p class="big-font">{State_Selected}</p></center>', unsafe_allow_html=True)



############################## CONSTITUENCY PLOT ##############################

cons_map_1,cons_map_2 = st.columns([1,6], gap="small")

with cons_map_1:
    v_spacer(8)

    st.write(f"{Top_constituency_name} with total {Top_constituency_crime} Criminal Cases by all candidates is at the top position of constituencies.")

with cons_map_2:
    fig_choropleth_assembly = px.choropleth(
                                                    data_frame= final_shp_trimmed,
                                                    geojson=final_shp_trimmed.__geo_interface__,
                                                    locations=final_shp_trimmed.index.astype(str),
                                                    color_continuous_scale="magma",
                                                    # range_color = (0,12), 
                                                    color = "Criminal_Case",
                                                    hover_name='AC_NAME',
                                                    hover_data=["Criminal_Case", "Total_Assets"]
                                                    # hover_data = {'locations':False, # https://stackoverflow.com/questions/74614344/selecting-hover-on-plotly-choropleth-map
                                                    #               'Criminal_Case':True
                                                    #               }
                                                    # title=f'{Top_constituency} is the Top Constituency'
                                                    )

    fig_choropleth_assembly.update_geos(fitbounds="locations", visible=False
                                        ).update_layout(
                                    paper_bgcolor = 'rgba(0, 0, 0, 0)',
                                    geo=dict(bgcolor= 'rgba(0,0,0,0)'), 
                                    # hoverlabel = {'bgcolor': 'rgba(0,0,0,0)'},
                                    height = 580, width = 450
                                    )

    # fig_choropleth_assembly = px.choropleth_mapbox(
    #                                                 data_frame= final_shp_trimmed,
    #                                                 geojson=final_shp_trimmed.__geo_interface__,
    #                                                 locations=final_shp_trimmed.index.astype(str),
    #                                                 color="Criminal_Case",
    #                                                 color_continuous_scale="Viridis",
    #                                                 center=dict(lat=25.9644, lon=85.2722),
    #                                                 mapbox_style="open-street-map",
    #                                                 zoom=6,
    #                                                 hover_name='AC_NAME')

    st.plotly_chart(fig_choropleth_assembly,use_container_width=True)


############################### Exapnder for Constituency Bar plot ###############################
# with st.expander("See explanation"):

Const_option_1,Const_option_2 = st.columns([7,1],gap = "small")

with Const_option_2:
    input_constituency = st.radio("Select All Parties?", ["No","Yes"], horizontal=True)

with Const_option_1:

    if input_constituency == "Yes":
        fig_const_crime_sum = px.bar(
                                    df_selected.groupby(['Constituency','Party']
                                        ).agg(pl.col('Criminal_Case').sum()
                                        ).sort(by='Criminal_Case',descending=True
                                        ).collect(
                                        ).to_pandas(),
                                    orientation='v',
                                    barmode = 'stack', 
                                    x='Constituency',y='Criminal_Case', color="Party",
                                    hover_name="Constituency",
                                    labels={
                                            "Total_Assets": "Total Assets (in Rs.)",
                                            "Party": "Political Parties"
                                        },
                                    
                                    title=f'<b>Constituencies with highest Criminal Cases Candidates from {State_Selected} in {Year_Selected} Elections</b>')

    else:
        fig_const_crime_sum = px.bar(
                                    df_selected.filter(
                                        pl.col('Party').is_in(Major_Parties)).groupby(['Constituency','Party']
                                        ).agg(pl.col('Criminal_Case').sum()
                                        ).sort(by='Criminal_Case',descending=True
                                        ).collect(
                                        ).to_pandas()
                                        
                                        ,
                                    orientation='v',
                                    barmode = 'stack', 
                                    x='Constituency',y='Criminal_Case', color="Party",
                                    hover_name="Constituency", 
                                    
                                    labels={
                                            "Total_Assets": "Total Assets (in Rs.)",
                                            "Party": "Political Parties"
                                        },
                                    
                                    title=f'<b>Constituencies with highest Criminal Cases Candidates of Top 6 Parties from {State_Selected[0]} in {Year_Selected[0]} Elections</b>')
                                    # title= " ".join('Constituencies with highest Criminal Cases Candidates of Top 6 Parties from', State_Selected[0], 'in', Year_Selected[0], 'Elections'))



    fig_const_crime_sum.update_xaxes(autorange="reversed")
    fig_const_crime_sum.update_layout(title_font_size=18, height = 600, 
                                        # showlegend=False
                                        )

    st.plotly_chart(fig_const_crime_sum,use_container_width=True)


############################## CONSTITUENCY PLOT DONE ##############################



parties_1,parties_2,parties_3 = st.columns([1,8,1],gap = "small")

with parties_2:
    st.markdown("""<style>.big-font {
    font-size:38px !important;}
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<p class="big-font">Criminal Cases by Political Parties</p>', unsafe_allow_html=True)




############################## FIRST PLOT ##############################
plt_box_1,plt_box_2 = st.columns([5,2],gap = "small")

highest_criminal_parties = df_selected.groupby(['Party']
                                ).agg(pl.col('Criminal_Case').sum()
                                ).sort(by='Criminal_Case',descending=True)

highest_criminal_party = highest_criminal_parties.select(pl.col('Party')).head(1).collect().to_series().to_list()
# highest_criminal_party6 = highest_criminal_parties.select(pl.col('Party')).head(6).to_series().to_list()

with plt_box_1:

    fig_party_crime_sum = px.bar(highest_criminal_parties.head(18).collect().to_pandas(),
                                orientation='h',
                                x='Criminal_Case',y='Party', color="Party",
                                hover_name='Party',
                                labels={
                                        "Criminal_Case": "Total Criminal Cases",
                                        "Party": "Political Parties"
                                    },
                            
                            title=f'<b>Top 18 Political Parties with Highest Total Criminal Records from {State_Selected} in {Year_Selected} Elections</b>')

    # fig_party_crime_sum.update_yaxes(autorange="reversed")
    fig_party_crime_sum.update_layout(title_font_size=18, height = 500, 
                                        showlegend=False
                                        )
    fig_party_crime_sum.add_annotation(
                                        showarrow=False,
                                        text='Data Source: https://myneta.info/',
                                        xanchor='right',
                                        x=2,
                                        xshift=575,
                                        yanchor='bottom',
                                        y=0.01 #,
                                        # font=dict(
                                        #     family="Courier New, monospace",
                                        #     size=22,
                                        #     color="#0000FF"
                                    )

    st.plotly_chart(fig_party_crime_sum,use_container_width=True)


with plt_box_2:
    v_spacer(8)

    st.write(f"*This Plot* demostrates the total number of criminal cases on the candidates of each party from the  \
            respective state of {State_Selected} in election year {Year_Selected} with maximum number of criminal cases at the top and lowest  \
            at the bottom. It considers top 18 Political Parties only.")

############################## FIRST PLOT DONE ##############################




############################## BOX PLOT ##############################

boxplt_1,boxplt_2 = st.columns([2,5],gap = "small")

with boxplt_2:
    fig_party_crime_box = px.box(df_selected.filter(
            (pl.col('Party').is_in(Major_Parties)) # highest_criminal_parties.select(pl.col('Party')).head(6).to_series().to_list()
                                    ).collect().to_pandas(),
            x = 'Party',
            y = 'Criminal_Case',
            color= 'Party',
            hover_name='Party',
            points = 'all', # will display dots next to the boxes 
            labels={
                        "Criminal_Case": "Count of Criminal Cases on Individual",
                        "Party": "Political Parties"
                                        },
                                
                                title=f'<b>Top 6 Political Parties with Individual Criminal Record points & boxplot from<br> {State_Selected} in {Year_Selected} Elections</b>'
        ).update_layout(
        title_font_size=18, height = 450, 
        # xaxis=dict(autorange="reversed")
        # plot_bgcolor = 'white'
        )

    st.plotly_chart(fig_party_crime_box,use_container_width=True)

with boxplt_1:
    v_spacer(9)

    st.write(f"*This Plot* shows each Individual Candidate as a point with respect to number of criminal cases against it for each Political Party from the  \
            respective state of {State_Selected} in election year {Year_Selected}. It considers top 6 Political Parties only.")

############################## BOX PLOT DONE ##############################




############################## FACET PLOT DONE ##############################

plt3_box_1,plt3_box_2 = st.columns([6,1],gap = "small")

with plt3_box_2:
    v_spacer(6)

    st.write(f"*This Plot* shows the count of candidates with highest number of criminal cases in their Party in  \
            respect to state of {State_Selected} in election year {Year_Selected} with maximum number of criminal cases on an indiviual at the top and lowest  \
            at the bottom. It considers top 6 Political Parties only and Individuals with  greater than 3 Criminal Cases.")
    

with plt3_box_1:
    fig_cases_count_party_facet = px.bar(df_selected.filter(pl.col('Party').is_in(Major_Parties) & 
                                        (pl.col('Criminal_Case') > 3)).sort(
                                        by='Criminal_Case', descending=True
                                        ).groupby(
                                        ['Party','Criminal_Case'], maintain_order=True).count().collect().to_pandas(),
                                        orientation='h',
                                        x='count',y='Criminal_Case', color="Party",
                                        hover_name='Party',
                                        facet_col="Party", facet_col_wrap=3,
                                        labels={
                                                "Criminal_Case": "Criminal Cases on a Candidate",
                                                "count": "Count of candidates with Cases #"
                                            },
                                        
                                        title=f'<b>Top 6 Parties with Highest number of Criminal Record Candidate in {State_Selected} {Year_Selected} Elections</b>'
                            )

    fig_cases_count_party_facet.update_layout(title_font_size=18, height = 600, 
                                        showlegend=False
                                        )

    st.plotly_chart(fig_cases_count_party_facet,use_container_width=True)

############################## FACET PLOT DONE ##############################


# Add a Explantion of below charts
v_spacer(2)
st.write("It is also important to see not just the 'Total Criminal Records' but also the 'Average Criminal Cases per Candidate'  \
          as some parties with small number of candidates may have individuals with high number of Criminal Cases too. Below  \
         is the breakdown of such 3 plots with Total Candidates, Total Criminal Cases, Average Criminal Cases  \
        per candidate for Political Parties")

############################## 3 PLOTS ##############################

fig_party_cand_count = px.bar(cases_agg_2022.sort(by='candidates_count',descending=True
                                ).head(18).collect().to_pandas(),
                                orientation='h',
                                x='candidates_count',y='Party', color="Party",
                                hover_name='Party',
                                labels={
                                        "candidates_count": "Total Candidates",
                                        "Party": "Political Parties"
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
                                ).head(18).collect().to_pandas(),
                                orientation='h',
                                x='avg_cases',y='Party', color="Party",
                                hover_name='Party',
                                labels={
                                        "avg_cases": "Average Case (Cases/Candidates) ",
                                        "Party": "Political Parties"
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

############################## 3 PLOTS DONE ##############################



# st.markdown("""---""")    
st.divider()

Asset_mark_1,Asset_mark_2,Asset_mark_3 = st.columns([1,8,1],gap = "small")

with Asset_mark_2:
    st.markdown("""<style>.big-font {
    font-size:38px !important;}
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<p class="big-font">Sum of Total Asset of Candidates from each Party</p>', unsafe_allow_html=True)




############################## ASSET PLOTS ##############################

asset_1,asset_2 = st.columns([2,1],gap = "small")

with asset_1:    
    # fig_party_asset_sum = px.bar(df_selected.groupby(['Party']
    #                             ).agg(pl.col('Total_Assets').sum()
    #                             ).sort(by='Total_Assets',descending=True
    #                             ).head(18).collect().to_pandas(),
    #                             orientation='h',
    #                             x='Total_Assets',y='Party', color="Party",
    #                             hover_name='Party',
    #                             labels={
    #                                     "Total_Assets": "Total Assets (in Rs.)",
    #                                     "Party": "Political Parties"
    #                                 },
                            
    #                         title=f'<b>Top 18 Political Parties with Highest Total Sum of Assets of candidates <br>from {State_Selected} in {Year_Selected} Elections</b>')

# converting above code to facet year
    fig_party_asset_sum = px.bar(df.filter(pl.col('State') == State_Selected).groupby(['Party','Year']
                                    ).agg(pl.col('Total_Assets').sum()/10**7
                                    ).sort(by='Total_Assets',descending=True
                                    ).head(18).collect().to_pandas(),
                                    orientation='h',
                                    x='Total_Assets',y='Party', color="Party",
                                    facet_col="Year", facet_col_wrap=2,
                                    hover_name='Party',
                                    labels={
                                            "Total_Assets": "Total Assets (in Crore Rs.)",
                                            "Party": "Political Parties"
                                        },
                                
                                title=f'<b>Top 18 Political Parties with Highest Total Sum of Assets of candidates <br>from {State_Selected} in Elections</b>')

                                        


    # fig_party_crime_sum.update_yaxes(autorange="reversed")
    fig_party_asset_sum.update_layout(title_font_size=18, height = 500, 
                                        showlegend=False
                                        )
    # fig_party_asset_sum.update_traces(hovertemplate= 'Rs. %{x:.2f}')

    # fig_party_asset_sum.add_annotation(
    #                                     showarrow=False,
    #                                     text='Data Source: https://myneta.info/',
    #                                     xanchor='right',
    #                                     x=2,
    #                                     xshift=575,
    #                                     yanchor='bottom',
    #                                     y=0.01 #,
    #                                     # font=dict(
    #                                     #     family="Courier New, monospace",
    #                                     #     size=22,
    #                                     #     color="#0000FF"
    #                                 )

    st.plotly_chart(fig_party_asset_sum,use_container_width=True)



with asset_2:
    fig_party_asset_buble = px.scatter(df_selected.filter(
                                        (pl.col('Party').is_in(Major_Parties)) 
                                        ).collect().to_pandas(),
                                        x = 'Party',
                                        y = 'Total_Assets',
                                        hover_name='Party',
                                        color = 'Party', # will display dots next to the boxes 
                                        labels={
                                                    "Total_Assets": "Total Assets (in Rs) of Candidate",
                                                    "Party": "Political Parties"
                                                                    },
                                                            
                                title=f'<b>Top 6 Political Parties with Individual <br>Total Asset Record points from {State_Selected} <br>in {Year_Selected} Elections</b>'
        ).update_layout(
        title_font_size=18, height = 500,
        showlegend = False
        )

    st.plotly_chart(fig_party_asset_buble,use_container_width=True)

############################## ASSET PLOTS DONE ##############################




############################## ASSET CRIME BUBBLE PLOT ##############################

fig_crime_asset_buble = px.scatter(df_selected.filter(pl.col('Party').is_in(Major_Parties)).collect().to_pandas(),
                                    x='Criminal_Case',y='Total_Assets', color="Party",
                                    hover_name="Party",
                                    # size = 'Total_Assets',
                                    labels={
                                            "Criminal_Case": "Total Criminal Cases",
                                            "Party": "Political Parties",
                                            "Total_Assets": "Total Assets (in Rs) of Candidate"
                                        },
                        
                        title=f'<b>Total Asset of Individual Vs Criminal Cases of Top 6 Political Parties from {State_Selected} in {Year_Selected} Elections</b>')

# fig_party_crime_sum.update_yaxes(autorange="reversed")
fig_crime_asset_buble.update_layout(title_font_size=18, height = 500, 
                                    # showlegend=False
                                    )

st.plotly_chart(fig_crime_asset_buble,use_container_width=True)

############################## ASSET CRIME BUBBLE PLOT DONE ##############################




# By Education Text
st.markdown("""---""")    

Const_1,Const_2,Const_3 = st.columns([1,5,1],gap = "small")

with Const_2:
    st.markdown("""<style>.big-font {
    font-size:38px !important;}
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<p class="big-font">Criminal Cases by Education</p>', unsafe_allow_html=True)



############################## EDUCATION BUBBLE PLOT ##############################

# fig__edu_crime_buble = px.scatter(df_selected.filter((pl.col('Party').is_in(Major_Parties)) &
#                                                      (pl.col('Criminal_Case') > 0)).collect().to_pandas(),
#                                     x='Education',y='Criminal_Case', color="Party", size = "Total_Assets",
#                                     hover_name="Party", opacity=0.5,
#                                     labels={
#                                             "Criminal_Case": "Total Criminal Cases",
#                                             "Party": "Political Parties",
#                                             "Total_Assets": "Total Assets (in Rs) of Candidate"
#                                         },
                        
#                         title=f'<b>Criminal Cases of Top 6 Political Parties by Education(Size wrt to Total Assets) from {State_Selected} in {Year_Selected} Elections</b>')


# fig__edu_crime_buble.update_layout(title_font_size=18, height = 500
#                                     # showlegend=False
#                                     )

edu_bub_1,edu_bub_2 = st.columns([7,1],gap = "small")

with edu_bub_2:
    edu_option = st.radio("Facet by Education ?",options=['No','Yes'])

with edu_bub_1:
    if edu_option == "No":

        fig__edu_crime_buble = px.scatter(df_selected.filter((pl.col('Party').is_in(Major_Parties)) &
                                                            (pl.col('Criminal_Case') > 0)).collect().to_pandas(),
                                            x = 'Criminal_Case', y = 'Total_Assets', color='Education', size='Criminal_Case',
                                            facet_col='Party', facet_col_wrap=3, opacity=0.6,
                                            labels={
                                                    "Criminal_Case": "Criminal Cases",
                                                    "Party": "Political Parties",
                                                    "Total_Assets": "Total Assets (in Rs)"
                                                },
                                            # from: https://plotly.com/python/facet-plots/?_gl=1*queipu*_ga*MTU0Nzk1NDk2NC4xNjgyMTYyMDYz*_ga_6G7EE0JNSC*MTY4MjY3NjAzOC4yOC4wLjE2ODI2NzYwNDUuMC4wLjA.#controlling-facet-ordering
                                            category_orders={"Education": ["Doctorate","Post Graduate", "Graduate", "Graduate Professional", 
                                                                        "12th Pass","10th Pass","8th Pass","5th Pass","Others","Literate"
                                                                        "Illiterate","Not Given"]},
                                
                                title=f'<b>Criminal Cases of Top 6 Political Parties by Education(Size wrt to Criminal Cases) from {State_Selected} in {Year_Selected} Elections</b>'
                                )


        fig__edu_crime_buble.update_layout(title_font_size=18, height = 600
                                            # showlegend=False
                                            # plot_bgcolor = 'rgba(0, 0, 0, 0)',
                                            # paper_bgcolor = 'rgba(0, 0, 0, 0)'
                                            )

    if edu_option == "Yes":

        fig__edu_crime_buble = px.scatter(df_selected.filter((pl.col('Party').is_in(Major_Parties)) &
                                                            (pl.col('Criminal_Case') > 0)).collect().to_pandas(),
                                            x = 'Criminal_Case', y = 'Total_Assets', color='Party', size='Criminal_Case',
                                            facet_col='Education', facet_col_wrap=3, opacity=0.6,
                                            labels={
                                                    "Criminal_Case": "Criminal Cases",
                                                    "Party": "Political Parties",
                                                    "Total_Assets": "Total Assets (in Rs)"
                                                },
                                            # from: https://plotly.com/python/facet-plots/?_gl=1*queipu*_ga*MTU0Nzk1NDk2NC4xNjgyMTYyMDYz*_ga_6G7EE0JNSC*MTY4MjY3NjAzOC4yOC4wLjE2ODI2NzYwNDUuMC4wLjA.#controlling-facet-ordering
                                            category_orders={"Education": ["Doctorate","Post Graduate", "Graduate", "Graduate Professional", 
                                                                        "12th Pass","10th Pass","8th Pass","5th Pass","Others","Literate"
                                                                        "Illiterate","Not Given"]},
                                
                                title=f'<b>Criminal Cases of Top 6 Political Parties by Education(Size wrt to Criminal Cases) from {State_Selected} in {Year_Selected} Elections</b>'
                                )


        fig__edu_crime_buble.update_layout(title_font_size=18, height = 700
                                            # showlegend=False
                                            # plot_bgcolor = 'rgba(0, 0, 0, 0)',
                                            # paper_bgcolor = 'rgba(0, 0, 0, 0)'
                                            )

    st.plotly_chart(fig__edu_crime_buble,use_container_width=True)




############################## EDUCATION BUBBLE PLOT DONE ##############################




############################## DISCALIMER ##############################

st.markdown("""---""")

v_spacer(1)

_1,box_left,_2 = st.columns([1,4,1],gap = "small")

with box_left:
    st.write("*Disclaimer:* - This app is for **educational** Purpose only and to demonstrate the use of **Python & Polars**  \n   \
             \n We do not guarantee for Authenticity of the data and would request you to do your own research.  \
             \n It uses very small portion of data from https://myneta.info/ and aggregates using **Polars Python** to handle **data processing** efficiently.   \n \
             \n Data used in this **Web App** is from https://myneta.info/ which is maintained by **ADR**. \
               \n Would request the viewers to visit https://myneta.info/ for more details and original content.")
    
############################## DISCALIMER DONE ##############################