"""Documentation for Kumulierte Tagessumme

# Kumulierte Tagessumme

## Beschreibung
Berechnet die laufende Summe einer Zeitreihe, die jeden Tag um Mitternacht wieder neu beginnt, z. B.
die bisherige Tagesmenge aus den 5-Minuten-Werten eines Massenstroms.

Zwei Faktoren rechnen die Werte dabei um: Der Faktor für die Zeiteinheit macht aus jedem Wert die
Menge in seinem Intervall, z. B. 300 für 5-Minuten-Werte in mg/s, da 5 Minuten 300 Sekunden haben.
Der Faktor für die Mengeneinheit rechnet die Summe in die gewünschte Einheit um, z. B. 0.000001 für
mg in kg.

Standardmäßig markieren die Zeitpunkte das Ende des Intervalls ihres Wertes (rechtsbündig), sodass
der Wert um Mitternacht zum Tag gehört, der dann endet. Für Zeitpunkte am Anfang der Intervalle
(linksbündig) schalten Sie rechtsbuendig aus.

## Eingänge
* **zeitreihe** (SERIES): Die Werte, die aufsummiert werden.
* **zeitzone** (STRING, optional): Die Zeitzone, in der die Tage um Mitternacht beginnen, z. B.
  `Europe/Berlin` für deutsche Zeit. Ohne Angabe die Zeitzone aus den Metadaten der Zeitreihe
  (`default_timezone`) und, wenn diese keine angeben, UTC.
* **faktor_zeiteinheit** (FLOAT, optional, Standard 1.0): Faktor, mit dem jeder Wert vor dem
  Aufsummieren multipliziert wird, z. B. 300 für 5-Minuten-Werte einer Größe pro Sekunde wie mg/s
  oder 0.25 für 15-Minuten-Werte einer Größe pro Stunde wie kW.
* **faktor_mengeneinheit** (FLOAT, optional, Standard 1.0): Faktor, mit dem die Summen
  multipliziert werden, z. B. 0.000001 für mg in kg oder 0.001 für Liter in Kubikmeter.
* **rechtsbuendig** (BOOLEAN, optional, Standard True): True, wenn die Zeitpunkte das Ende des
  Intervalls markieren, für das ein Wert gilt, z. B. 00:05 Uhr für den Wert von 00:00 bis
  00:05 Uhr. Der Wert um Mitternacht gehört dann zum Tag, der endet. False, wenn sie den Anfang
  markieren, z. B. 00:00 Uhr für den Wert von 00:00 bis 00:05 Uhr. Der Wert um Mitternacht gehört
  dann zum neuen Tag.

## Ausgänge
* **kumulierte_summe** (SERIES): Die bisherige Summe des Tages zu jedem Zeitpunkt der Zeitreihe,
  mit den Zeitpunkten in UTC. Die Summe des ganzen Tages ist der Wert um Mitternacht am Ende des
  Tages, mit rechtsbuendig False der letzte Wert vor Mitternacht, z. B. um 23:55 Uhr.

## Beispiel
Für die 5-Minuten-Werte eines Massenstroms in mg/s ab 23:50 Uhr deutscher Zeit mit der zeitzone
`Europe/Berlin`, dem faktor_zeiteinheit 300 und dem faktor_mengeneinheit 0.000001:
* 23:50 Uhr: 1000 mg/s, also 0,3 kg in den 5 Minuten bis 23:50 Uhr, ergibt die Summe 0,3 kg
* 23:55 Uhr: 1000 mg/s, also 0,3 kg, ergibt die Summe 0,6 kg
* 00:00 Uhr: 2000 mg/s, also 0,6 kg, ergibt die Summe 1,2 kg des Tages, der um Mitternacht endet
* 00:05 Uhr: 1000 mg/s, also 0,3 kg, ergibt die Summe 0,3 kg des neuen Tages
* 00:10 Uhr: 3000 mg/s, also 0,9 kg, ergibt die Summe 1,2 kg

Mit rechtsbuendig False gilt der Wert um 00:00 Uhr für die 5 Minuten ab 00:00 Uhr und beginnt den
neuen Tag. Die Summen sind dann 0,3 kg, 0,6 kg (die Summe des Tages, der um Mitternacht endet),
0,6 kg, 0,9 kg und 1,8 kg.

Im Ergebnis stehen diese Summen bei denselben Zeitpunkten in UTC, im Winter also von 22:50 bis
23:10 Uhr UTC.

## Gut zu wissen
* **Tage** beginnen um Mitternacht in der Zeitzone, auch an den Tagen mit 23 oder 25 Stunden, an
  denen die Sommerzeit beginnt oder endet.
* **Zeitpunkte ohne Zeitzone**, z. B. von manuellen Eingaben ohne `Z` am Ende, werden als
  Zeitpunkte in der Zeitzone genommen.
* **Fehlende Werte** werden übersprungen: Zu ihrem Zeitpunkt fehlt auch die Summe, danach wird mit
  den übrigen Werten des Tages weitergezählt.
* Das Ergebnis hat weder einen Namen noch Metadaten, da es eine neue Größe in einer anderen Einheit
  ist.

## Details
Die Summen werden wie mit der pandas-Formel
`(a.tz_convert(zeitzone) * faktor_zeiteinheit).groupby(pd.Grouper(freq="D", closed="right")).cumsum().tz_convert("UTC") * faktor_mengeneinheit`
für die nach ihren Zeitpunkten sortierte Zeitreihe a berechnet. `closed="right"` zählt den Wert um
Mitternacht zum Tag, der dann endet. Mit rechtsbuendig False ist es `closed="left"`, das den Wert
um Mitternacht zum neuen Tag zählt.

Zeitzonen werden wie in der IANA-Zeitzonendatenbank geschrieben, z. B. `Europe/Berlin` oder `UTC`,
auch als feste Abstände zu UTC wie `+01:00`. Die Zeitzone aus den Metadaten ist die
`default_timezone` der Metrik, sonst die des Datensatzes, wie es die
[Metadaten-Konventionen](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/)
(auf Englisch) festlegen. Die Zeitzone, in der Diagramme Zeitpunkte anzeigen sollen
(`plot_target_timezone`), spielt keine Rolle, damit die Summen nicht davon abhängen, wer die
Komponente ausführt.
"""

import contextvars

import pandas as pd
import pytest
from hdhelpers import modify_timezone
from hdhelpers.metadata import get_series_default_timezone

from hdutils import ComponentInputValidationException, parse_value
from hetdesrun.runtime.context import RuntimeExecutionContext, set_runtime_exec_context


def invalid_input(message, input_name):
    return ComponentInputValidationException(
        message, error_code=422, invalid_component_inputs=[input_name]
    )


def as_numbers(zeitreihe):
    try:
        return pd.to_numeric(zeitreihe).astype("float64")
    except (ValueError, TypeError) as error:
        raise invalid_input(
            "Die Zeitreihe hat Werte, die keine Zahlen sind.", "zeitreihe"
        ) from error


def is_time_zone(time_zone):
    try:
        pd.Timestamp(0, tz=time_zone)
    except KeyError, ValueError:  # ZoneInfoNotFoundError is a KeyError
        return False
    return True


def day_time_zone(zeitreihe, zeitzone):
    """The time zone in which the days start at midnight

    The given one, otherwise the default_timezone of the metadata, otherwise UTC. Not the time zone
    of the plot target settings, to which modify_timezone falls back for None: It is a display
    preference of the caller, and the sums should not depend on who executes the component.
    """
    if zeitzone is not None and zeitzone.strip() != "":
        time_zone = zeitzone.strip()
        if not is_time_zone(time_zone):
            raise invalid_input(
                f"Die Zeitzone {time_zone} ist unbekannt. Zeitzonen werden wie Europe/Berlin oder"
                " UTC geschrieben. Groß- und Kleinschreibung spielt eine Rolle.",
                "zeitzone",
            )
        return time_zone

    # None also for metadata not following the conventions, e.g. with an unknown time zone
    time_zone = get_series_default_timezone(zeitreihe)
    return time_zone if time_zone is not None else "UTC"


def in_time_zone(values, time_zone):
    """The values with their points in time in the time zone

    Points in time without time zone are taken as points in time in the time zone.
    """
    try:
        return modify_timezone(values, time_zone)
    except (ValueError, TypeError) as error:
        # only for points in time without time zone which do not exist or exist twice in the time
        # zone, around the changes from and to daylight saving time
        raise invalid_input(
            f"Die Zeitpunkte der Zeitreihe haben keine Zeitzone und können nicht als Zeitpunkte in"
            f" der Zeitzone {time_zone} genommen werden: {error}. Geben Sie die Zeitpunkte mit"
            " Zeitzone an, z. B. 2026-01-01T00:05:00Z für 00:05 Uhr UTC.",
            "zeitreihe",
        ) from error


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "zeitreihe": {"data_type": "SERIES"},
        "zeitzone": {"data_type": "STRING", "default_value": None},
        "faktor_zeiteinheit": {"data_type": "FLOAT", "default_value": 1.0},
        "faktor_mengeneinheit": {"data_type": "FLOAT", "default_value": 1.0},
        "rechtsbuendig": {"data_type": "BOOLEAN", "default_value": True},
    },
    "outputs": {
        "kumulierte_summe": {"data_type": "SERIES"},
    },
    "name": "Kumulierte Tagessumme",
    "category": "Arithmetic",
    "description": "Laufende Summe einer Zeitreihe, die jeden Tag um Mitternacht neu beginnt",
    "version_tag": "0.1.0",
    "id": "8f7982f7-fb6d-4886-a0da-3487bfebfb4a",
    "revision_group_id": "0e24be6a-483f-4399-8564-bbe6e09be32e",
    "state": "RELEASED",
    "released_timestamp": "2026-11-13T15:39:34+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    zeitreihe,
    zeitzone=None,
    faktor_zeiteinheit=1.0,
    faktor_mengeneinheit=1.0,
    rechtsbuendig=True,
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    values = as_numbers(zeitreihe)
    if len(values) == 0:
        return {
            "kumulierte_summe": pd.Series([], index=pd.DatetimeIndex([], tz="UTC"), dtype="float64")
        }
    if not isinstance(values.index, pd.DatetimeIndex):
        raise invalid_input(
            "Die Zeitreihe braucht Zeitpunkte wie 2026-01-01T00:05:00Z, um ihre Werte Tagen"
            " zuzuordnen.",
            "zeitreihe",
        )

    # the time zone from zeitreihe, since pd.to_numeric drops the metadata
    local_values = in_time_zone(values.sort_index(), day_time_zone(zeitreihe, zeitzone))
    # closed="right": the value at midnight belongs to the day ending then, since its point in time
    # marks the end of the interval of the value. closed="left": it belongs to the new day.
    days = pd.Grouper(freq="D", closed="right" if rechtsbuendig else "left")
    daily_sums = (local_values * faktor_zeiteinheit).groupby(days).cumsum() * faktor_mengeneinheit

    # in UTC, since e.g. generic REST adapters only accept timeseries in UTC
    result = daily_sums.tz_convert("UTC").rename(None)
    # neither the unit nor other metadata of the values apply to the sums
    result.attrs = {}
    return {"kumulierte_summe": result}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "zeitreihe",
            "filters": {
                "value": '{"2026-01-01T22:00:00Z": 1.0, "2026-01-01T23:00:00Z": 2.0, "2026-01-02T00:00:00Z": 3.0, "2026-01-02T01:00:00Z": 4.0, "2026-01-02T02:00:00Z": 5.0}'
            },
        },
        {
            "workflow_input_name": "zeitzone",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "faktor_zeiteinheit",
            "use_default_value": True,
            "filters": {"value": "1.0"},
        },
        {
            "workflow_input_name": "faktor_mengeneinheit",
            "use_default_value": True,
            "filters": {"value": "1.0"},
        },
        {
            "workflow_input_name": "rechtsbuendig",
            "use_default_value": True,
            "filters": {"value": "True"},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "zeitreihe",
            "filters": {
                "value": '{"2026-01-01T22:00:00Z": 1.0, "2026-01-01T23:00:00Z": 2.0, "2026-01-02T00:00:00Z": 3.0, "2026-01-02T01:00:00Z": 4.0, "2026-01-02T02:00:00Z": 5.0}'
            },
        },
        {
            "workflow_input_name": "zeitzone",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "faktor_zeiteinheit",
            "use_default_value": True,
            "filters": {"value": "1.0"},
        },
        {
            "workflow_input_name": "faktor_mengeneinheit",
            "use_default_value": True,
            "filters": {"value": "1.0"},
        },
        {
            "workflow_input_name": "rechtsbuendig",
            "use_default_value": True,
            "filters": {"value": "True"},
        },
    ]
}


# Unit tests, see https://hetida.github.io/hetida-designer/user_guide/component_writing/unit_testing/
# ruff: noqa: S101


def timeseries(values, start, freq="5min"):
    return pd.Series(
        values, index=pd.date_range(start, periods=len(values), freq=freq), dtype="float64"
    )


def with_time_zone(series, time_zone):
    """The series with metadata following the conventions, specifying the time zone"""
    series.attrs = {
        "dataset_metadata": {
            "metric_key": "id",
            "single_metric": "flow",
            "queried_metrics": ["flow"],
            "ref_interval_start_timestamp": "2026-01-01T00:00:00+00:00",
            "ref_interval_end_timestamp": "2026-01-03T00:00:00+00:00",
            "ref_interval_type": "right_open",
            "default_timezone": time_zone,
        },
        "metrics": [
            {
                "id": "flow",
                "name": "Massenstrom",
                "value_dimensions": [{"column": "value", "unit": "mg/s", "measurement": "flow"}],
            }
        ],
    }
    return series


def test_run_with_test_wiring():
    result = main(
        **{
            inp_wiring["workflow_input_name"]: parse_value(
                inp_wiring["filters"]["value"],
                COMPONENT_INFO["inputs"][inp_wiring["workflow_input_name"]]["data_type"],
                nullable=True,
            )
            for inp_wiring in TEST_WIRING_FROM_PY_FILE_IMPORT["input_wirings"]
        }
    )["kumulierte_summe"]

    # days in UTC, the value at midnight belongs to the day ending then
    pd.testing.assert_series_equal(
        result,
        timeseries([1.0, 3.0, 6.0, 4.0, 9.0], "2026-01-01T22:00:00Z", freq="h"),
        check_freq=False,
    )


@pytest.mark.parametrize(
    ("rechtsbuendig", "expected"),
    [(True, [0.3, 0.6, 1.2, 0.3, 1.2]), (False, [0.3, 0.6, 0.6, 0.9, 1.8])],
)
def test_example_of_the_documentation(rechtsbuendig, expected):
    # 5-minute values in mg/s from 23:50 in German time
    zeitreihe = timeseries([1000.0, 1000.0, 2000.0, 1000.0, 3000.0], "2026-01-15T22:50:00Z")

    result = main(
        zeitreihe=zeitreihe,
        zeitzone="Europe/Berlin",
        faktor_zeiteinheit=300.0,
        faktor_mengeneinheit=0.000001,
        rechtsbuendig=rechtsbuendig,
    )["kumulierte_summe"]

    pd.testing.assert_series_equal(
        result, timeseries(expected, "2026-01-15T22:50:00Z"), check_freq=False
    )


@pytest.mark.parametrize("rechtsbuendig", [True, False])
@pytest.mark.parametrize(
    ("first_day", "values_per_day"),
    [
        # daylight saving time starts on 2026-03-29 and ends on 2026-10-25
        ("2026-03-28", [288, 276, 288]),
        ("2026-10-24", [288, 300, 288]),
    ],
)
def test_days_start_at_midnight_also_with_23_or_25_hours(first_day, values_per_day, rechtsbuendig):
    # 1.0 every 5 minutes for three days in German time, from 00:05 to 00:00 if the points in time
    # mark the end of the intervals of the values, otherwise from 00:00 to 23:55
    first_midnight = pd.Timestamp(first_day, tz="Europe/Berlin")
    first_value = first_midnight + pd.Timedelta("5min" if rechtsbuendig else "0min")
    index = pd.date_range(
        first_value, first_value + pd.offsets.Day(3) - pd.Timedelta("5min"), freq="5min"
    )
    zeitreihe = pd.Series(1.0, index=index.tz_convert("UTC"))

    result = main(zeitreihe=zeitreihe, zeitzone="Europe/Berlin", rechtsbuendig=rechtsbuendig)[
        "kumulierte_summe"
    ]

    assert result.index.equals(zeitreihe.index)
    german_result = result.tz_convert("Europe/Berlin")
    starts_of_days = german_result[german_result == 1.0].index
    assert starts_of_days.tolist() == [first_value + pd.offsets.Day(day) for day in range(3)]
    # the sums of the whole days, before the next day starts
    ends_of_days = german_result[german_result.shift(-1, fill_value=1.0) == 1.0]
    assert ends_of_days.tolist() == values_per_day


BERLIN_DAYS = [1.0, 2.0, 3.0, 1.0, 2.0, 3.0]
UTC_DAYS = [1.0, 2.0, 3.0, 4.0, 1.0, 2.0]


@pytest.mark.parametrize(
    ("metadata_time_zone", "zeitzone", "expected"),
    [
        ("Europe/Berlin", None, BERLIN_DAYS),
        ("Europe/Berlin", "", BERLIN_DAYS),
        ("Europe/Berlin", "UTC", UTC_DAYS),
        (None, None, UTC_DAYS),
        (None, "Europe/Berlin", BERLIN_DAYS),
        (None, " Europe/Berlin ", BERLIN_DAYS),
        (None, "+01:00", BERLIN_DAYS),
    ],
)
def test_time_zone_is_given_or_from_metadata_or_utc(metadata_time_zone, zeitzone, expected):
    # hourly from 21:00 UTC, midnight in German time is at 23:00 UTC in winter
    zeitreihe = timeseries([1.0] * 6, "2026-01-01T21:00:00Z", freq="h")
    if metadata_time_zone is not None:
        zeitreihe = with_time_zone(zeitreihe, metadata_time_zone)

    result = main(zeitreihe=zeitreihe, zeitzone=zeitzone)["kumulierte_summe"]

    pd.testing.assert_series_equal(
        result, timeseries(expected, "2026-01-01T21:00:00Z", freq="h"), check_freq=False
    )


def test_days_do_not_depend_on_the_time_zone_of_plots():
    def execute_with_plot_target_time_zone():
        # as provided by the caller, e.g. from the browser of a user in Germany
        set_runtime_exec_context(
            RuntimeExecutionContext(plot_target_settings={"plot_target_timezone": "Europe/Berlin"})
        )
        return main(zeitreihe=timeseries([1.0] * 6, "2026-01-01T21:00:00Z", freq="h"))

    # in a copy of the context, so that the time zone of plots does not apply to other tests
    result = contextvars.copy_context().run(execute_with_plot_target_time_zone)

    pd.testing.assert_series_equal(
        result["kumulierte_summe"],
        timeseries(UTC_DAYS, "2026-01-01T21:00:00Z", freq="h"),
        check_freq=False,
    )


def test_points_in_time_without_time_zone_are_taken_in_the_time_zone():
    # as from a manual input without Z
    zeitreihe = timeseries([1.0] * 3, "2026-01-01T23:00:00", freq="h")

    result = main(zeitreihe=zeitreihe, zeitzone="Europe/Berlin")["kumulierte_summe"]

    pd.testing.assert_series_equal(
        result, timeseries([1.0, 2.0, 1.0], "2026-01-01T22:00:00Z", freq="h"), check_freq=False
    )


def test_values_are_summed_up_in_the_order_of_their_points_in_time():
    zeitreihe = timeseries([1.0, 2.0, 3.0], "2026-01-01T00:05:00Z").iloc[[2, 0, 1]]

    result = main(zeitreihe=zeitreihe)["kumulierte_summe"]

    pd.testing.assert_series_equal(
        result, timeseries([1.0, 3.0, 6.0], "2026-01-01T00:05:00Z"), check_freq=False
    )


def test_missing_values_are_skipped():
    zeitreihe = timeseries([1.0, None, 2.0, 3.0], "2026-01-01T00:05:00Z")

    result = main(zeitreihe=zeitreihe)["kumulierte_summe"]

    pd.testing.assert_series_equal(
        result, timeseries([1.0, None, 3.0, 6.0], "2026-01-01T00:05:00Z"), check_freq=False
    )


def test_result_has_neither_name_nor_metadata_and_input_is_unchanged():
    zeitreihe = with_time_zone(
        timeseries([1000.0, 2000.0], "2026-01-01T00:05:00Z").rename("Massenstrom"),
        "Europe/Berlin",
    )
    expected_input = zeitreihe.copy()
    expected_attrs = zeitreihe.attrs.copy()

    result = main(zeitreihe=zeitreihe, faktor_zeiteinheit=300.0)["kumulierte_summe"]

    assert result.name is None
    assert result.attrs == {}
    pd.testing.assert_series_equal(zeitreihe, expected_input)
    assert zeitreihe.attrs == expected_attrs


@pytest.mark.parametrize(
    "zeitreihe",
    [
        pd.Series([], dtype="float64"),
        pd.Series([], index=pd.DatetimeIndex([], tz="UTC"), dtype="float64"),
    ],
)
def test_empty_timeseries(zeitreihe):
    result = main(zeitreihe=zeitreihe, zeitzone="Europe/Berlin")["kumulierte_summe"]

    pd.testing.assert_series_equal(
        result, pd.Series([], index=pd.DatetimeIndex([], tz="UTC"), dtype="float64")
    )


@pytest.mark.parametrize(
    ("zeitreihe", "zeitzone", "invalid_input_name", "message_part"),
    [
        (
            timeseries([1.0], "2026-01-01T00:05:00Z"),
            "europe/berlin",
            "zeitzone",
            "Die Zeitzone europe/berlin ist unbekannt",
        ),
        (
            timeseries([1.0], "2026-01-01T00:05:00Z"),
            "../etc/passwd",
            "zeitzone",
            "ist unbekannt",
        ),
        (
            pd.Series(["keine Zahl"], index=pd.to_datetime(["2026-01-01T00:05:00Z"])),
            None,
            "zeitreihe",
            "keine Zahlen",
        ),
        (pd.Series([1.0, 2.0]), None, "zeitreihe", "braucht Zeitpunkte"),
        (
            # 02:30 does not exist in German time on 2026-03-29
            timeseries([1.0], "2026-03-29T02:30:00"),
            "Europe/Berlin",
            "zeitreihe",
            "können nicht als Zeitpunkte in der Zeitzone Europe/Berlin genommen werden",
        ),
    ],
)
def test_errors_explain_what_to_change(zeitreihe, zeitzone, invalid_input_name, message_part):
    with pytest.raises(ComponentInputValidationException) as exc_info:
        main(zeitreihe=zeitreihe, zeitzone=zeitzone)

    assert exc_info.value.extra_information["invalid_component_inputs"] == [invalid_input_name]
    assert message_part in str(exc_info.value)
