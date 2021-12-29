import pandas as pd
from plotly.subplots import make_subplots
import numpy as np
import streamlit as st

RANGE=120
HOSPITAL_OFFSET=7
ICU_OFFSET=14
FONT_SIZE=12
DEATH_DELAY=3
ADJ=1 # hacky adjustment factor for periods when reporting delays are long
TEMPLATE='none'

st.set_page_config(layout="wide")

def get_remote_data():
    df_cases=pd.read_csv('https://www.opendata.nhs.scot/dataset/b318bddf-a4dc-4262-971f-0ba329e09b87/resource/287fc645-4352-4477-9c8c-55bc054b7e76/download/daily_cuml_scot_20211210.csv', index_col='Date',parse_dates=True)
    df_hospital=pd.read_csv('https://www.opendata.nhs.scot/dataset/b318bddf-a4dc-4262-971f-0ba329e09b87/resource/2dd8534b-0a6f-4744-9253-9565d62f96c2/download/trend_hb_20211210.csv', index_col='Date',parse_dates=True)
    gov_uk_hospital_scot=pd.read_csv('https://coronavirus.data.gov.uk/api/v1/data?filters=areaType=nation;areaName=Scotland&structure=%7B%22areaType%22:%22areaType%22,%22areaName%22:%22areaName%22,%22areaCode%22:%22areaCode%22,%22date%22:%22date%22,%22hospitalCases%22:%22hospitalCases%22%7D&format=csv',index_col='date',parse_dates=True)
    df_hospital=df_hospital[df_hospital['HBName']=='Scotland']

    df_cases.to_csv('data/df_cases.csv')
    df_hospital.to_csv('data/df_hospital.csv')

    return df_cases, df_hospital, gov_uk_hospital_scot

def get_local_data():
    df_cases=pd.read_csv('data/df_cases.csv', index_col='Date',parse_dates=True)
    df_hospital=pd.read_csv('data/df_hospital.csv', index_col='Date',parse_dates=True)
    gov_uk_hospital_scot=pd.read_csv('data/gov_uk_hospital_scot.csv', index_col='date',parse_dates=True)
    df_hospital=df_hospital[df_hospital['HBName']=='Scotland']

    return df_cases, df_hospital, gov_uk_hospital_scot

@st.cache(ttl=3600,suppress_st_warning=True, show_spinner=False)
def get_data():
    try:
        df_cases, df_hospital, gov_uk_hospital_scot = get_remote_data()
        return df_cases, df_hospital, gov_uk_hospital_scot
    except:
        df_cases, df_hospital, gov_uk_hospital_scot = get_local_data()
        return df_cases, df_hospital, gov_uk_hospital_scot


# @st.cache(suppress_st_warning=True, show_spinner=False)
def make_plots():

    df_cases, df_hospital, gov_uk_hospital_scot = get_data()
    st.title('Scotland Covid Update')
    # b,c = st.columns([1,5])
    col, buff, buff2 = st.columns(3)
    buff.write('')
    col.info('Updated on '+(df_cases.index[-1]+pd.Timedelta(days=1, hours=14)).strftime("%d/%m/%Y %H:%M:%S"))
    global RANGE
    col, buff1, buff2, buff3 = st.columns(4)
    buff1.write('')
    buff2.write('')
    buff3.write('')
    range_option=col.selectbox('',['Recent','All'])
    if range_option=='Recent':
        RANGE=121
    else:
        RANGE=-1
    st.subheader('National Data')
    
    cases_ma=df_cases.iloc[-2*RANGE:-2].rolling(window=7).mean()
    hosp_ma=df_hospital.iloc[-2*RANGE:-2].rolling(window=7).mean()
    hosp_ma_no_na=hosp_ma.dropna()
    hosp_occ_ma=gov_uk_hospital_scot.rolling(window=7).mean()
    
    case_box,pos_box,adm_box,icu_box, death_box=st.columns([1,1,1,1,1])
    
    case_diff=cases_ma.iloc[-1].values[0]-cases_ma.iloc[-8].values[0]
    pos_diff=hosp_ma['PositivePercentage'].iloc[-1]-hosp_ma['PositivePercentage'].iloc[-8]
    adm_diff=hosp_ma_no_na['HospitalAdmissions'].iloc[-1]-hosp_ma_no_na['HospitalAdmissions'].iloc[-8]
    icu_diff=hosp_ma_no_na['ICUAdmissions'].iloc[-1]-hosp_ma_no_na['ICUAdmissions'].iloc[-8]
    death_diff=hosp_ma_no_na['DailyDeaths'].iloc[-1]-hosp_ma_no_na['DailyDeaths'].iloc[-8]
    
    case_box.metric(label="Daily Cases (vs last wk)", value=str(int(cases_ma.iloc[-1].values[0])), delta=str(int(case_diff)),delta_color="inverse")
    pos_box.metric(label="Daily Positive Rate (vs last wk)", value=str(np.round(hosp_ma['PositivePercentage'].iloc[-1],1))+"%", delta=str(np.round(pos_diff,1))+"%",delta_color="inverse")
    adm_box.metric(label="Daily Admissions (vs last wk)",value=str(int(np.round(hosp_ma_no_na['HospitalAdmissions'].iloc[-1],0))), delta=str(int(np.round(adm_diff,0))),delta_color="inverse")
    icu_box.metric(label="Daily ICU Admissions (vs last wk)",value=str(int(np.round(hosp_ma_no_na['ICUAdmissions'].iloc[-1],0))), delta=str(int(np.round(icu_diff,0))),delta_color="inverse")
    death_box.metric(label="Daily Deaths (vs last wk)",value=str(int(np.round(hosp_ma_no_na['DailyDeaths'].iloc[-1],0))), delta=str(int(np.round(death_diff,1))),delta_color="inverse")

    specs=[[{"secondary_y": False}, {"secondary_y": False},{"secondary_y": True}], 
                           [{"secondary_y": False}, {"secondary_y": True},{"secondary_y": False}]
                           ]

    fig = make_subplots(rows=2,cols=3,specs=specs,shared_xaxes='all',subplot_titles=['Cases','Positive Test Rate','Hospital','ICU Admissions', 'Hospital and ICU Rates', 'Deaths'],vertical_spacing = 0.15,horizontal_spacing = 0.1)

    #
    # Cases
    #
    fig.add_scatter(x=df_cases.iloc[-2*RANGE:-ADJ].index, y=df_cases['DailyCases'].iloc[-2*RANGE:-1], mode='lines',name='Cases',line_color='blue',opacity=0.25,row=1,col=1)
    fig.add_scatter(x=cases_ma.index, y=cases_ma['DailyCases'], mode='lines',name='Cases (Ave)',line_color='blue',line_width=3,row=1,col=1)

    #
    # Pos Rate
    #

    fig.add_scatter(x=df_hospital.iloc[-2*RANGE:-ADJ].index, y=df_hospital['PositivePercentage'].iloc[-2*RANGE:-1], mode='lines',name='Pos Rate',line_color='green',opacity=0.25,row=1,col=2)
    fig.add_scatter(x=hosp_ma.index, y=hosp_ma['PositivePercentage'], mode='lines',name='Pos Rate (Ave)',line_color='green',line_width=3,row=1,col=2)
    # fig.add_bar(x=df_hospital.iloc[-2*RANGE:-1].index,y=df_hospital['TotalTests'].iloc[-2*RANGE:-1],opacity=0.3,row=1,col=2,secondary_y=True,name='Tests',marker_color='orange')

    #
    # Hospital Admissions
    #
    fig.add_scatter(x=df_hospital.iloc[-2*RANGE:].index, y=df_hospital['HospitalAdmissions'].iloc[-2*RANGE:], mode='lines',name='Admissions',line_color='red',opacity=0.25,row=1,col=3)
    fig.add_scatter(x=df_hospital.iloc[-2*RANGE:].rolling(window=7).mean().index, y=df_hospital['HospitalAdmissions'].iloc[-2*RANGE:].rolling(window=7).mean(), mode='lines',name='Admissions (Ave)',line_color='red',line_width=3,row=1,col=3)
    # Hospital Patients
    fig.add_scatter(x=gov_uk_hospital_scot.index, y=gov_uk_hospital_scot['hospitalCases'], mode='lines',name='In Hospital',line_color='navy',row=1,col=3,secondary_y=True, line_width=3)
    
    #
    # Hosp Rate
    #

    fig.add_scatter(x=df_hospital.iloc[-RANGE:-ADJ-HOSPITAL_OFFSET].index, y=((df_hospital['HospitalAdmissions'].iloc[-RANGE:-1].shift(-HOSPITAL_OFFSET)/df_cases['DailyCases'].iloc[-RANGE:-1])*100), mode='lines',name='Hosp. Rate',line_color='purple',opacity=0.1,row=2,col=2)
    fig.add_scatter(x=df_hospital.iloc[-RANGE:-ADJ-HOSPITAL_OFFSET].index, y=((df_hospital['HospitalAdmissions'].iloc[-RANGE:-1].shift(-HOSPITAL_OFFSET)/df_cases['DailyCases'].iloc[-RANGE:-1])*100).rolling(window=7).mean(), mode='lines',name='Hosp. Rate (Ave)',line_color='purple',line_width=3,row=2,col=2)
    if RANGE==-1:
        fig['layout']['yaxis6'].update(range=[-0.01, 45], autorange=False)
        fig['layout']['yaxis7'].update(range=[-0.01, 45], autorange=False)
    else:
        fig['layout']['yaxis6'].update(range=[-0.01, 10], autorange=False)
        fig['layout']['yaxis7'].update(range=[-0.01, 1], autorange=False)
    #
    # ICU Rate
    #
    icu_rate=(df_hospital['ICUAdmissions'].iloc[-2*RANGE:].shift(ICU_OFFSET).dropna()/df_cases['DailyCases'].iloc[-RANGE:-1])*100
    fig.add_scatter(x=icu_rate.iloc[-ADJ*RANGE:].index,y=icu_rate.iloc[-ADJ*RANGE:], mode='lines',name='ICU Rate',line_color='brown',opacity=0.1,row=2,col=2,secondary_y=True)
    fig.add_scatter(x=icu_rate.iloc[-ADJ*RANGE:].index,y=icu_rate.iloc[-ADJ*RANGE:].rolling(window=7).mean(), mode='lines',name='ICU Rate (Ave)',line_color='brown',line_width=3,row=2,col=2,secondary_y=True)   
    # fig.add_scatter(x=df_hospital['ICUAdmissions'].iloc[-ADJ*RANGE:-1].index, y=((df_hospital['ICUAdmissions'].iloc[-2*RANGE:-1].shift(ICU_OFFSET)/df_cases['DailyCases'].iloc[-RANGE:-1])*100), mode='lines',name='ICU Rate',line_color='brown',opacity=0.1,row=2,col=2,secondary_y=True)
    # fig.add_scatter(x=df_hospital['ICUAdmissions'].iloc[-ADJ*RANGE:-1].index, y=((df_hospital['ICUAdmissions'].iloc[-2*RANGE:-1].shift(ICU_OFFSET)/df_cases['DailyCases'].iloc[-RANGE:-1])*100).rolling(window=7).mean(), mode='lines',name='ICU Rate (Ave)',line_color='brown',line_width=3,row=2,col=2,secondary_y=True)
    # if RANGE==-1:
    #         fig['layout']['yaxis7'].update(range=[-0.1, 2], autorange=False)
  
    
    # ICU Admissions
    fig.add_scatter(x=df_hospital.iloc[-2*RANGE:].index, y=df_hospital['ICUAdmissions'].iloc[-2*RANGE:], mode='lines',name='Admissions',line_color='red',opacity=0.25,row=2,col=1)
    fig.add_scatter(x=df_hospital.iloc[-2*RANGE:].rolling(window=7).mean().index, y=df_hospital['ICUAdmissions'].iloc[-2*RANGE:].rolling(window=7).mean(), mode='lines',name='Admissions (Ave)',line_color='red',line_width=3,row=2,col=1)
   
    
    #
    # Deaths
    #

    fig.add_scatter(x=df_hospital['DailyDeaths'].iloc[-2*RANGE:-DEATH_DELAY].index, y=df_hospital['DailyDeaths'].iloc[-2*RANGE:-DEATH_DELAY], mode='lines',name='Deaths',line_color='black',opacity=0.25,row=2,col=3)
    fig.add_scatter(x=df_hospital['DailyDeaths'].iloc[-2*RANGE:-DEATH_DELAY].index, y=df_hospital['DailyDeaths'].iloc[-2*RANGE:-DEATH_DELAY].rolling(window=7).mean(), mode='lines',name='Deaths (Ave)',line_color='black',line_width=3,row=2,col=3)

    # Cases
    fig['layout']['yaxis']['title']='Cases/Day'
    
    # Pos Rate
    fig['layout']['yaxis2']['title']='Positive Test Rate (%)'
    
    # Hospital
    fig['layout']['yaxis3']['title']='Hospital Occupancy'
    fig['layout']['yaxis3']['color']='navy'
    fig['layout']['yaxis4']['title']='Admissions/Day'
    fig['layout']['yaxis4']['color']='red'
    
    # ICU
    fig['layout']['yaxis5']['title']='ICU Admissions/day'
    
    # Rates
    fig['layout']['yaxis6']['title']='Hospitalisation Rate (%)'
    fig['layout']['yaxis6']['color']='purple'
    fig['layout']['yaxis7']['title']='ICU Rate (%)'
    fig['layout']['yaxis7']['color']='brown'
    
    fig['layout']['yaxis8']['title']='Deaths'
    fig['layout']['plot_bgcolor']='rgba(0,0,0,0)'


    fig.update_layout(height=600, width=1400,   margin=dict(l=60, r=60, t=60, b=60))
    fig.update_layout(showlegend=False)
    fig.update_xaxes(range = [df_cases.iloc[-RANGE:-1].index[0], (df_cases.iloc[-RANGE:-1].index[-1].date()+pd.Timedelta(days=7))])
    fig.update_layout(template=TEMPLATE)
    st.plotly_chart(fig)
    data=pd.merge(df_hospital, df_cases, left_index=True, right_index=True)
    data.to_csv('data/merged_data.csv')
    return data

def get_remote_city_data():
    df_city=pd.read_csv('https://www.opendata.nhs.scot/dataset/b318bddf-a4dc-4262-971f-0ba329e09b87/resource/427f9a25-db22-4014-a3bc-893b68243055/download/trend_ca_20211213.csv', index_col='Date',parse_dates=True)
    df_city.to_csv('data/df_city.csv')
    return df_city

def get_local_city_data():
    df_city=pd.read_csv('data/df_city.csv', index_col='Date',parse_dates=True)
    return df_city

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
    # city_option = st.selectbox('Local Cases',(sorted(city_data['CAName'].unique().tolist())),index=14)
    
    col1, buff4, buff5, buff6 = st.columns(4)
    buff4.write('')
    buff5.write('')
    buff6.write('')
    city_option=col1.selectbox('',(sorted(city_data['CAName'].unique().tolist())),index=14)

    fig_city = make_subplots(rows=1,cols=3,shared_xaxes='all',subplot_titles=['Cases per Day in '+city_option,'Positive Test Rate in '+city_option,'Deaths in '+city_option])
    fig_city.add_scatter(x=city_data[city_data['CAName']==city_option]['DailyPositive'].iloc[-RANGE:-2].index, y=city_data[city_data['CAName']==city_option].iloc[-RANGE:-2]['DailyPositive'], mode='lines',name='Cases',line_color='blue',opacity=0.25,row=1,col=1)
    fig_city.add_scatter(x=city_data[city_data['CAName']==city_option]['DailyPositive'].iloc[-RANGE:-2].rolling(window=7).mean().index, y=city_data[city_data['CAName']==city_option].iloc[-RANGE:-2]['DailyPositive'].rolling(window=7).mean(), mode='lines',name='Cases (Ave)',line_color='blue',line_width=3,row=1,col=1)
    
    fig_city.add_scatter(x=city_data[city_data['CAName']==city_option]['PositivePercentage'].iloc[-RANGE:-2].index, y=city_data[city_data['CAName']==city_option].iloc[-RANGE:-2]['PositivePercentage'], mode='lines',name='Pos Rate',line_color='green',opacity=0.25,row=1,col=2)
    fig_city.add_scatter(x=city_data[city_data['CAName']==city_option]['PositivePercentage'].iloc[-RANGE:-2].rolling(window=7).mean().index, y=city_data[city_data['CAName']==city_option].iloc[-RANGE:-2]['PositivePercentage'].rolling(window=7).mean(), mode='lines',name='Pos Rate (Ave)',line_color='green',line_width=3,row=1,col=2)

    fig_city.add_scatter(x=city_data[city_data['CAName']==city_option]['DailyDeaths'].iloc[-RANGE:-1].index, y=city_data[city_data['CAName']==city_option].iloc[-RANGE:-1]['DailyDeaths'], mode='lines',name='Deaths',line_color='black',opacity=0.25,row=1,col=3)
    fig_city.add_scatter(x=city_data[city_data['CAName']==city_option]['DailyDeaths'].iloc[-RANGE:-1].rolling(window=7).mean().index, y=city_data[city_data['CAName']==city_option].iloc[-RANGE:-1]['DailyDeaths'].rolling(window=7).mean(), mode='lines',name='Deaths (Ave)',line_color='black',line_width=3,row=1,col=3)

    fig_city.update_layout(showlegend=False)
    fig_city.update_layout(height=400, width=1400,   margin=dict(l=60, r=60, t=60, b=60))
    fig_city.update_xaxes(range = [city_data[city_data['CAName']==city_option].iloc[-RANGE:-1].index[0], (city_data[city_data['CAName']==city_option].iloc[-RANGE:-1].index[-1].date()+pd.Timedelta(days=7))])

    fig_city['layout']['yaxis']['title']='Cases/Day'
    fig_city['layout']['yaxis2']['title']='Daily Positive Test Rate (%)'
    fig_city['layout']['yaxis3']['title']='Deaths/Day'
    
    fig_city.update_layout(template=TEMPLATE)
    fig_city['layout']['plot_bgcolor']='rgba(0,0,0,0)'

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
        st.dataframe(data[['DailyPositive','CumulativePositive','DailyDeaths','CumulativeDeaths','TotalTests',
                           'PositivePercentage','HospitalAdmissions','ICUAdmissions']])
    
    with st.expander('View Local Data'):
        st.dataframe(city_data[city_data['CAName']==city_option][['DailyPositive','CumulativePositive','DailyDeaths','CumulativeDeaths','TotalTests',
                           'PositivePercentage']])

st.subheader('Notes')
st.success("""
-   Data is updated each weekday at 2pm. 
\n\n-    Very hacky/basic code available at [https://github.com/nowaycomputer/scotvid](https://github.com/nowaycomputer/scotvid)
\n\n-    Latest merged [national data](https://github.com/nowaycomputer/scotvid/blob/main/data/merged_data.csv) and [local data](https://github.com/nowaycomputer/scotvid/blob/main/data/df_city.csv) as .csv
\n\n-    All test/case data is by sample date
\n\n-    Hospitalisation and ICU rates are rough estimates calculated using the ratio of hospital and ICU admissions 7 and 14 days respectively after the cases by sample date
\n\n-    Not all data is synchronised to the same date and the most recent day isn't shown because it is always significantly incomplete
\n\n-    All data is sourced from the [PHS OpenData Service](https://www.opendata.nhs.scot/dataset/covid-19-in-scotland)
""")
