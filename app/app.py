import datetime
from shiny import Inputs, Outputs, Session, App, reactive, render, ui, req
from shiny.types import FileInfo
from shiny.types import SilentException
import asyncio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pathlib
#import matplotlib.
from casas_measures import pattern_search

def hover(hover_color="#add8e6"):
    return dict(selector="tbody tr:hover",
            props=[("background-color", "%s" % hover_color)])

styles = [
    #table properties
    dict(selector=" ", 
         props=[("margin","1"),
                ("font-family",'"Helvetica", "Arial", sans-serif'),
                ("border-collapse", "collapse"),
                ("border","none"),
                ("border", "2px solid #ccf")
                   ]),

    #header color - optional
    dict(selector="thead", 
         props=[("background-color","#e3dedd")
               ]),

    #background shading
    dict(selector="tbody tr:nth-child(even)",
         props=[("background-color", "#fff")]),
    dict(selector="tbody tr:nth-child(odd)",
         props=[("background-color", "#eee")]),

    #cell spacing
    dict(selector="td", 
         props=[("padding", ".5em")]),

    #header cell properties
    dict(selector="th", 
         props=[("font-size", "98%"),
                ("text-align", "center")]),

    #caption placement
    dict(selector="caption", 
         props=[("caption-side", "bottom")]),

    #render hover last to override background-color
    hover()
]

filepath = pathlib.Path(r"C:\Users\Wuestney\Documents\GitHub\casas_measures\tests\tm000.20160210-20160212_20220819.192044.txt").resolve()

sensordata = pattern_search.SensorData(filepath)

pt_choices = {'tm024' : 'TM024', 'tm026' : 'TM026', 'tm027' : 'TM027', 'tm029' : 'TM029', 'tm030': 'TM030'}

patternchoice = {'sensorname': "Sensor name from a drop down menu", 
    'specialcase':'Special case sensor pattern/activity type from the special case menu', 
    'custompattern': 'Custom text pattern to match sensor names to'}

special_cases = {'Bedroom': 'Bedroom', 'OutofHome': 'Socialization/Time out of Home', 'Fatigue':'Inactivity Intervals'}

#ui.input_text("file", "Please give full file path to data file to analyze", placeholder=r"E.g. C:\Users\User\Documents\SHdata_raw\tm000.20160912-20160914.txt")
#value=pattern_search.SensorSeries(data, namepatterns=["A"])
app_ui = ui.page_fluid(
    ui.panel_title("Welcome to the Wuestney-Fritz Smart Home Data Pattern Finder", "Wuestney-Fritz Analyzer"),
    ui.layout_sidebar(
        ui.panel_sidebar(
            ui.row(
                ui.column(
                    12, 
                    ui.input_file("file", "Select tab delimited data file to analyze", accept=[".txt"], multiple=False),
                ),
            ),
            ui.row(
                ui.column(6, ui.input_checkbox("header", "Check if file has header row", False)),
                ui.column(6, ui.output_text("file_txt")),
            ),
            ui.row(
                ui.column(
                    12,
                    ui.br(),
                    ui.input_action_button("upload", "Load file ->"),
                    ui.br(),
                    "First rows of loaded sensor data:",
                    ui.output_table("data_head"),
                    ui.input_radio_buttons("patterntype", ui.h3("To visualize a sensor pattern, first select pattern type:"), patternchoice),
                    ui.panel_conditional(
                        "input.patterntype == 'sensorname'",
                        ui.input_select("sensorname", "Choose Sensor Name", [], multiple=True),
                    ),
                    ui.panel_conditional(
                        "input.patterntype == 'specialcase'",
                        ui.input_select("specialcase", "Special Pattern/Activity Case Menu", special_cases),
                    ),
                    ui.panel_conditional(
                        "input.patterntype == 'specialcase'",
                        ui.input_text("specificnames", "Provide specific sensor names to use with special case type if desired."),
                    ),
                    ui.panel_conditional(
                        "input.patterntype == 'custompattern'",
                        ui.input_text("custompattext", "Enter list of sensor names or name snippets to match")
                    ),
                    ui.input_switch("params", "Advanced options...", value=False),
                    ui.panel_conditional(
                        "input.params == True",
                        ui.input_numeric("lookahead", "How many sensor events to look ahead before defining episode end?", value=None, min=0),
                        ui.input_checkbox("include_end", "Include first sensor event after episode end with episode?", value=False),
                        ui.input_checkbox("nighttime", "Find episodes during nighttime? (ie after evening_time and before morning_time)", value=False),
                        ui.input_text("morning_time", "Enter AM time associated with time period for search."),
                        ui.input_text("morning_time", "Enter PM time associated with time period for search."),
                    ),
                    ui.input_action_button("findpattern", "Go"),
                ),
            ),
        ),
        ui.panel_main(
            ui.navset_tab(
                ui.nav(
                    "Dataframe",
                    ui.h2("DataFrame of Pattern Episodes."),
                    ui.row(
                        ui.column(4, ui.input_text("countabove", "Count Time Intervals above:", placeholder="Default 10 seconds")),
                        ui.column(4, ui.input_date_range("datebetween", "Filter DataFrame by Specific Date Range"))
                    ),
                    ui.output_table("summary_df"),
                ),
                ui.nav(
                    "Hourly", 
                    ui.h2("Episodes Summarized by Hour"),
                    ui.output_table("hourly_df"),
                ),
                ui.nav(
                    "Daily",
                    ui.h2("Episodes Summarized by Day"),
                ),
                id="inTabset",
            ),
        ),
    ),
)


def server(input: Inputs, output: Outputs, session: Session):
    @output
    @render.text
    def file_txt():
        if input.file() is None:
            return "No file selected."
        else:
            f: list[FileInfo] = input.file()
            return f"Selected: {f[0]['name']}"
    
    data = reactive.Value(value=[{'DateTime':"", 'Sensor':"", 'Message': ""}])
    #sensorseries = reactive.Value()

    @reactive.Effect
    @reactive.event(input.upload)
    def load_data():
        if input.file() is None:
            return
        else:
            f: list[FileInfo] = input.file()
            #filepath = pathlib.Path(input.file()).resolve()
            sensordata = pattern_search.SensorData(f[0]["datapath"])
            data.set(sensordata.data)
            return

    @output
    @render.table
    def data_head():
        datadf = pd.DataFrame.from_dict(data.get())

        return (datadf.head().style)


    @reactive.Calc
    def sensor_set():
        sensors_series = pd.DataFrame.from_dict(data.get())
        names = list(sensors_series['Sensor'].unique())
        #names = {name.lower():name for name in names}
        return names

    @reactive.Effect()
    def _():
        x = sensor_set()

        ui.update_select(
            "sensorname", 
            label="Choose Sensor Name/s", 
            choices=x, 
            selected=None,
        )

    @reactive.Calc
    #@reactive.event(lambda: input.findpattern, ignore_none=True)
    def find_pattern():
        #input.findpattern()
        ui.notification_show("Compiling sensor name patterns")
        
        patterntype = input.patterntype()
        if patterntype == 'sensorname':
            name_patterns = list(input.sensorname())
            print(name_patterns)
            if not name_patterns:
                raise SilentException()
            else:
                ui.notification_show("Finding pattern episodes.")
                sensordata = data.get()
                episodes = pattern_search.SensorSeries(sensordata, namepatterns=name_patterns)
                episodes.find()
                #sensorseries.set(episodes)
                #sensorseriesdf.set(episodes.summarize())
                return episodes
        elif patterntype == 'specialcase':
            specialcases = {'Bedroom': pattern_search.Bedroom, 'OutofHome': pattern_search.OutofHome, 'Fatigue':pattern_search.Fatigue}
            if input.specificnames() is None:
                name_patterns = None
            else:
                name_patterns = input.specificnames().split(",")
        elif patterntype == 'custompattern':
            name_patterns = input.custompattext().split(",")
            return
    
    #sensorseriesdf = reactive.Value(pd.DataFrame())
    sensorseriesdf = reactive.Value(pd.DataFrame(columns=['firstevent', 'lastevent', 'eventcount', 'min_timeint', 'max_timeint', 'med_timeint'], index=[pd.Timestamp.today()]))

    @reactive.Effect()
    @reactive.event(input.findpattern)
    def dataframe():
        episodes = find_pattern()
        if not input.countabove():
            countabove = pd.Timedelta('10seconds')
        else:
            try:
                countabove = pd.Timedelta(input.countabove()).to_pytimedelta()
            except:
                m = ui.modal("Please input minimum duration in any of the following formats\n '5hr12m10s', '2h32m', '2 days 23:12:00 10 sec'\n A format like '4:13' does not work.", title="Error parsing time threshold.", easy_close=True)
                ui.modal_show(m)
        df, cols = episodes.summarize()
        sensorseriesdf.set(df)

    @reactive.Effect()
    def _():
        df = sensorseriesdf.get()
        dates = df.index.get_level_values(level=0).unique().to_list()
        if dates:
            ui.update_date_range(
                "datebetween",
                start=dates[0],
                end=dates[-1],
                min=dates[0] - pd.Timedelta(days=5),
                max=dates[-1] + pd.Timedelta(days=5),
            )


    @output
    @render.table
    def summary_df():
        #dataframe()
        #print(episodes.episodes)
        df = sensorseriesdf.get()
        print(df)
        if input.datebetween():
            #dates = input.datebetween()
            df = df.loc[pd.Timestamp(input.datebetween()[0]):pd.Timestamp(input.datebetween()[1])]
            #ui.HTML(df.to_html(index=True, index_names=True))
            return (df.style.set_table_styles(styles).set_caption("Hover to highlight."))
        else:
            return (df.style.set_table_styles(styles).set_caption("Hover to highlight.")) 
        
    @output
    @render.table
    def hourly_df():
        df = sensorseriesdf.get()
        df_hourly = df.resample('H', on='firstevent')
        return df_hourly.agg({'eventcount':sum, 'totalduration':lambda x:pd.to_timedelta(sum(x, datetime.timedelta(0))), 'timeint_above':sum})


    # @output
    # @render.plot
    # def a_scatter_plot():
    #     """ fig2, ax2 = plt.subplots()
    #     ax2.plot({1}_df['firstevent'], {1}_df['totalduration'].dt.total_seconds()/60)
    #     ax2.set_ylim(top=2)
    #     ax2.xaxis.set_major_locator(ticker.LinearLocator(numticks=len({1}_df['firstevent'])))
    #     ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    #     fig2.autofmt_xdate(rotation=90)
    #     fig2.set_size_inches(10, 6)
    #     ax2.title('{0} duration by start time') """
    #     return plt.scatter([1,2,3], [5, 2, 3])


app = App(app_ui, server)
