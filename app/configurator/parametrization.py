# pylint:disable=line-too-long                                 # Allows for longer line length inside a Parametrization
"""Copyright (c) 2022 VIKTOR B.V.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

VIKTOR B.V. PROVIDES THIS SOFTWARE ON AN "AS IS" BASIS, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from munch import Munch
from viktor.parametrization import (
    Parametrization,
    Step,
    NumberField,
    GeoPointField,
    OptionField,
    ToggleButton,
    Text,
)


def _get_inverter_name_list(params: Munch, **kwargs):
    """Create list of options for the inverter name dependent on the type"""
    if params.step_2.system_type == "California Energy Commission":
        return [
            "ABB: PVI-0.3 Inverter",
            "Outback Power Tech. Inverter",
            "Hanwa Q-Cells Inverter",
        ]
    if params.step_2.system_type == "Sandia National Laboratories":
        return [
            "Generac Power Systems Inverter",
            "Delta Electronics Inverter",
            "Enphase Energy Inc Inverter",
        ]
    return []


class ConfiguratorParametrization(Parametrization):
    """Defines the input fields for the mapview (step 1) and dataview (step 2)"""

    step_1 = Step("Step 1 Define location of your home", views="get_map_view")

    step_1.text = Text(
        """## Location definition
        \n Different locations around the globe interact with the sun differently.
        \n Moreover the different climates produce specific weather patterns.
        \n By choosing the location of your home on the map on the right, weather data for a
        *Typical Meteorological Year* (TMY) at your location will be gathered from the
        [EU Science Hub](https://ec.europa.eu/jrc/en/pvgis). This TMY is used in the calculation of energy yield by your
        system."""
    )
    step_1.text2 = Text("""## Choose location""")
    step_1.point = GeoPointField("enter a point", description='Click a location on the map to select it for calculation')
    step_1.text3 = Text("""Define the surface area available on the roof:""")
    step_1.surface = NumberField("Surface area", suffix="m2", default=0, min=0,
                                 description='Use the arrows to select your available surface area or enter a number '
                                             '  \n (if applicable use a decimal point **\' . \'** instead of a comma **\' , \'** )')

    step_2 = Step("Step 2 Choose your system configuration", views="get_data_view")

    step_2.text = Text(
        """## PV-System explanation
        \n A consumer-home PV-system always consist of
        \n - One inverter unit
        \n - One or more modules
        \n The PV-systems included here are all approved by either the
        [Sandia National Laboratory](https://tinyurl.com/4jf5nkpy) or the
        [California Energy Commission](https://tinyurl.com/2p87uwkj), both of which use different calculations
        for their approval protocols."""
    )
    step_2.text2 = Text(
        """## Choose PV-System configuration
        \n By choosing either institution as the *System type* one is able to choose different
        configurations of inverters and modules.
        \n All up-to-date secifications of the chosen system configuration are
        provided by the *System Advisor Model* (SAM) as developed by the
        [National Renewable Energy Laboratory](https://sam.nrel.gov/)."""
    )

    step_2.system_type = OptionField(
        "System type",
        options=["Sandia National Laboratories", "California Energy Commission"],
        default="Sandia National Laboratories",
        flex=70,
        autoselect_single_option=True)

    step_2.inverter_name = OptionField(
        "Inverter model",
        options=_get_inverter_name_list,
        default="Generac Power Systems Inverter",
        flex=50,
        autoselect_single_option=True)

    step_2.module_name = OptionField(
        "Module model",
        options=[
            "AstroPower APX-120",
            "BP Solar SX160B",
            "Kyocera Solar PV110",
            "Mitsubishi PV - MF185UD4",
            "Sanyo HIP - 200BE11",
            "Sharp ND - L3E1U",
            "Siemens Solar SP75(6V)",
            "Suntech STP200S - 18 - ub - 1 Module",
        ],
        flex=50,
        autoselect_single_option=True,
        default="AstroPower APX-120")

    # Step 3 contains the calculation of the break-even point and visualisation thereof
    step_3 = Step("Step 3 Visualise your return-on-investment", views="get_plotly_view")
    step_3.text = Text(
        """## Forecast and Break-even
        \n Here you are able to forecast the energy yield of your chosen system. Based on the **KWh price** indicated
        The forecast will automatically calculate the revenue produced by your system.
        \n The break-even point is also indicated, this is the moment in time where the investment will be fully
        compensated by the revenue produced."""
    )
    step_3.forecast_horizon = NumberField(
        "Enter the forecasting horizon",
        suffix="years",
        default=5,
        flex=80,
        min=1,
        description="Amount of years starting at"
        "  \n the beginning of this year"
        "  \n (enter only whole years)",
    )
    step_3.kwh_cost = NumberField(
        "Enter KWh price to calculate break-even",
        suffix="€/KWh",
        default=0.22,
        flex=80,
        min=0,
        description="KWh price which is applicable to you."
        "  \n Prices may differ between energy providers."
        " \n"
        "  \n Note that prices for KWh supplied **to** the grid often"
        " differ from those of KWh's **taken from** the grid",
    )
    step_3.text2 = Text(
        """If you are only interested in a detailed time period you could choose to not show the break-even point
        in the graph and choose for a short forecasting horizon.
        \n Alternatively you could use the viewing-tools in the top-right corner of the graph to zoom to a specific
        point."""
    )
    step_3.break_even_toggle = ToggleButton("Show break-even point", default=True)
