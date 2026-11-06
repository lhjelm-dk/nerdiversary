# Nørdilæum · Nerdiversary

Finder de skæve mærkedage, en almindelig kalender ikke kender — dit
gigasekund, din 10.000. dag, dit 1234567890. sekund, din 500. fuldmåne — og
lægger dem i din kalender.

Dansk og engelsk. Regnet på sekundet.

## Kør den

```bash
.venv/Scripts/python.exe -m streamlit run streamlit_app.py
```

Eller via `.claude/launch.json` (port 8512).

Første gang:

```bash
python -m venv --system-site-packages .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

## Hvad den kan

**390 mærkedage i 16 grupper.** Alle er slået til fra start undtagen
legenderne. Du vælger selv i fanen *Vælg mærkedage*, hvor et søgefelt leder
gennem navn, forklaring, gruppe og selve tallet — også uden tusindtalsskilletegn,
så `5318008` finder "5.318.008 minutter". Under en søgning ophæves
grupperingen, så de fundne står samlet.

**Jer to.** Udfyld en anden fødselsdato i sidepanelet, og gruppen 👥 vågner:
det ene øjeblik i livet, hvor den ene er dobbelt så gammel som den anden, og
de datoer hvor jeres to aldre lagt sammen runder et pænt tal. Begge dele har
en lukket formel. Kalder vi den ældstes fødsel *a* og den yngstes *b*:

| | ligning | løsning |
|---|---|---|
| forhold *n* | (t − a) = n · (t − b) | t = (n·b − a) / (n − 1) |
| sum *s* | (t − a) + (t − b) = s | t = (a + b + s) / 2 |

Forholdet mellem to aldre falder hele livet, så hvert forhold passeres præcis
én gang. "Dobbelt så gammel" er samme sekund, som den yngste når den alder,
den ældste havde den dag, den yngste blev født. En sum, der er mindre end
aldersforskellen, blev nået før den yngste fandtes, og falder derfor ud.

**Syv pakker** til ét klik, øverst i samme fane. En pakke erstatter hele dit
nuværende valg:

| Pakke | Hvad den tager |
|---|---|
| ⭐ Klassikere | de fremhævede — gigasekundet, 10.000 dage, 1.000 måneder, 1234567890 |
| 🔟 Runde tal | kun de pæne multipla i sekunder, minutter, timer, dage, uger, måneder og år |
| 🧮 Nørd-pakken | konstanter, nørdetal, 73, palindromer, eksotiske enheder |
| 🚀 Rumpakken | Månen, kilometrene om Solen, stjernerne dit fødselslys når, Jordens historie |
| ❤️ Kropspakken | hjerteslag, åndedrag, søvn, måltider, skridt, procent af et liv |
| ⏳ Alt inden for 10 år | alt fra hele kataloget, der falder i det næste årti |
| 🎸 Legenderne | de 30 personer, du kan nå at overhale |

| Gruppe | Indhold |
|---|---|
| ⏱️ Sekunder | 10⁶ til 4×10⁹, 1234567890, 123456789, ni syvere, ni ottere |
| 🕐 Minutter og timer | 525.600 (Seasons of Love), 10!, 2²⁵, 100.000 timer |
| 📅 Dage og uger | 1.000 / 10.000 / 20.000 dage, 1.000 uger, 404 uger |
| 🗓️ Måneder og år | 1.000 måneder, 42 år, π år, τ år, Gelfonds konstant |
| 🔬 Konstanter | π, e, φ, τ, γ, √2, Avogadro, lysets fart, 12! |
| 🧮 Nørdetal | 2ⁿ, 0xBEEF, 0xCAFE, 0xDEADBEEF, Fibonacci, Lucas, Mersenne, Kaprekar 6174, taxitallet 1729, perfekte tal, 1337, 42 |
| 🧪 73 — tallenes Chuck Norris | 73 / 730 / 7.300 dage, uger, måneder, 1001001 (73 binært) og 5318008 |
| 🔢 Gentagne og spejlvendte | repdigits og palindromer i alle enheder |
| ⚛️ Eksotiske enheder | cæsium-133-perioder, jiffies og kulstof-14-henfald |
| 🌙 Månen | synodiske måneder, din 500. fuldmåne |
| 🚀 Rumrejsen | km rundt om Solen, og hvilken stjerne dit fødselslys har nået |
| 🌋 Jordens historie | dit liv som hele Jordens 4,54 mia. år |
| ❤️ Kroppen | hjerteslag, åndedrag, søvntimer, måltider, skridt |
| 📊 Procent af et liv | 25 %, ⅓, 50 %, ⅔, 75 % |
| 👥 Jer to | kræver en anden fødselsdato: aldersforhold og jeres to aldre lagt sammen |
| 🎸 Legender | 30 personer, du kan nå at overhale |

**Levende tællere.** Alderen i sekunder tikker med én decimal. Under den står
aldersstigen — timer, døgn, måneder og år med to decimaler — og dit
fødselstidsstempel, skudsekunder siden fødslen og stjernedato. Timer og døgn
er rene SI-enheder; måneder og år regnes på kalenderen, så tælleren står på
rundt 100,00 netop når mærkedagen "100 måneder" indtræffer.

**Kalender.** Måned, år og agenda, farvet efter gruppe. Åbner automatisk på
måneden for din næste mærkedag. Hold musen over en begivenhed for at se dato,
din alder og forklaringen; klik for at få den stående under kalenderen.

Værktøjstippet er et almindeligt `title`-attribut, sat direkte i komponentens
iframe, som ligger på samme domæne. `streamlit-calendar` kan kun det ene:
sende et kald tilbage til serveren ved `eventMouseEnter`, hvilket ville
genkøre hele scriptet for hver begivenhed, musen strøg hen over. Nu går der
ikke ét kald over nettet. Tilknytningen er en løkke og ikke en
`MutationObserver`, fordi skift af visning giver komponenten en ny nøgle og
bygger hele iframen forfra — en observer ville blive hængende i det dokument,
der ikke er der længere.

**Tidslinje.** Problemet først: 390 mærkedage ligger ekstremt ujævnt i et liv.
Det første million sekunder falder på **dag 11**, det første gigasekund først
ved **31 år**, og sidst i livet kan der gå ti år mellem to. En almindelig,
lineær tidslinje over hundrede år bliver derfor en sort stribe i barndommen og
tom bagefter — og en skydeknap flytter bare det problem. Derfor to skalaer, der
begge går til roden af det:

| Skala | Hvad den gør |
|---|---|
| 🪜 Kaskade | Den geologiske tidsskalas opbygning: Æon → Æra → Periode → Epoke → Alder. Fire rækker over hinanden, hvor hver zoomer ind på et udsnit af rækken over. Du ser helheden og detaljen på samme tid uden at trække i noget. |
| 📈 Logaritmisk | Aksen i tierpotenser fra fødslen, så 10⁶, 10⁷, 10⁸ og 10⁹ sekunder ligger lige langt fra hinanden. Det virker, fordi kataloget i forvejen er bygget på tierpotenser. |

For standardprofilen fordeler kaskaden sig 370 → 143 → 30 → 10 mærkedage ned
gennem rækkerne. Skydeknapperne styrer, hvor i livet der zoomes ind, hvor tæt
den nederste række går, og hvor mange trin der er imellem. Forholdet mellem to
naborækker er det samme hele vejen ned, og mellemrækkerne rundes bagefter til
noget læseligt, så der står "10 år" og ikke "11,4 år".

Etiketterne fordeles på baner med henvisningslinjer, som på Wikipedias
livstidslinjer: kan to navne ikke stå ved siden af hinanden, ryger det ene en
linje længere ned og får en streg tilbage til sit punkt. De fremhævede
klassikere kommer først i køen, så det er de jævne mærkedage, der må nøjes med
deres mærke, når pladsen slipper op; resten tælles op i hjørnet. Bredden af en
etiket må skønnes, for SVG kan ikke måle en tekst, før den er tegnet — skønnet
er efterprøvet mod browserens egne mål på 142 etiketter uden ét overlap.

Tidslinjen viser **hele livet, fortid og fremtid**, uanset hvad *Hvornår* og
*Tidsrum* står på; en tidslinje uden fortid mangler halvdelen af pointen og
hele "du er her". Gruppefilteret og fritekstsøgningen gælder stadig. Over
tegningen står hvor stor en del af livet der er levet, hvor mange mærkedage der
er på hver side — og **det længste stille stræk**, det tidsrum uden en eneste
valgt mærkedag. De tomme år har ingen række i en tabel.

Tegningen er ren SVG og kan hentes ned som fil: en tidslinje over et helt liv
er den eneste af visningerne, man kunne finde på at printe. `st.html` kan ikke
bruges til at vise den — Streamlit renser sin HTML med DOMPurify i ren
HTML-tilstand, og den fjerner hele SVG-træet uden at sige noget. Tegningen går
derfor i en komponent-iframe, hvor intet renses bort, og hvor browserens egne
værktøjstip virker. Rammen måler sig selv bagefter og retter iframens højde,
for hvor høj tegningen bliver, afhænger af skærmens bredde, og det ved Python
ikke.

**Tabel.** Kronologisk, med gruppe, skøn-markør, dato, ugedag, klokkeslæt,
din alder, nedtælling og forklaring. **Hver eneste mærkedag har en
forklaring** — enten skrevet i hånden (230 af dem) eller regnet ud som en
omregning, så kolonnen aldrig står tom. Tre undtagelser er med vilje tomme. Filtrér på
gruppe, tidsrum, fortid/fremtid og fritekst.

**Eksport.** `.ics` til Google Kalender, Outlook og Apple Kalender, CSV til
Google Kalenders egen import, og direkte "læg i Google Kalender"-links.
Begivenhederne har stabile id'er, så en ny import opdaterer i stedet for at
lave dubletter. Filerne bygges bag en cache: Streamlit kører koden i alle
faneblade ved hver gentegning, så uden den blev der bygget 261 KB kalenderfil
hver gang man satte et flueben et helt andet sted i appen.

## Festdagene

Resten af kataloget regner fremad fra fødselsøjeblikket: et gigasekund, 10.000
døgn. Festdagene gør det omvendte. De ligger fast på kalenderen — den 4. maj,
den 11.11., den første fredag i november — og det personlige er, hvor gammel du
er, når de falder. Alle tyve grupper er slået **fra** fra start; de tændes med
ét klik fra en pakke under *Vælg mærkedage*.

De har to kilder, og det er det skarpe snit:

**Skrevet ned** — 291 dage i `data/celebrations/*.json`, én fil pr. kategori:
popkultur, danske skæve dage, fiktive helligdage, figurernes fødselsdage,
science fiction-kanon, videnskabens festdage og gennembrud, teknologiens
mærkedage, nørdernes fødselsdage og nørdehistorie. `utils/celebrations.py`
læser mappen, tjekker hver post og lægger den i sin gruppe. En post, der ikke
kan læses, forsvinder ikke i stilhed — den havner i `Import.skipped` med en
grund.

**Runde årsdage** — 624 dage, udledt af de 104 begivenheder i filerne, der
har et årstal på. En fast dato hører kun med, hvis selve øjeblikket faldt
inden for dit liv, så månelandingen når ingen, der er født efter 1969 — og
det er forkert, for 100-årsdagen i 2069 når mange af dem. Derfor får hver
dateret begivenhed sin 25-, 50-, 75-, 100-, 150- og 200-årsdag.

De årlige dage tæller med: et `since`-årstal i datafilen gør, at Månedagen
den 20. juli 2069 selv siger, at den er 100-året. Tallet kan først regnes
ud, når man ved hvilken forekomst det er, så det sker i `build_label()` og
ikke i filen.

**Regnet ud** — 439 dage, som ingen har skrevet ned, fordi en regel finder
dem. `utils/datepatterns.py` har ni familier: palindromdage, sekvensdage
(01.02.03), repunitdage (11.11.11), binære dage, pythagoræiske dage
(4² + 3² = 5²), kvadratrodsdage, Fibonacci-datoer, produktdage (06.07.42 —
seks gange syv er toogfyrre) og sumdage (12.12.24).

Produkt- og sumdagene er skåret med vilje. Uden et krav om, at de to tal
hører sammen, går de op over fem hundrede gange i et århundrede — flere gange
om måneden — og en mærkedag, der falder så tit, er ingen mærkedag. Nu skal
dagen og måneden være nabotal (produkt) eller det samme tal (sum). Det tog de
to familier fra 1.731 til 84.
`utils/geoyear.py` lægger Jordens 4,54 milliarder år ned i ét kalenderår, hvor
1. januar er dannelsen og 31. december er i dag — dinosaurerne dør den 26.
december, og civilisationen fylder årets sidste 81 sekunder.

Fire slags datoangivelser:

| Skrives | Betyder |
| --- | --- |
| `05-04` | hvert år den 4. maj |
| `11-05 20:59` | hvert år, på klokkeslættet |
| `nth:11:fri:1` | den første fredag i november (`-1` = den sidste) |
| `1969-07-21` | én gang, den dag |

En post med `"since": 1969` tæller fra det år. En engangsdato får automatisk
sine runde årsdage.

En tilbagevendende dag vises som den næste gang, den falder. En fast dato
hører kun med, hvis den ligger inden for det indtastede liv: DOOM's udgivelse
i 1993 er ikke din mærkedag, hvis du er født i 1998.

Datoer, der kan forveksles mellem dansk og amerikansk rækkefølge, siger det
selv. `05.04` er den 4. maj her og den 5. april i USA, og det står i
forklaringen. Står dag og måned ens — `11.11`, `02.02` — siger den det i
stedet. Er dagen over den tolvte, kan den ikke læses forkert, og så tier noten.

## Levetidsberegneren

Resten af appen regner på en *antaget* levetid, man selv skyder på. Beregneren
under **Antagelser og satser** giver et kvalificeret bud at skyde med, og
skyderen starter dér i stedet for på et rundt hundrede.

Tavlerne hentes med `tools/fetch_lifetables.py` og ligger i
`data/lifetables.json` — 36 lande, 240 KB. Danmark kommer fra **Danmarks
Statistik, tabel HISB8** (aldre 0–99, toårsperioder, det nationale tal). De
øvrige kommer fra **Eurostat, demo_mlifetable** (aldre 0–95), så de kan
sammenlignes indbyrdes. Begge er frit tilgængelige uden registrering.

Af hver tavle bruges `lx` — hvor mange af 100.000 nyfødte der stadig lever ved
hver alder. Middellevetiden er bare gennemsnittet af den kurve, men kurven selv
kan svare på mere: hvad medianen er, hvor kvartilerne ligger, og hvad chancen
er for at nå en hvilken som helst alder man taster ind.

Tre ting kan skrues på:

**Periode eller kohorte.** En periodetavle antager, at dødeligheden bliver
stående, som den er i dag. Det gør den ikke. En fyrreårig møder først
dødeligheden ved halvfjerds om tredive år, og til den tid er den lavere.
Kohortetallet regner 1 % årlig bedring ind — en antagelse, der står ét sted i
koden og er til at skrue på. Begge tal vises, så forskellen kan ses: for en
nyfødt dansk dreng er det 80,3 mod 88,0 år, for en halvfemsårig næsten
ingenting.

**Livsstil.** Fire faktorer — rygning, motion, BMI og alkohol — hver med et
risikoforhold fra et navngivet studie, som står i værktøjstippet. De ganges på
dødeligheden i alle aldre. Fordi faktorerne hænger sammen indbyrdes, vises
resultatet som et spænd: den samme udregning med og uden hensyn til, at de
overlapper.

**Halen.** Tavlen stopper ved 95 eller 99. Den forlænges med en konstant
dødelighed, valgt så restlevetiden i sidste alderstrin bliver præcis den,
tavlen selv angiver — så halen er tavlens eget tal og ikke et skøn.

Testene efterprøver det hele mod tavlerne selv: kurven bygges kun af `lx`, og
den skal give den `ex`, statistikkontoret har regnet ud hver for sig. Den
stemmer på 0,1 år for alle 36 lande, begge køn, i hele aldersspændet.

Det er ikke en forudsigelse om et menneske. Det er, hvad der i gennemsnit skete
for folk med de træk i de år, tavlen dækker.

## Sådan regnes der

* **Eksakt:** sekunder, minutter, timer, dage og uger er nøjagtige multipla af
  SI-sekunder fra fødselsøjeblikket.
* **Kalender:** måneder og år regnes på væguret, så 600 måneder rammer samme
  dato og klokkeslæt 50 år senere. 31. januar + 1 måned klemmes til den sidste
  gyldige dag.
* **Tidszoner:** alt regnes i UTC og vises i den valgte zone. Sommertiden
  flytter visningen, ikke øjeblikket — derfor kan en mærkedag ligge en time fra
  fødselstidspunktet.
* **Par:** aldersforhold og summer regnes på absolut tid; aldersforskellen
  vises derimod på væguret. Vær opmærksom på, at `dt1 - dt2` på to
  tidszonebevidste datoer med *samme* `ZoneInfo` giver vægurets forskel, ikke
  den absolutte — derfor går alt gennem UTC først.
* **Skudsekunder** tælles ikke med i regnestykket, men appen viser, hvor mange
  der er indsat siden fødslen (27 i alt siden 1972, senest 31. december 2016).
  Det tal kommer efter al sandsynlighed aldrig højere: skudsekundet afskaffes
  senest i 2035 efter CGPM's resolution 4 fra 2022.
* **Skøn** er markeret med ⚠ og bygger på satser, du selv kan ændre.

## Projektet

```
streamlit_app.py          hele brugerfladen
utils/
  catalog.py              kataloget med mærkedage og pakker
  legends.py              de 30 legender
  geology.py              Jordens tidslinje
  celebrations.py         festdagene — indlæser og tjekker datafilerne
  datepatterns.py         dage, hvor datoen selv går op (palindrom, sum, …)
  geoyear.py              Jordens historie lagt ned i ét kalenderår
  lifetable.py            levetid regnet på officielle dødelighedstavler
  engine.py               udregningen
  timeline.py             kaskaden og den logaritmiske skala, tegnet som SVG
  units.py                enheder og naturkonstanter
  formatting.py           tal, datoer og varigheder på dansk/engelsk
  exporters.py            ICS, CSV og Google-links
  leapseconds.py          skudsekundtabellen
  stardate.py             stjernedatoer
  notes.py                de lange forklaringer
  i18n.py                 brugerfladens tekster
tools/
  fetch_lifetables.py     henter dødelighedstavlerne fra DST og Eurostat
data/
  celebrations/*.json     291 festdage, én fil pr. kategori
  lifetables.json         dødelighedstavler for 36 lande
tests/
  test_engine.py           83 test af datoregningen
  test_timeline.py         80 test af kaskaden og etiketterne
  test_celebrations.py    135 test af festdagene og talmønstrene
  test_lifetable.py       386 test af levetidsberegneren
```

```bash
.venv/Scripts/python.exe tools/fetch_lifetables.py
```

```bash
.venv/Scripts/python.exe -m pytest -q
```

## Noter

`streamlit-calendar` melder ikke sin højde til Streamlit 1.62, så iframen
sættes med én regel CSS i `streamlit_app.py`. Komponenten bruger FullCalendars
gratis licens (CC BY-NC-ND), som dækker privat brug.

## Licens

Koden her er MIT — se [LICENSE](LICENSE). Brug den til hvad du vil, så længe
navnet følger med.

Det gælder koden i dette repo og ikke dens afhængigheder. Særligt
`streamlit-calendar`, som nævnt ovenfor: FullCalendars gratis licens er
CC BY-NC-ND, så kalenderfanen må ikke uden videre køre i et kommercielt
produkt. Resten af appen virker uden den.
