# CITATIONS — DodgysDD, the UCLA lecture

Every rule in `docs/RESEARCH-dodgysdd-lecture.md` and `config/dodgysdd.yaml`, attached to
a video id and a timestamp. Regenerate with `python scripts/dodgy_cite.py`.

| | |
|---|---|
| part 1 | `WQycR82IOD4` — 11:57:19, 5,986 caption lines, 99,528 words |
| part 2 | `r43i9rRIjoQ` — 11:59:53, 5,795 caption lines, 93,167 words |
| total | **23h 56m, 192,695 words** |
| backend | yt-dlp `json3` auto-captions, `player_client=ios` |
| fetched | 2026-08-19 |

**Two things about this fetch, because they will bite the next person.**

`youtube-transcript-api` is still wrong (it IP-blocks, as `fetch_channel_transcripts.py`
records) — but as of this fetch **plain yt-dlp is also blocked**: the default `web` client
returns *"Sign in to confirm you're not a bot"* and there is no JS runtime on this host.
`player_client=ios` (also `android`, `web_embedded`, `web_safari`) clears it. `mweb` and
`tv` connect but expose **no caption tracks at all**, which reads like a missing video
rather than a wrong client — do not conclude the captions do not exist.

`--skip-download` alone is not enough; yt-dlp still resolves a media format and dies with
*"Requested format is not available"*. `--ignore-no-formats-error` is required.

**json3, not VTT.** VTT auto-captions are rolling — each cue repeats the previous line, so
a naive read roughly doubles the corpus. json3 carries discrete timed segments, so
de-duplication is exact rather than heuristic. `scripts/parse_json3_captions.py` handles it.

**Caption corruption is systematic** and any regex mining must allow for it: IFVG renders
as *IPG / IFG*, fair value gap as *"for value gap" / "fair rally gap" / "reality gap"*,
Judas as *Judah*, data wick as *dataix*, bisi/sibi as *busy / civvy / city*. CISD never
appears. Words also join across cue boundaries (*"Butyeah"*, *"ofa trade"*), which is why
`scripts/dodgy_cite.py` searches a whitespace-stripped projection — a literal regex misses
about one quote in six.

---

rule   video         ts         label / quote
--------------------------------------------------------------------------------------------------------------
ID     WQycR82IOD4   09:36:38   identity: DD = due diligence
                                "....>>Mygamertagwasdodgythelegend.Butyeah,>>what'sthewhat?DDstandsforduediligence.>>Adirtydog.>>ButitwasbetterforwhenIdidpennystockscuzyouactuallyhaveto,youknow,howli..."
E1     r43i9rRIjoQ   06:41:03   iFVG is the whole strategy
                                "...dandfairvaluegaps.FairvaluegapsandusingfairvaluegapsaremywholestrategyandeverythingIdorevolvesaroundfairvaluegaps.Okay,which[clearsthroat]I'llteachyouwhatthatisandthenwhyt..."
E1b    WQycR82IOD4   05:16:50   bullish iFVG definition
                                "...esbackbelowthecandle.WritethisbullishIPGequalswhenpriceclosesaboveabearishrealitygap.SoabullishIPGequalswhenpriceclosesaboveabearishgap.Right.Nowwhatdoyouthink..."
E2     WQycR82IOD4   05:21:02   entry = market on close of break
                                "...totakeanentryattheconsequentapproachment.Idonotdothis.Igetinthesecondthiscannoncloses,Igetinhere.Doyouthinkifwe'rereversingallthesesellorders,doyouthinkwe'regoingtoretrac..."
E2b    r43i9rRIjoQ   10:21:53   does NOT wait for retracement
                                "...llsrallygapsarehereandhere,>>right?>>So,formystrategy,Idon'tactuallywaitforustogobackintothebullishvalleygap.Doyouguysrealizethat?>>Yeah.>>IjusttakeIjustWhatWhattypeoforderam..."
E3     WQycR82IOD4   02:00:54   bodies tell the story
                                "...hat'stheWhat'sthesayingItoldyouguys?>>Wicksdothedamage.Bodiestellthestory.Oh.>>So,wouldwehaveeverlookedforalongthere?>>No.>>Oh.>>Okay.Isthisanorderblock?>>Yes..."
E4     WQycR82IOD4   01:00:00   drake candle = displacement
                                "...odifIsawatrendlineliquidityuphereandlikeagiant,youknow,Drakecandleherethatsweptthislowthislow,right?Icanalreadyassume,okay,themarket'sprobablygoingtost..."
E5.1   WQycR82IOD4   07:00:22   gap must be singular
                                "...e.Solikethisisgoingtobeabeginner'sguide,butruleoneistheIPGmustbesingular.IfyouwanttotakeanIPG,itshouldbesingular.Asabeginner,itmustbebiganditmustbeobvious.Al..."
E5.2   r43i9rRIjoQ   02:38:57   ten-foot obviousness test
                                "...goingtobeactuallyanorangelineoritdoesn'tmatter.Okay.IfIbackawayfromthescreenallthewaybackhere,whatlineamImorelikelytowhatlowamImorelikelytosee?Theorangeorthered?>>Exactly..."
E5.4   WQycR82IOD4   04:19:44   target must still be unswept
                                "...havebeenagoodlongbutifyoueverseelikeaTrumpcandletakeout50millionhighsorlowsinthesamecandledonotenterthatcandlethere'snomoreliquiditybecausewetookeveryone'..."
Q1     WQycR82IOD4   02:02:43   sweep required before any entry
                                "...liquiditysweep.>>Damn.>>Writethereinyournotes.Thatistheonethinglikeyouguysshouldbelookingforbeforeanytypeofentry.Whyisitnotdrawingaline?>>Um,thereyougo.Okay.Isthattheliquiditysweep?Isthatwhatyouthi..."
Q1b    WQycR82IOD4   08:35:40   manipulation leg = liquidity sweep
                                "...lationlegisalsoawhat?>>Yeah.Makesureyouwriteinyournotesmanipulationlegequalsliquiditysweep.Allright.>>Writethatinyournotes.Right.>>Yeah.Yeah.Yeah.Yeah.Yeah.>>Allright.>>Manipu..."
Q2     r43i9rRIjoQ   08:01:41   displacement vs prior leg size
                                "...atwe'reshootingoutofisitlikethesamesizelikeareweisitthesamesizeastherangewejustputin?Thisisgoingtomakenosense.LikeIdon'tknowhowelsetoexplainthis.SoIjustkindof..."
Q3     WQycR82IOD4   00:43:34   spent levels are deleted
                                "...rthisrallygap."Butremember,Isaiddeletethelevelafterit'salreadybeenran.>>Okay.>>Wealreadyranthesedoublehighs.Thesearenotrelevantanymore.>>You'dhavetotarget..."
L1     WQycR82IOD4   03:30:46   equal-highs probability ladder
                                "...dtakeapictureofthis.Equalhighsandequallows.Ifweonlyhavetwowicksrightnexttoeachother,it'slike50%probabilitybeinghit.Twowicksseveralcandlesapart,7080%.Threepluswicksstack..."
L2     r43i9rRIjoQ   05:59:37   trend line 45-degree preference
                                "...goingtolookforliketrendlinebuildsup.Um,bytheway,Ireallyprefertrendlinesthatarekindoflikethis,notlikethis.Whatdoyoumean?>>Drawthisinyournotes.Drawa45degreean..."
L2b    r43i9rRIjoQ   06:27:58   more touches = stronger
                                "...isibletofullyconfirmitstrength.Doyouthinkatrendlinewitheighttouchesinthesamespotisgoingtobestrongerorweakerthanatrendlinewithtwotouches?>>Yeah,it'sgoingtobemuchstronger.Whichatrendlinewitheighttoucheshashowmanyclustersof..."
L9     WQycR82IOD4   00:00:38   intermediate-term high/low
                                "...>it'sonabigdown>>downspikeandthenweclosebackaboveagain.ItlookslikeahammerwhereI>>Itlookslikeithas>>Right.Imagineyouhaveaoneofthemallethammers.I..."
X1     WQycR82IOD4   04:45:19   trade off of a trade (HTF nest)
                                "...ingandthenfindaoneminuteentryoutofthatrallygap.So,it'satradeoffofatrade.Doesthatmakesense?So,ourmainmethodtofindthebestentriesaregoingtobemarkingahighertime..."
X2     r43i9rRIjoQ   10:02:03   stop anchors to the HTF zone
                                "...o,it'snot.Itjustwickedbelow.Seewhatjusthappened?So,Igotstoppedoutontheoneminutetimeframe,butwestillheldthefiveminuteforgapjustasthevideosaid,andweendupgoingwaytotheupside.Allright.AndwehitthatTP,..."
T1     r43i9rRIjoQ   08:25:54   targets are highs and lows, not R
                                "...et2everytime?Yeah.Allright.There'sareason,right?95%ofmytargetsarealwayshighsandlows,guys.Allright.They'realwayshighsorlowsthere.It'snotjusttwoR.SowhenIsay,"Oh,we'reonly..."
T1b    r43i9rRIjoQ   08:27:20   market cannot see your RR tool
                                "...djustfor2R,whichisanarbitrarynumber.Doyouthinkthemarketseesyourlittleriskrewardpositiontoolonthescreen?>>No.>>No,ititdoesn't.Doyouthinkitseesthehighsandlowsonthecan..."
T3     WQycR82IOD4   05:53:59   breakeven at 1R
                                "...Iwouldhavemovedon.Soraiseyourhandifyouthinkyouwouldhavemovedthestoptobreakeven.>>100%.Becauseshouldwebereversinghere?>>No.>>Whatdidwejustcreatehere?>>Equal.>>Anoth..."
T4     WQycR82IOD4   04:58:28   two-loss rule
                                "...tolikeanyprofessionaldaytrader,they'llusuallysaythey'redoneaftertwolosses.EvenifIthinkI'minsyncwiththemarketandItooktwolossesandIseelikeanotherreallyreallygoo..."
T4b    WQycR82IOD4   04:55:39   daily lockout feature
                                "...brokerwhichyoucanputmoneyinorpropfirmsandthere'scalledadailylockoutfeature.Whatdoyouthinkadailylockoutfeaturedoes?>>Yeah.Whatdoyouthink?>>Yeah.>>Like>>Y..."
S1     WQycR82IOD4   07:22:57   SMT is fifth in the checklist
                                "...arketcircuit,allthatstuffbeforeIlookforanSMT.Thisislikefifthinmychecklist.Okay,somepeoplegetcarriedawayandtrytomakesurethere'sanSMTeverytrade,butIdon'tdothat...."
S1b    WQycR82IOD4   07:15:32   do not trade SMT religiously
                                "...llright.Okay,writedownthisSMTequalssmartmoneytechnique.Donottradethisreligiously.JustbecausewehaveanSMTdoesnotmeanwe'regoingtoreverse,butitcanbeasignofareversal.Allr..."
P2     WQycR82IOD4   01:49:16   order block = sandwich candle
                                "...ok.>>No.Okay,thisisbasicallyyourorderblock.Theredcandlesandwichbetweentwogreencandles.ThegreencandlesmatterandthethisislikethisiswhatwecallanOB.Sowh..."
P4     WQycR82IOD4   09:15:50   breaker = failed order block
                                "...lstarttoseeallthis.Abreakerblock.>>No,I'mnotdoingthat.Abreakerblockis>>afailedorderblock.Likeit'safailedorderblock.EverysinglePDarraythereiscantechnicallybeaninverse.Raiseyo..."
K2     WQycR82IOD4   01:14:25   NY AM is the primary session
                                "...edtotradebecauseumthat'sjusthowfutureswork.So,thisistheprimarysession.Ithasthebestvolume.Andremember,thebestvolumeequalswhatvolatility?>>Usuallyhighvolati..."
M1     WQycR82IOD4   07:32:43   macro times
                                "...t'snotexactbutlessthanthat.Sothesearejustmoreterms.Okaymacrotimesumthere'ssomethingcalledmacrotimes.Thesearetimeswherepriceisverylikelytorunahigherlo..."
R1     WQycR82IOD4   07:35:51   10am is a reversal time
                                "...smove,knowingwhenit'sgoingtoreverse.Writedownyournotes.10a.m.equalsgreatreversaltime.There'ssomethingcalledP3,whichisapowerofthree.Um,okay.Whounderstandsthisconcept?..."
J1     WQycR82IOD4   01:11:28   Judas swing = false move at open
                                "...the1minuteandthenitfadesitandgoesdown.That'swhatwecallaJudahswing.Soit'slikeafakemoveatopen.Whydoyouthinkwemightgetalotoffakemovesatopen?>>Okay.Whatdo..."
F1     r43i9rRIjoQ   08:38:53   big overnight move -> choppy AM
                                "...essionwetendtotobechoppy.So,Iwantyoutowriteinyournotes,bigovernightmoveequalschoppyorsidewaysNewYorkAMsession.Thatisveryimportanttounderstand.>>Choppy,>>cho..."
F1b    r43i9rRIjoQ   08:39:30   300 points is substantial
                                "...h.Nowyoucanputanarrowfromthewordbigandbeandsaymaybelike300ishpluspoints.Soyou'reprobablywonderinglikewhat'sabigovernightmove?Isit50points?Isittwop..."
DW     WQycR82IOD4   07:48:34   data wick ~85% same day
                                "...amework.Allright.Now,there'sstatisticsthattellme80about85%ofthetimeyouformanewswicklikethat,wewillhititinthesameday.Isthatgoodinformationtoprobablyknow?>>Why?Be..."
DW2    WQycR82IOD4   07:42:23   one setup for life
                                "...elves.Allright.Ididnotlearnthisfromanyone.ButIcallittheonesetupforlife.IfIcanonlytakeonesetfortherestofmylife,thiswouldbeit.Allright.Thiswillmakethisisaver..."
P5     WQycR82IOD4   01:09:02   premium/discount, buy discount
                                "...kay,thisisathat'sthenumberonePDarrayinmyopinionandit'sapremiumanddiscountarraywhichIrememberwho'srememberwhenwetalkedaboutpremiumdiscountkindoffromtheYouTubev..."
--------------------------------------------------------------------------------------------------------------
attached 38/38 rules; 0 unattached
