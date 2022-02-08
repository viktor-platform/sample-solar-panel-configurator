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
import pandas as pd
import pvlib


def calculate_energy_generation(latitude, longitude):
    """Calculates the yearly energy yield as a result of the coorinates"""
    name = "Your"

    # get the module and inverter specifications from SAM
    sandia_modules = pvlib.pvsystem.retrieve_sam("SandiaMod")
    sapm_inverters = pvlib.pvsystem.retrieve_sam("cecinverter")
    module = sandia_modules["Canadian_Solar_CS5P_220M___2009_"]
    inverter = sapm_inverters["ABB__MICRO_0_25_I_OUTD_US_208__208V_"]

    # get temperature specifications of module materials (default most used in consumer-systems)
    temperature_model_parameters = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS[
        "sapm"
    ]["open_rack_glass_glass"]

    # retreive weather data and elevation (altitude)
    weather, *inputs = pvlib.iotools.get_pvgis_tmy(
        latitude, longitude, map_variables=True
    )
    weather.index.name = "utc_time"
    temp_air = weather["temp_air"]  # [degrees_C]
    wind_speed = weather["wind_speed"]  # [m/s]
    pressure = weather["pressure"]  # [Pa]

    altitude = inputs[1]["location"]["elevation"]

    # declare system
    system = {"module": module, "inverter": inverter, "surface_azimuth": 180}
    system["surface_tilt"] = latitude

    # determine solar position
    solpos = pvlib.solarposition.get_solarposition(
        time=weather.index,
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        temperature=temp_air,
        pressure=pressure,
    )

    # calculate energy produced based on entered data
    dni_extra = pvlib.irradiance.get_extra_radiation(weather.index)
    airmass = pvlib.atmosphere.get_relative_airmass(solpos["apparent_zenith"])
    am_abs = pvlib.atmosphere.get_absolute_airmass(airmass, pressure)
    aoi = pvlib.irradiance.aoi(
        system["surface_tilt"],
        system["surface_azimuth"],
        solpos["apparent_zenith"],
        solpos["azimuth"],
    )
    total_irrad = pvlib.irradiance.get_total_irradiance(
        system["surface_tilt"],
        system["surface_azimuth"],
        solpos["apparent_zenith"],
        solpos["azimuth"],
        weather["dni"],
        weather["ghi"],
        weather["dhi"],
        dni_extra=dni_extra,
        model="haydavies",
    )
    tcell = pvlib.temperature.sapm_cell(
        total_irrad["poa_global"], temp_air, wind_speed, **temperature_model_parameters
    )
    effective_irradiance = pvlib.pvsystem.sapm_effective_irradiance(
        total_irrad["poa_direct"], total_irrad["poa_diffuse"], am_abs, aoi, module
    )
    dc_yield = pvlib.pvsystem.sapm(effective_irradiance, tcell, module)
    ac_yield = pvlib.inverter.sandia(dc_yield["v_mp"], dc_yield["p_mp"], inverter)

    # prepare data for presentation and visualisation
    acdp = ac_yield.to_frame()
    acdp["utc_time"] = pd.to_datetime(acdp.index)
    acdp["utc_time"] = acdp.index.strftime("%m-%d %H:%M:%S")
    acdp.columns = ["val", "dat"]

    # possible plot
    acdp.plot(x="dat", y="val")
    annual_energy = acdp["val"].sum()
    # plt.show()

    energies = {}
    energies[name] = annual_energy
    energies = pd.Series(energies)

    # final result in KWh*hrs
    energy_yield = int(energies.round(0)) / 1000

    return energy_yield
