"""De lange forklaringer, appen viser under "Noter".

Hver note findes paa dansk og engelsk og er skrevet i Markdown. De er med,
fordi halvdelen af fornoejelsen ved en skaev maerkedag er at kunne forklare,
hvorfor tallet overhovedet er sjovt.
"""

from __future__ import annotations

NOTES: dict[str, dict[str, str]] = {
    # ------------------------------------------------------------------
    "sheldon73": {
        "da": """\
### 73 — tallenes Chuck Norris

**Scenen.** I *The Big Bang Theory* — afsnittet "The Alien Parasite
Hypothesis", sæson 4 — spørger Sheldon Cooper ud i lokalet, hvad det bedste
tal er, og tilføjer hjælpsomt, at der kun findes ét rigtigt svar. Raj byder
ind med **5.318.008**. Forkert, fastslår Sheldon: det bedste tal er **73**.

Der bliver stille. Sheldon bemærker, at de sikkert undrer sig over hvorfor.
Leonard og Howard forsikrer ham om, at det gør de ikke.

Han forklarer det alligevel: 73 er det 21. primtal, spejlvendingen 37 er det
12., og 21 er — hold fast i hatten — hvad man får ved at gange 7 og 3.
Leonard giver op og konstaterer, at *"73 is the Chuck Norris of numbers."*
Hvortil Sheldon svarer, at Chuck Norris kun kan ønske sig det: binært er 73
nemlig palindromen 1001001, mens alt, man får ud af at vende Chuck Norris om,
er Sirron Kcuhc.

*Replikkerne er gengivet i sammendrag. Den fulde ordlyd findes på
the-big-bang-theory.com/quotes/quote/1022/.*

**Og Sheldon har ret.** Argumentet bygger på tre lag:

**1. Produktegenskaben.** 73 er det **21.** primtal (2, 3, 5, 7, 11 … og som
nummer 21 kommer 73). Og 21 er netop **7 × 3** — produktet af 73's egne
cifre. Et primtal, hvis plads i rækken er lig med produktet af dets cifre,
er sjældent.

**2. Spejlegenskaben.** Vender man 73 om, får man **37**, som også er et
primtal — og 37 er det **12.** primtal. 12 er 21 vendt om. Spejlingen slår
altså igennem i begge lag på én gang: 73 ↔ 37 og 21 ↔ 12.

**3. Binært.** 73 skrevet i totalssystemet er **1001001** — en palindrom, der
læses ens begge veje. (Det er showets ekstra pointe, ikke en del af den
matematiske definition.)

**Og så blev det alvor.** Matematikere døbte et primtal med egenskab 1 og 2 et
*Sheldon-primtal* og formodede, at 73 er det eneste i hele talrækken. I 2019
beviste **Carl Pomerance og Chris Spicer** det i *Proof of the Sheldon
conjecture* (American Mathematical Monthly 126(8), s. 688–698). Resultatet
gælder for alle primtal — også dem langt ud over, hvad en computer kan nå at
tjekke. 73 er altså beviseligt enestående.

For en god ordens skyld er 73 desuden et **emirp** (et primtal, der også er et
primtal bagfra), et **primtalstvillingetal** sammen med 71, et **Pierpont-primtal**
og et **stjernetal** (6·4·3 + 1 = 73). I morsekode er 73 radioamatørernes
hilsen "best regards" — og også dér en palindrom.

Derfor fejrer denne app runde antal 73'ere: 73 dage, 730 dage, 73 uger,
73 måneder, 73 millioner sekunder og så videre.
""",
        "en": """\
### 73 — the Chuck Norris of numbers

**The scene.** In *The Big Bang Theory* — the episode "The Alien Parasite
Hypothesis", season 4 — Sheldon Cooper asks the room what the best number is,
helpfully adding that there is only one correct answer. Raj offers
**5,318,008**. Wrong, says Sheldon: the best number is **73**.

Silence follows. Sheldon observes that they are probably wondering why.
Leonard and Howard assure him that they are not.

He explains anyway: 73 is the 21st prime, its mirror 37 is the 12th, and 21
is — hold on to your hats — what you get by multiplying 7 and 3. Leonard
gives up and concludes that *"73 is the Chuck Norris of numbers."* To which
Sheldon replies that Chuck Norris only wishes: in binary, 73 is the palindrome
1001001, whereas all you get from reversing Chuck Norris is Sirron Kcuhc.

*The dialogue is given in summary. The full wording is at
the-big-bang-theory.com/quotes/quote/1022/.*

**And Sheldon is right.** The argument has three layers:

**1. The product property.** 73 is the **21st** prime number (2, 3, 5, 7,
11 … and at position 21 you reach 73). And 21 is exactly **7 × 3** — the
product of 73's own digits. A prime whose index equals the product of its
digits is a rare thing.

**2. The mirror property.** Reverse 73 and you get **37**, which is also
prime — and 37 is the **12th** prime. 12 is 21 reversed. So the mirroring
holds on both levels at once: 73 ↔ 37 and 21 ↔ 12.

**3. In binary.** 73 written in base two is **1001001** — a palindrome that
reads the same both ways. (That is the show's bonus flourish, not part of the
mathematical definition.)

**And then it got serious.** Mathematicians named a prime with properties 1
and 2 a *Sheldon prime*, and conjectured that 73 is the only one in the entire
number line. In 2019 **Carl Pomerance and Chris Spicer** proved it in *Proof
of the Sheldon conjecture* (American Mathematical Monthly 126(8), pp.
688–698). The result holds for all primes — including those far beyond what a
computer could ever check. 73 is provably unique.

For the record, 73 is also an **emirp** (a prime that is still prime
backwards), a **twin prime** with 71, a **Pierpont prime** and a **star
number** (6·4·3 + 1 = 73). In Morse code 73 is the radio amateur's sign-off
for "best regards" — and a palindrome there too.

Which is why this app celebrates round counts of 73: 73 days, 730 days, 73
weeks, 73 months, 73 million seconds and so on.
""",
    },
    # ------------------------------------------------------------------
    "stardate": {
        "da": """\
### Stjernedatoer

Der findes **ingen officiel omregning** mellem vores kalender og Star Treks
stjernedatoer. Paramount har aldrig udgivet en formel, og i *The Original
Series* blev tallene i praksis fundet på fra afsnit til afsnit. To
fankonventioner har dog vundet haevd, og appen viser begge:

**TNG-stil.** 1000 stjernedato-enheder svarer til ét år, og stardate 41000.0
er år 2364 — starten på *The Next Generation*, sæson 1. Formlen er
`(år − 2323) × 1000 + årets brøkdel × 1000`. Regnet råt på nutiden giver det
et negativt tal, så de fleste beregnere lægger **340 år** til først: 2026
behandles som 2366, og du lander i 43xxx, midt i TNG-æraen. Det er en
konvention, ikke kanon.

**Film-stil.** J.J. Abrams' film fra 2009 brugte `ÅÅÅÅ.DDD` — årstallet,
punktum, dagen i året. 2233.04 er altså 4. januar 2233. Den er utvetydig og
kræver ingen forskydning.

Stjernedatoen for lige nu står på tælleren øverst, og hver enkelt mærkedag får
sin egen med i kalenderfilens beskrivelse — så du kan føre logbog som en
voksen.
""",
        "en": """\
### Stardates

There is **no official conversion** between our calendar and Star Trek
stardates. Paramount never published a formula, and in *The Original Series*
the numbers were effectively made up episode by episode. Two fan conventions
have stuck, and the app shows both:

**TNG style.** 1000 stardate units equal one year, and stardate 41000.0 is the
year 2364 — the start of *The Next Generation*, season 1. The formula is
`(year − 2323) × 1000 + fraction of year × 1000`. Applied raw to the present
day it gives a negative number, so most calculators add **340 years** first:
2026 is treated as 2366, landing you in 43xxx, the middle of the TNG era. That
is a convention, not canon.

**Film style.** J.J. Abrams' 2009 film used `YYYY.DDD` — the year, a dot, and
the day of the year. So 2233.04 is 4 January 2233. It is unambiguous and needs
no offset.

The stardate for right now sits on the counter at the top, and every single
milestone carries its own in the calendar file's description — so you can keep
a captain's log like a grown-up.
""",
    },
    # ------------------------------------------------------------------
    "cs133": {
        "da": """\
### Cæsium-133 — hvad et sekund *egentlig* er

Et sekund er ikke længere defineret ud fra Jordens rotation. Siden 1967 har
SI-definitionen lydt:

> Ét sekund er varigheden af **9 192 631 770 perioder** af den stråling, der
> svarer til overgangen mellem de to hyperfine niveauer i grundtilstanden af
> cæsium-133-atomet — i hvile, ved det absolutte nulpunkt.

Med andre ord: et cæsiumatom svinger lidt over nine komma to milliarder gange
i sekundet, og vi har besluttet at kalde dét et sekund. Alle atomure i verden
tæller netop de svingninger.

Det betyder, at du kan oplyse din alder i **cæsiumperioder** — og tallene
bliver fuldstændig absurde. Du runder din første trillion perioder, før du er
to minutter gammel. Et helt år er omkring 2,9 × 10¹⁷ perioder, så de runde tal
værd at fejre ligger oppe omkring 10¹⁸ og 10¹⁹.

Den smukkeste af dem: **9 192 631 770 × 10⁹ perioder** er præcis ét
gigasekund. Du fejrer altså det samme øjeblik to gange, i to forskellige
enheder.
""",
        "en": """\
### Caesium-133 — what a second *actually* is

A second is no longer defined by the Earth's rotation. Since 1967 the SI
definition has read:

> One second is the duration of **9,192,631,770 periods** of the radiation
> corresponding to the transition between the two hyperfine levels of the
> ground state of the caesium-133 atom — at rest, at absolute zero.

In other words: a caesium atom oscillates a little over nine point two billion
times per second, and we have decided to call that a second. Every atomic
clock in the world counts exactly those oscillations.

Which means you can state your age in **caesium periods** — and the numbers
turn completely absurd. You pass your first trillion periods before you are
two minutes old. A whole year is about 2.9 × 10^17 periods, so the round
numbers worth celebrating sit up around 10^18 and 10^19.

The prettiest of them: **9,192,631,770 × 10^9 periods** is exactly one
gigasecond. You get to celebrate the same instant twice, in two different
units.
""",
    },
    # ------------------------------------------------------------------
    "jiffy": {
        "da": """\
### Jiffyen — "jeg er der om et øjeblik"

"I'll be there in a jiffy" er engelsk for "jeg er der om et øjeblik". Men en
jiffy er faktisk en rigtig enhed — den er bare ikke den samme for alle:

* **Fysikerens jiffy** (den, appen bruger): den tid, lyset bruger om at
  tilbagelægge **én centimeter** i vakuum. Det er 33,356 **pikosekunder**,
  altså 0,000 000 000 033 356 sekund.
* **Elektrikerens jiffy**: én periode af vekselstrømmen, 20 ms i Danmark
  (50 Hz) og 16,7 ms i USA (60 Hz).
* **Datalogens jiffy**: ét tik af styresystemets ur, typisk 1–10 ms.

Med fysikerens definition er du omkring **10¹⁸ jiffies** gammel, når du fylder
ét år. Så når nogen næste gang siger, de er der om et øjeblik, kan du gøre
opmærksom på, at det giver dem 33 billiontedele af et sekund.
""",
        "en": """\
### The jiffy — "I'll be there in a jiffy"

A jiffy really is a unit of time. It just is not the same unit for everyone:

* **The physicist's jiffy** (the one this app uses): the time light takes to
  travel **one centimetre** in a vacuum. That is 33.356 **picoseconds**, or
  0.000 000 000 033 356 seconds.
* **The electrician's jiffy**: one cycle of mains AC — 20 ms in Europe
  (50 Hz), 16.7 ms in the US (60 Hz).
* **The computer scientist's jiffy**: one tick of the operating system clock,
  typically 1–10 ms.

Using the physicist's definition, you are roughly **10^18 jiffies** old when
you turn one. So the next time somebody says they will be there in a jiffy,
you may point out that this gives them 33 trillionths of a second.
""",
    },
    # ------------------------------------------------------------------
    "carbon14": {
        "da": """\
### Kulstof-14 — uret, der tikker i alt levende

Kulstof-14 er en ustabil udgave af kulstof. Den dannes hele tiden højt oppe i
atmosfæren, når kosmisk stråling rammer kvælstof, og den henfalder igen ved
**beta-henfald**: en neutron i kernen bliver til en proton, og ud ryger en
elektron og en elektron-antineutrino.

> ¹⁴₆C → ¹⁴₇N + e⁻ + ν̄ₑ

Kulstoffet bliver altså til **kvælstof-14** — grundstoffet skifter, men
massetallet 14 bliver stående, fordi en neutron blot er blevet til en proton.

**Halveringstiden er 5730 år.** Henfaldet følger

> N(t) = N₀ · (½)^(t/5730)

og vendt om giver det tiden, før en bestemt andel er tilbage:

> t = 5730 · ln(andel) / ln(½)

**Den eksakte 99 %-dato.** Sætter man andelen til 0,99, får man
**83,08 år** — altså 83 år og godt en måned. Dit gæt på "omkring 83 år" var
rigtigt. Appen regner tallet ud af halveringstiden hver gang, så det er ikke
et afrundet skøn.

| Tilbage | Alder |
|---|---|
| 99,9 % | 8,3 år |
| 99,5 % | 41,5 år |
| **99 %** | **83,1 år** |
| 98,5 % | 124,9 år |

**Og så det vigtige forbehold.** Dine egne kulstof-14-atomer tæller *ikke*
ned, mens du lever. Du spiser og trækker vejret hele tiden, så kroppens
kulstof-14 bliver løbende skiftet ud og holdes på nøjagtig samme niveau som
atmosfærens. Uret starter først, **når man dør** og holder op med at optage
nyt kulstof.

Det er præcis derfor kulstof-14-datering virker: man måler, hvor langt uret er
nået, siden det gik i gang. Derfor er mærkedagene her formuleret om en prøve
kulstof-14, der blev lukket inde den dag, du blev født — den tæller ned, også
selvom du ikke gør.
""",
        "en": """\
### Carbon-14 — the clock ticking inside everything alive

Carbon-14 is an unstable form of carbon. It is created continuously high in
the atmosphere when cosmic rays strike nitrogen, and it decays again by
**beta decay**: a neutron in the nucleus turns into a proton, throwing out an
electron and an electron antineutrino.

> ¹⁴₆C → ¹⁴₇N + e⁻ + ν̄ₑ

So the carbon becomes **nitrogen-14** — the element changes, but the mass
number 14 stays put, because a neutron has simply become a proton.

**The half-life is 5730 years.** Decay follows

> N(t) = N₀ · (½)^(t/5730)

and inverted, that gives the time until a given fraction is left:

> t = 5730 · ln(fraction) / ln(½)

**The exact 99% date.** Put the fraction at 0.99 and you get **83.08 years** —
83 years and a good month. Your guess of "around 83 years" was right. The app
recomputes it from the half-life every time, so it is not a rounded estimate.

| Left | Age |
|---|---|
| 99.9% | 8.3 years |
| 99.5% | 41.5 years |
| **99%** | **83.1 years** |
| 98.5% | 124.9 years |

**And now the important caveat.** Your own carbon-14 atoms do *not* count down
while you are alive. You eat and breathe constantly, so your body's carbon-14
is continuously replaced and held at exactly the same level as the
atmosphere's. The clock only starts **when you die** and stop taking in fresh
carbon.

That is precisely why radiocarbon dating works: it measures how far the clock
has run since it started. So the milestones here are framed around a sample of
carbon-14 sealed away on the day you were born — it counts down even though
you do not.
""",
    },
    # ------------------------------------------------------------------
    "leapseconds": {
        "da": """\
### Skudsekunder — de sekunder, du fik forærende

Jordens rotation er ikke helt regelmæssig. Tidevandet bremser den langsomt,
og store jordskælv og bevægelser i kernen rykker en anelse på døgnets længde.
Atomurene er derimod ubevægelige.

For at UTC ikke skal løbe fra solen, indsætter **IERS** i Paris af og til et
ekstra sekund — klokken bliver **23.59.60**, før den bliver midnat. Det sker
kun sidst i juni eller december og bliver varslet et halvt år før i IERS
Bulletin C.

Siden 1972 er der indsat **27 skudsekunder**, alle positive. Det seneste kom
**31. december 2016**, og pausen siden er den længste i hele rækken — IERS
bekræftede i juli 2026, at der heller ikke kommer et ved udgangen af 2026.

Hvorfor det betyder noget her: når appen regner "en milliard sekunder efter
din fødsel", mener den en milliard *sande* sekunder, altså SI-sekunder på et
atomur. Dit kalenderur har i mellemtiden faaet nogle sekunder forærende. Tallet
i kortet er præcis, hvor mange.

**Og så er tælleren færdig med at tælle.** På den 27. Generalkonference om Mål
og Vægt i november 2022 blev det med resolution 4 besluttet at afskaffe
skudsekundet: senest i 2035 bliver den tilladte afvigelse mellem UTC og
Jordens rotation sat så meget op, at der ikke længere skal indsættes nogen.
Står der 27 i dit kort, er det efter al sandsynlighed det tal, der kommer til
at stå der resten af dit liv.

Der har i øvrigt aldrig været et *negativt* skudsekund, hvor klokken springer
fra 23.59.58 til midnat. Jorden har de seneste år roteret en anelse hurtigere
end før, og derfor blev muligheden for første gang nogensinde diskuteret for
alvor — lige inden man besluttede at holde op med at bruge dem.
""",
        "en": """\
### Leap seconds — the seconds you were given

The Earth's rotation is not quite regular. Tides slow it down, and major
earthquakes and motion in the core nudge the length of the day. Atomic clocks,
by contrast, do not budge.

To stop UTC drifting away from the sun, **IERS** in Paris occasionally inserts
an extra second — the clock reads **23:59:60** before it reaches midnight.
This only ever happens at the end of June or December, and is announced six
months ahead in IERS Bulletin C.

Since 1972, **27 leap seconds** have been inserted, all positive. The most
recent was **31 December 2016**, and the gap since is the longest on record —
in July 2026 IERS confirmed there would be none at the end of 2026 either.

Why it matters here: when the app computes "one billion seconds after your
birth" it means a billion *true* seconds, that is, SI seconds on an atomic
clock. Your wall clock has been handed a few extra seconds along the way. The
number on the card is exactly how many.

**And the counter is now done counting.** At the 27th General Conference on
Weights and Measures in November 2022, Resolution 4 decided to abolish the
leap second: by 2035 at the latest, the tolerated gap between UTC and the
Earth's rotation will be widened so far that none need ever be inserted again.
If your card reads 27, that is in all likelihood the number it will read for
the rest of your life.

There has, incidentally, never been a *negative* leap second, where the clock
jumps from 23:59:58 straight to midnight. The Earth has been spinning slightly
faster in recent years, which is why the possibility was seriously discussed
for the first time ever — just before the decision to stop using them at all.
""",
    },
    # ------------------------------------------------------------------
    "geology": {
        "da": """\
### Dit liv som hele Jordens historie

Hvis hele Jordens historie blev klemt ned i ét menneskeliv, hvornår skete der
så hvad? Jorden er **4,54 milliarder år** gammel, så med en antaget levetid på
100 år svarer ét leveår til godt **45 millioner år** planethistorie.

Det sjove er fordelingen. Jorden var dybest set en bakteriekultur i næsten
hele sin levetid: du når at være encellet gennem barndom, ungdom og
midtvejskrise. Alt det, nogen gider høre om — trilobitter, dinosaurer,
mammutter, mennesker — klemmes sammen i de sidste tolv år. Og hele den
menneskelige civilisation, fra pyramiderne til computeren, ligger i de sidste
**halvanden time** før din 100-års fødselsdag.

Du kan justere den antagne levetid i sidepanelet; hele tidslinjen skalerer
med. Aldrene bruger ICS/IUGS' officielle periodegrænser, ikke runde tal.
""",
        "en": """\
### Your life as the whole history of Earth

If the entire history of the Earth were squeezed into one human life, when
would things happen? The Earth is **4.54 billion years** old, so with an
assumed lifespan of 100 years, one year of your life is about **45 million
years** of planetary history.

The fun is in the distribution. The Earth was essentially a bacterial culture
for nearly all of its existence: you spend childhood, youth and your midlife
crisis as a single cell. Everything anyone actually wants to hear about —
trilobites, dinosaurs, mammoths, humans — is crammed into the last twelve
years. And the whole of human civilisation, from the pyramids to the computer,
falls in the final **ninety minutes** before your hundredth birthday.

You can change the assumed lifespan in the sidebar; the whole timeline scales
with it. The ages use the official ICS/IUGS period boundaries, not round
numbers.
""",
    },
    # ------------------------------------------------------------------
    "constants": {
        "da": """\
### Konstanterne

**π ≈ 3,14159** — forholdet mellem en cirkels omkreds og dens diameter. Det
samme for enhver cirkel i universet, uanset størrelse. Irrationelt, så
decimalerne stopper aldrig og gentager sig aldrig.

**e ≈ 2,71828** — Eulers tal, grundtallet for den naturlige logaritme. Det er
vækstens konstant: renters rente, bakteriekulturer, radioaktivt henfald og
afkøling følger alle e. Funktionen eˣ er sin egen afledede — den eneste, der
kan det.

**φ ≈ 1,61803** — det gyldne snit, (1+√5)/2. Det ene forhold hvor a/b =
(a+b)/a. Forholdet mellem to på hinanden følgende Fibonacci-tal nærmer sig
φ, og netop fordi φ er det "mest irrationelle" tal af alle, er det den bedste
måde at pakke ting, der ikke må ligge oven i hinanden — derfor spiralerne i
solsikker, kogler og ananas.

**τ ≈ 6,28318** — tau, simpelthen 2π. Tilhængerne mener, at τ er den rigtige
cirkelkonstant, fordi én hel omgang er τ radianer og ikke 2π. Tau-dagen er
28. juni.

**√2 ≈ 1,41421** — diagonalen i et kvadrat med siden 1, og det første tal
mennesket beviste var irrationelt. Ifølge legenden blev den pythagoræer, der
røbede beviset, kastet i havet.

**γ ≈ 0,57722** — Euler-Mascheronis konstant. Den måler præcis, hvor meget
den harmoniske række (1 + ½ + ⅓ + …) løber foran den naturlige logaritme.
Efter 300 år ved ingen endnu, om γ overhovedet er rationelt.

**e^π ≈ 23,1407** — Gelfonds konstant. Beviseligt transcendent, hvilket er
bemærkelsesværdigt svært at vise. π^e, derimod, ved man stadig ikke noget om.

**c = 299 792 458 m/s** — lysets fart. Ikke målt, men *defineret*: siden 1983
er metren defineret ud fra den, så tallet er eksakt pr. konstruktion.
""",
        "en": """\
### The constants

**π ≈ 3.14159** — the ratio of a circle's circumference to its diameter. The
same for every circle in the universe, whatever its size. Irrational, so the
decimals never stop and never repeat.

**e ≈ 2.71828** — Euler's number, the base of the natural logarithm. It is the
constant of growth: compound interest, bacterial cultures, radioactive decay
and cooling all follow e. The function e^x is its own derivative — the only
one that manages it.

**φ ≈ 1.61803** — the golden ratio, (1+√5)/2. The one ratio where a/b =
(a+b)/a. The ratio of consecutive Fibonacci numbers converges on φ, and
precisely because φ is the "most irrational" number there is, it is the best
way to pack things that must not overlap — hence the spirals in sunflowers,
pine cones and pineapples.

**τ ≈ 6.28318** — tau, simply 2π. Its advocates argue τ is the true circle
constant, since one full turn is τ radians rather than 2π. Tau Day is 28 June.

**√2 ≈ 1.41421** — the diagonal of a unit square, and the first number humans
proved irrational. Legend says the Pythagorean who leaked the proof was thrown
into the sea.

**γ ≈ 0.57722** — the Euler-Mascheroni constant. It measures exactly how far
the harmonic series (1 + ½ + ⅓ + …) runs ahead of the natural logarithm. Three
hundred years on, nobody knows whether γ is even rational.

**e^π ≈ 23.1407** — Gelfond's constant. Provably transcendental, which is
remarkably hard to establish. π^e, on the other hand, remains a mystery.

**c = 299,792,458 m/s** — the speed of light. Not measured but *defined*:
since 1983 the metre has been defined from it, so the number is exact by
construction.
""",
    },
    # ------------------------------------------------------------------
    "calendar": {
        "da": """\
### Festdagene — hvor de kommer fra

Størstedelen af kataloget regnes **fra dit fødselsøjeblik**: et gigasekund,
10.000 døgn, 1.000 måneder. Dem findes der en formel for.

Festdagene er noget andet. De ligger fast på kalenderen — den 4. maj, den
11.11., den første fredag i november — og det eneste personlige ved dem er,
hvor gammel du er, når de falder. De kan ikke regnes; nogen har bestemt dem.

**Hvor de står.** De skrevne dage ligger i `data/celebrations/` som almindelige
tekstfiler, én pr. kategori, og kan rettes uden at røre et eneste stykke kode.
En post, der ikke kan læses, forsvinder ikke i stilhed — den bliver sprunget
over med en begrundelse, så en tastefejl er til at finde.

**Kilderne.** Popkulturens dage og de fiktive helligdage er samlet fra Atlas
Obscuras kalender over fiktive helligdage og fra lovethynerd.com's nørdekalender.
De pastafarianske kommer fra pastafariancalendar.com, som har en helligdag for
hver eneste dag i året — alle 365 er med. De skæve dage verden over er efterprøvet
enkeltvis mod kilder uden for programmet.

**Én dag er opdigtet.** Tjek-holdbarheden-på-din-worcestershiresauce-dagen den
29. februar findes ikke. Den står i kataloget, fordi den burde findes, og den
siger det selv i sin egen forklaring. Den er den eneste af slagsen.

**De dage, der flytter sig.** Nogle hænger i påskens snor: store bededag er den
fjerde fredag efter påske, Kristi legemsfest den tresindstyvende dag efter,
luilak lørdagen før pinse. Påsken regnes med kirkeårets egen computus, så de
følger med af sig selv. Andre hænger i ugedagen — tredje lørdag i januar,
sidste mandag i maj — og flytter sig dermed også.

**Datoformatet.** En dato som 05.04 er den 4. maj i europæisk rækkefølge og
den 5. april i amerikansk. Det er en reel fælde i et katalog samlet fra
engelsksprogede kilder, så de dage, der *kan* læses forkert, siger det selv i
deres forklaring. De dage, hvor dagen er over den tolvte, kan kun læses én vej
og siger ingenting.
""",
        "en": """\
### The calendar days — where they come from

Most of the catalogue is counted **from the moment you were born**: a
gigasecond, 10,000 days, 1,000 months. Those have a formula.

The calendar days are something else. They sit fixed on the calendar — the
4th of May, 11/11, the first Friday in November — and the only personal thing
about them is how old you are when they fall. They cannot be computed;
somebody decided them.

**Where they live.** The written days sit in `data/celebrations/` as ordinary
text files, one per category, and can be edited without touching a line of
code. An entry that cannot be read does not vanish quietly — it is skipped
with a reason, so a typo is findable.

**The sources.** The pop-culture days and the fictional holidays were gathered
from Atlas Obscura's calendar of the world's fictional holidays and from
lovethynerd.com's nerd calendar. The Pastafarian ones come from
pastafariancalendar.com, which has a holy day for every single day of the
year — all 365 are here. The world's odd days were each checked against
sources outside this program.

**One day is invented.** Check the Date on Your Worcestershire Sauce Day, on
29 February, does not exist. It is in the catalogue because it ought to exist,
and it says so in its own explanation. It is the only one of its kind.

**The days that move.** Some hang on Easter's string: Store Bededag is the
fourth Friday after Easter, Corpus Christi the sixtieth day after, Luilak the
Saturday before Pentecost. Easter is worked out with the church calendar's own
computus, so they follow along by themselves. Others hang on a weekday — third
Saturday in January, last Monday in May — and move for that reason.

**The date format.** A date like 05.04 is 4 May in day-first order and 5 April
in month-first order. That is a real trap in a catalogue gathered from
English-language sources, so the days that *can* be read wrongly say so in
their own explanation. Days where the day is past the twelfth can only be read
one way and say nothing.
""",
    },
    # ------------------------------------------------------------------
    "levels": {
        "da": """\
### De tre niveauer

Kataloget er på godt to tusind mærkedage. Det er flere, end nogen kan bruge på
én gang, og det er grunden til, at hver mærkedag har et **niveau**.

Niveauet er med vilje **ikke** en dom om, hvor god dagen er. Det er en
egenskab ved dagen selv: hvor mange der holder den.

**① Den kender folk.** Du kan nævne den i en frokostpause, og nogen nikker.
Star Wars-dagen, pi-dagen, gigasekundet, murmeldyrets dag.

**② Den har et rigtigt publikum, bare et lille et.** Nogen møder faktisk op.
Håndklædedagen, mol-dagen, VM i mosesnorkling, N7-dagen.

**③ Den findes nærmest kun på en liste.** Ingen fejrer den, men den er sjov at
vide. Repunitdage, de fleste figurfødselsdage, de tre hundrede pastafarianske
dage, hele Jordens år.

Skruen står i **Vælg mærkedage**, fordi niveauet handler om, hvad der
overhovedet er med — ikke om hvilket udsnit af tiden du kigger på. Den skærer
på tværs af alle grupper og er derfor det eneste, der kan bringe to tusind
mærkedage ned i noget, man kan overskue, uden at man først skal vide, hvilke
grupper man ikke vil have.

**Hvordan niveauet bliver sat.** De skrevne festdage har fået deres i hånden og
kan rettes i datafilerne. De udregnede familier får deres af reglen, der laver
dem: talmønstre og Jordens år er altid ③, fordi ingen fejrer en repunitdag — en
regel fandt den. En rund årsdag ligger et hak under dagen, den tæller fra:
100-året for månelandingen bliver markeret, 25-året for en spiludgivelse ikke.
De mærkedage, der regnes fra din fødsel, følger stjernen: en fremhævet
klassiker er ①, resten ②.
""",
        "en": """\
### The three levels

The catalogue runs to a good two thousand milestones. That is more than anyone
can use at once, and it is why every milestone carries a **level**.

The level is deliberately **not** a judgement about how good the day is. It is
a property of the day itself: how many people keep it.

**① People know it.** Mention it over lunch and somebody nods. Star Wars Day,
Pi Day, the gigasecond, Groundhog Day.

**② It has a real audience, just a small one.** Somebody actually turns up.
Towel Day, Mole Day, the Bog Snorkelling Championships, N7 Day.

**③ It barely exists outside a list.** Nobody keeps it, but it is fun to know.
Repdigit days, most characters' birthdays, the three hundred Pastafarian days,
the whole of Earth's year.

The slider sits in **Choose milestones**, because the level is about what is in
at all — not about which slice of time you are looking at. It cuts across every
group, which makes it the only thing that can bring two thousand milestones
down to something readable without your first having to know which groups you
do not want.

**How the level is set.** The written calendar days got theirs by hand and can
be changed in the data files. The computed families get theirs from the rule
that makes them: number patterns and Earth's year are always ③, because nobody
celebrates a repdigit day — a rule found it. A round anniversary sits one step
below the day it counts from: the centenary of the Moon landing gets marked,
the twenty-fifth anniversary of a game release does not. The milestones counted
from your birth follow the star: a highlighted classic is ①, the rest ②.
""",
    },
    # ------------------------------------------------------------------
    "accuracy": {
        "da": """\
### Hvor præcis er den her?

**Det eksakte.** Sekunder, minutter, timer, dage og uger regnes som nøjagtige
multipla af SI-sekunder fra dit fødselsøjeblik. Hvis du har indtastet
fødselstiden rigtigt, er disse mærkedage korrekte på sekundet.

**Kalenderregning.** Måneder og år regnes på vægurets tid, ikke på sekunder.
1000 måneder betyder "samme dag i måneden, samme klokkeslæt, 83 år og 4
måneder senere". Falder dagen ikke i målmåneden (31. januar + 1 måned),
rykkes der til månedens sidste dag.

**Tidszoner og sommertid.** Alt regnes på absolut tid i UTC og vises bagefter
i din valgte tidszone. Det er grunden til, at din 10.000-dages mærkedag kan
have et klokkeslæt, der ligger en time fra fødselstidspunktet: sommertiden
har flyttet væguret, ikke dig.

**Skudsekunder regnes ikke med.** Python regner i SI-sekunder uden
skudsekunder, og det gør appen også. Kortet med skudsekunder viser, hvor mange
der er sat ind, siden du blev født — i praksis op til 27 sekunders forskel for
de ældste brugere, og nul for alle født efter 2016.

**Skønnene.** Hjerteslag, åndedrag, søvntimer, måltider, månemåneder og
kilometer omkring Solen er markeret med ⚠. De afhænger af en sats, du selv
kan skrue på i sidepanelet, og de skal tages som et godt gæt — ikke som en
måling.

**Levetiden.** Beregneren i sidepanelet regner på officielle dødelighedstavler
— Danmarks Statistik og Eurostat — og ikke på en tommelfingerregel. Men en
dødelighedstavle er et øjebliksbillede af, hvordan dødeligheden så ud i det år,
den blev målt, ikke en spådom om din årgang. Tallet er et gennemsnit for alle
med dit køn, din alder og dit land; det siger intet om dig. Faktorerne for
rygning, motion, BMI og alkohol er hentet fra offentliggjorte studier og lagt
oven på hinanden med en dæmpning, fordi de overlapper. Over 99 år er halen
lukket med en konstant dødelighed — der er for få mennesker tilbage i tavlerne
til at sige mere — og derfor er appen for optimistisk om de allerældste.

**Den geologiske tidslinje** forudsætter en levetid, du selv vælger, og er
altså pr. definition et tankeeksperiment.
""",
        "en": """\
### How accurate is this?

**The exact ones.** Seconds, minutes, hours, days and weeks are computed as
precise multiples of SI seconds from your birth instant. If you entered your
birth time correctly, these milestones are right to the second.

**Calendar arithmetic.** Months and years are computed on wall-clock time, not
on seconds. 1000 months means "same day of the month, same time of day, 83
years and 4 months later". If that day does not exist in the target month
(31 January + 1 month), it clamps to the last day of the month.

**Time zones and DST.** Everything is computed on absolute time in UTC and
then displayed in your chosen time zone. That is why your 10,000-day milestone
can land an hour off your birth time: daylight saving moved the wall clock,
not you.

**Leap seconds are not counted.** Python works in SI seconds without leap
seconds, and so does this app. The leap-second card shows how many have been
inserted since you were born — in practice a difference of up to 27 seconds
for the oldest users, and zero for anyone born after 2016.

**The estimates.** Heartbeats, breaths, hours slept, meals, lunar months and
kilometres around the Sun are marked with ⚠. They depend on a rate you can
adjust in the sidebar, and should be read as a good guess, not a measurement.

**The lifespan.** The calculator in the sidebar works from official mortality
tables — Statistics Denmark and Eurostat — not from a rule of thumb. But a
mortality table is a snapshot of how mortality looked in the year it was
measured, not a forecast for your cohort. The figure is an average across
everyone of your sex, age and country; it says nothing about you. The factors
for smoking, activity, BMI and alcohol come from published studies and are
laid on top of each other with a damping, because they overlap. Above 99 the
tail is closed with a constant hazard — there are too few people left in the
tables to say more — which makes the app too optimistic about the very oldest.

**The geological timeline** assumes a lifespan you choose yourself, and is by
definition a thought experiment.
""",
    },
}


def note(key: str, lang: str) -> str:
    """Hent en note paa det valgte sprog."""
    return NOTES[key][lang]


NOTE_TITLES: dict[str, dict[str, str]] = {
    "sheldon73": {"da": "73 — tallenes Chuck Norris", "en": "73 — the Chuck Norris of numbers"},
    "stardate": {"da": "Stjernedatoer", "en": "Stardates"},
    "cs133": {"da": "Cæsium-133 og sekundet", "en": "Caesium-133 and the second"},
    "jiffy": {"da": "Jiffyen", "en": "The jiffy"},
    "carbon14": {"da": "Kulstof-14", "en": "Carbon-14"},
    "leapseconds": {"da": "Skudsekunder", "en": "Leap seconds"},
    "geology": {"da": "Dit liv som Jordens historie", "en": "Your life as Earth's history"},
    "constants": {"da": "Konstanterne", "en": "The constants"},
    "calendar": {"da": "Festdagene — hvor de kommer fra",
                 "en": "The calendar days — where they come from"},
    "levels": {"da": "De tre niveauer", "en": "The three levels"},
    "accuracy": {"da": "Hvor præcis er den her?", "en": "How accurate is this?"},
}
