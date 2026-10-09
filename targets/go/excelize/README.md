# go/excelize

[xuri/excelize](https://github.com/xuri/excelize) (v2.11.0 plus 38 commits): a library for
reading and writing Office Open XML spreadsheets, with a formula calculator (`CalcCellValue`)
of some 530 functions written to Excel's documentation. This target tests the calculator on
its mathematical, statistical and probability functions, about 220 of them, its 23 date and
time functions, 30 text functions and 26 logical and information functions: a formula is
written to a cell of a fresh workbook, its range arguments to columns A, B, ..., and the
computed value compared with what Excel documents.

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` and a `hegel/` package of test files:
`go test -count=1 -run TestHegel -v ./hegel`. `TestHegelMath`, `TestHegelStat` and
`TestHegelDist` need `python3` with `numpy` and `scipy` on PATH (the zoo's venv in CI);
`TestHegelDate`, `TestHegelText` and `TestHegelLogic` need `python3` alone.

## Oracles

Python over a JSON-lines subprocess, floats travelling as their shortest round-trip text.
`math` for the elementary functions; `decimal` for Excel's decimal semantics of ROUND,
ROUNDUP, ROUNDDOWN, TRUNC, MROUND, CEILING, FLOOR and their `.MATH`/`.PRECISE` forms (Excel
rounds the 15-digit decimal, not the binary value); exact integers for FACT, COMBIN, PERMUT,
MULTINOMIAL, GCD, LCM, BASE and DECIMAL; ROMAN in its classic form and ARABIC. NumPy for the
descriptive statistics (`ddof` as each function documents, PERCENTILE.INC as `linear`,
PERCENTILE.EXC as `weibull` within [1/(n+1), n/(n+1)]), the sums of products, the regression
functions (`polyfit`), TRIMMEAN (floor(n·percent/2) values off each end); SciPy for the
moments, RANK, the t-, z-, F- and chi-squared tests (T.TEST's p as two-sided·tails/2, Z.TEST
as 1 − Φ, F.TEST two-tailed, CHISQ.TEST with n − 1 degrees of freedom for one row), the
confidence intervals, and every distribution (`norm`, `lognorm`, `t`, `chi2`, `f`, `beta`,
`gamma`, `expon`, `poisson`, `binom`, `nbinom`, `hypergeom`, `weibull_min`, `erf`, `erfc`,
`jv`/`yv`/`iv`/`kv`), with Excel's documented domain rules (arguments truncated to integers,
the errors #NUM!, #DIV/0!, #VALUE!, #N/A by function). A range is "constant" when its minimum
equals its maximum (the numpy standard deviation of eleven copies of -0.17 is not 0). The
library against itself: SUBTOTAL and AGGREGATE against the functions they number,
ARABIC(ROMAN(n, form)) = n for every form, DECIMAL(BASE(n, radix), radix) = n.

The date model is Excel's 1900 system written out in Python: serial 61 is 1 March 1900 and the
real calendar follows (`date(1899, 12, 30) + serial`), serials 1 to 59 are 1 January to
28 February 1900, 60 the fictitious 29 February and 0 the "0 January"; the weekday of a serial is
(serial − 1) mod 7 from Sunday, the range ends at 2958465 (31 December 9999), DATE adds 1900 to
years 0..1899 and normalises the month with divmod, EDATE and EOMONTH clamp to the month's length
(29 days for Excel's February 1900), WEEKNUM's week 1 holds 1 January for the return types 1 to
17 and type 21 is the ISO week, YEARFRAC's bases follow OpenFormula (US 30/360 with the February
rules, actual/actual as Excel's whole-year average, actual/360, actual/365, European 30/360),
DAYS360 and DATEDIF as documented, NETWORKDAYS and WORKDAY (and the `.INTL` forms with weekend
codes and masks) by counting days, TIME modulo a day, DATEVALUE and TIMEVALUE for ISO and
US-slash dates (a two-digit year read as 2000–2029 and 1930–1999, Excel's rule) and 12/24-hour
times.

The text model is Python's `str` with Excel's rules written out: a number in a text context
becomes its General text of at most 15 significant digits (judged between 1E-04 and 1E+15, where
Excel shows plain digits); TRIM removes only spaces and collapses interior runs; CLEAN drops the
characters below 32; PROPER capitalises a letter after a non-letter; LEFT/RIGHT/MID/REPLACE/FIND
count characters (BMP text, where UTF-16 units and characters agree); SEARCH's wildcards `?`, `*`
and the `~` escape become a regular expression; SUBSTITUTE's instance counts non-overlapping
occurrences; FIXED and TEXT round the 15-digit decimal half away from zero (`decimal`), with the
`#,##0`, `0%`, `0.00E+00`, `@`/General and the common date and time formats (`mm` is minutes after
`hh` or before `ss`); VALUE accepts Excel's spellings (grouped thousands, a percent sign, an
exponent, surrounding spaces, ISO and US dates, times) and nothing else; TEXTAFTER and
TEXTBEFORE reject an instance of 0 or beyond the text's length with #VALUE! (Excel's documented
rule) and answer #N/A, or if_not_found, when the delimiter's instance is missing; CHAR/CODE follow
Windows-1252 where it agrees with Latin-1 (1–127, 160–255) and UNICHAR/UNICODE are code points
with the surrogates rejected. The logical model: TRUE/FALSE, non-zero numbers and the texts
"TRUE"/"FALSE" are logical values, other texts #VALUE!; IF's omitted value_if_false is FALSE;
SWITCH compares like `=` (numbers with numbers, texts case-insensitively, never across types);
the IS functions never return errors; ISEVEN/ISODD truncate and reject booleans; N of a text
is 0; TYPE and ERROR.TYPE as documented. Errors are passed as `NA()`, `1/0`, `SQRT(-1)` and
`VALUE("a")`.

## Generator

Numbers of one profile: integers to 1000, decimals of one to three places, multiples of
10^3..10^12, fractions down to 10^-9, quarters, decimals starting with zeros, small integers;
negative 40% of the time.
Series of 1 to 12 values (13 to 60 a tenth of the time) of one profile: small integers, tenths,
0..100, thousandths, thousands; a third drawn from a pool of one to three values, so ties and
constant ranges are common; pairs independent or a noisy linear image. Probabilities in
(0, 1) with the ends, tiny values and 1 − 10^-6 included; degrees of freedom, counts and
shapes from 0 to about 30 with fractional and negative values, and a count of 200; num_digits
from -6 to 8 and fractional; every ROMAN form; radixes 2 to 36 and out of range; the Bessel
orders 0 to 30, arguments to 75. Results are compared at 15 significant digits (Excel's
precision and the calculator's formatting), tighter for the exact functions.
Date serials of six profiles: the quirk region 0..62, the rest of 1900, the far end around
2958465, negatives, 1950..2100 and any year to 9999, a quarter of them with a time fraction;
year/month/day triples with months −20..30 and days −40..70 for DATE; month offsets that reach a
December or its neighbours and month ends for EDATE and EOMONTH; the first days of January and
the last of December with return type 21 for WEEKNUM; the five bases, equal dates and
February-end starts for YEARFRAC; weekend codes, masks and invalid ones, holiday lists with
duplicates and holidays before the span for the workday functions; date and time texts in the
accepted formats with am/pm and out-of-range fields.
Texts of 0 to 12 characters (to 40 a tenth of the time) from an alphabet of letters, digits,
spaces, the wildcard and regular-expression characters, a few Latin-1 letters and the euro sign,
with control characters for CLEAN and TRIM (spliced in as `CHAR(n)`); substrings of the text as
the thing to find or replace; counts −1..14 with fractions; numbers of eight profiles (integers,
cents, millions and beyond, small fractions, thirds, sums like 0.1 + 0.2) wherever a text
function takes a value; TEXT's 29 formats with matching values; VALUE texts in fifteen
spellings (grouped, spaced, percent, exponent, Go-only forms, garbage, dates with four- and
two-digit years and invalid ones, times); logical
arguments as booleans, small numbers, fractions and the texts TRUE/FALSE/true/1/0/x; error
values for the information functions and the result branches.

## Properties

- `TestHegelMath`: 70 functions of one to six numbers (rounding, elementary, trigonometric
  and hyperbolic, combinatorial, number-theoretic, BASE/DECIMAL, ROMAN/ARABIC, sums and
  products) agree with the oracle to 1e-12, or return the documented error; the two round
  trips. A case is a record of the function and its arguments drawn from per-function
  generators built from the argument kinds, with the shape of every recorded Math bug drawn
  by default (see "Drawn shapes" below) and named by the classifier before the library is
  called; it fails every run (basin SEC, the first entry of its table, excelize/2).
- `TestHegelMath…`: twenty narrow properties, one per Math bug (excelize/2, 6, 7, 8, 9, 10,
  15, 17, 18, 19, 21, 23, 29, 31, 33, 34, 79, 80, 81, 82), each drawing random contents of
  its bug's shape, judged by the same judge, and the neighbouring region past it; each fails
  every run naming its bug and passes under `HEGEL_NO_KNOWN=1`.
- `TestHegelStat`: 76 functions over ranges (descriptive statistics, percentiles, quartiles,
  ranks, sums of products, regressions, correlations, tests and confidence intervals, and the
  `A` forms and legacy names) agree with the oracle to 1e-9, or return the documented error;
  SUBTOTAL and AGGREGATE agree with the function they number. A case is a record of the
  function, its arguments (ranges drawn as counted series of one profile, the second range a
  function of the first) and the SUBTOTAL/AGGREGATE numbers it also checks, with the shape of
  every recorded Stat bug drawn by default (see "Drawn shapes" below) and named by the
  classifier before the library is called; it fails every run (basin HARMEAN of a range, the
  first entry of its table, excelize/3).
- `TestHegelStat…`: fourteen narrow properties, one per Stat bug (excelize/1, 3, 4, 5, 10, 12,
  15, 17, 20, 21, 22, 24, 26, 83), each drawing random contents of its bug's shape, judged by
  the same judge, and the neighbouring region past it; each fails every run naming its bug and
  passes under `HEGEL_NO_KNOWN=1`.
- `TestHegelDist`: 73 distribution functions (densities, cumulatives, inverses, legacy
  names, GAMMA, GAMMALN, PHI, GAUSS, the error and Bessel functions) agree with SciPy to
  1e-8 (1e-6 for the Bessel functions, 1e-12 for the inverse normals), or return the
  documented error. A case is a record of the function and its arguments from per-function
  generators over the argument kinds, with the shape of every recorded Dist bug drawn by
  default (see "Drawn shapes" below) and named by the classifier before the library is
  called; it fails every run (basin NORM.S.INV, the first entry of its table, excelize/12).
- `TestHegelDist…`: sixteen narrow properties, one per Dist bug (excelize/10, 11, 12, 13,
  14, 15, 16, 21, 25, 26, 27, 28, 30, 32, 84, 85), each drawing random contents of its bug's
  shape, judged by the same judge, and the neighbouring region past it; each fails every run
  naming its bug and passes under `HEGEL_NO_KNOWN=1`.
- `TestHegelDate`: 23 date and time functions (DATE, DAY, MONTH, YEAR, WEEKDAY, WEEKNUM,
  ISOWEEKNUM, EDATE, EOMONTH, DAYS, DAYS360, DATEDIF, NETWORKDAYS, NETWORKDAYS.INTL, WORKDAY,
  WORKDAY.INTL, YEARFRAC, TIME, HOUR, MINUTE, SECOND, DATEVALUE, TIMEVALUE) agree with the
  1900-system model to 1e-12, or return the documented error, and never panic. A case is a
  record of the function and its arguments from per-function generators over the kinds
  (serials of six profiles, the quirk region first; days, weekends, holidays near the start,
  texts), with the shape of every recorded Date bug drawn by default (see "Drawn shapes"
  below) and named by the classifier before the library is called, by replicas of the
  library's calendar beside the model; it fails every run (basin MONTH(0), the first entry of
  its table and the first serial profile, excelize/38).
- `TestHegelDate…`: sixteen narrow properties, one per Date bug (excelize/35 to 47) and one
  each for the Date instances of 15 and 21, each drawing random contents of its bug's shape,
  judged by the same judge, and the neighbouring region past it; each fails every run naming
  its bug and passes under `HEGEL_NO_KNOWN=1`.
- `TestHegelText`: 30 text functions (CHAR, CODE, UNICODE, UNICHAR, CLEAN, TRIM, UPPER, LOWER,
  PROPER, LEN, LEFT, RIGHT, MID, REPT, CONCAT, CONCATENATE, TEXTJOIN, EXACT, FIND, SEARCH,
  REPLACE, SUBSTITUTE, FIXED, TEXT, TEXTAFTER, TEXTBEFORE, VALUE, T, N, VALUETOTEXT) return the
  model's text, number or boolean exactly, or the documented error. A case is a record of the
  function and its arguments from per-function generators over the kinds (texts of an
  alphabet, substrings, numbers for a text context, counts, formats, logical values, VALUE's
  spellings), with the shape of every recorded Text bug drawn by default (see "Drawn shapes"
  below) and named by the classifier before the library is called, by replicas of the
  library's text rules beside the model; it fails every run (basin CHAR(0), the first entry of
  its table, excelize/59).
- `TestHegelLogic`: 26 logical and information functions (AND, OR, XOR, NOT, IF, IFS, SWITCH,
  IFERROR, IFNA, the IS functions, TYPE, ERROR.TYPE, N, T, NA, TRUE, FALSE) agree with the model;
  the same record and classifier, with the shape of every recorded Logic bug drawn by default;
  it fails every run (basin IF(2,0): the first entry of its table and the first alternative
  of IF's arguments, excelize/69).
- `TestHegelText…`, `TestHegelLogic…`: thirty-three narrow properties, one per Text and Logic
  bug (excelize/48 to 78) and one each for the Text instances of 15 and 21, each drawing random
  contents of its bug's shape, judged by the same judge, and the neighbouring region past it;
  each fails every run naming its bug and passes under `HEGEL_NO_KNOWN=1`.
- `TestHegelPin…`: one per recorded bug, asserting the Excel behaviour; expected failures.

## Bugs

Eighty-five, recorded in `bugs.toml`. Four crash or destroy the result outright: PERCENTILE.EXC
and QUARTILE.EXC panic with an index out of range for k outside (1/(n+1), n/(n+1)) (excelize/1);
SEC returns the cosine (2); HARMEAN of a range is always #N/A (3); AVEDEV takes a range as one
value (4). Several lose most digits: the inverse searches of CHISQ.INV.RT, CHIINV and GAMMA.INV
return their bound 5·mean (every df ≥ 30 gives 5·df), and BETA.INV's runs to 0 or 1 for shapes of
0.1 (13); cumulative GAMMA.DIST is a 33-term series that collapses beyond twice the mean
(GAMMA.DIST(75,15,1,TRUE) = 0.00035) (27); BESSELJ diverges from x = 50 and BESSELY is 1% off from
x = 10 (28); the one-pass variance in VAR, VARP, STDEVP and friends (STDEVP of nine 31.2s is 4e-7,
of 48 0.005s #NUM!) (22); NORM.S.INV is Acklam's approximation unrefined, 1e-9 (12); the T.INV
family converges to an absolute tolerance (26); the cumulative normal 0.5(1 + erf) flushes below z
≈ -8.3 (11). Wrong formulas: CORREL and the SUMX functions drop every pair containing a 0 (5);
COMBIN rounds its floating product up, COMBIN(20,18) = 191 (6); cumulative HYPGEOM.DIST sums
impossible outcomes and exceeds 1 (14); CEILING.MATH and FLOOR.MATH misread the mode and the sign
of significance, and FLOOR(0,-1) is #NUM! (9); the zero-variance checks compare sums of rounding
noise with 0 or test the covariance, and T.TEST type 2 of two constant ranges is 0 (24); ODD(0.5)
= 3 (7); a fractional num_digits is used as a power of ten (8); ROUNDDOWN, TRUNC, MROUND and the
FLOOR family round the binary quotient, ROUNDDOWN(0.0031,5) = 0.00309, FLOOR(5460.2,0.2) = 5460,
MROUND(0.15,0.1) = 0.1 (29); TRUNC returns the number itself when its fractional digits are small,
TRUNC(3.0318,1) = 3.0318 (33); PERCENTRANK's significance is decimal places, not significant
digits (20); DEGREES(0) is #DIV/0! and ATAN2(0,0) is 0 (31). Overflows: the discrete distributions
from 171 trials and the F.DIST and GAMMA.DIST densities from 342 degrees of freedom or from x = 20
at df1 = 200 (32), GAMMALN from 172 (30), COTH at 710 and FISHERINV at 355 (17); GAMMA rejects
negative arguments (16). Contract: infinite results come back as the text +INF/-INF instead of
#NUM! (10); integer arguments are not truncated (15); ROMAN, BASE, DECIMAL, COMBIN, PERMUT and
MULTINOMIAL accept out-of-range arguments (18, 19, 23); a dozen domain ends are the wrong way
round (25); error codes differ from the documented ones in some 20 functions (21); a negative zero
is formatted as -0 (34).

Found by the rewritten Math property (79–82): COMBINA(0,0) is 0 (79); TRUNC floors a negative
fractional num_digits, TRUNC(685,-1.5) = 600 (80); TRUNC converts the scaled number to an
int64 and overflows, TRUNC(123456.789,15) = -9223.37203685478 (81); DECIMAL strips a 0x prefix
in every radix, DECIMAL("0x1F",16) = 31 where X is no hexadecimal digit and DECIMAL("0x1F",36)
= 51 where the text is the base-36 number 42819 (82). Found by the Stat property at a thousand
cases: GEOMEAN is PRODUCT^(1/COUNT) and overflows to +INF for a long range of large values,
GEOMEAN(1E+200,1E+200) = +INF, or underflows to #NUM! (83); the property reached it at its
natural rate (about one case in a thousand) until part 2a drew the shape.

Found by the rewritten Dist property (84, 85): the inverse F is (1 / BETA.INV(1 - p) - 1) · d2/d1
and cancels for a tiny quantile, F.INV(0.0000000001,1,1) = 0 (want 2.47E-20) and
FINV(0.999999,1,38) is 2e-3 off (84); the binomial densities multiply a coefficient by two
powers and a power underflows while the value is representable, BINOM.DIST(41,163,0.998,FALSE)
= 0 (want 2.97E-291), NEGBINOMDIST(120,50,0.998) = 0 (want 1.26E-281) (85).

Dates and times (35–47): EDATE panics with an index out of range for a December after the 28th
reached through a multiple of twelve months (40) and lands a year early whenever the month sum
is 12 to 23, EDATE(DATE(2020,12,15),0) is 15 December 2019 (39); the serials 0 to 60 are placed
on the real calendar a day before Excel's (MONTH(1) = 12), DATE is a day late in January and
February 1900 unless the year is literally 1900, WEEKNUM counts 1900 from a Monday 1 January
where Excel's is a Sunday (the Monday-start return types a week short), DAY between 60 and 61
is the real 28 February, and DATEVALUE of the phantom 29 February 1900 is #VALUE! (38); DAY of the first sixty serials is serial mod 31 with the fraction
(DAY(31) = 0, DAY(2.5) = 2.5) (35); DATE does not add 1900 to a year below 1900 and accepts a
negative one (37); WEEKNUM's return type 21 is not the ISO week where the ISO year differs (44);
YEARFRAC does not swap a start after the end (42) and skips the 31st-to-30th rule after a
February start (43); WORKDAY backwards skips only the holidays before the first one found (46);
NETWORKDAYS and WORKDAY count a holiday listed twice as two (45); TIME does not wrap at 24 hours
(41). Contract: serials beyond 9999 and DATE results outside the range are accepted, DATEDIF
alone accepts a negative serial, and EDATE and EOMONTH return 0 for a result before 1900 (36);
YEARFRAC of equal dates, WORKDAY.INTL of 0 days and DATEDIF of equal dates return before
checking the basis, the weekend argument (any invalid mask too) or the unit (47). Shared with
the other properties: WEEKDAY's return type, the weekend numbers of NETWORKDAYS.INTL and
WORKDAY.INTL and DATEDIF's unit are #VALUE! where Excel documents #NUM! (21); TIME keeps a
fractional argument and WORKDAY a fractional count below 1 moves a weekend start (15).

Text (48–68, 77, 78): TEXTAFTER and TEXTBEFORE panic with a slice bound below zero when a
backward search reaches a delimiter at the start of the text and wants another (77) and skip an
adjacent delimiter when searching backwards (78); a number reaching a text function is formatted with Go's `%g`, so a million
becomes `1e+06`, 1/3 has 16 digits and 0.1 + 0.2 is `0.30000000000000004` (48); REPLACE slices
bytes and splits non-ASCII characters into invalid UTF-8, and accepts a negative count (57); MID
appends a NUL when the range ends one past the text (49); TRIM neither collapses interior spaces
nor spares tabs (50); SUBSTITUTE with an empty old_text inserts new_text everywhere (53); FIXED
defaults to the number's own decimals instead of two (54), drops the thousands separators for
any third argument, reading the flag's type (55), and rounds the binary value through an int that
overflows (56); CODE and UNICODE return the first UTF-8 byte (58); UNICHAR rejects everything
above 55295 (60); FIND treats ? and * as wildcards (61) while SEARCH lacks the tilde escape and
leaks regular-expression syntax (62); TEXTAFTER/TEXTBEFORE cut at byte offsets (65) and return ""
instead of #N/A when the delimiter is missing (66); VALUE takes Go's number spellings (0x10, 1_000,
inf, misplaced commas), rejects surrounding spaces and turns an invalid date text into 0 (67);
TEXT rounds the binary value (68);
REPT rejects a number (51) and builds texts beyond the cell limit (52); CHAR(0) is a NUL (59);
FIND accepts a start of 0 (63); TEXTJOIN wants a literal boolean (64). Logical (69–76): IF and IFS
treat only the number 1 as TRUE, IF(2,1,0) = 0 (69); ISEVEN is TRUE for every odd number except 1
(74); AND and OR stop reading their arguments at the first decisive one and miss errors (72); IF
returns a boolean result as 1/0 and an error result as text (71) and "" instead of FALSE when
value_if_false is omitted (70); ISTEXT("1") is FALSE, N("1") is 1, ISLOGICAL("TRUE") and
ISNUMBER(TRUE) are TRUE (75); SWITCH compares texts (76); the logical text coercions differ from
function to function (73). Shared with the other properties: ISEVEN of an error is #VALUE!
instead of the error, and IFS of a non-logical text is #N/A instead of #VALUE! (21); TEXTAFTER
and TEXTBEFORE compare a fractional instance untruncated with the text's length (15).

## Drawn shapes (every property, parts 1 to 4 of the rewrite)

`TestHegelMath` follows the zoo's standard: nothing steers off a recorded bug by default. The
argument kinds are package-level generators of weighted alternatives, the simplest first, and
every Math bug's shape is one of them at a solid weight — ODD in (0, 1) (7), a fractional
num_digits (8), significance 0 and the mode and negative-significance forms of CEILING.MATH and
FLOOR.MATH (9), the arguments whose true result is infinite, LN(0), ATANH(1), FACT(171), EXP and
SINH overflowing, MULTINOMIAL and SERIESSUM overflowing (10), fractional counts (15), COTH at
710 and under 0.01 (17), ROMAN outside 0..3999, a form outside 0..4 and the form TRUE (18),
BASE's min_length outside 0..255, a number outside 0..2^53 and DECIMAL's radix 0 (19), the
error-code cases (21), negative counts (23), DEGREES(0) and ATAN2(0,0) (31), a 0x prefix for
DECIMAL (82), a negative fractional num_digits and a num_digits that overflows TRUNC (80, 81),
zero counts for COMBINA (79), SEC itself (2) — or a relation between the drawn values that the
generator selects with a filter over a Go-side exact-decimal model of the function (the binary
quotient or product within rounding of an integer, 29; TRUNC's shortcut, 33; COMBIN's floating
product rounding up, 6). The classifier `mathShape` names the bug from the case and the
oracle's verdict before the library is called, the most specific shape first (80 and 81 before
33 and 29, 82 before 21, 79 before 21 and 23); every comparison is made and a mismatch fails
naming the shape. A negative zero (34) is the shape of one check on the result's text, failing
by default where the true result is 0 and the library prints -0 (the rounding functions,
QUOTIENT and PRODUCT of a small negative). Under `HEGEL_NO_KNOWN=1` the alternatives have weight
zero, the relations are filtered out, the -0 check is dropped, and the property passes (at
three thousand cases: 0 mismatches, 2.4% of the cases filtered or skipped). Per thousand cases
by default, 86 mismatch: 21 in 27, 34 in 10, 8 in 9, 2 and 19 in 7, 10 in 6, 18 and 82 in 4,
29 in 3, 6, 17 and 23 in 2, 15 and 7 in 1, 31, 33 and 79 under one, 80 one in thirty thousand
and 81 none in thirty thousand (the long num_digits alternative is at the tail of its choice;
their narrow properties reach them every case). Model facts that are not gates: ACOT to 1e-9,
the binary sums to 1e-12 of the largest term, COMBINA with n < k, MROUND with multiple 0 and
SECH/CSCH beyond 700 not judged by the oracle.

`TestHegelStat` (part 2a) draws the same way: the ranges are counted series of one profile
(integers, tenths, thousandths, thousands, or a pool of one to three values repeated, so that
ties and constant ranges are common), the second range a function of the first (the same
length, a noisy linear image of it, or another length), and every Stat bug's shape is an
alternative at a solid weight — k outside [1/(n+1), n/(n+1)] or at n/(n+1) for PERCENTILE.EXC,
QUARTILE.EXC and AGGREGATE 18/19, which panics (1), the range form of HARMEAN (3, every case:
the literal form is the region past it) and of AVEDEV (4), a 0 planted in a pair for CORREL
and the SUMX functions (5), a fractional size, quart or significance (15), FISHERINV at 355
(17), FISHER at 1, a literal HARMEAN of a non-positive, a PERCENTILE k outside [0, 1],
STANDARDIZE with a standard deviation of 0 or below, STEYX with constant known_x, T.TEST and
COVARIANCE.S of ranges too short (21), a range whose exponents sum past 308 or below -308 for
GEOMEAN (83) — or a relation decided by a replica of the library's arithmetic in Go, since
the oracle cannot be asked at draw time: SKEW.P of a constant range whose one-pass variance
comes out exactly 0 is -INF (10), the one-pass variance of a narrow range off the two-pass
value by more than the tolerance (22, with STEYX's one-pass sums), a constant range whose
mean is inexact in binary passing the zero-variance checks and a covariance of exactly 0 or
constant known_y in the regressions (24), a PERCENTRANK result below 0.1 whose truncation to
significance decimal places differs from significant digits (20, an exact rational rank
model), a binary floor of an exact decimal rank (29). The precision of CONFIDENCE and
CONFIDENCE.NORM (12, the inverse normal's 1e-9) is the shape of one check: the result is
judged to 1e-10 and a mismatch within 1e-8 fails naming 12; CONFIDENCE.T is the same at
1e-7 (26), its region alpha ≥ 0.99 drawn deliberately. The classifier `statShape` names the
bug from the case and the oracle's verdict (3 before 21 for HARMEAN, the replica's verdict
deciding 10 against 22 and 21 against 24). Under `HEGEL_NO_KNOWN=1` the alternatives have
weight zero, the relations are filtered out, the precise checks are relaxed to 1e-8 and 1e-7,
and the property passes (at three thousand cases: 0 mismatches, one SUBTOTAL of a shared
narrow range skipped, at most 17 cases per function filtered). Per thousand cases by default,
95 mismatch: 12 in 26, 3 in 13, 1 in 12, 5 and 21 in 10, 15 in 7, 4 in 6, 22 in 5, 24 in 4,
20 in 2, 17, 26 and 83 in 1, 10 and 29 under one. Model facts that are not gates: the
tolerances of `hzStatTol`; LARGE and SMALL with a fractional k, MODE with a tie, a PERCENTRANK
rank within 1e-9 of a digit boundary not judged by the oracle.

`TestHegelDist` (part 2b) draws the same way: the standard scores, locations, scales,
probabilities, degrees of freedom, shapes and counts are package-level kinds, each
function's arguments a tuple of them with the bug's region a one-in-ten alternative
(`withShape`), off under NO_KNOWN — the far tail of the normal from z = -5.6 down, where
0.5(1 + erf(z/√2)) has lost its digits, and of LOGNORM.DIST through ln(x) (11; the F and
negative-binomial cumulatives below 1e-8 are named by a replica of the reflected incomplete
beta tail), a fractional df, count or Bessel order of 2.5 and up, and a df below 1 (15),
GAMMA of a negative non-integer (16), the domain ends (25: BETA.INV at 1, F.INV at 0,
CHISQ.DIST.RT at 0, the CHISQ.DIST density at 0 with df above 2, BINOM.INV at 0 and 1,
POISSON with mean 0, a standard deviation of 0, a negative x for CHIDIST with an even df or
df 1 and for WEIBULL, s2 below s), the error-code cases (21: GAMMA at 0 and the negative
integers, the inverse normals at 0 and 1 and beyond, a negative standard deviation, WEIBULL
with beta 0, POISSON with a negative mean), GAMMALN past 171.62 (30), counts above 170 and
the F, gamma and Poisson densities whose factors overflow while the true density is
representable (32), a hypergeometric support starting above 0 whose spoiled sum exceeds the
tolerance (14, by a replica of the sum with the library's fact of a negative), the
cumulative GAMMA.DIST where the library's 33-term series differs from the converged value
(27, by a replica of the series), BESSELJ beyond |x| = 25.25 + 0.4·max(0, n − 5) and BESSELY
beyond x = 5 (28, measured on a half-step grid), the inverse searches CHISQ.INV.RT, CHIINV,
GAMMA.INV and GAMMAINV as functions (13, off the table under NO_KNOWN) and BETA.INV's flat
region of small equal shapes, infinities (10: the CHISQ.DIST density at 0 with df 1, BESSELK
and BESSELY at a small x and a high order, LOGNORM.INV overflowing), a tiny F quantile with
q·d1/d2 below 5e-10 (84) and a binomial power underflowing while the value is representable
(85, by a replica of the powers). The precision of the inverse normals (12, 1e-9 against
1e-12) and of the T inverses (26, 1e-7 against 1e-12) is the shape of one check: judged at
the model's tolerance, a mismatch within the relaxed one fails naming the bug, and under
NO_KNOWN the relaxed tolerance stands. The classifier `distShape` orders 13 before 27 and 25,
30 and 32 before 10, 32 before 85, 84 before 11 and 25. Under `HEGEL_NO_KNOWN=1` the property
passes (at three thousand cases: 0 mismatches, no case skipped; at most 33 cases per function
filtered). Per thousand cases by default, 181 mismatch: 12 in 84, 13 in 50, 15 in 20, 11 in
19, 21 in 10, 26 in 9, 28 in 8, 32 in 7, 25 and 85 in 4, 14 and 84 in 3, 10 in 2, 30 under
one, 16 and 27 one in three thousand. Not shapes, found by the drawn regions: FINV at 1 and 0 are right
(only F.INV is 10 at 1 and 25 at 0), CHIDIST truncates a fractional df of 1 and up, the
binomial cumulative with a fractional number_s is right, BESSELK and BESSELY take the integer
part of an order below 2; the LOGNORM.INV results in the subnormals at a huge standard
deviation pass through the 1e-300 atol (a model fact).

`TestHegelDate` draws the same way: serials of six profiles with the quirk region 0..62 first
and a time fraction a quarter of the time, and every Date bug's shape among the kinds — the
day-early calendar below serial 61 read by MONTH, YEAR, WEEKNUM, EDATE, EOMONTH and the
two-date functions, DAY between 60 and 61, DATE's January and February 1900 reached by a
month or day offset, the Monday-start WEEKNUM types through 1900 and the phantom 29 February
1900 as a DATEVALUE text (38, named only where a replica of the library's calendar differs
from Excel's: MONTH(2) is right, MONTH(1) is not), DAY of a fraction or of 31 on the modulo
path (35), the far end past 2958465, DATE years past 9999, results outside the range and
DATEDIF's negative serials (36), DATE years below 1900 (37), EDATE offsets 0..11 that reach a
December (39, by a replica of the month arithmetic) and month ends whose month sum is a
multiple of twelve (40, the panic), TIME totals of a day or more (41), reversed YEARFRAC pairs
at a fifth (42), February-end starts to a 31st with basis 0 (43), the January and December
days whose ISO year differs with type 21 (44, by a replica of the library's count), a holiday
listed twice (45) and an early holiday sorted before one inside a backward WORKDAY span (46,
by a replica of the walk), equal dates with a basis or unit outside the table and 0 days with
an invalid weekend (47), the error-code cases (21: WEEKDAY's type, the weekend numbers,
DATEDIF's unit) and fractional TIME arguments and WORKDAY counts below 1 (15). The
classifier `dateShape` orders 40 before 39 and before the skips, 21 before 36, 47 before 42,
46 before 45, and 35 before 38 for DAY. Under `HEGEL_NO_KNOWN=1` the property passes (at three
thousand cases: 0 mismatches, no case skipped; EDATE a fifth and WORKDAY.INTL a seventh of
their draws filtered, the rest under a tenth). Per thousand cases by default, about 170
mismatch (two runs of three thousand): 36 in 40 to 50, 38 in 30 to 45, 21 in 15, 39 in 9 to
15, 35 in 10, 45 in 6 to 11, 41 in 3 to 12, 15 in 5 to 10, 47 in 6 to 8, 46 in 6, 42 in 5,
37 in 2 to 4, 43 in 3, 44 in 1 to 3, 40 in 2. Not shapes, found by the drawn regions: DATE, EDATE,
EOMONTH, WEEKDAY, WEEKNUM and YEARFRAC truncate a fractional argument; the WEEKNUM types
12 to 17 are right through 1900; a negative serial is #NUM! on both sides for every function
but DATEDIF; excelize/10 has no Date instance.

The Text and Logic properties (part 4) draw the shape of every bug 48 to 78 and of the Text
instances of 15 and 21 as alternatives of the kinds: numbers whose `%g` text differs from
Excel's General (48), MID's range ending one past the text (49), interior double spaces and
tabs for TRIM (50), a number or boolean for REPT (51) and a count that overshoots the cell
limit for this text (52), an empty old_text (53), FIXED alone (54), with a false no_commas and
a number of a thousand or more (55) and at a decimal half case (56), non-ASCII text and a
negative count for REPLACE (57), a non-ASCII first character or the empty text for CODE (58),
CHAR of a value truncating to 0 (59), UNICHAR beyond 55295 (60), a wildcard in FIND's find
text (61), a tilde or a regexp character beside a wildcard in SEARCH's (62), a start of 0 for
FIND (63), a non-boolean ignore_empty (64), non-ASCII text before the delimiter (65), a missing
delimiter or instance (66), Go's spellings, surrounding spaces and invalid dates for VALUE
(67), TEXT at a half case (68), IF/IFS tests beyond 0 and 1 (69), IF of two arguments with a
false test (70), a boolean or error branch (71), a decisive AND/OR argument followed by an
error text (72), the ParseBool spellings and XOR's texts (73), odd numbers, booleans and errors
for ISEVEN/ISODD (74), numeric and TRUE/FALSE texts for the IS functions (75), SWITCH values
whose texts agree across kinds or differ in case (76), the backward search from a delimiter at
the start (77) and over adjacent delimiters (78), a fractional instance beyond the length whose
truncation is within it (15) and the error-code cases (21: ISEVEN of an error, IFS of a
non-logical text). The classifiers `textShape` and `logicShape` decide the relation shapes by
replicas of the library's rules beside the model (the `%g` text against General, the byte cut
against the character cut, `int(x·10^d + 0.5)` against the decimal rounding, the backward
search's resume point, AND/OR's early return, SWITCH's text equality), naming only the cases
that fail: a half case that rounds right by luck, a non-ASCII character after the cut or a
SWITCH text case that differs in content are plain. The function is drawn from a table of
thirty (Text) or twenty-six (Logic): the engine's draw over a table that long is lumpy (at
three thousand cases the least-drawn function came 33 to 66 times and the most 156 to 175),
so each function's shapes are alternatives at a fifth of its draws. Under `HEGEL_NO_KNOWN=1`
both properties pass (at three thousand cases: 0 mismatches, no case skipped; FIND, MID,
TEXTAFTER, ISEVEN, OR and SWITCH filtered under one per cent). Per thousand cases by default,
about 120 Text and 90 Logic mismatches (three thousand cases): 48 in 15, 64 in 10, 50, 58, 65
and 66 in 8 to 9, 57 and 59 in 6 to 7, 67 in 5, 51, 53, 55, 60 in 4, 61, 62 in 4, 56, 63 in 3,
49, 54, 68 in 2, 77 and 78 in 1 to 2, 15 and 52 in about one per three thousand; 73 in 26, 69
in 17, 74 in 13, 72 in 8, 70, 71, 21 in 5 to 6, 75 in 5, 76 in 4. Not shapes, found by the
drawn regions: FIXED with one decimal never shows 56 (the binary product lands on the half) and
the format "0.0" never shows 68; the scientific formats show 68 only at exact binary halves;
TEXTAFTER's length check reads a positive instance only.

## Not judged

ACOT to 1e-9 and within |x| ≤ 10^5 only (the calculator's π/2 − atan(x) cancels for large
x; the oracle uses atan(1/x)); SUM, AVERAGE and SUMSQ to 1e-12 of their largest term (binary
sums cancel); BETA.DIST's density at a bound A or B (always 0 here, SciPy's limit or inf;
Excel's answer unknown); BINOM.INV when a cumulative probability ties with alpha within
rounding; paired T.TEST whose differences are constant within rounding
(#DIV/0! on both sides once the oracle allows an ulp); COMBINA with n < k (Excel's
documentation is unclear); MODE with tied counts (either value); MROUND with multiple 0; SECH
and CSCH beyond |x| = 700 and Bessel values SciPy overflows or underflows; LARGE and SMALL
with a fractional k; PERCENTRANK of one value; T.TEST with fractional tails or type;
CONFIDENCE.T to 1e-8, F.INV to 1e-7 and F.TEST to 1e-6 only; 1 − exp(−x) cumulatives to an
absolute 1e-15; the legacy BETADIST/BETAINV with bounds only when A < B. Dates: DAYS360's US
method when the end date is the last day of February (Excel's rule there is disputed); DATEDIF's
MD when the end day precedes the start day and YD from a 29 February; YEARFRAC with a start in
the quirk region or basis 1 within 1900 (whether Excel's 1900 has 366 days there); WEEKNUM of a
serial below 1; EDATE of day 0; TIMEVALUE with minutes or seconds above 59, hour 0 with am/pm or
above 23 without. Texts: numbers beyond 1E+15 or below 1E-04 in a text context (where Excel
switches to an exponent is not modelled); CHAR 128–159 and CODE of characters beyond Latin-1
(code-page dependent); UNICHAR(65534) and (65535); lower-case "true"/"false" as logical texts;
counts in (−1, 0); a space before a percent sign in VALUE; a trailing tilde in a SEARCH pattern;
the sign of a negative that rounds to zero in FIXED and TEXT; TEXTAFTER with an empty delimiter,
an empty text (whether Excel's "instance beyond the length" #VALUE! or the "not found" #N/A comes
first) or a fractional instance below 1; VALUE of a dash-separated date with a two-digit year
("20-05-03": Excel's reading is not modelled; the calculator gives 0); the B functions (LENB,
LEFTB, ...: DBCS-locale semantics), DBCS,
BAHTTEXT, ARRAYTOTEXT and UNIQUE; ISBLANK, ISREF, ISFORMULA, SHEET and SHEETS of references.

## Not tested

The lookup, financial and engineering functions (probes saw BITAND(1.5,3) = 1, BITRSHIFT(4,-2)
= #NUM! where Excel shifts left, BITLSHIFT(1,60) = 1.15E+18 beyond the 2^48 limit, BIN2DEC of
eleven digits accepted), the database functions, NOW and TODAY, the operators (`0^0` = 1 where
POWER(0,0) is #NUM!), array formulas, cell references across sheets, the cell-name helpers and
the file format itself: a fourth part. A lowercase `1e-7` literal is parsed as a name (#NAME?,
the efp parser's).

## History

- 2026-09-22: new target, three properties, 34 bugs.
- 2026-09-22: part 2, the date and time functions (`TestHegelDate`), 13 bugs (35–47).
- 2026-09-22: part 3, the text, logical and information functions (`TestHegelText`,
  `TestHegelLogic`), 31 bugs (48–78).
- 2026-10-09: part 1 of the rewrite in combinator style (the harness idioms, `TestHegelMath`
  drawing every Math shape, twenty narrow properties), 5 bugs (79–83).
- 2026-10-09: part 2a of the rewrite (`TestHegelStat` drawing every Stat shape, fourteen
  narrow properties); the notes of 21, 22, 26 and 29 widened by the drawn shapes.
- 2026-10-09: part 2b of the rewrite (`TestHegelDist` drawing every Dist shape, sixteen
  narrow properties), 2 bugs (84, 85).
- 2026-10-09: part 3 of the rewrite (`TestHegelDate` drawing every Date shape, sixteen
  narrow properties); the notes of 15, 21, 36, 38 and 47 widened by the drawn regions.
- 2026-10-09: part 4 of the rewrite (`TestHegelText` and `TestHegelLogic` drawing every Text
  and Logic shape, thirty-three narrow properties; the old per-bug switches removed, so
  `HEGEL_NO_KNOWN=1` is the only switch); the notes of 15, 21 and 67 widened; the model's
  DATEVALUE reads a two-digit year as Excel does and TEXTAFTER/TEXTBEFORE reject an instance
  beyond the text's length as Excel documents.
