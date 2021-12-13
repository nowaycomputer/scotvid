import pandas as pd
from plotly.subplots import make_subplots
import numpy as np
import streamlit as st


RANGE=120
HOSPITAL_OFFSET=7
ICU_OFFSET=14
FONT_SIZE=12
DEATH_DELAY=3
TEMPLATE='seaborn'

st.set_page_config(layout="wide")

def get_remote_data():
    df_cases=pd.read_csv('https://www.opendata.nhs.scot/dataset/b318bddf-a4dc-4262-971f-0ba329e09b87/resource/287fc645-4352-4477-9c8c-55bc054b7e76/download/daily_cuml_scot_20211210.csv', index_col='Date',parse_dates=True)
    df_hospital=pd.read_csv('https://www.opendata.nhs.scot/dataset/b318bddf-a4dc-4262-971f-0ba329e09b87/resource/2dd8534b-0a6f-4744-9253-9565d62f96c2/download/trend_hb_20211210.csv', index_col='Date',parse_dates=True)

    df_cases.to_csv('data/df_cases.csv')
    df_hospital.to_csv('data/df_hospital.csv')

    return df_cases, df_hospital

def get_local_data():
    df_cases=pd.read_csv('data/df_cases.csv', index_col='Date',parse_dates=True)
    df_hospital=pd.read_csv('data/df_hospital.csv', index_col='Date',parse_dates=True)

    return df_cases, df_hospital

@st.cache(ttl=3600,suppress_st_warning=True, show_spinner=False)
def get_data():
    try:
        df_cases, df_hospital = get_remote_data()
        return df_cases, df_hospital
    except:
        df_cases, df_hospital = get_local_data()
        return df_cases, df_hospital


# @st.cache(suppress_st_warning=True, show_spinner=False)
def make_plots(location='Scotland'):

    df_cases, df_hospital = get_data()
    df_hospital=df_hospital[df_hospital['HBName']==location]
    
    st.title('Scotland Covid Update')
    st.write('(Data up to '+df_cases.index[-1].strftime("%d/%m/%Y")+")")
    
    st.subheader('National Data')
    specs=[[{"secondary_y": False}, {"secondary_y": False},{"secondary_y": False}], 
                           [{"secondary_y": False}, {"secondary_y": False},{"secondary_y": False}]
                           ]

    fig = make_subplots(rows=2,cols=3,specs=specs, subplot_titles=['Cases','Positive Test Rate','Hospitalisations','Hospitalisation Rate', 'ICU Rate', 'Deaths'],vertical_spacing = 0.15,horizontal_spacing = 0.1)

    #
    # Cases
    #
    fig.add_scatter(x=df_cases.iloc[-RANGE:-1].index, y=df_cases['DailyCases'].iloc[-RANGE:-1], mode='lines',name='Cases',line_color='blue',opacity=0.25,row=1,col=1)
    fig.add_scatter(x=df_cases.iloc[-RANGE:-1].rolling(window=7).mean().index, y=df_cases['DailyCases'].iloc[-RANGE:-1].rolling(window=7).mean(), mode='lines',name='Cases (Ave)',line_color='blue',line_width=3,row=1,col=1)

    #
    # Pos Rate
    #

    fig.add_scatter(x=df_hospital.iloc[-RANGE:-1].index, y=df_hospital['PositivePercentage'].iloc[-RANGE:-1], mode='lines',name='Pos Rate (Ave)',line_color='green',opacity=0.25,row=1,col=2)
    fig.add_scatter(x=df_hospital.iloc[-RANGE:-1].rolling(window=7).mean().index, y=df_hospital['PositivePercentage'].iloc[-RANGE:-1].rolling(window=7).mean(), mode='lines',name='Pos Rate (Ave)',line_color='green',line_width=3,row=1,col=2)

    #
    # Hospital Admissions
    #
    fig.add_scatter(x=df_hospital.iloc[-RANGE:-1].index, y=df_hospital['HospitalAdmissions'].iloc[-RANGE:-1], mode='lines',name='Admissions',line_color='red',opacity=0.25,row=1,col=3)
    fig.add_scatter(x=df_hospital.iloc[-RANGE:-1].rolling(window=7).mean().index, y=df_hospital['HospitalAdmissions'].iloc[-RANGE:-1].rolling(window=7).mean(), mode='lines',name='Admissions (Ave)',line_color='red',line_width=3,row=1,col=3)

    #
    # Hosp Rate
    #

    fig.add_scatter(x=df_hospital.iloc[-RANGE:-1].index, y=((df_hospital['HospitalAdmissions'].iloc[-RANGE:-1]/df_cases['DailyCases'].iloc[-RANGE:-1].shift(HOSPITAL_OFFSET))*100), mode='lines',name='Hosp. Rate',line_color='purple',opacity=0.25,row=2,col=1)
    fig.add_scatter(x=df_hospital.iloc[-RANGE:-1].index, y=((df_hospital['HospitalAdmissions'].iloc[-RANGE:-1]/df_cases['DailyCases'].iloc[-RANGE:-1].shift(HOSPITAL_OFFSET))*100).rolling(window=7).mean(), mode='lines',name='Hosp. Rate (Ave)',line_color='purple',line_width=3,row=2,col=1)

    #
    # ICU Rate
    #

    fig.add_scatter(x=df_hospital['ICUAdmissions'].iloc[-RANGE:-1].index, y=((df_hospital['ICUAdmissions'].iloc[-RANGE:-1]/df_cases['DailyCases'].iloc[-RANGE:-1].shift(ICU_OFFSET))*100), mode='lines',name='ICU Rate',line_color='brown',opacity=0.25,row=2,col=2)
    fig.add_scatter(x=df_hospital['ICUAdmissions'].iloc[-RANGE:-1].index, y=((df_hospital['ICUAdmissions'].iloc[-RANGE:-1]/df_cases['DailyCases'].iloc[-RANGE:-1].shift(ICU_OFFSET))*100).rolling(window=7).mean(), mode='lines',name='ICU Rate (Ave)',line_color='brown',line_width=3,row=2,col=2)

    #
    # Deaths
    #

    fig.add_scatter(x=df_hospital['DailyDeaths'].iloc[-RANGE:-DEATH_DELAY].index, y=df_hospital['DailyDeaths'].iloc[-RANGE:-DEATH_DELAY], mode='lines',name='Deaths',line_color='black',opacity=0.25,row=2,col=3)
    fig.add_scatter(x=df_hospital['DailyDeaths'].iloc[-RANGE:-DEATH_DELAY].index, y=df_hospital['DailyDeaths'].iloc[-RANGE:-DEATH_DELAY].rolling(window=7).mean(), mode='lines',name='Deaths (Ave)',line_color='black',line_width=3,row=2,col=3)

    fig['layout']['yaxis']['title']='Cases/Day'
    fig['layout']['yaxis2']['title']='Positive Test Rate (%)'
    fig['layout']['yaxis3']['title']='Admissions/Day'
    fig['layout']['yaxis4']['title']='Hospitalisation Rate (%)'
    fig['layout']['yaxis5']['title']='ICU Rate (%)'
    fig['layout']['yaxis6']['title']='Deaths'

    fig.update_layout(height=600, width=1400,   margin=dict(l=60, r=60, t=60, b=60))
    fig.update_layout(showlegend=False)
    fig.update_xaxes(range = [df_cases.iloc[-RANGE:-1].index[0], (df_cases.iloc[-RANGE:-1].index[-1].date()+pd.Timedelta(days=7))])

    # fig.layout.template = TEMPLATE
    # fig.show()

    st.plotly_chart(fig)
    data=pd.merge(df_hospital, df_cases, left_index=True, right_index=True)
    data.to_csv('data/merged_data.csv')
    return data

def get_remote_city_data():
    df_city=pd.read_csv('https://www.opendata.nhs.scot/dataset/b318bddf-a4dc-4262-971f-0ba329e09b87/resource/427f9a25-db22-4014-a3bc-893b68243055/download/trend_ca_20211213.csv', index_col='Date',parse_dates=True)
    return df_city

def get_local_city_data():
    df_city=pd.read_csv('data/df_city.csv', index_col='Date',parse_dates=True)

@st.cache(ttl=3600,suppress_st_warning=True, show_spinner=False)
def get_city_data():
    try:
        city_data = get_remote_city_data()
        return city_data
    except:
        city_data = get_local_city_data()
        return city_data

with st.spinner('Grabbing latest data...'):
    data=make_plots()
    city_data=get_city_data()
    st.subheader('Local Data')
    city_option = st.selectbox('Local Cases',(sorted(city_data['CAName'].unique().tolist())),index=14)
    
    fig_city = make_subplots(rows=2,cols=1,subplot_titles=['Cases per Day in '+city_option,'Positive Test Rate in '+city_option])
    fig_city.add_scatter(x=city_data[city_data['CAName']==city_option]['DailyPositive'].iloc[-RANGE:-1].index, y=city_data[city_data['CAName']==city_option].iloc[-RANGE:-1]['DailyPositive'], mode='lines',name='Cases',line_color='blue',opacity=0.25,row=1,col=1)
    fig_city.add_scatter(x=city_data[city_data['CAName']==city_option]['DailyPositive'].iloc[-RANGE:-1].rolling(window=7).mean().index, y=city_data[city_data['CAName']==city_option].iloc[-RANGE:-1]['DailyPositive'].rolling(window=7).mean(), mode='lines',name='Cases (Ave)',line_color='blue',line_width=3,row=1,col=1)
    
    fig_city.add_scatter(x=city_data[city_data['CAName']==city_option]['PositivePercentage'].iloc[-RANGE:-1].index, y=city_data[city_data['CAName']==city_option].iloc[-RANGE:-1]['PositivePercentage'], mode='lines',name='Pos Rate',line_color='red',opacity=0.25,row=2,col=1)
    fig_city.add_scatter(x=city_data[city_data['CAName']==city_option]['PositivePercentage'].iloc[-RANGE:-1].rolling(window=7).mean().index, y=city_data[city_data['CAName']==city_option].iloc[-RANGE:-1]['PositivePercentage'].rolling(window=7).mean(), mode='lines',name='Pos Rate (Ave)',line_color='red',line_width=3,row=2,col=1)


    fig_city.update_layout(showlegend=False)
    fig_city.update_layout(height=600, width=1400,   margin=dict(l=60, r=60, t=60, b=60))
    fig_city.update_xaxes(range = [city_data[city_data['CAName']==city_option].iloc[-RANGE:-1].index[0], (city_data[city_data['CAName']==city_option].iloc[-RANGE:-1].index[-1].date()+pd.Timedelta(days=7))])

    fig_city['layout']['yaxis']['title']='Cases/Day'
    fig_city['layout']['yaxis2']['title']='Positive Test Rate (%)'

    st.plotly_chart(fig_city)

    # st.header('TLDR')
    # st.write("""
    # -   Cases: 
    # -   Positive Test Rate:
    # -   Hospital Admissions:
    # -   Hospitalisation Rate:
    # -   ICU Rate:
    # -   Deaths: 
    # """)
    # st.info('- <b>Cases</b>'
    # +'\n\n- Positive Test Rate: '+str(np.round(data['PositivePercentage'].iloc[-RANGE:-1].rolling(window=7).mean()[-3],2))+'%'+' (Last week: '+str(np.round(data['PositivePercentage'].iloc[-RANGE:-8].rolling(window=7).mean()[-1],2))+'%'+')'
    # +'\n\n')

    with st.expander('View National Data'):
        st.write(data)
    
    with st.expander('View Local Data'):
        st.write(city_data)

st.subheader('Notes')
st.success("""
-   Data is updated each weekday at 2pm. Very hacky/basic code available at [https://github.com/nowaycomputer/scotvid](https://github.com/nowaycomputer/scotvid)
\n\n-    Latest merged [national data](https://github.com/nowaycomputer/scotvid/blob/main/merged_data.csv) and [local data](https://github.com/nowaycomputer/scotvid/blob/main/df_city.csv) as .csv
\n\n-    All test/case data is by sample date
\n\n-    Hospitalisation and ICU rates are rough estimates calculated using the ratio of hospital and ICU admissions 7 and 14 days respectively after the cases by sample date
\n\n-    Not all data is synchronised to the same date and the most recent day isn't shown because it is always significantly incomplete
\n\n-    All data is sourced from the [PHS OpenData Service](https://www.opendata.nhs.scot/dataset/covid-19-in-scotland)
""")
