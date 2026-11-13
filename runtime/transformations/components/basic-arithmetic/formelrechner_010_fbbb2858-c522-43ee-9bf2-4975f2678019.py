"""Documentation for Formelrechner

# Formelrechner

## Beschreibung
Berechnet eine Formel mit bis zu fünf Zeitreihen, ähnlich wie eine Formel in Excel.

Verbinden Sie die Zeitreihen, die Sie brauchen, mit den Eingängen **a**, **b**, **c**, **d** und
**e** und schreiben Sie eine Formel mit diesen Buchstaben, z. B. `(a + b) / 2` für den Mittelwert
von a und b. Die Formel wird für jeden Zeitpunkt einzeln berechnet: Das Ergebnis um 10:00 Uhr wird
aus den Werten von a und b um 10:00 Uhr berechnet, das Ergebnis um 10:15 Uhr aus den Werten um
10:15 Uhr und so weiter.

Auch Methoden der Zeitreihen können verwendet werden, z. B. `a - a.mean()` für die Abweichung von
a von seinem Mittelwert, `a.rolling("1h").mean()` für den gleitenden Mittelwert der letzten Stunde
oder `abcde.std(axis=1)` für die Standardabweichung aller verbundenen Zeitreihen zu jedem
Zeitpunkt.

Auch die Metadaten der Zeitreihen, wie die Properties ihrer Signale, können verwendet werden, z. B.
`a > meta.a.max` für die Zeitpunkte, zu denen a größer als seine Property max ist.

Diese Komponente gibt es auch auf Englisch: "Formula Calculator".

## Eingänge
* **a**, **b**, **c**, **d**, **e** (SERIES, optional): Die Zeitreihen, die in der Formel verwendet
  werden. Verbinden Sie nur die, die Sie brauchen.
* **formel** (STRING): Die Formel, z. B. `(a + b) / 2`.
* **zeitzone_aus_metadaten** (BOOLEAN, optional, Standard True): Berechnet die Formel in der
  Zeitzone aus den Metadaten der Zeitreihen, z. B. für Tage von Mitternacht bis Mitternacht
  deutscher Zeit, siehe die Beispiele zu Zeitzonen. Schalten Sie es mit False aus, um die Formel
  in den Zeitzonen zu berechnen, die die Zeitreihen haben, meist UTC.

## Ausgänge
* **ergebnis** (SERIES): Das Ergebnis der Formel für jeden Zeitpunkt.

## So schreiben Sie eine Formel
Schreiben Sie Formeln wie in Excel oder auf einem Taschenrechner:
* `+` plus, `-` minus, `*` mal, `/` geteilt durch
* `**` hoch, z. B. `a**2` für a zum Quadrat (in Excel: `^`)
* `( )` Klammern, die zuerst berechnet werden, z. B. `(a + b) * 2`. Ohne Klammern wird zuerst
  hoch gerechnet, dann mal und geteilt, dann plus und minus. `a + b * 2` ist also a plus zweimal
  b.
* Dezimalzahlen mit einem Punkt statt einem Komma, z. B. `1.5` für 1,5. Sehr große und sehr
  kleine Zahlen können wie `2.5e6` für 2,5 Millionen (2,5 mal 10 hoch 6) und `3e-3` für 0,003
  geschrieben werden.
* `pi` für die Zahl π = 3,14159...
* Funktionen in Kleinbuchstaben mit Klammern dahinter, z. B. `sqrt(a)` für die Wurzel aus a. Die
  Funktionen haben englische Namen, z. B. sqrt für square root (Quadratwurzel).
* Methoden einer Zeitreihe nach einem Punkt, z. B. `a.mean()` für den Mittelwert aller Werte von a
  oder `a.round(2)` für a gerundet auf 2 Nachkommastellen. Alle Methoden stehen in der
  [pandas-Dokumentation von Series](https://pandas.pydata.org/docs/reference/series.html)
  (auf Englisch).
* `abcde` für eine Tabelle mit allen verbundenen Zeitreihen als Spalten, z. B. `abcde.max(axis=1)`
  für den größten Wert aller verbundenen Zeitreihen zu jedem Zeitpunkt.
* `meta` für die Metadaten der verbundenen Zeitreihen, z. B. `meta.a.max` für das Feld max der
  Metadaten von a, siehe die Beispiele zu Metadaten unten.
* `modify_timezone(a, "Europe/Berlin")` für a mit seinen Zeitpunkten in deutscher Zeit, z. B. für
  Tage von Mitternacht bis Mitternacht deutscher Zeit, wenn a keine Metadaten hat, siehe die
  Beispiele zu Zeitzonen unten.
* `pd`, `np` und `hdhelpers` für die Python-Bibliotheken pandas, numpy und hdhelpers, z. B.
  `pd.Grouper(freq="D")`, `np.sign(a)` oder `hdhelpers.metadata.get_series_info(a, "max")`.
* Text in Anführungszeichen, z. B. Zeitdauern wie `"1h"` für eine Stunde in
  `a.rolling("1h").mean()`.

Leerzeichen spielen keine Rolle: `a+b` ist dasselbe wie `a + b`. Groß- und Kleinschreibung aber
schon: Schreiben Sie `a` und `sqrt`, nicht `A` und `SQRT`.

## Unterschiede zu Excel
* Die Eingänge a, b, c, d, e treten an die Stelle von Zellen wie A1 oder B2.
* Dezimalzahlen: `1.5` statt `1,5`.
* Die Formel muss nicht mit `=` beginnen (darf es aber).
* Potenzen: `a**2` statt `a^2`.
* Prozent: `a * 19 / 100` oder `a * 0.19` statt `a * 19%`. Das Zeichen `%` ist hier der Rest
  einer Division, z. B. `a % 60` (Excel: REST(a; 60)).
* Vergleiche: `==` für gleich und `!=` für ungleich statt `=` und `<>`.
* Leere Zellen zählen in Excel als 0. Hier bleibt ein fehlender Wert fehlend: `a + b` hat keinen
  Wert, wo ein Wert von a oder b fehlt. Damit fehlende Werte als 0 zählen, schreiben Sie
  `a.add(b, fill_value=0)` statt `a + b`, siehe die Beispiele zu fehlenden Werten unten.
* Funktionen und Methoden haben englische Namen, z. B. `sqrt(a)` statt WURZEL(a), und mehrere Werte
  in Klammern werden mit Komma statt Semikolon getrennt, z. B. `a.clip(0, 100)`.
* Logarithmen: `log` ist der natürliche Logarithmus (Excel: LN). Der Logarithmus zur Basis 10 ist
  `log10` (Excel: LOG).
* Winkel eines Punktes: `arctan2(b, a)` ist ARCTAN2(a; b) in Excel, mit vertauschtem a und b.
* Funktionen wie SUMME, MITTELWERT, MAX, MIN, RUNDEN und WENN werden anders geschrieben, z. B.
  `abcde.sum(axis=1)`, `abcde.mean(axis=1)`, `a.round(2)` oder `a.where(c > 0, b)`, siehe die
  Beispiele unten.

## Beispiele
Für die Zeitreihen
* a: 10 um 00:00 Uhr, 20 um 01:00 Uhr und 30 um 02:00 Uhr
* b: 30 um 00:00 Uhr, 50 um 01:00 Uhr und 40 um 02:00 Uhr

ergibt die Formel `(a + b) / 2` 20 um 00:00 Uhr, 35 um 01:00 Uhr und 35 um 02:00 Uhr.

Die folgenden Beispiele sind vollständige Formeln, die Sie kopieren können.

### Grundrechenarten
* `a + b` : a plus b
* `a + b + c + d + e` : Summe aller fünf Zeitreihen
* `a - b` : a minus b, z. B. die Differenz zwischen Zufluss und Abfluss
* `a * b` : a mal b
* `a / b` : a geteilt durch b
* `a * 2.5` : a mal 2,5
* `-a` : a mit umgekehrtem Vorzeichen (Taste +/-)
* `(a + b) / 2` : Mittelwert (Durchschnitt) von a und b
* `(a + b + c) / 3` : Mittelwert von a, b und c
* `1 / a` : Kehrwert von a (Taste 1/x)
* `a % 60` : Rest beim Teilen von a durch 60, z. B. die Minuten nach den vollen Stunden einer
  Dauer in Minuten

### Prozent
* `a * 19 / 100` : 19 Prozent von a
* `a * 1.19` : a plus 19 Prozent
* `a * (1 - 0.25)` : a minus 25 Prozent
* `a / b * 100` : a in Prozent von b
* `(b - a) / a * 100` : Änderung von a nach b in Prozent

### Potenzen und Wurzeln
* `a**2` : a zum Quadrat (Taste x²)
* `a**3` : a hoch 3
* `a**b` : a hoch b (Taste xʸ)
* `10**a` : 10 hoch a (Taste 10ˣ)
* `sqrt(a)` : Quadratwurzel aus a (Taste √, Excel: WURZEL)
* `a**(1/3)` : dritte Wurzel aus a
* `a**(1/b)` : b-te Wurzel aus a
* `sqrt(a**2 + b**2)` : Hypotenuse eines rechtwinkligen Dreiecks mit den Seiten a und b
  (Pythagoras)

### Logarithmen und Exponentialfunktion
* `log(a)` : natürlicher Logarithmus von a (Taste ln, Excel: LN)
* `log10(a)` : Logarithmus von a zur Basis 10 (Taste log, Excel: LOG)
* `log(a) / log(2)` : Logarithmus von a zur Basis 2
* `log(a) / log(b)` : Logarithmus von a zur Basis b
* `exp(a)` : e hoch a (Taste eˣ, Excel: EXP)
* `exp(1) * a` : a mal die Eulersche Zahl e = 2,71828...

### Betrag und Runden
* `abs(a)` : Betrag von a, also a ohne Vorzeichen (Excel: ABS)
* `abs(a - b)` : Abstand zwischen a und b, immer positiv
* `a.round(2)` : a gerundet auf 2 Nachkommastellen
* `a.round()` : a gerundet auf eine ganze Zahl. Werte genau in der Mitte werden auf die gerade
  Zahl gerundet, z. B. wird 2,5 zu 2 und 3,5 zu 4.
* `floor(a + 0.5)` : a gerundet auf eine ganze Zahl wie mit RUNDEN(a; 0) in Excel für positive
  Zahlen, z. B. wird 2,5 zu 3
* `floor(a * 100 + 0.5) / 100` : a gerundet auf 2 Nachkommastellen wie mit RUNDEN(a; 2) in Excel
  für positive Zahlen
* `floor(a)` : a abgerundet auf eine ganze Zahl, z. B. wird 2,7 zu 2 und -2,3 zu -3 (Excel:
  GANZZAHL)
* `ceil(a)` : a aufgerundet auf eine ganze Zahl, z. B. wird 2,3 zu 3 und -2,7 zu -2
* `floor(a / 15) * 15` : a abgerundet auf ein Vielfaches von 15

### Winkel (Trigonometrie)
Wie in Excel werden Winkel im Bogenmaß angegeben. Ein voller Kreis hat im Bogenmaß 2 mal π, das
sind 360 Grad.
* `sin(a)` : Sinus des Winkels a im Bogenmaß (ebenso `cos(a)` und `tan(a)`)
* `sin(a * pi / 180)` : Sinus des Winkels a in Grad (ebenso mit cos und tan)
* `arcsin(a)` : Winkel im Bogenmaß, dessen Sinus a ist (Taste sin⁻¹, ebenso `arccos(a)` und
  `arctan(a)`)
* `arcsin(a) * 180 / pi` : Winkel in Grad, dessen Sinus a ist
* `arctan2(b, a)` : Winkel im Bogenmaß des Punktes mit der x-Koordinate a und der y-Koordinate b
  (Excel: ARCTAN2(a; b))
* `a * 180 / pi` : Winkel a vom Bogenmaß in Grad umgerechnet
* `a * pi / 180` : Winkel a von Grad ins Bogenmaß umgerechnet
* `sinh(a)` : Sinus hyperbolicus von a (ebenso `cosh`, `tanh`, `arcsinh`, `arccosh` und
  `arctanh`)

### Vergleiche
Ein Vergleich ergibt für jeden Zeitpunkt True (wahr) oder False (falsch).
* `a > 100` : True, wo a größer als 100 ist (ebenso `>=`, `<` und `<=`)
* `a == b` : True, wo a gleich b ist
* `a != 0` : True, wo a nicht 0 ist
* `10 < a < 20` : True, wo a zwischen 10 und 20 liegt
* `a.between(10, 20)` : True, wo a zwischen 10 und 20 liegt, einschließlich 10 und 20
* `a > 10 and b > 10` : True, wo beide größer als 10 sind (Excel: UND)
* `a > 10 or b > 10` : True, wo mindestens einer von beiden größer als 10 ist (Excel: ODER)
* `not a > 10` : True, wo a nicht größer als 10 ist (Excel: NICHT)

### Bedingungen, Grenzen, größerer und kleinerer Wert
* `a.where(c > 0, b)` : a, wo c größer als 0 ist, sonst b (Excel: WENN(c > 0; a; b))
* `a.where(a > 0, 0)` : a, wo a größer als 0 ist, sonst 0 (Excel: WENN(a > 0; a; 0))
* `a.where(a > 0)` : a, wo a größer als 0 ist, sonst kein Wert, z. B. um ungültige Werte
  wegzulassen
* `a.clip(0, 100)` : a begrenzt auf den Bereich von 0 bis 100, also werden Werte unter 0 zu 0 und
  Werte über 100 zu 100
* `a.clip(lower=b)` : der größere Wert von a und b (Excel: MAX(a; b))
* `a.clip(upper=b)` : der kleinere Wert von a und b (Excel: MIN(a; b))
* `(a > 0) * a` : ebenfalls a, wo a größer als 0 ist, sonst 0, da beim Rechnen True als 1 und
  False als 0 zählt

### Statistik einer Zeitreihe
Methoden wie `a.mean()` berechnen einen einzelnen Wert aus allen Werten der Zeitreihe a. Verwenden
Sie sie in einer Formel, damit das Ergebnis wieder eine Zeitreihe ist. Solche Methoden sind `mean`
(Mittelwert), `median`, `std` (Standardabweichung), `var` (Varianz), `min`, `max`, `sum`, `count`
(Anzahl der Werte) und `quantile`.
* `a - a.mean()` : Abweichung von a von seinem Mittelwert
* `(a - a.mean()) / a.std()` : standardisierte Werte (z-Werte), also die Abweichung vom Mittelwert
  in Vielfachen der Standardabweichung
* `abs(a - a.mean()) > 3 * a.std()` : True, wo a um mehr als 3 Standardabweichungen von seinem
  Mittelwert abweicht, z. B. um Ausreißer zu finden
* `a / a.max() * 100` : a in Prozent seines größten Wertes
* `(a - a.min()) / (a.max() - a.min())` : a skaliert auf den Bereich von 0 bis 1
* `a / a.sum() * 100` : Anteil jedes Wertes an der Summe aller Werte in Prozent
* `a > a.quantile(0.9)` : True für die höchsten 10 Prozent der Werte
* `a * 0 + a.mean()` : der Mittelwert von a zu jedem Zeitpunkt, z. B. um ihn als Linie in einem
  Diagramm zu zeigen

### Werte im Zeitverlauf
Diese Methoden berechnen zu jedem Zeitpunkt einen Wert aus den Werten davor:
* `a.diff()` : Änderung gegenüber dem vorherigen Wert
* `a.shift(1)` : der vorherige Wert von a
* `a.pct_change() * 100` : Änderung gegenüber dem vorherigen Wert in Prozent
* `a.cumsum()` : laufende Summe von a
* `a.cummax()` : der bisher größte Wert (ebenso `a.cummin()`)
* `a.rolling(5).mean()` : gleitender Mittelwert der letzten 5 Werte (die ersten 4 Zeitpunkte haben
  keinen Wert)
* `a.rolling("1h").mean()` : gleitender Mittelwert der Werte der letzten Stunde (Zeitdauern wie
  `"15min"`, `"1h"` oder `"1D"` werden in Anführungszeichen geschrieben)
* `a.rolling(5).std()` : gleitende Standardabweichung der letzten 5 Werte (ebenso `max`, `min`,
  `sum` und `median` statt `std`)
* `a.ewm(span=10).mean()` : exponentiell gewichteter gleitender Mittelwert, bei dem neuere Werte
  mehr zählen
* `a.resample("1h").mean()` : Stundenmittelwerte mit einem Wert pro Stunde (ebenso `"15min"` oder
  `"1D"` und `sum`, `max` oder `min` statt `mean`)
* `a.resample("1D").sum()` : Tagessummen (Tage von Mitternacht bis Mitternacht in der Zeitzone
  von a, siehe die Beispiele zu Zeitzonen)

### Zeitzonen
Tage beginnen um Mitternacht in der Zeitzone, in der die Zeitreihen laut ihren Metadaten
ausgewertet werden sollen (`default_timezone`), z. B. in deutscher Zeit für Zeitreihen aus einer
Anlage in Deutschland, auch an den Tagen mit 23 oder 25 Stunden, an denen die Sommerzeit beginnt
oder endet. Dasselbe gilt für Uhrzeiten, Wochentage, Wochen und Monate. Dazu werden die Zeitreihen,
die die Formel verwendet, vor der Berechnung in diese Zeitzone umgerechnet. Geben ihre Metadaten
unterschiedliche Zeitzonen an, wird die Formel in UTC berechnet. Zeitreihen ohne Metadaten, z. B.
manuelle Eingaben, werden ebenfalls in UTC berechnet, oder in der Zeitzone der anderen Zeitreihen.
Ist der Eingang zeitzone_aus_metadaten ausgeschaltet (False), werden die Zeitreihen nicht
umgerechnet, sodass die Formel in den Zeitzonen berechnet wird, die sie haben, meist UTC. Das
Ergebnis hat seine Zeitpunkte wieder in UTC, wie die Zeitreihen von Datenquellen, z. B. die
Tagessumme des 28. März deutscher Zeit um 23:00 Uhr UTC am 27. März.

`modify_timezone(a, "Europe/Berlin")` rechnet die Zeitpunkte von a in deutsche Zeit um, z. B. für
Zeitreihen ohne Metadaten. Zeitpunkte ohne Zeitzone werden dann als deutsche Zeit genommen. Andere
Zeitzonen werden wie `"Europe/London"` oder `"UTC"` geschrieben.
* `a.groupby(pd.Grouper(freq="D")).cumsum()` : laufende Summe von a, die jeden Tag um Mitternacht
  wieder neu beginnt
* `a.where(a.index.hour < 6)` : a nur von Mitternacht bis 6:00 Uhr
* `a.where(a.index.day_of_week < 5)` : a nur von Montag bis Freitag
* `modify_timezone(a, "Europe/Berlin").resample("1D").sum()` : Tagessummen für die Tage in
  deutscher Zeit, auch wenn die Metadaten von a keine oder eine andere Zeitzone angeben
* `modify_timezone(a, "UTC").resample("1D").sum()` : Tagessummen für die Tage in UTC

### Fehlende Werte
* `a.fillna(0)` : a mit 0 statt fehlender Werte
* `a.fillna(b)` : a mit den Werten von b statt fehlender Werte
* `a.ffill()` : a mit dem vorherigen Wert statt fehlender Werte
* `a.interpolate(method="time")` : a mit fehlenden Werten auf einer geraden Linie zwischen den
  Werten davor und danach aufgefüllt
* `a.dropna()` : a ohne die Zeitpunkte mit fehlenden Werten
* `a.isna()` : True, wo ein Wert von a fehlt

`a + b` hat keinen Wert, wo ein Wert von a oder b fehlt, und gar keinen Wert, wenn b keine Werte
hat. Mit den folgenden Formeln zählen fehlende Werte stattdessen als 0, wie leere Zellen in Excel:
* `a.add(b, fill_value=0)` : a plus b, wobei ein fehlender Wert von a oder b als 0 zählt. Nur wo
  beide Werte fehlen, fehlt auch das Ergebnis.
* `a.sub(b, fill_value=0)` : a minus b, wobei ein fehlender Wert von a oder b als 0 zählt
* `abcde.sum(axis=1, min_count=1)` : Summe aller verbundenen Zeitreihen zu jedem Zeitpunkt, wobei
  fehlende Werte als 0 zählen. Nur wo alle Werte fehlen, fehlt auch das Ergebnis (bei
  `abcde.sum(axis=1)` ist es dort 0).
* `a.resample("1h").mean().add(b.resample("1h").mean(), fill_value=0)` : Summe der
  Stundenmittelwerte von a und b, z. B. für Zeitreihen mit unterschiedlichen Zeitpunkten. Hat a
  oder b in einer Stunde keine Werte, zählt sein Stundenmittelwert als 0.
* `abcde.resample("1h").mean().sum(axis=1, min_count=1)` : Summe der Stundenmittelwerte aller
  verbundenen Zeitreihen, wobei fehlende Stundenmittelwerte als 0 zählen

### Mehrere Zeitreihen zu jedem Zeitpunkt
`abcde` ist eine Tabelle mit allen verbundenen Zeitreihen als Spalten a, b, c, d und e. Mit
`axis=1` berechnen ihre Methoden einen Wert aus den Werten aller verbundenen Zeitreihen zu jedem
Zeitpunkt. Fehlende Werte werden dabei weggelassen.
* `abcde.mean(axis=1)` : Mittelwert der Zeitreihen zu jedem Zeitpunkt (Excel: MITTELWERT)
* `abcde.std(axis=1)` : Standardabweichung der Zeitreihen zu jedem Zeitpunkt (Excel: STABW.S)
* `abcde.max(axis=1)` : größter Wert zu jedem Zeitpunkt (Excel: MAX)
* `abcde.min(axis=1)` : kleinster Wert zu jedem Zeitpunkt (Excel: MIN)
* `abcde.max(axis=1) - abcde.min(axis=1)` : Differenz zwischen dem größten und dem kleinsten Wert
* `abcde.sum(axis=1)` : Summe der Zeitreihen zu jedem Zeitpunkt, wobei fehlende Werte als 0 zählen
  (Excel: SUMME)
* `abcde.median(axis=1)` : Median der Zeitreihen zu jedem Zeitpunkt (Excel: MEDIAN)
* `abcde.count(axis=1)` : Anzahl der Zeitreihen mit einem Wert zu jedem Zeitpunkt

### Metadaten
Zeitreihen aus Datenquellen wie der hetida Plattform haben Metadaten, z. B. ihre Einheit, die
Anzahl der Nachkommastellen, mit der sie angezeigt werden sollen, und die Properties ihrer
Signale. `meta.a.max` ist das Feld max der Metadaten von a, z. B. die Property max des Signals,
das mit a verbunden ist. Felder, deren Namen Leerzeichen oder andere Sonderzeichen enthalten,
schreiben Sie in eckigen Klammern und Anführungszeichen, z. B. `meta.a["oberer Grenzwert"]`. Auch
hier spielt Groß- und Kleinschreibung eine Rolle. Enthalten die Metadaten ein Feld nicht, nennt
die Fehlermeldung die Felder, die sie enthalten.
* `a > meta.a.max` : True, wo a größer als seine Property max ist
* `a.where(a <= meta.a.max)` : a ohne die Werte, die größer als seine Property max sind, z. B. um
  unplausible Werte wegzulassen
* `a.clip(lower=meta.a.min, upper=meta.a.max)` : a begrenzt auf den Bereich von seiner Property
  min bis zu seiner Property max
* `a / meta.a.max * 100` : a in Prozent seiner Property max
* `(a - meta.a.min) / (meta.a.max - meta.a.min) * 100` : Lage von a im Bereich von seiner
  Property min bis zu seiner Property max in Prozent
* `a.round(meta.a.decimals)` : a gerundet auf die Anzahl der Nachkommastellen seiner Metadaten
* `a.resample("1D").agg(meta.a.default_aggregation_method.lower())` : Tageswerte von a,
  aggregiert mit der Aggregationsmethode aus seinen Metadaten, z. B. der Mittelwert oder die Summe

Auch die Funktionen von hdhelpers für Metadaten können verwendet werden, z. B. für den Zeitraum,
für den die Zeitreihen abgefragt wurden, siehe die
[hdhelpers-Dokumentation](https://hetida.github.io/hdhelpers/index.html#module-hdhelpers.metadata)
(auf Englisch):
* `a > hdhelpers.metadata.get_series_info(a, "max")` : dasselbe wie `a > meta.a.max`
* `a.reindex(pd.date_range(hdhelpers.metadata.get_queried_interval(a)[0], hdhelpers.metadata.get_queried_interval(a)[1], freq=meta.a.data_frequency, inclusive="left"))` :
  a zu allen Zeitpunkten des abgefragten Zeitraums gemäß seiner Datenfrequenz, mit fehlenden
  Werten, wo a keinen Wert hat, z. B. um Lücken zu finden

### Beispiele aus dem Alltag
* `a * 1000` : Kubikmeter in Liter
* `a / 3.6` : km/h in m/s
* `a * 9 / 5 + 32` : Grad Celsius in Grad Fahrenheit
* `a + 273.15` : Grad Celsius in Kelvin
* `a * b / 1000` : elektrische Leistung in kW aus der Spannung a in V und dem Strom b in A
* `b / a * 100` : Wirkungsgrad in Prozent aus der zugeführten Leistung a und der abgegebenen
  Leistung b
* `pi * a**2 / 4` : Fläche eines Kreises mit dem Durchmesser a
* `a * b * c` : Volumen eines Quaders mit der Länge a, der Breite b und der Höhe c

## Gut zu wissen
* **Zeitpunkte**: Werte verschiedener Zeitreihen werden nur zu genau gleichen Zeitpunkten
  miteinander verrechnet. Gibt es einen Zeitpunkt in a, aber nicht in b, hat das Ergebnis von
  `a + b` dort keinen Wert. Haben Ihre Zeitreihen unterschiedliche Zeitpunkte, bringen Sie sie
  zuerst auf gemeinsame Zeitpunkte, z. B. mit
  `a.resample("15min").mean() + b.resample("15min").mean()` oder mit der Komponente "Resample
  Datetime Index using Mean".
* **Tage** beginnen um Mitternacht in der Zeitzone aus den Metadaten der Zeitreihen, sonst in UTC,
  siehe die Beispiele zu Zeitzonen. Der Eingang zeitzone_aus_metadaten schaltet das aus. Das
  Ergebnis ist in UTC.
* **Fehlende Werte**: Wo ein Wert fehlt, fehlt auch das Ergebnis, außer bei Methoden, die fehlende
  Werte weglassen, wie `a.mean()` oder `abcde.mean(axis=1)`. Damit fehlende Werte als 0 zählen,
  schreiben Sie z. B. `a.add(b, fill_value=0)` statt `a + b`, siehe die Beispiele zu fehlenden
  Werten.
* **Unmögliche Berechnungen** wie eine Division durch 0, die Wurzel aus einer negativen Zahl oder
  der Logarithmus von 0 brechen die Berechnung nicht ab. Das Ergebnis fehlt dann zu diesem
  Zeitpunkt oder ist unendlich (NaN oder inf, in der Ergebnisanzeige beide als null).
* **e** ist der fünfte Eingang, nicht die Eulersche Zahl 2,71828... Schreiben Sie `exp(1)` für die
  Eulersche Zahl und `exp(a)` für e hoch a.
* **True und False** als Werte eines Eingangs zählen als 1 und 0.
* **Fehlermeldungen** sagen Ihnen, was Sie ändern müssen, z. B. wenn die Formel b verwendet, aber
  mit dem Eingang b nichts verbunden ist.

## Details
Die Formel wird mit der pandas-Funktion eval berechnet, siehe die
[pandas-Dokumentation von eval](https://pandas.pydata.org/docs/reference/api/pandas.eval.html)
und ihre [unterstützte Syntax](https://pandas.pydata.org/docs/user_guide/enhancingperf.html#supported-syntax)
(alle auf Englisch). Alles, was dort unterstützt wird, kann verwendet werden, insbesondere die
Methoden der Zeitreihen, die pandas Series sind, und von `abcde`, einem pandas DataFrame, siehe
die [pandas-Dokumentation von Series](https://pandas.pydata.org/docs/reference/series.html) und
[von DataFrame](https://pandas.pydata.org/docs/reference/frame.html). Die Funktionen sind `sqrt`,
`exp`, `expm1`, `log`, `log1p`, `log10`, `abs`, `floor`, `ceil`, `sin`, `cos`, `tan`, `arcsin`,
`arccos`, `arctan`, `arctan2`, `sinh`, `cosh`, `tanh`, `arcsinh`, `arccosh` und `arctanh`.
Zusätzlich zu pandas eval können `pi`, `abcde`, `meta`, die Python-Bibliotheken pandas als `pd`,
numpy als `np` und hdhelpers als `hdhelpers` und die Funktion `modify_timezone` von hdhelpers
verwendet werden, siehe die [hdhelpers-Dokumentation](https://hetida.github.io/hdhelpers/) (auf
Englisch), und die Formel darf mit `=` beginnen.

`meta.a.max` liest das Feld max der Metadaten von a, wie es die
[Metadaten-Konventionen](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/)
(auf Englisch) festlegen: Ein Feld wird in der Wertdimension "value", in der Metrik, in
`value_dimensions_shared` und zuletzt in den Properties gesucht, die die Metrik erbt (`inherited`),
in denen die hetida Plattform die Properties von Signalen liefert. Felder, die die Konventionen
für die Zeitreihe selbst festlegen, wie `unit`, werden nicht aus den geerbten Properties genommen.
Die Felder dazu, wie die Werte aufgezeichnet werden, wie `data_frequency`, und `default_timezone`
fallen auf die Metadaten des Datensatzes zurück.

Die Werte der Eingänge werden vor der Berechnung in Gleitkommazahlen umgewandelt. Sie behalten
ihre Namen und Metadaten, sodass z. B. die Funktionen von hdhelpers ihre Metadaten lesen können.
Das Ergebnis hat weder einen Namen noch Metadaten, da die Formel eine neue Größe berechnet.

Die Formel wird in der `default_timezone` der Zeitreihen berechnet, die sie verwendet (mit dem
Rückfall auf die Metadaten des Datensatzes), wenn alle davon, die eine haben, dieselbe angeben,
sonst in UTC. Dazu werden die Zeitpunkte dieser Zeitreihen in diese Zeitzone umgerechnet, außer
sie haben keine Zeitzone oder zeitzone_aus_metadaten ist False. Die Zeitpunkte des Ergebnisses werden in UTC umgerechnet, wenn sie eine
Zeitzone haben, da z. B. generische REST-Adapter nur Zeitreihen in UTC annehmen.
"""

import re

import pandas as pd
import pytest

from hdutils import ComponentInputValidationException, parse_value
from hetdesrun.component.load import import_comp

# "Formula Calculator", the English version of this component, which calculates the formulas. Its
# messages explaining mistakes in formulas are translated here.
formula_calculator = import_comp("1e0e71d0-cd86-4068-bf11-19df7d002737")

MESSAGES = {
    "empty": "Bitte geben Sie eine Formel ein, z. B. (a + b) / 2.",
    "syntax": (
        "Die Formel kann nicht gelesen werden. Bitte prüfen Sie: Sind alle Klammern geschlossen?"
        " Steht ein * zwischen Zahlen und Buchstaben, z. B. 2 * a statt 2a? Dezimalzahlen werden"
        " mit Punkt geschrieben, z. B. 1.5, Vergleiche mit == und != statt = und <>, und Prozent"
        " als / 100, z. B. a * 19 / 100."
    ),
    "power": "Potenzen werden mit ** statt ^ geschrieben, z. B. a**2 für a zum Quadrat.",
    "decimal_comma": "Dezimalzahlen werden mit Punkt statt Komma geschrieben: 1.5 statt 1,5.",
    "not_connected": (
        "Die Formel verwendet {name}, aber mit dem Eingang {name} ist keine Zeitreihe verbunden."
    ),
    "not_connected_e": " Für die Eulersche Zahl 2,71828... schreiben Sie exp(1).",
    "uppercase_input": "Die Eingänge werden kleingeschrieben: {lower} statt {name}.",
    "unknown_name": (
        "{name} ist unbekannt. Die Formel kann die Eingänge a, b, c, d, e (kleingeschrieben), die"
        " Tabelle abcde aus allen, ihre Metadaten wie meta.a.max, Zahlen, die Zahl pi, die Funktion"
        " modify_timezone und die Python-Bibliotheken pandas als pd, numpy als np und hdhelpers"
        " verwenden."
    ),
    "metadata_input": (
        "Nach meta folgt der Eingang, dessen Metadaten die Formel verwendet, z. B. meta.a.max für"
        " das Feld max der Metadaten von a."
    ),
    "metadata_field": (
        "Nach meta.{name} folgt das Feld der Metadaten, das die Formel verwendet, z. B."
        " meta.{name}.max."
    ),
    "no_metadata": (
        "Die mit dem Eingang {name} verbundene Zeitreihe hat keine Metadaten, oder ihre Metadaten"
        " folgen nicht den Metadaten-Konventionen von hetida designer."
    ),
    "unknown_metadata": (
        "Die Metadaten von {name} enthalten kein Feld {field}. Vorhandene Felder: {fields}. Felder"
        " mit Leerzeichen oder anderen Sonderzeichen schreiben Sie wie"
        ' meta.{name}["oberer Grenzwert"].'
    ),
    "nothing_connected": (
        "Die Formel verwendet abcde, aber mit keinem der Eingänge a, b, c, d, e ist eine Zeitreihe"
        " verbunden."
    ),
    "function_without_brackets": "{name} ist eine Funktion und braucht Klammern, z. B. {example}.",
    "unknown_function": "Die Funktion {name} gibt es hier nicht.",
    "replacement": " Schreiben Sie stattdessen z. B. {replacement}.",
    "functions": " Verfügbare Funktionen: {functions}.",
    "multiplication": "Zum Multiplizieren braucht es ein *, z. B. a * (b + c) statt a(b + c).",
    "one_value": "{name} braucht genau einen Wert in den Klammern, z. B. {example}.",
    "two_values": (
        "{name} braucht genau zwei Werte in den Klammern, getrennt durch ein Komma, z. B."
        " {example}."
    ),
    "log_base": (
        " Den Logarithmus zu einer anderen Basis berechnen Sie wie log(a) / log(2) für die Basis 2."
    ),
    "not_numbers": (
        "Die mit dem Eingang {name} verbundene Zeitreihe hat Werte, die keine Zahlen sind."
    ),
    "no_timeseries": (
        "Die Formel berechnet keine Zeitreihe. Verwenden Sie mindestens einen der Eingänge a, b,"
        " c, d, e, z. B. a * 2. Einzelne Werte wie a.mean() können in einer Formel verwendet"
        " werden, z. B. a - a.mean()."
    ),
    "failed": "Die Formel konnte nicht berechnet werden: {error}",
}

GERMAN = formula_calculator.Language(formula_input_name="formel", messages=MESSAGES)


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "a": {"data_type": "SERIES", "default_value": None},
        "b": {"data_type": "SERIES", "default_value": None},
        "c": {"data_type": "SERIES", "default_value": None},
        "d": {"data_type": "SERIES", "default_value": None},
        "e": {"data_type": "SERIES", "default_value": None},
        "formel": {"data_type": "STRING"},
        "zeitzone_aus_metadaten": {"data_type": "BOOLEAN", "default_value": True},
    },
    "outputs": {
        "ergebnis": {"data_type": "SERIES"},
    },
    "name": "Formelrechner",
    "category": "Basic Arithmetic",
    "description": "Berechnet eine Formel wie in Excel mit bis zu fünf Zeitreihen a, b, c, d, e",
    "version_tag": "0.1.0",
    "id": "fbbb2858-c522-43ee-9bf2-4975f2678019",
    "revision_group_id": "92beb254-a16a-428b-b202-ae2645815282",
    "state": "RELEASED",
    "released_timestamp": "2026-11-12T12:10:05+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    formel,
    a=parse_default_value(COMPONENT_INFO, "a"),
    b=parse_default_value(COMPONENT_INFO, "b"),
    c=parse_default_value(COMPONENT_INFO, "c"),
    d=parse_default_value(COMPONENT_INFO, "d"),
    e=parse_default_value(COMPONENT_INFO, "e"),
    zeitzone_aus_metadaten=True,
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {
        "ergebnis": formula_calculator.calculate(
            formel,
            {"a": a, "b": b, "c": c, "d": d, "e": e},
            GERMAN,
            time_zone_from_metadata=zeitzone_aus_metadaten,
        )
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "a",
            "filters": {
                "value": '{"2026-01-01T00:00:00Z": 10.0, "2026-01-01T01:00:00Z": 20.0, "2026-01-01T02:00:00Z": 30.0}'
            },
        },
        {
            "workflow_input_name": "b",
            "filters": {
                "value": '{"2026-01-01T00:00:00Z": 30.0, "2026-01-01T01:00:00Z": 50.0, "2026-01-01T02:00:00Z": 40.0}'
            },
        },
        {
            "workflow_input_name": "c",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "d",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "e",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {"workflow_input_name": "formel", "filters": {"value": "(a + b) / 2"}},
        {
            "workflow_input_name": "zeitzone_aus_metadaten",
            "use_default_value": True,
            "filters": {"value": "True"},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "a",
            "filters": {
                "value": '{"2026-01-01T00:00:00Z": 10.0, "2026-01-01T01:00:00Z": 20.0, "2026-01-01T02:00:00Z": 30.0}'
            },
        },
        {
            "workflow_input_name": "b",
            "filters": {
                "value": '{"2026-01-01T00:00:00Z": 30.0, "2026-01-01T01:00:00Z": 50.0, "2026-01-01T02:00:00Z": 40.0}'
            },
        },
        {
            "workflow_input_name": "c",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "d",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "e",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {"workflow_input_name": "formel", "filters": {"value": "(a + b) / 2"}},
        {
            "workflow_input_name": "zeitzone_aus_metadaten",
            "use_default_value": True,
            "filters": {"value": "True"},
        },
    ]
}


# Unit tests, see https://hetida.github.io/hetida-designer/user_guide/component_writing/unit_testing/
# ruff: noqa: S101


def timeseries(*values):
    return pd.Series(
        values,
        index=pd.date_range("2026-01-01T00:00:00Z", periods=len(values), freq="h"),
        dtype="float64",
    )


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
    )["ergebnis"]

    pd.testing.assert_series_equal(result, timeseries(20.0, 35.0, 35.0), check_freq=False)


def documented_example_formulas(documentation):
    examples = documentation.split("\n## Beispiele\n")[1].split("\n## Gut zu wissen\n")[0]
    return [line.split("`")[1] for line in examples.splitlines() if line.startswith("* `")]


def test_documented_examples_are_those_of_the_formula_calculator():
    formulas = formula_calculator.documented_example_formulas()
    assert len(formulas) > 60

    assert documented_example_formulas(__doc__) == formulas


def test_messages_are_translated():
    def placeholders(messages):
        return {key: sorted(re.findall(r"{(\w+)}", message)) for key, message in messages.items()}

    assert placeholders(MESSAGES) == placeholders(formula_calculator.MESSAGES)


@pytest.mark.parametrize(
    ("zeitzone_aus_metadaten", "days"),
    [(True, ["2026-03-27T23:00:00Z", "2026-03-28T23:00:00Z"]), (False, ["2026-03-28T00:00:00Z"])],
)
def test_time_zone_from_metadata_can_be_switched_off(zeitzone_aus_metadaten, days):
    # from 21:00 to 00:00 in German time
    a = formula_calculator.with_time_zone(
        pd.Series(1.0, index=pd.date_range("2026-03-28T20:00:00Z", periods=4, freq="h")),
        "Europe/Berlin",
    )

    result = main(
        formel='a.resample("1D").sum()', a=a, zeitzone_aus_metadaten=zeitzone_aus_metadaten
    )["ergebnis"]

    assert result.index.tolist() == pd.to_datetime(days).tolist()


def test_all_inputs_are_used():
    result = main(
        formel="a + 10 * b + 100 * c + 1000 * d + 10000 * e",
        **{
            name: timeseries(value)
            for name, value in zip("abcde", (1.0, 2.0, 3.0, 4.0, 5.0), strict=True)
        },
    )["ergebnis"]

    pd.testing.assert_series_equal(result, timeseries(54321.0))


@pytest.mark.parametrize(
    ("formula", "invalid_input", "message_part"),
    [
        ("", "formel", "eine Formel ein"),
        (" = ", "formel", "eine Formel ein"),
        ("(a + b", "formel", "Klammern"),
        ("2a", "formel", "2 * a"),
        ("a * 19%", "formel", "/ 100"),
        ("a <> b", "formel", "!="),
        ("a = b", "formel", "=="),
        ("a^2", "formel", "a**2"),
        ("a * 1,5", "formel", "1.5"),
        ("c * 2", "c", "mit dem Eingang c ist keine Zeitreihe verbunden"),
        ("e * a", "e", "exp(1)"),
        ("A + B", "formel", "a statt A"),
        ("a + x", "formel", "x ist unbekannt"),
        ("a * sqrt", "formel", "sqrt(a)"),
        ("SQRT(a)", "formel", "sqrt(a)"),
        ("WURZEL(a)", "formel", "sqrt(a)"),
        ("LN(a)", "formel", "log(a)"),
        ("LOG(a)", "formel", "log10(a)"),
        ("ROUND(a, 2)", "formel", "a.round(2)"),
        ("MAX(a, b)", "formel", "abcde.max(axis=1)"),
        ("PI()", "formel", "Schreiben Sie stattdessen z. B. pi"),
        ("ATAN2(a, b)", "formel", "arctan2(b, a)"),
        ("quadrat(a)", "formel", "Verfügbare Funktionen: sqrt,"),
        ("MEDIAN(a, b)", "formel", "abcde.median(axis=1)"),
        ("IF(c > 0, a, b)", "formel", "a.where(c > 0, b)"),
        ("log(a, 2)", "formel", "log(a) / log(2)"),
        ("sqrt(1,5)", "formel", "1.5"),
        ("arctan2(a)", "formel", "zwei Werte"),
        ("a(b + 1)", "formel", "a * (b + c)"),
        ("2(a + 1)", "formel", "a * (b + c)"),
        ("a.mean()", "formel", "berechnet keine Zeitreihe"),
        ("abcde * 2", "formel", "berechnet keine Zeitreihe"),
        ("2 + 3", "formel", "berechnet keine Zeitreihe"),
        ("a.Mean()", "formel", "konnte nicht berechnet werden: 'Series' object has no attribute"),
        ('a.rolling("one hour").mean()', "formel", "konnte nicht berechnet werden"),
        ("a.where(x > 0)", "formel", "x ist unbekannt"),
        ("a + x", "formel", "pandas als pd, numpy als np und hdhelpers verwenden."),
        ("quadrat(a)", "formel", ", arctan2, modify_timezone."),
        ("pd(a)", "formel", "Die Funktion pd gibt es hier nicht."),
    ],
)
def test_errors_explain_what_to_change(formula, invalid_input, message_part):
    with pytest.raises(ComponentInputValidationException) as exc_info:
        main(formel=formula, a=timeseries(1.0), b=timeseries(2.0), d=timeseries(3.0))

    assert exc_info.value.extra_information["invalid_component_inputs"] == [invalid_input]
    assert message_part in str(exc_info.value)


def test_values_which_are_not_numbers():
    with pytest.raises(ComponentInputValidationException) as exc_info:
        main(formel="a + b", a=timeseries(1.0), b=pd.Series(["keine Zahl"]))

    assert exc_info.value.extra_information["invalid_component_inputs"] == ["b"]


def with_metadata(series, inherited):
    """The series with metadata following the conventions, in their JSON form"""
    series.attrs = {
        "dataset_metadata": {
            "metric_key": "id",
            "single_metric": "level",
            "queried_metrics": ["level"],
            "ref_interval_start_timestamp": "2026-01-01T00:00:00+00:00",
            "ref_interval_end_timestamp": "2026-01-02T00:00:00+00:00",
            "ref_interval_type": "right_open",
            "ref_data_frequency": "1h",
            "default_timezone": "Europe/Berlin",
        },
        "metrics": [
            {
                "id": "level",
                "name": "Wasserstand",
                "value_dimensions": [
                    {"column": "value", "unit": "m", "measurement": "level", "decimals": 1}
                ],
                "inherited": inherited,
            }
        ],
    }
    return series


@pytest.mark.parametrize(
    ("formula", "invalid_input", "message_part"),
    [
        ("a > meta", "formel", "Nach meta folgt der Eingang"),
        ("a > meta.x.max", "formel", "Nach meta folgt der Eingang"),
        ('a > meta["a"].max', "formel", "Nach meta folgt der Eingang"),
        ("a > meta.a", "formel", "Nach meta.a folgt das Feld"),
        ("a > meta.c.max", "c", "mit dem Eingang c ist keine Zeitreihe verbunden"),
        (
            "a > meta.a.Max",
            "formel",
            (
                "Die Metadaten von a enthalten kein Feld Max. Vorhandene Felder: column,"
                " data_frequency, decimals, default_aggregation_method, default_timezone, id, max,"
                " measurement, name, unit."
            ),
        ),
        ('a > meta.a["oberer Grenzwert"]', "formel", "enthalten kein Feld oberer Grenzwert"),
        ("a > meta.b.max", "b", "Die mit dem Eingang b verbundene Zeitreihe hat keine Metadaten"),
    ],
)
def test_metadata_errors_explain_what_to_change(formula, invalid_input, message_part):
    a = with_metadata(timeseries(1.0), {"max": 2.0})

    with pytest.raises(ComponentInputValidationException) as exc_info:
        main(formel=formula, a=a, b=timeseries(1.0))

    assert exc_info.value.extra_information["invalid_component_inputs"] == [invalid_input]
    assert message_part in str(exc_info.value)
