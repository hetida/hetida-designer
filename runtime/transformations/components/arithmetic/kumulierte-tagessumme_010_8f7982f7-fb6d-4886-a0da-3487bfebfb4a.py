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

Beginnt der abgefragte Zeitraum mitten am Tag, z. B. bei den letzten 24 Stunden, fehlen die Werte
vom Anfang dieses Tages. Die Komponente verwirft ihn daher und beginnt mit dem nächsten Tag.

## Eingänge
* **zeitreihe** (SERIES): Die Werte, die aufsummiert werden.
* **zeitzone** (STRING, optional): Die Zeitzone, in der die Tage um Mitternacht beginnen, z. B.
  `Europe/Berlin` für deutsche Zeit. Ohne Angabe die Zeitzone aus den Metadaten der Zeitreihe
  (`default_timezone`) oder, wenn diese keine angeben, die Zeitzone, in der das aufrufende System
  Zeitpunkte anzeigt (`plot_target_timezone`), z. B. in der hetida Plattform die Zeitzone des
  Mandanten oder des Benutzers, der sich das Ergebnis ansieht. Ohne sie, z. B. im hetida designer,
  UTC.
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
* **kumulierte_summe** (SERIES): Die bisherige Summe des Tages zu jedem Zeitpunkt der Zeitreihe ab
  dem ersten vollständigen Tag, mit den Zeitpunkten in UTC. Die Summe des ganzen Tages ist der Wert
  um Mitternacht am Ende des Tages, mit rechtsbuendig False der letzte Wert vor Mitternacht, z. B.
  um 23:55 Uhr.

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
* **Unvollständige Tage am Anfang** werden verworfen: Beginnt der abgefragte Zeitraum aus den
  Metadaten der Zeitreihe nicht um Mitternacht in der Zeitzone, z. B. bei den letzten 24 Stunden ab
  10:00 Uhr, wären die Summen dieses ersten Tages zu klein. Die Summen beginnen dann erst mit dem
  nächsten Tag, also mit dem Wert um 00:05 Uhr, mit rechtsbuendig False mit dem Wert um 00:00 Uhr.
  Beginnt der Zeitraum um Mitternacht, ist sein erster Tag vollständig. Ein Wert genau um diese
  Mitternacht gehört standardmäßig (rechtsbuendig) aber zum Vortag und wird mit ihm verworfen.
  Reicht der Zeitraum nicht bis zum nächsten Tag, ist das Ergebnis leer. Ohne abgefragten Zeitraum
  in den Metadaten, z. B. bei manuellen Eingaben, werden alle Werte aufsummiert.
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

Vorher werden die Werte vor dem ersten vollständigen Tag verworfen, mit rechtsbuendig wie mit
`a[a.index > erster_tag]`, sonst wie mit `a[a.index >= erster_tag]`. erster_tag ist die erste
Mitternacht in der Zeitzone ab dem Beginn des abgefragten Zeitraums
(`ref_interval_start_timestamp` in den Metadaten des Datensatzes), also der Beginn selbst, wenn er
auf Mitternacht fällt. Mit rechtsbuendig False gilt das nur, wenn der Zeitraum laut
`ref_interval_type` an seinem Anfang geschlossen ist (`closed`, `left_closed` oder `right_open`)
und so den Wert um diese Mitternacht enthält, sonst ist erster_tag die Mitternacht danach. Für
diskrete Datensätze (`ref_dataset_discrete`),
d. h. einzelne Zeitpunkte statt eines Zeitraums, und Metadaten, die den Konventionen nicht folgen,
wird nichts verworfen.

Zeitzonen werden wie in der IANA-Zeitzonendatenbank geschrieben, z. B. `Europe/Berlin` oder `UTC`,
auch als feste Abstände zu UTC wie `+01:00`. Die Zeitzone aus den Metadaten ist die
`default_timezone` der Metrik, sonst die des Datensatzes, wie es die
[Metadaten-Konventionen](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/)
(auf Englisch) festlegen. Geben weder der Eingang zeitzone noch die Metadaten eine Zeitzone an,
beginnen die Tage wie im Formelrechner in der `plot_target_timezone` der Plot-Einstellungen des
Ausführungskontexts, auf die auch `modify_timezone` zurückfällt, z. B. für Versionen der hetida
Plattform, die dort die Zeitzone des Mandanten liefern, aber noch nicht in den Metadaten, und ohne
sie in UTC.
"""

import contextvars

import pandas as pd
import pytest
from hdhelpers import modify_timezone
from hdhelpers.metadata import get_series_default_timezone, read_metadata
from hdhelpers.plot_target_settings import get_plot_target_settings

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

    The given one, otherwise the default_timezone of the metadata, otherwise the time zone of the
    plot target settings, like modify_timezone(zeitreihe, None) and the Formula Calculator, e.g. the
    tenant's time zone, which hetida platform versions provide there before their metadata specify
    it, otherwise UTC.
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
    if time_zone is not None:
        return time_zone

    # the plot target settings modify_timezone falls back to, blank like missing
    plot_target_time_zone = (get_plot_target_settings().plot_target_timezone or "").strip()
    return plot_target_time_zone if plot_target_time_zone != "" else "UTC"


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


# ref interval types which contain the start of the interval
CONTAINING_START = {"closed", "left_closed", "right_open"}


def start_of_day(date, time_zone):
    """The first point in time of the date (without time zone) in the time zone

    Midnight, or where the clocks are changed at midnight, e.g. in America/Santiago, the first
    point in time existing on the day, where the day also starts when grouping by days.
    """
    return date.tz_localize(time_zone, ambiguous=True, nonexistent="shift_forward")


def start_of_first_whole_day(zeitreihe, time_zone, rechtsbuendig):
    """The start of the first day whose values all are in the queried interval of the timeseries

    The queried interval is the ref interval of the metadata. None without it, e.g. for manual
    inputs, metadata not following the conventions or discrete datasets, which are isolated points
    in time instead of an interval, so that no day is dropped. Days start at midnight in the time
    zone.

    The day on which the interval starts is whole if the interval starts at its midnight. With
    rechtsbuendig, the values of the day are after midnight, so the interval need not contain its
    start. Otherwise the value at midnight is the first value of the day, which only intervals
    closed at the start contain.
    """
    meta = read_metadata(zeitreihe, "SERIES")
    if (
        meta is None
        or meta.dataset_metadata.ref_dataset_discrete
        or meta.dataset_metadata.ref_interval_start_timestamp is None
    ):
        return None
    # the conventions require the type with the start unless the dataset is discrete
    start = pd.Timestamp(meta.dataset_metadata.ref_interval_start_timestamp)
    contains_start = meta.dataset_metadata.ref_interval_type in CONTAINING_START

    date = start.tz_convert(time_zone).tz_localize(None).normalize()
    if start == start_of_day(date, time_zone) and (rechtsbuendig or contains_start):
        return start
    return start_of_day(date + pd.Timedelta(days=1), time_zone)


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

    # the time zone and the queried interval from zeitreihe, since pd.to_numeric drops the metadata
    time_zone = day_time_zone(zeitreihe, zeitzone)
    local_values = in_time_zone(values.sort_index(), time_zone)
    # the sums of the days before would be too small, since the values of their start are missing
    first_day = start_of_first_whole_day(zeitreihe, time_zone, rechtsbuendig)
    if first_day is not None:
        # with rechtsbuendig, the value at midnight belongs to the day before
        in_whole_days = (
            local_values.index > first_day if rechtsbuendig else local_values.index >= first_day
        )
        local_values = local_values[in_whole_days]
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


def with_metadata(
    series, time_zone=None, start="2025-12-31T00:00:00+00:00", interval_type="right_open"
):
    """The series with metadata following the conventions

    With the time zone, if given, and the queried interval from the start. The default start is
    more than a day before the values of the tests, so that no values are dropped.
    """
    series.attrs = {
        "dataset_metadata": {
            "metric_key": "id",
            "single_metric": "flow",
            "queried_metrics": ["flow"],
            "ref_interval_start_timestamp": start,
            "ref_interval_end_timestamp": "2027-01-01T00:00:00+00:00",
            "ref_interval_type": interval_type,
        }
        | ({} if time_zone is None else {"default_timezone": time_zone}),
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
        zeitreihe = with_metadata(zeitreihe, metadata_time_zone)

    result = main(zeitreihe=zeitreihe, zeitzone=zeitzone)["kumulierte_summe"]

    pd.testing.assert_series_equal(
        result, timeseries(expected, "2026-01-01T21:00:00Z", freq="h"), check_freq=False
    )


def with_plot_target_time_zone(time_zone, function):
    """The result of the function, executed with the time zone in the plot target settings

    As the hetida platform provides it, e.g. the tenant's time zone. In a copy of the context, so
    that the time zone does not apply to other tests.
    """

    def execute():
        set_runtime_exec_context(
            RuntimeExecutionContext(plot_target_settings={"plot_target_timezone": time_zone})
        )
        return function()

    return contextvars.copy_context().run(execute)


@pytest.mark.parametrize(
    ("metadata_time_zone", "zeitzone", "plot_target_time_zone", "expected"),
    [
        # neither given nor in the metadata
        (None, None, "Europe/Berlin", BERLIN_DAYS),
        (None, "", "Europe/Berlin", BERLIN_DAYS),
        (None, None, "UTC", UTC_DAYS),
        (None, None, " ", UTC_DAYS),
        # the given time zone and the time zone of the metadata first
        (None, "UTC", "Europe/Berlin", UTC_DAYS),
        ("UTC", None, "Europe/Berlin", UTC_DAYS),
        ("Europe/Berlin", None, "UTC", BERLIN_DAYS),
    ],
)
def test_without_time_zone_given_or_in_the_metadata_days_are_days_in_the_plot_target_time_zone(
    metadata_time_zone, zeitzone, plot_target_time_zone, expected
):
    # hourly from 21:00 UTC, midnight in German time is at 23:00 UTC in winter
    zeitreihe = timeseries([1.0] * 6, "2026-01-01T21:00:00Z", freq="h")
    if metadata_time_zone is not None:
        zeitreihe = with_metadata(zeitreihe, metadata_time_zone)

    result = with_plot_target_time_zone(
        plot_target_time_zone, lambda: main(zeitreihe=zeitreihe, zeitzone=zeitzone)
    )["kumulierte_summe"]

    pd.testing.assert_series_equal(
        result, timeseries(expected, "2026-01-01T21:00:00Z", freq="h"), check_freq=False
    )


@pytest.mark.parametrize(
    ("zeitzone", "plot_target_time_zone"), [("Europe/Berlin", None), (None, "Europe/Berlin")]
)
def test_points_in_time_without_time_zone_are_taken_in_the_time_zone(
    zeitzone, plot_target_time_zone
):
    # as from a manual input without Z
    zeitreihe = timeseries([1.0] * 3, "2026-01-01T23:00:00", freq="h")

    result = with_plot_target_time_zone(
        plot_target_time_zone, lambda: main(zeitreihe=zeitreihe, zeitzone=zeitzone)
    )["kumulierte_summe"]

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


def hourly_values(**metadata):
    """1.0 every hour from 21:00 on 2026-01-14 to 02:00 on 2026-01-16 in German time

    Midnight in German time is at 23:00 UTC in winter.
    """
    return with_metadata(timeseries([1.0] * 30, "2026-01-14T20:00:00Z", freq="h"), **metadata)


GERMAN_MIDNIGHT = "2026-01-14T23:00:00Z"


@pytest.mark.parametrize(
    ("start", "interval_type", "rechtsbuendig", "first_result"),
    [
        # 20:30 in German time: from the next day on
        ("2026-01-14T19:30:00Z", "right_open", True, "2026-01-15T00:00:00Z"),
        ("2026-01-14T19:30:00Z", "right_open", False, GERMAN_MIDNIGHT),
        # midnight in UTC is 01:00 in German time
        ("2026-01-15T00:00:00Z", "right_open", True, "2026-01-16T00:00:00Z"),
        ("2026-01-15T00:00:00Z", "right_open", False, "2026-01-15T23:00:00Z"),
        # midnight in German time: the day is whole, but the value at midnight belongs to the day
        # before with rechtsbuendig
        (GERMAN_MIDNIGHT, "right_open", True, "2026-01-15T00:00:00Z"),
        (GERMAN_MIDNIGHT, "right_open", False, GERMAN_MIDNIGHT),
        (GERMAN_MIDNIGHT, "closed", True, "2026-01-15T00:00:00Z"),
        (GERMAN_MIDNIGHT, "closed", False, GERMAN_MIDNIGHT),
        (GERMAN_MIDNIGHT, "left_closed", False, GERMAN_MIDNIGHT),
        # without the value at midnight, which only starts the day without rechtsbuendig
        (GERMAN_MIDNIGHT, "left_open", True, "2026-01-15T00:00:00Z"),
        (GERMAN_MIDNIGHT, "left_open", False, "2026-01-15T23:00:00Z"),
        (GERMAN_MIDNIGHT, "open", False, "2026-01-15T23:00:00Z"),
    ],
)
def test_days_the_queried_interval_does_not_contain_whole_at_its_start_are_dropped(
    start, interval_type, rechtsbuendig, first_result
):
    zeitreihe = hourly_values(time_zone="Europe/Berlin", start=start, interval_type=interval_type)

    result = main(zeitreihe=zeitreihe, rechtsbuendig=rechtsbuendig)["kumulierte_summe"]

    # the sums of the following days are unchanged and start with a new day
    all_days = main(
        zeitreihe=hourly_values(time_zone="Europe/Berlin"), rechtsbuendig=rechtsbuendig
    )["kumulierte_summe"]
    pd.testing.assert_series_equal(
        result, all_days[all_days.index >= pd.Timestamp(first_result)], check_freq=False
    )
    assert result.iloc[0] == 1.0


@pytest.mark.parametrize(
    ("metadata_time_zone", "zeitzone", "plot_target_time_zone", "first_result"),
    [
        # 01:00 in German time: from the next day on
        ("Europe/Berlin", None, None, "2026-01-16T00:00:00Z"),
        (None, "Europe/Berlin", None, "2026-01-16T00:00:00Z"),
        (None, None, "Europe/Berlin", "2026-01-16T00:00:00Z"),
        # midnight in UTC: the day is whole, but the value at midnight belongs to the day before
        ("Europe/Berlin", "UTC", None, "2026-01-15T01:00:00Z"),
        (None, None, "UTC", "2026-01-15T01:00:00Z"),
        (None, None, None, "2026-01-15T01:00:00Z"),
    ],
)
def test_days_start_at_midnight_in_the_time_zone_of_the_days(
    metadata_time_zone, zeitzone, plot_target_time_zone, first_result
):
    def daily_sums(start):
        zeitreihe = hourly_values(time_zone=metadata_time_zone, start=start)
        return with_plot_target_time_zone(
            plot_target_time_zone, lambda: main(zeitreihe=zeitreihe, zeitzone=zeitzone)
        )["kumulierte_summe"]

    result = daily_sums("2026-01-15T00:00:00Z")

    all_days = daily_sums("2025-12-31T00:00:00Z")
    pd.testing.assert_series_equal(
        result, all_days[all_days.index >= pd.Timestamp(first_result)], check_freq=False
    )
    assert result.iloc[0] == 1.0


@pytest.mark.parametrize("rechtsbuendig", [True, False])
@pytest.mark.parametrize(("start_after_midnight", "dropped_days"), [("0h", 0), ("1h", 1)])
# daylight saving time starts on 2026-03-29 and ends on 2026-10-25
@pytest.mark.parametrize("first_day", ["2026-03-29", "2026-10-25"])
def test_whole_days_also_with_23_or_25_hours(
    first_day, start_after_midnight, dropped_days, rechtsbuendig
):
    # 1.0 every 5 minutes for two days in German time, from 00:05 to 00:00 if the points in time
    # mark the end of the intervals of the values, otherwise from 00:00 to 23:55
    first_midnight = pd.Timestamp(first_day, tz="Europe/Berlin")
    first_value = first_midnight + pd.Timedelta("5min" if rechtsbuendig else "0min")
    index = pd.date_range(
        first_value, first_value + pd.offsets.Day(2) - pd.Timedelta("5min"), freq="5min"
    )
    start = (first_midnight + pd.Timedelta(start_after_midnight)).tz_convert("UTC").isoformat()
    zeitreihe = with_metadata(
        pd.Series(1.0, index=index.tz_convert("UTC")), "Europe/Berlin", start=start
    )

    result = main(zeitreihe=zeitreihe, rechtsbuendig=rechtsbuendig)["kumulierte_summe"]

    first_result = first_value + pd.offsets.Day(dropped_days)
    assert result.index.equals(zeitreihe.index[zeitreihe.index >= first_result])
    assert result.iloc[0] == 1.0


def test_result_is_empty_if_the_queried_interval_does_not_reach_the_next_day():
    # from 10:00 to 16:00 in German time
    zeitreihe = with_metadata(
        timeseries([1.0] * 7, "2026-01-15T09:00:00Z", freq="h"),
        "Europe/Berlin",
        start="2026-01-15T09:00:00Z",
    )

    result = main(zeitreihe=zeitreihe)["kumulierte_summe"]

    assert len(result) == 0
    assert str(result.index.tz) == "UTC"
    assert result.dtype == "float64"


def test_no_day_is_dropped_for_discrete_datasets():
    zeitreihe = hourly_values(time_zone="Europe/Berlin", start="2026-01-15T00:00:00Z")
    expected = main(zeitreihe=hourly_values(time_zone="Europe/Berlin"))["kumulierte_summe"]
    # isolated points in time instead of an interval, for which the type is not required
    zeitreihe.attrs["dataset_metadata"]["ref_dataset_discrete"] = True
    del zeitreihe.attrs["dataset_metadata"]["ref_interval_type"]

    result = main(zeitreihe=zeitreihe)["kumulierte_summe"]

    pd.testing.assert_series_equal(result, expected)


def test_result_has_neither_name_nor_metadata_and_input_is_unchanged():
    zeitreihe = with_metadata(
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
