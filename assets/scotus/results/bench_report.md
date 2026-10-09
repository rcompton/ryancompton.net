# Supreme Court benchmark

2977 answers on 200 split decisions, 650 on 50 unanimous ones; 13 models.
Every section except the last uses split decisions only.

## How often each model sides with the dissent

Real justices in these same cases dissent about 31% of the time.

The last two columns split by which side's opinions were shown first. A big difference means the model is swayed by order, not argument.

| model | sides with dissent | majority shown first | dissent shown first |
|---|---|---|---|
| opus-5.5 | 15% (221) | 15% | 15% |
| sonnet-5.5 | 13% (233) | 8% | 17% |
| gpt-6.1-sol | 32% (214) | 35% | 28% |
| gemini-3.8-flash | 16% (224) | 19% | 14% |
| grok-4.7 | 45% (235) | 45% | 45% |
| llama-4-maverick | 65% (240) | 74% | 57% |
| deepseek-v4-pro | 61% (240) | 71% | 51% |
| qwen3.8-max | 29% (239) | 26% | 32% |
| kimi-k3 | 33% (219) | 27% | 39% |
| glm-5.3 | 40% (213) | 37% | 43% |
| mistral-large-4 | 62% (240) | 62% | 63% |
| command-a-plus | 34% (220) | 36% | 32% |
| jev-router | 26% (239) | 23% | 29% |

## Cases where models split

Models counted as siding with the dissent if at least half their samples did.

| case | Court's vote | models siding with dissent |
|---|---|---|
| Florence v. Board of Chosen Freeholders of the County of Bur (2011) | 5-4 | 13/13 |
| Utah v. Strieff (2015) | 5-3 | 13/13 |
| Fischer v. United States (2023) | 6-3 | 13/13 |
| Douglas v. Independent Living Center of Southern California (2011) | 5-4 | 12/13 |
| Prado Navarette v. California (2013) | 5-4 | 12/13 |
| Nieves v. Bartlett (2018) | 8-1 | 12/13 |
| Lamps Plus, Inc. v. Varela (2018) | 5-4 | 12/13 |
| Samia v. United States (2022) | 6-3 | 12/13 |
| FAA v. Cooper (2011) | 5-3 | 11/13 |
| Messerschmidt v. Millender (2011) | 6-3 | 11/13 |
| Christopher v. SmithKline (2011) | 5-4 | 11/13 |
| Kaley v. United States (2013) | 6-3 | 11/13 |
| Scialabba v. Cuellar De Osorio (2013) | 5-4 | 11/13 |
| Walker v. Texas Division, Sons of Confederate Veterans, Inc. (2014) | 5-4 | 11/13 |
| Ohio v. American Express Co. (2017) | 5-4 | 11/13 |
| Office of the United States Trustee v. John Q. Hammons Fall  (2023) | 6-3 | 11/13 |
| Trump v. United States (2023) | 6-3 | 11/13 |
| Central Va. Community College v. Katz (2005) | 5-4 | 10/13 |
| T-Mobile South, LLC v. City of Roswell, Georgia (2014) | 6-3 | 10/13 |
| Turner v. United States (2016) | 6-2 | 10/13 |
| Murr v. Wisconsin (2016) | 5-3 | 10/13 |
| Abbott v. Perez (2017) | 5-4 | 10/13 |
| Rucho v. Common Cause (2018) | 5-4 | 10/13 |
| McKinney v. Arizona (2019) | 5-4 | 10/13 |
| Jones v. Mississippi (2020) | 6-3 | 10/13 |
| Federal Election Commission v. Ted Cruz for Senate (2021) | 6-3 | 10/13 |
| Arizona v. Navajo Nation (2022) | 5-4 | 10/13 |
| Ohio v. Environmental Protection Agency (2023) | 5-4 | 10/13 |
| Bost v. Illinois State Board of Elections (2025) | 7-2 | 10/13 |
| Salinas v. Texas (2012) | 5-4 | 9/13 |
| Texas Dept. of Housing and Community Affairs v. Inclusive Co (2014) | 5-4 | 9/13 |
| Trump v. Hawaii (2017) | 5-4 | 9/13 |
| Cummings v. Premier Rehab Keller, P.L.L.C. (2021) | 6-3 | 9/13 |
| Mallory v. Norfolk Southern Railway Co. (2022) | 5-4 | 9/13 |
| Landor v. Louisiana Department of Corrections (2025) | 6-3 | 9/13 |
| Town of Greece v. Galloway (2013) | 5-4 | 8/13 |
| Burwell v. Hobby Lobby Stores (2013) | 5-4 | 8/13 |
| Kerry v. Din (2014) | 5-4 | 8/13 |
| Dart Cherokee Basin Operating Company LLC v. Owens (2014) | 5-4 | 8/13 |
| Armstrong v. Exceptional Child Center, Inc. (2014) | 5-4 | 8/13 |
| Home Depot U.S.A., Inc. v. Jackson (2018) | 5-4 | 8/13 |
| United States Forest Service v. Cowpasture River Preservatio (2019) | 7-2 | 8/13 |
| United States Agency for International Development v. Allian (2019) | 5-3 | 8/13 |
| United States v. Arthrex, Inc. (2020) | 5-4 | 8/13 |
| Gallardo v. Marstiller (2021) | 7-2 | 8/13 |
| Brown v. United States (2023) | 6-3 | 8/13 |
| Rutherford v. United States (2025) | 6-3 | 8/13 |
| Young v. United Parcel Service, Inc. (2014) | 6-3 | 7/13 |
| Davis v. Ayala (2014) | 5-4 | 7/13 |
| Epic Systems Corp. v. Lewis (2017) | 5-4 | 7/13 |
| Manhattan Community Access Corp. v. Halleck (2018) | 5-4 | 7/13 |
| Mont v. United States (2018) | 5-4 | 7/13 |
| The Dutra Group v. Batterton (2018) | 6-3 | 7/13 |
| Google LLC v. Oracle America Inc. (2020) | 6-2 | 7/13 |
| Minerva Surgical, Inc. v. Hologic, Inc. (2020) | 5-4 | 7/13 |
| HollyFrontier Cheyenne Refining LLC v. Renewable Fuels Assoc (2020) | 6-3 | 7/13 |
| Yellen v. Confederated Tribes of the Chehalis Reservation (2020) | 6-3 | 7/13 |
| Berger v. North Carolina State Conference of the NAACP (2021) | 8-1 | 7/13 |
| The Ohio Adjutant General’s Department v. Federal Labor Rela (2022) | 7-2 | 7/13 |
| Securities and Exchange Commission v. Jarkesy (2023) | 6-3 | 7/13 |
| Diaz v. United States (2023) | 6-3 | 7/13 |
| McLaughlin Chiropractic Associates, Inc. v. McKesson Corpora (2024) | 6-3 | 7/13 |
| Martinez v. Ryan (2011) | 7-2 | 6/13 |
| Coleman v. Maryland Court of Appeals (2011) | 5-4 | 6/13 |
| Minneci v. Pollard (2011) | 8-1 | 6/13 |
| CompuCredit Corp. v. Greenwood (2011) | 8-1 | 6/13 |
| University of Texas Southwestern Medical Center v. Nassar (2012) | 5-4 | 6/13 |
| Husky Electronics v. Ritz (2015) | 7-1 | 6/13 |
| Husted v. A. Philip Randolph Institute (2017) | 5-4 | 6/13 |
| Nielsen v. Preap (2018) | 5-4 | 6/13 |
| Washington State Department of Licensing v. Cougar Den, Inc. (2018) | 5-4 | 6/13 |
| Bucklew v. Precythe (2018) | 5-4 | 6/13 |
| County of Maui, Hawaii v. Hawaii Wildlife Fund (2019) | 6-3 | 6/13 |
| City of Austin, Texas v. Reagan National Advertising of Texa (2021) | 6-3 | 6/13 |
| Lac du Flambeau Band of Lake Superior Chippewa Indians v. Co (2022) | 8-1 | 6/12 |
| Financial Oversight and Management Board for Puerto Rico v.  (2022) | 8-1 | 6/13 |
| Stanley v. City of Sanford, Florida (2024) | 8-1 | 6/13 |
| United States Postal Service v. Konan (2025) | 5-4 | 6/13 |
| Gonzalez v. Thaler (2011) | 8-1 | 5/13 |
| Henderson v. United States (2012) | 6-3 | 5/13 |
| McQuiggin v. Perkins (2012) | 5-4 | 5/13 |
| Harris v. Quinn (2013) | 5-4 | 5/12 |
| Abramski v. United States (2013) | 5-4 | 5/13 |
| Comptroller of the Treasury of Maryland v. Wynne (2014) | 5-4 | 5/13 |
| Montgomery v. Louisiana (2015) | 6-3 | 5/13 |
| Ocasio v. United States (2015) | 5-3 | 5/13 |
| Luis v. United States (2015) | 5-3 | 5/13 |
| Perry v. Merit Systems Protection Board (2016) | 7-2 | 5/13 |
| Rosales-Mireles v. United States (2017) | 7-2 | 5/13 |
| Cedar Point Nursery v. Hassid (2020) | 6-3 | 5/13 |
| Warner Chappell Music, Inc. v. Nealy (2023) | 6-3 | 5/13 |
| Williams v. Reed (2024) | 5-4 | 5/13 |
| Pitchford v. Cain (2025) | 5-4 | 5/13 |
| Blanche v. Lau  (2025) | 6-3 | 5/13 |
| Schaffer ex rel. Schaffer v. Weast (2005) | 6-2 | 4/13 |
| Perry v. New Hampshire (2011) | 8-1 | 4/13 |
| Miller v. Alabama (2011) | 5-4 | 4/13 |
| United States v. Alvarez (2011) | 6-3 | 4/13 |
| Arizona v. Inter Tribal Council of Arizona (2012) | 7-2 | 4/13 |
| Wos v. E.M.A. et al. (2012) | 6-3 | 4/13 |
| Fernandez v. California (2013) | 6-3 | 4/13 |
| United States v. Kwai Fun Wong (2014) | 5-4 | 4/13 |
| Michigan v. Environmental Protection Agency (2014) | 5-4 | 4/13 |
| Tyson Foods, Inc. v. Bouaphakeo (2015) | 6-2 | 4/13 |
| WesternGeco LLC v. ION Geophysical Corp. (2017) | 7-2 | 4/13 |
| Sveen v. Melin (2017) | 8-1 | 4/13 |
| Hughes v. United States (2017) | 6-3 | 4/13 |
| United States v. Haymond (2018) | 5-4 | 4/13 |
| Apple v. Pepper (2018) | 5-4 | 4/13 |
| Rehaif v. United States (2018) | 7-2 | 4/13 |
| Our Lady of Guadalupe School v. Morrissey-Berru (2019) | 7-2 | 4/13 |
| California v. Texas (2020) | 7-2 | 4/13 |
| Niz-Chavez v. Garland (2020) | 6-3 | 4/13 |
| 303 Creative LLC v. Elenis (2022) | 6-3 | 4/13 |
| Cruz v. Arizona (2022) | 5-4 | 4/13 |
| United States v. Hansen (2022) | 7-2 | 4/13 |
| City of Grants Pass v. Johnson (2023) | 6-3 | 4/13 |
| Chiaverini v. City of Napoleon, Ohio (2023) | 6-3 | 4/13 |
| Glossip v. Oklahoma (2024) | 6-2 | 4/13 |
| Esteras v. United States (2024) | 7-2 | 4/13 |
| Wagnon v. Prairie Band Potawatomi Nation (2005) | 7-2 | 3/13 |
| Kirtsaeng v. John Wiley & Sons, Inc. (2012) | 6-3 | 3/13 |
| Environmental Protection Agency v. EME Homer City Generation (2013) | 6-2 | 3/13 |
| B&B Hardware Inc. v. Hargis Industries Inc. (2014) | 7-2 | 3/13 |
| Johnson v. United States (2014) | 8-1 | 3/13 |
| Elonis v. United States (2014) | 8-1 | 3/13 |
| Taylor v. United States (2015) | 7-1 | 3/13 |
| Whole Woman’s Health v. Hellerstedt (2015) | 5-3 | 3/13 |
| Moore v. Texas (2016) | 5-3 | 3/13 |
| Weaver v. Massachusetts (2016) | 7-2 | 3/13 |
| California Public Employees’ Retirement System v. ANZ Securi (2016) | 5-4 | 3/13 |
| Carpenter v. United States (2017) | 5-4 | 3/13 |
| Class v. United States (2017) | 6-3 | 3/13 |
| Oil States Energy Services LLC v. Greene’s Energy Group, LLC (2017) | 7-2 | 3/13 |
| Lorenzo v. Securities and Exchange Commission (2018) | 6-2 | 3/12 |
| Espinoza v. Montana Department of Revenue (2019) | 5-4 | 3/13 |
| Haaland v. Brackeen (2022) | 7-2 | 3/13 |
| Corner Post, Inc. v. Board of Governors of the Federal Reser (2023) | 6-3 | 3/13 |
| Garland v. Cargill (2023) | 6-3 | 3/13 |
| Setser v. United States (2011) | 6-3 | 2/13 |
| CTS Corp. v. Waldburger (2013) | 7-2 | 2/13 |
| Mellouli v. Lynch (2014) | 7-2 | 2/13 |
| Trinity Lutheran Church of Columbia, Inc. v. Comer (2016) | 7-2 | 2/13 |
| Wisconsin Central Ltd. v. United States (2017) | 5-4 | 2/13 |
| Jam v. International Finance Corp. (2018) | 7-1 | 2/13 |
| Tennessee Wine and Spirits Retailers Association v. Thomas (2018) | 7-2 | 2/13 |
| Nasrallah v. Barr (2019) | 7-2 | 2/13 |
| Liu v. Securities and Exchange Commission (2019) | 8-1 | 2/13 |
| Banister v. Davis (2019) | 7-2 | 2/13 |
| Hemphill v. New York (2021) | 8-1 | 2/13 |
| Reed v. Goertz (2022) | 6-3 | 2/13 |
| Loper Bright Enterprises v. Raimondo (2023) | 6-2 | 2/13 |
| Hunter v. United States (2025) | 8-1 | 2/13 |
| Chiles v. Salazar (2025) | 8-1 | 2/13 |
| Federal Communications Commission v. AT&T, Inc. (2025) | 8-1 | 2/13 |
| Unitherm Food Systems, Inc. v. Swift-Eckrich, Inc. (2005) | 7-2 | 1/13 |
| Knox v. Service Employees International Union (2011) | 7-2 | 1/13 |
| Missouri v. McNeely (2012) | 5-4 | 1/13 |
| Fisher v. University of Texas (2012) | 7-1 | 1/13 |
| FTC v. Actavis Inc. (2012) | 5-3 | 1/13 |
| Brandt Revocable Trust v. United States (2013) | 8-1 | 1/13 |
| Jennings v. Stephens (2014) | 6-3 | 1/13 |
| Manuel v. City of Joliet (2016) | 6-2 | 1/13 |
| Bristol-Myers Squibb Co. v. Superior Court of California (2016) | 8-1 | 1/13 |
| McWilliams v. Dunn (2016) | 5-4 | 1/13 |
| Herrera v. Wyoming (2018) | 5-4 | 1/13 |
| Nestlé USA, Inc. v. Doe I (2020) | 8-1 | 1/13 |
| Cameron v. EMW Women’s Surgical Center (2021) | 8-1 | 1/13 |
| Health and Hospital Corporation of Marion County v. Talevski (2022) | 7-2 | 1/13 |
| Helix Energy Solutions Group, Inc. v. Hewitt (2022) | 6-3 | 1/13 |
| Consumer Financial Protection Bureau v. Community Financial  (2023) | 7-2 | 1/13 |
| Harrington v. Purdue Pharma L.P. (2023) | 5-4 | 1/13 |
| Food and Drug Administration v. R.J. Reynolds Vapor Co. (2024) | 7-2 | 1/13 |
| Diamond Alternative Energy LLC v. Environmental Protection A (2024) | 7-2 | 1/13 |
| Rico v. United States (2025) | 8-1 | 1/13 |
| Hencely v. Fluor Corporation (2025) | 6-3 | 1/13 |
| Taniguchi v. Kan Pacific Saipan (2011) | 6-3 | 0/13 |
| Southern Union Company v. United States (2011) | 6-3 | 0/13 |
| Moncrieffe v. Holder (2012) | 7-2 | 0/13 |
| Bailey v. United States (2012) | 6-3 | 0/13 |
| Chadbourne and Parke LLP v. Troice (2013) | 7-2 | 0/13 |
| City of Los Angeles v. Patel (2014) | 5-4 | 0/13 |
| Rodriguez v. United States (2014) | 6-3 | 0/13 |
| Montanile v. Board of Trustees of the National Elevator Indu (2015) | 8-1 | 0/13 |
| Puerto Rico v. Sanchez Valle (2015) | 6-2 | 0/13 |
| Czyzewski v. Jevic Holding Corp. (2016) | 6-2 | 0/13 |
| Buck v. Davis (2016) | 6-2 | 0/13 |
| Collins v. Virginia (2017) | 8-1 | 0/13 |
| Minnesota Voters Alliance v. Mansky (2017) | 7-2 | 0/13 |
| McCoy v. Louisiana (2017) | 6-3 | 0/13 |
| Garza v. Idaho (2018) | 6-3 | 0/13 |
| Azar v. Allina Health Services (2018) | 7-1 | 0/13 |
| McDonough v. Smith (2018) | 6-3 | 0/13 |
| Babb v. Wilkie (2019) | 8-1 | 0/13 |
| U.S. Fish and Wildlife Service v. Sierra Club (2020) | 7-2 | 0/13 |
| Van Buren v. United States (2020) | 6-3 | 0/13 |
| Johnson v. Guzman Chavez (2020) | 6-3 | 0/13 |
| Badgerow v. Walters (2021) | 8-1 | 0/13 |
| Babcock v. Kijakazi (2021) | 8-1 | 0/13 |
| Ramirez v. Collier (2021) | 8-1 | 0/13 |

## Which justice each model votes like

Agreement = share of shared cases where the model's side matches the justice's vote (cases with at least 8 in common). Top 3 and bottom 1 per model.

| model | most similar | least similar |
|---|---|---|
| opus-5.5 | Barrett 81% (68), Kavanaugh 75% (95), Kagan 75% (193) | Thomas 48% (200) |
| sonnet-5.5 | Barrett 85% (68), Kavanaugh 83% (95), Roberts 77% (199) | Jackson 51% (45) |
| gpt-6.1-sol | Kagan 82% (193), Ginsburg 79% (131), Sotomayor 79% (196) | Thomas 34% (200) |
| gemini-3.8-flash | Barrett 85% (68), Kavanaugh 78% (95), Roberts 77% (199) | Jackson 53% (45) |
| grok-4.7 | Scalia 78% (65), Barrett 69% (68), Thomas 64% (200) | Jackson 37% (45) |
| llama-4-maverick | Kagan 57% (193), Ginsburg 57% (131), Sotomayor 55% (196) | Kavanaugh 37% (95) |
| deepseek-v4-pro | Scalia 65% (65), Barrett 54% (68), Sotomayor 54% (196) | Kavanaugh 40% (95) |
| qwen3.8-max | Kagan 76% (192), Ginsburg 74% (130), Sotomayor 74% (195) | Thomas 42% (199) |
| kimi-k3 | Kagan 72% (191), Jackson 72% (44), Ginsburg 67% (130) | Thomas 46% (198) |
| glm-5.3 | Kagan 74% (193), Sotomayor 73% (196), Ginsburg 72% (131) | Thomas 39% (200) |
| mistral-large-4 | Jackson 58% (45), Ginsburg 58% (131), Kagan 57% (193) | Alito 37% (194) |
| command-a-plus | Jackson 68% (45), Kagan 67% (193), Ginsburg 65% (131) | Thomas 46% (200) |
| jev-router | Ginsburg 72% (131), Barrett 71% (68), Kagan 70% (193) | Thomas 45% (200) |

Caution: a model that always sided with the Court would score Kavanaugh 91%, Barrett 85%, Roberts 84%, Kennedy 84%, Gorsuch 70%, Kagan 65%, Alito 65%, Breyer 65%, Scalia 65%, Ginsburg 63%, Thomas 60%, Sotomayor 59%, Jackson 53%. High similarity to the justices usually in the majority mostly means agreeing with the Court; the next section shows which way a model breaks when it doesn't.

## When a model breaks from the Court, who dissented with it

Cases where the model sided with the dissent: share of them in which each justice also dissented. Top 3.

| model | cases it dissents in | justices dissenting alongside it |
|---|---|---|
| opus-5.5 | 30 | Sotomayor 83%, Kagan 82%, Ginsburg 79% |
| sonnet-5.5 | 28 | Sotomayor 67%, Kagan 62%, Ginsburg 50% |
| gpt-6.1-sol | 63 | Sotomayor 81%, Kagan 77%, Ginsburg 77% |
| gemini-3.8-flash | 33 | Scalia 73%, Sotomayor 55%, Kagan 52% |
| grok-4.7 | 92 | Scalia 65%, Thomas 54%, Alito 43% |
| llama-4-maverick | 132 | Sotomayor 46%, Ginsburg 45%, Jackson 44% |
| deepseek-v4-pro | 131 | Scalia 50%, Jackson 48%, Sotomayor 46% |
| qwen3.8-max | 61 | Sotomayor 75%, Kagan 69%, Ginsburg 68% |
| kimi-k3 | 66 | Jackson 75%, Sotomayor 62%, Kagan 62% |
| glm-5.3 | 78 | Sotomayor 68%, Jackson 67%, Kagan 61% |
| mistral-large-4 | 128 | Jackson 54%, Sotomayor 48%, Ginsburg 46% |
| command-a-plus | 68 | Jackson 65%, Sotomayor 55%, Kagan 52% |
| jev-router | 53 | Sotomayor 69%, Ginsburg 68%, Jackson 60% |

## Law vs outcome

How often the model says the law requires a result it thinks is bad for the country, or the reverse.

| model | majority right, outcome bad | dissent right, outcome good | n |
|---|---|---|---|
| opus-5.5 | 10% | 1% | 221 |
| sonnet-5.5 | 14% | 2% | 233 |
| gpt-6.1-sol | 9% | 1% | 214 |
| gemini-3.8-flash | 17% | 6% | 224 |
| grok-4.7 | 6% | 20% | 235 |
| llama-4-maverick | 9% | 2% | 240 |
| deepseek-v4-pro | 8% | 18% | 240 |
| qwen3.8-max | 13% | 3% | 239 |
| kimi-k3 | 14% | 9% | 219 |
| glm-5.3 | 8% | 7% | 213 |
| mistral-large-4 | 8% | 11% | 240 |
| command-a-plus | 22% | 10% | 220 |
| jev-router | 13% | 6% | 239 |

## Legal vote vs preferred outcome, left/right

Cases where the liberal and conservative justices split. 'Liberal on the law' = voted with the side the liberal justices took; 'prefers liberal outcome' = said the liberal side's result is better for the country (the Court's result if it called the outcome good, the dissent's if bad). The last two columns count answers where the two disagree, in each direction.

| model | liberal on the law | prefers liberal outcome | gap (points) | law conservative, outcome liberal | law liberal, outcome conservative | n |
|---|---|---|---|---|---|---|
| opus-5.5 | 61% | 70% | +9 | 10% | 1% | 177 |
| sonnet-5.5 | 54% | 70% | +16 | 16% | 1% | 187 |
| gpt-6.1-sol | 78% | 87% | +8 | 9% | 1% | 171 |
| gemini-3.8-flash | 51% | 72% | +21 | 23% | 2% | 179 |
| grok-4.7 | 34% | 54% | +20 | 24% | 4% | 190 |
| llama-4-maverick | 58% | 64% | +7 | 9% | 2% | 194 |
| deepseek-v4-pro | 51% | 72% | +21 | 24% | 3% | 194 |
| qwen3.8-max | 68% | 81% | +13 | 14% | 1% | 193 |
| kimi-k3 | 60% | 80% | +19 | 20% | 1% | 176 |
| glm-5.3 | 69% | 83% | +14 | 15% | 1% | 170 |
| mistral-large-4 | 59% | 78% | +19 | 19% | 1% | 194 |
| command-a-plus | 58% | 81% | +24 | 27% | 3% | 177 |
| jev-router | 63% | 79% | +16 | 18% | 2% | 194 |

## Opinion closest to the model's view

| model | most-picked authors (count) |
|---|---|
| opus-5.5 | Kagan 26, Alito 26, Breyer 23, Sotomayor 23, Roberts 19 |
| sonnet-5.5 | Sotomayor 26, Roberts 25, Breyer 24, Alito 24, Kagan 22 |
| gpt-6.1-sol | Sotomayor 38, Breyer 27, Kagan 25, Ginsburg 19, Thomas 18 |
| gemini-3.8-flash | Sotomayor 28, Roberts 24, Alito 24, Kennedy 21, Kagan 21 |
| grok-4.7 | Thomas 35, Roberts 31, Alito 28, Gorsuch 25, Sotomayor 22 |
| llama-4-maverick | Sotomayor 43, Thomas 28, Alito 26, Breyer 22, Ginsburg 22 |
| deepseek-v4-pro | Sotomayor 40, Thomas 28, Alito 27, Breyer 25, Roberts 19 |
| qwen3.8-max | Sotomayor 38, Breyer 35, Kagan 30, Thomas 18, Alito 17 |
| kimi-k3 | Sotomayor 34, Alito 24, Kagan 22, Breyer 20, Gorsuch 20 |
| glm-5.3 | Sotomayor 35, Kagan 26, Alito 23, Breyer 20, Ginsburg 18 |
| mistral-large-4 | Sotomayor 42, Thomas 24, Gorsuch 23, Roberts 23, Ginsburg 21 |
| command-a-plus | Sotomayor 30, Kagan 25, Thomas 25, Breyer 24, Alito 24 |
| jev-router | Sotomayor 31, Kagan 27, Thomas 24, Breyer 24, Alito 24 |

## Unanimous decisions (baseline)

When every Justice agreed, the legal answer is rarely close, so a model's dissent rate here is roughly its noise floor or contrarianism. Compare with its split-decision rate.

| model | dissents from unanimous Court | dissents in split cases | unanimous outcome bad |
|---|---|---|---|
| opus-5.5 | 0% (50) | 15% | 6% |
| sonnet-5.5 | 0% (50) | 13% | 2% |
| gpt-6.1-sol | 0% (50) | 32% | 16% |
| gemini-3.8-flash | 0% (50) | 16% | 10% |
| grok-4.7 | 2% (50) | 45% | 6% |
| llama-4-maverick | 0% (50) | 65% | 26% |
| deepseek-v4-pro | 2% (50) | 61% | 12% |
| qwen3.8-max | 0% (50) | 29% | 14% |
| kimi-k3 | 0% (50) | 33% | 12% |
| glm-5.3 | 0% (50) | 40% | 4% |
| mistral-large-4 | 0% (50) | 62% | 16% |
| command-a-plus | 6% (50) | 34% | 14% |
| jev-router | 0% (50) | 26% | 16% |

Unanimous cases drawing the most model dissents: Kiobel v. Royal Dutch Petroleum (1); Rehberg v. Paulk (1); Sturgeon v. Frost (1); Menominee Indian Tribe of Wisconsin v. United States (1); Devillier v. Texas (1)
