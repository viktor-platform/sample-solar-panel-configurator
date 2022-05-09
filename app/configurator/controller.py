"""Copyright (c) 2022 VIKTOR B.V.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

VIKTOR B.V. PROVIDES THIS SOFTWARE ON AN "AS IS" BASIS, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT
SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import datetime

from viktor.core import ViktorController
from viktor.views import DataResult
from viktor.views import DataView
from viktor.views import DataItem
from viktor.views import DataGroup
from viktor.views import MapPoint
from viktor.views import MapResult
from viktor.views import MapView
from viktor.views import PlotlyView
from viktor.views import PlotlyResult

from munch import Munch
from .constants import type_dict
from .constants import inverter_name_dict
from .constants import module_name_dict
from .parametrization import ConfiguratorParametrization
from .pv_calculations import calculate_energy_generation


class Controller(ViktorController):
    """Controller class which acts as interface for the Configurator entity type.
    Connects the Parametrization (left-side of web UI), with the Views (right-side of web UI)."""

    label = "Configurator"
    parametrization = ConfiguratorParametrization(width=30)

    @MapView("Map", duration_guess=1)  # only visible on "Step 1"
    def get_map_view(self, params: Munch, **kwargs):
        """Creates mapview for step 1"""
        features = []

        if params.step_1.point:
            marker = params.step_1.point
            features.append(MapPoint.from_geo_point(marker))

        return MapResult(features)

    @DataView("Data", duration_guess=1)  # only visible on "Step 2"
    def get_data_view(self, params, **kwargs):
        """Creates dataview for step 2 from the pv_calculation"""

        energy_generation = self.get_energy_generation(params)

        energy_info = DataItem(
            label="Yearly energy yield per module",
            value=energy_generation[0],
            suffix="Kwh/year",
            number_of_decimals=2,
        )
        number_of_modules = DataItem(
            label="Number of modules possible on surface",
            value=energy_generation[1],
            number_of_decimals=0,
        )
        inverter_cost = DataItem(
            label="Cost of Inverter",
            value=inverter_name_dict[params.step_2.inverter_name]["price"],
            prefix="€",
            suffix=",-",
            number_of_decimals=2,
        )
        module_cost = DataItem(
            label="Cost per Module",
            value=module_name_dict[params.step_2.module_name]["price"],
            prefix="€",
            suffix=",-",
            number_of_decimals=2,
        )
        total_cost = DataItem(
            label="Total system cost",
            value=inverter_name_dict[params.step_2.inverter_name]["price"]
                  + module_name_dict[params.step_2.module_name]["price"]
                  * energy_generation[1],
            prefix="€",
            suffix=",-",
            number_of_decimals=2,
        )

        data = DataGroup(
            energy_info, number_of_modules, inverter_cost, module_cost, total_cost
        )

        return DataResult(data)

    @PlotlyView("Plot", duration_guess=10)  # only visible on "Step 3"
    def get_plotly_view(self, params, **kwargs):
        """Shows the plot of the energy yield with break-even point"""

        energy_generation = self.get_energy_generation(params)

        # get yearly yield data
        yield_df = energy_generation[2]
        yield_df["val"] *= params.step_3.kwh_cost

        # calculate break-even (total costs / kwh price)
        break_even = (
                inverter_name_dict[params.step_2.inverter_name]["price"]
                + module_name_dict[params.step_2.module_name]["price"]
                * energy_generation[1]
        )

        # forecast the length of the entered forecast horizon
        yield_df_copy = yield_df.copy()

        for i in range(1, params.step_3.forecast_horizon):
            new_year = yield_df_copy.copy()
            new_year["dat"] = self.replace_year(new_year["dat"], i)
            yield_df = yield_df.append(new_year)

        yield_df["dat"] = yield_df["dat"].dt.strftime("%Y-%m-%d %H:%M")

        # add a cumulative column
        yield_df["cumulative_yield"] = yield_df["val"].cumsum(axis=0)
        x_dat = yield_df["dat"].to_list()

        # prepare data for plotly
        y_dat = yield_df["cumulative_yield"].to_list()
        z_dat = [break_even] * len(x_dat)
        if params.step_3.break_even_toggle is True:
            fig = {
                "data": [
                    {"type": "line", "x": x_dat, "y": y_dat, "name": "Energy yield"},
                    {
                        "type": "line",
                        "x": x_dat,
                        "y": z_dat,
                        "name": "Break-even point",
                    },
                ],
                "layout": {
                    "title": {"text": "Energy generation over time"},
                    "xaxis": {"title": {"text": "Forecast horizon"}},
                    "yaxis": {"title": {"text": "Revenue produced by system [€]"}},
                },
            }
        else:
            fig = {
                "data": [
                    {"type": "bar", "x": x_dat, "y": y_dat, "name": "Energy yield"}
                ],
                "layout": {
                    "title": {"text": "Energy generation over time"},
                    "xaxis": {"title": {"text": "Forecast horizon"}},
                    "yaxis": {"title": {"text": "Revenue produced by system [€]"}},
                },
            }

        return PlotlyResult(fig)
    def get_energy_generation(self, params):
        '''Generate energy yield data'''
        return calculate_energy_generation(
            params.step_1.point.lat,
            params.step_1.point.lon,
            type_dict[params.step_2.system_type],
            inverter_name_dict[params.step_2.inverter_name]["name"],
            module_name_dict[params.step_2.module_name]["name"],
            area=params.step_1.surface,
        )

    @staticmethod
    def replace_year(frame, increment):
        '''Update year of the dates in yield dataframe'''
        current_year = datetime.date.today().year
        frame = frame.apply(lambda dt: dt.replace(year=current_year + increment))
        return frame
