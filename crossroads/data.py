"""Facts the whole site shares: services, addresses, people, links.
Change a thing here and every page that mentions it changes."""

SITE = "Crossroads Christian Church"
SITE_SHORT = "Crossroads"
TAGLINE = "One church in Canberra, four Sunday services: 9.30am in Braddon and Belconnen, 6.30pm at ANU and in Belconnen."
BASE_URL = "https://crossroads.org.au"
OFFICE_EMAIL = "office@crossroads.asn.au"
YOUTH_EMAIL = "youth@crossroads.asn.au"
INCIDENTS_EMAIL = "incidents@crossroads.asn.au"
DIVORCECARE_EMAIL = "divorcecare@crossroads.asn.au"
STORIES_EMAIL = "anita@crossroads.asn.au"

CENTRE = dict(
    name="Crossroads Ministry Centre",
    line1="Level 1, 8 Chandler Street",
    line2="Belconnen ACT 2617",
    note="Entrance off Margaret Timpson Park, opposite Westfield Belconnen.",
    maps="https://www.google.com/maps/search/?api=1&query=8+Chandler+Street+Belconnen+ACT+2617",
)

FACEBOOK = "https://www.facebook.com/CrossroadsCanberra"
INSTAGRAM = "https://www.instagram.com/crossroadscbr/"
CLASSIFIEDS = "https://www.facebook.com/groups/CrossroadsClassifieds"
ELVANTO = "https://crossroadschurch.elvanto.com.au"
GIVENOW = "https://www.givenow.com.au/crossroadschurch"
APPLE_PODCASTS = "https://podcasts.apple.com/au/channel/crossroadscbr/id6445546663"
SPOTIFY = "https://open.spotify.com/user/crossroadscbr"
YOUTUBE = "https://www.youtube.com/channel/UC2HVSrTcCfJQ6Lw7g2wdjaw"
SERMON_LIBRARY = "https://subsplash.com/u/-KQBRDK/media/embed/d/*?"
SERMON_VIDEO = "https://www.youtube.com/embed/dMCf9smYbP8?rel=0&autoplay=1"
APP_IOS = "https://itunes.apple.com/us/app/id1046672842?mt=8&uo=4"
APP_ANDROID = "https://play.google.com/store/apps/details?id=com.customchurchapps.crossroadschristianchurch"
FIEC = "https://www.fiec.org.au/"
MTS_ORG = "https://mts.com.au/"
AFES = "https://support.afes.org.au/"
DIVORCECARE_ORG = "https://find.divorcecare.org/groups/302176"
CROSSROADS_ENGLISH_FB = "https://www.facebook.com/CrossroadsEnglishForSpeakersOfOtherLanguages"

FORM_PARTNERSHIP = "https://crossroadschurch.elvanto.com.au/form/cf63d1d2-ca1c-421d-96ef-c51a1066297b"
FORM_NEWSLETTER = "https://crossroadschurch.elvanto.com.au/form/7be6636a-9987-40de-8b66-77af3a98a910"
FORM_SAFE_MINISTRY = "https://crossroadschurch.elvanto.com.au/form/d2e3e0bf-d449-4af7-946a-309388157bc9"
FORM_REPORT = "https://form.jotform.com/241791257932059"
FORM_EVENT = "https://form.jotform.com/241697985585076"
FORM_VENUE = "https://form.jotform.com/243147791025052"
FORM_KIDS_VISITOR = "https://docs.google.com/forms/d/e/1FAIpQLSdF1FrqWFzOlX1q0txIdjpRNA9n9X8JtpZavGTmLbpYM_xqVw/viewform"
FORM_YOUTH_VISITOR = "https://docs.google.com/forms/d/e/1FAIpQLSfIQvO4x6YIzLkrXvlfRNBrLHwMPlHH5G2saQNhMItI6owpWw/viewform"

BANK = dict(name="Crossroads Christian Church", bsb="062-919", acct="10115993")

SERVICES = [
    dict(
        slug="north", name="North", full="Crossroads North", time="9.30", ampm="am",
        when="Sundays at 9.30am", venue="Merici College Auditorium", addr="Wise Street, Braddon ACT 2612",
        area="the inner north", img="north", img2="north-2", pos="nw",
        maps="https://www.google.com/maps/search/?api=1&query=Merici+College+Wise+Street+Braddon+ACT+2612",
        fb="https://www.facebook.com/groups/566884763463245",
        card="https://docs.google.com/forms/d/e/1FAIpQLSd66bcbI5Le4W-9evJ2pHzQ3fO3i5ykNxxtlGpJOT7ECb7NEQ/viewform",
        kids=True, connect="Connect Lunch", pastor="Marcus Reeves", kids_pastor="Sarah Rootes",
        blurb="Right in the heart of Canberra's inner north. A church family of all ages and stages, with kids and youth programs every Sunday morning.",
    ),
    dict(
        slug="belconnen", name="Belconnen", full="Crossroads Belconnen", time="9.30", ampm="am",
        when="Sundays at 9.30am", venue="Lake Ginninderra College Gym", addr="2 Emu Bank, Belconnen ACT 2617",
        area="Belconnen", img="belconnen", img2="belconnen-2", pos="ne",
        maps="https://www.google.com/maps/search/?api=1&query=Lake+Ginninderra+College+2+Emu+Bank+Belconnen+ACT",
        fb="https://www.facebook.com/groups/695327337248531",
        card="https://docs.google.com/forms/d/e/1FAIpQLSdSZ3L9_3jE9bdOapnL_iyJMY69MVwIYmRXGKtd_CFz7kZegQ/viewform",
        kids=True, connect="Connect Lunch", pastor="Simon Nixey", kids_pastor="Kerryn Rudder",
        blurb="Our morning church family in Belconnen, keen to reach this part of Canberra and beyond, with children's and teens' ministry each Sunday.",
    ),
    dict(
        slug="city", name="City", full="Crossroads City", time="6.30", ampm="pm",
        when="Sundays at 6.30pm", venue="Manning Clark Hall", addr="Kambri Cultural Centre, ANU, Acton ACT 2601",
        area="the city and ANU", img="city", img2="city-2", pos="sw",
        maps="https://www.google.com/maps/search/?api=1&query=Manning+Clark+Hall+Kambri+ANU+Acton+ACT",
        fb="https://www.facebook.com/groups/637217603044376",
        card="https://docs.google.com/forms/d/e/1FAIpQLScFptl_31f21dAEFgsqt1sDLac5UU8UMYdyKGQp2mAyIGikoQ/viewform",
        kids=False, connect="Connect-In", pastor="Simon Nixey", kids_pastor=None,
        blurb="Especially keen to reach students and young workers from across Canberra. Strong links to the ANU campus, and people from all over Australia and the world.",
    ),
    dict(
        slug="lake-g", name="Lake G", full="Crossroads Lake G", time="6.30", ampm="pm",
        when="Sundays at 6.30pm", venue="Crossroads Ministry Centre", addr="Level 1, 8 Chandler Street, Belconnen ACT 2617",
        area="Lake Ginninderra and the University of Canberra", img="lake-g", img2="lake-g-900", pos="se",
        maps=CENTRE["maps"],
        fb="https://www.facebook.com/groups/513940419628219",
        card="https://docs.google.com/forms/d/e/1FAIpQLSfYxdeAV6k31rQ2Z1H5HE395O09Jo9yPWSy7ZBDkUs8s0hUVQ/viewform",
        kids=False, connect="Connect-In", pastor="Revin Blanchard", kids_pastor=None,
        blurb="Keen to reach students and young workers. Anyone and everyone is welcome, and every Sunday we share dinner together after the service.",
        dinner=True,
    ),
]
SVC = {s["slug"]: s for s in SERVICES}

STAFF = [
    ("Marcus Reeves", "Senior Pastor and Point Pastor, North", "marcus-reeves", "marcus@crossroads.asn.au"),
    ("Kerryn Rudder", "Connect and Children, Belconnen", "kerryn-rudder", "kerryn@crossroads.asn.au"),
    ("Owen Chadwick", "Grow and Global Mission", "owen-chadwick", "owen@crossroads.asn.au"),
    ("Simon Nixey", "Belconnen, City and Serve; MTS Pastor", "simon-nixey", "simon@crossroads.asn.au"),
    ("Revin Blanchard", "Point Pastor, Lake G, and Reach", "revin-blanchard", "rblanchard@crossroads.asn.au"),
    ("Sarah Rootes", "Kids and Youth", "sarah-rootes", "sarah@crossroads.asn.au"),
    ("Andy Copeman", "Youth Pastor", "andy-copeman", "andy@crossroads.asn.au"),
    ("Annabel Nixey", "Grow", "annabel-nixey", "annabel@crossroads.asn.au"),
    ("Cassandra Buttsworth", "Student Pastor: Serve, Lake G and Belconnen", "cassandra-buttsworth", "cassandra@crossroads.asn.au"),
]

COUNCIL = [
    ("Marcus Reeves", "Chair"), ("Matt Miller", "Treasurer"), ("Kristen Tripet", "Secretary"),
    ("Doug Griffin", "Member"), ("Alison Brake", "Member"), ("Rob Roper", "Member"),
]

BOARD = [
    ("Archie Poulos", "Experienced church planter and consultant; lecturer at Moore College."),
    ("Andrew Heard", "Senior Pastor at EV Church on the Central Coast."),
    ("Andrea Pryde", "Connect Grow Serve Director at Living Church, Brisbane."),
    ("Bryson Smith", "Senior Pastor at Bathurst Presbyterian."),
    ("Peter Nelson", "Previously minister at the Austral-Asian Church; chaplain at the AIS; ministry consultant to many Canberra churches."),
    ("Rick Lewers", "Minister at St Peter's, Shoalhaven Heads."),
    ("Derek and Anna Brotherson", "Derek is Principal of the Sydney Missionary and Bible College (SMBC), where Anna also lectures and serves in the college community."),
]

CONSTITUTION = "https://drive.google.com/file/d/10US17GAOv90CJ-Yej83yjFrMtQkw276Q/view?usp=sharing"

POLICIES = [
    ("Crossroads Christian Church Constitution", "https://drive.google.com/file/d/10US17GAOv90CJ-Yej83yjFrMtQkw276Q/view?usp=sharing"),
    ("Staff Code of Conduct", "https://drive.google.com/file/d/11_gCXwr55uxA21-gXHbdM4nyfQd07z4Q/view?usp=sharing"),
    ("Volunteer Code of Conduct", "https://drive.google.com/file/d/18XQ8Htyld9-xzZGREVZdcWkm7wt-7ZvP/view?usp=sharing"),
    ("Privacy Policy", "https://drive.google.com/file/d/1x4YipwTQtuHrTS-8NWTTvxNNxxmAIDbE/view?usp=sharing"),
    ("Incident Reporting and Complaints Policy", "https://drive.google.com/file/d/1U1VCD7LXqXebDqtXekq679H-xB7k9B-d/view?usp=sharing"),
]
SAFE_POLICIES = [
    ("Safe Ministry Policy", "https://storage1.snappages.site/KQBRDK/assets/files/WHS01-Work-Health-and-Safety-Policy.pdf"),
    ("Safe Ministry Guidelines", "https://storage1.snappages.site/KQBRDK/assets/files/WHS02-Work-Health-and-Safety-Guidelines-22.pdf"),
    ("Domestic and Family Violence Policy", "https://storage1.snappages.site/KQBRDK/assets/files/SM03-Domestic-and-Family-Violence-Policy-47.pdf"),
    ("Work Health and Safety Policy", "https://storage1.snappages.site/KQBRDK/assets/files/WHS01-Work-Health-and-Safety-Policy.pdf"),
    ("Work Health and Safety Guidelines", "https://storage1.snappages.site/KQBRDK/assets/files/WHS02-Work-Health-and-Safety-Guidelines-22.pdf"),
    ("Peacemaker Guidelines", "https://storage1.snappages.site/KQBRDK/assets/files/SM04-Peacemaker-Guidelines-1.pdf"),
]

VIDEOS = {
    "welcome": ("545352758", "Welcome to Crossroads", "2 min"),
    "history30": ("1172050786", "30 years of Crossroads: Marcus Reeves", "7 min"),
    "history25": ("516022286", "Dave McDonald and Marcus Reeves on 25 years of Crossroads", "21 min"),
    "english1": ("522575591", "Crossroads English", "1 min"),
    "english2": ("1227225237", "Crossroads English classes", "1 min"),
    "dc1": ("704768486", "What DivorceCare is", "3 min"),
    "dc2": ("915016891", "Kim on DivorceCare", "2 min"),
    "jol": ("365676232", "Jesus on Life", "1 min"),
    "wtl": ("1064982176", "Word to Life podcast", "2 min"),
}
JOL_STORIES = [
    ("1121386506", "Phil, Crossroads Belconnen", "3 min"),
    ("1074567152", "Steph and Wes", "3 min"),
    ("1074567207", "Amy and Rhett", "3 min"),
    ("880745502", "Jesus on Life at Springfest", "3 min"),
    ("912409256", "James and Kelly", "4 min"),
    ("912804520", "Kate and Sarah", "10 min"),
    ("626101883", "Ben", "2 min"),
    ("695957192", "Josh", "2 min"),
    ("761672144", "Lianne", "2 min"),
    ("625133028", "Lucy", "4 min"),
]

STORIES = [
    ("trevor-belconnen-2026", "Trevor", "Belconnen, 2026", "5r5f3ys", "", "story-crowd"),
    ("angus-city-2026", "Angus", "City, June 2026", "qpsf67p", "", "city-2"),
    ("genevieve-city-2026", "Genevieve", "City, June 2026", "4npx72v", "", "story-woman"),
    ("darren-north-2025", "Darren", "North, September 2025", "fkzzjcr",
     "Darren grew up on a farm in northern NSW and, after seasons living in Canberra and on the South Coast, has recently returned to Canberra and Crossroads. Looking back, he recalls a time on the South Coast when he was challenged to put God first, even standing against a minister who wasn't putting God's word first. As you hear his story, may you be encouraged to stay grounded in God's truth and courageous in following Jesus, whatever the cost.", "north-2"),
    ("choi-family-city-2025", "The Choi family", "City, 2025", "nwc8wg8",
     "None of us knows what tomorrow will bring, and that can feel overwhelming. The Choi family's story shows what it looks like to pray and keep trusting God even when the future feels uncertain. As you listen, may you be encouraged to place your own unknowns into the hands of the One who holds all things together.", "city-group"),
    ("blessy-north-2025", "Blessy", "North, 2025", "g47mkhg",
     "Life can feel unbearably heavy when suffering hits, but Blessy's story reminds us that even in the darkest moments, God is near. As you hear her journey, we pray you'll see how turning to Him brings comfort, hope and strength that nothing else can give.", "interview"),
    ("al-s-story-north-2024", "Al", "North, October 2024", "gbhjxvs", "Come and listen to Al's story.", "stage-chat"),
    ("emma-belconnen-2023", "Emma", "Belconnen, 2023", "tv43jqf", "", "belconnen-2"),
    ("debbie-november-2022", "Debbie", "November 2022", "kxz5c2k", "", "stage-two"),
    ("jo-november-2022", "Jo", "November 2022", "22vst63", "", "listening"),
    ("mackenzie-november-2022", "Mackenzie", "November 2022", "xmvs7px", "", "conversation"),
    ("stephanie-november-2022", "Stephanie", "November 2022", "k5g9ppp", "", "two-women"),
]

WTL_EPISODES = [
    ("Joy revival (Romans 5)", "16 September 2026", "Annabel Nixey", "b963hrr"),
    ("Guaranteed by God (Romans 4)", "9 September 2026", "Annabel Nixey and Andy Copeman", "5q3r39g"),
    ("I quit! The job God wants you to give up (Romans 4)", "2 September 2026", "Annabel Nixey and Andy Copeman", "m2k9kp3"),
    ("God's rightness is revealed (Romans 3)", "26 August 2026", "Annabel Nixey and Simon Nixey", "6sktgmn"),
    ("Jesus has never failed a sinner (Luke 7)", "19 August 2026", "Annabel Nixey and Marcus Reeves", "h5h6gdw"),
    ("God has no favourites (Romans 2)", "4 August 2026", "Annabel Nixey and Kevin Yeung", "w96q6ww"),
    ("When good behaviour becomes a bad foundation (Romans 2)", "29 July 2026", "Cassandra Buttsworth and Aisha Dunkley", "px54vvk"),
    ("The obedience of faith (Romans 1)", "22 July 2026", "Owen Chadwick and Annabel Nixey", "4dx3j4m"),
    ("Hope in the rubble (Jeremiah 52)", "15 July 2026", "Annabel Nixey and Simon Nixey", "2c46283"),
    ("The joy of smallness (Jeremiah 45)", "1 July 2026", "Annabel Nixey and Simon Nixey", "5bckwjh"),
    ("Sin makes us do stupid things (Jeremiah 44)", "24 June 2026", "Annabel Nixey", "nsv85q3"),
    ("God, the changemaker (Jeremiah 34)", "17 June 2026", "Annabel Nixey and Simon Nixey", "dwvrw3y"),
]

MTS_PASTOR = ("Simon Nixey", "MTS Pastor", "simon-nixey", "simon@crossroads.asn.au")
MTS_CURRENT = [
    ("Amy Wiles", "MTS 2026–27", "amy-wiles", "Amy grew up attending Cooma Baptist Church. She joined Crossroads in 2011 as a student and never left. She is serving at the North and Lake G congregations."),
    ("Emily Gates", "MTS 2025–26", "emily-gates", "Emily grew up in Canberra and has been part of Crossroads her whole life. She is excited to serve at the City and Belconnen congregations."),
    ("Aisha Dunkley", "MTS 2025–26", "aisha-dunkley", "Aisha arrived in Canberra in 2018, walked into Crossroads and called it home. God has been growing her love of the church, and she is excited to serve at City and Belconnen."),
]
MTS_COLLEGE = [
    ("Willis Lo", "MTS 2024–25", "willis-lo", "Part of the Crossroads family since 2018, serving in the Belconnen and City congregations.", "willis.lo733@gmail.com"),
    ("Alice Gerty", "MTS 2024–25", "alice-gerty", "Alice grew up in Newcastle, where she became a Christian through the local youth group, and joined Crossroads in 2022. She serves at North and City.", "alice.gerty@gmail.com"),
    ("Wira Wibowo", "MTS 2023–24", "wira-wibowo", "Studying a Bachelor of Theology at Moore Theological College after finishing MTS in 2024.", "wirahandokowibowo@gmail.com"),
    ("Caleb Dallos", "MTS 2023–24", "caleb-dallos", "Studying a Bachelor of Theology at Christ College in Sydney after finishing MTS in 2024.", "caleb.dallos@gmail.com"),
    ("Andy and Bethany Rowlands", "MTS 2023–24", "andy-rowlands", "At Moore Theological College after Andy finished MTS in 2024.", "rowlands.a96@gmail.com"),
    ("Davey and Charlotte Lovell", "MTS 2023–24", "davey-lovell", "At Moore Theological College after Davey finished MTS in 2024.", "daveylovell00@gmail.com"),
    ("Jennifer Tait", "MTS 2021–22", "jennifer-tait", "Studying a Bachelor of Theology at Moore Theological College after finishing MTS in 2022.", "jenj02@outlook.com"),
    ("Ming En-Chin", "MTS 2021–22", "ming-en-chin", "Studying at Moore College and serving as a student minister at South West Evangelical Church in their Bankstown service.", "mingenchin@gmail.com"),
]
MTS_NOW = [
    ("Caitlin Roberts", "MTS 2019–20", "caitlin-roberts", "From the blue skies of Canberra to the blue skies of the Sunshine Coast: since January 2024 Caitlin has been Children and Youth Pastor at Lakeshore Community Church of Christ.", "Roberts.caitlintherese@gmail.com"),
    ("Lizzy Hammond", "MTS 2023–24", "lizzy-hammond", "Part of the Crossroads family since 2019, when she moved to Canberra to work as a nurse. She serves in the Belconnen and Lake G congregations.", "elizabethannahammond@gmail.com"),
]

PARTNERS = {
    "north": [("phil-lil-west-asia", "Phil and Lil, West Asia"), ("wilsons-italy", "The Wilsons, Italy")],
    "belconnen": [("dave-jenny-west-africa", "Dave and Jenny, West Africa"), ("grocotts-romania", "The Grocotts, Romania"), ("jemma-phen-sydney", "Jemma with Phen, Sydney (regional partner)"), ("m-2", "M, global partner")],
    "city": [("dave-jenny-west-africa", "Dave and Jenny, West Africa"), ("hickels-germany", "The Hickels, Germany"), ("kelly-nicholas-japan", "Kelly Nicholas, Japan")],
    "lake-g": [("jemma-phen-sydney", "Jemma with Phen, Sydney (regional partner)"), ("grocotts-romania", "The Grocotts, Romania"), ("m-1", "M, global partner")],
}

BELIEFS = [
    ("God", "There is only one God, who exists in three persons: Father, Son and Spirit, in perfect unity. God is the almighty and loving Creator, Saviour and Judge who sustains and governs all things according to his sovereign will for his own glory."),
    ("The Bible", "The Bible is the God-breathed and infallible word of God. This precious, life-giving word is sufficient for our knowledge of God and the supreme authority in all matters of faith and conduct."),
    ("Humanity", "All people, men and women, are created in God's image and are called to love God with their whole beings. Since the fall, however, all people are guilty of rebellion against God and human nature has been thoroughly corrupted by sin. This means that everyone is subject to God's righteous anger and condemnation."),
    ("Jesus Christ", "God demonstrated his love towards us by sending us his Son, the Lord Jesus Christ, who is both fully God and fully human. Jesus was conceived by the Holy Spirit, born of a virgin, and lived a sinless life in obedience to the Father. Jesus died on the cross, rose bodily from the dead, ascended into heaven and is now exalted as ruler over all things."),
    ("Salvation", "Salvation is entirely the gracious gift of God which cannot be earned or deserved. It is accomplished through the atoning death, once for all time, of our representative and substitute, Jesus Christ, the only mediator between God and sinful people. By Jesus' death God's anger is turned aside, we are redeemed from sin and death, and we are declared to be righteous in God's sight. This salvation is offered in the gospel and received by turning to God from sin and trusting in Jesus Christ."),
    ("The Holy Spirit", "The Holy Spirit has been sent from heaven by the Father and the Son. He enables people to turn to God, the Father, and to trust Jesus Christ, the Lord. He makes the death of Christ effective to individual sinners, imparting spiritual life. God's Spirit dwells in all those whom he has regenerated, producing in them likeness to Christ in their attitudes, actions and speech."),
    ("The people of God", "The Lord Jesus Christ builds the Church, his people, through the proclamation and teaching of his word. All who have been saved through the work of Christ are members of his Church and united with one another. God has equipped his people with gifts to be used for mutual edification in the Church, for good works, and for the proclamation of the gospel to the world."),
    ("The future", "The Lord Jesus Christ will return from heaven. He will execute God's judgement on all who have not turned to God through Jesus Christ, and he will welcome his people into a life of eternal joy in fellowship with God. On that day all sin, suffering and death will be completely destroyed and God will be glorified forever."),
]

NAV = [
    ("I'm new", "/im-new/"),
    ("Sundays", "/sundays/"),
    ("Kids & youth", "/kids/"),
    ("Connect", "/connect/"),
    ("Sermons", "/teaching/"),
    ("About", "/about/"),
    ("Contact", "/contact/"),
]
CTA = ("Plan a visit", "/im-new/")

# Short excerpts from public Google reviews of Crossroads, quoted word for word
# with first names only. The church should confirm it is happy to show them.
REVIEWS = [
    ("The first day we were met at the door and welcomed.", "Carly", "visiting Crossroads North with her son"),
    ("I really like how the church goes through books of the Bible sequentially, so we can see what it says and how we can apply it to our lives.", "Jordan", "attending for two years"),
    ("A welcoming church, offering patient answers to life-related questions, not just spiritual concerns.", "Rachel", "Google review"),
    ("The people here are so warm and friendly without being pushy. The teaching was heartfelt, well-researched and practical for my life.", "Lynn", "Google review"),
    ("Crossroads was my first contact for church on my first week in Canberra. I was always welcomed and taken care of. I felt like home.", "Yan", "new to Canberra"),
]

MENU = [
    ("Visit", [("I'm new", "/im-new/"), ("Sundays", "/sundays/"), ("Kids", "/kids/"), ("Youth", "/youth/"), ("Who is Jesus?", "/who-is-jesus/")]),
    ("Get involved", [("Connect", "/connect/"), ("Growth groups", "/growth-groups/"), ("Jesus on Life", "/jesus-on-life/"), ("Serve", "/serving/"), ("Give", "/giving/"), ("Events and venue hire", "/events/")]),
    ("Sermons and teaching", [("Sermons", "/sermons/"), ("Word to Life podcast", "/word-to-life/"), ("Bible studies", "/bible-studies/"), ("Crosstrain", "/crosstrain/"), ("Resources", "/resources/"), ("Apps", "/apps/")]),
    ("About", [("Who we are", "/who-we-are/"), ("What we believe", "/what-we-believe/"), ("Stories", "/stories/"), ("History", "/history/"), ("Global partners", "/global-partners/"), ("MTS", "/mts/"), ("Policies and safe ministry", "/policies/"), ("Employment", "/employment/"), ("Contact", "/contact/")]),
]

# Old site addresses that should keep working.
REDIRECTS = {
    "/i-m-new": "/im-new/",
    "/visiting-1": "/im-new/",
    "/9-30-am-north": "/sundays/north/",
    "/9-30-am-belconnen": "/sundays/belconnen/",
    "/6-30-pm-city-anu": "/sundays/city/",
    "/6-30-pm-lake-g-uc": "/sundays/lake-g/",
    "/kids": "/kids/",
    "/youth": "/youth/",
    "/connecting-1": "/connect/",
    "/connect-card": "/connect-card/",
    "/connect-in": "/connect-lunch/",
    "/growth-groups-test-2026": "/growth-groups/",
    "/jesus-on-life": "/jesus-on-life/",
    "/divorce-care": "/divorce-care/",
    "/crossroads-english": "/english/",
    "/partnership": "/partnership/",
    "/apps": "/apps/",
    "/about-1": "/about/",
    "/who-we-are": "/who-we-are/",
    "/what-we-believe": "/what-we-believe/",
    "/crossroads-stories": "/stories/",
    "/crossroads-history": "/history/",
    "/global-regional-partners": "/global-partners/",
    "/mts": "/mts/",
    "/policies-and-reporting": "/policies/",
    "/contact-us": "/contact/",
    "/employment": "/employment/",
    "/teaching-1": "/teaching/",
    "/online-bible-talks": "/sermons/",
    "/library-of-bible-talks": "/sermons/",
    "/word-to-life-podcast": "/word-to-life/",
    "/library-of-bible-studies": "/bible-studies/",
    "/leaders-bible-study-resources": "/bible-studies/",
    "/recommended-resources": "/resources/",
    "/crosstrain": "/crosstrain/",
    "/training-opportunities": "/crosstrain/",
    "/serving-1": "/serving/",
    "/want-to-serve": "/serving/",
    "/giving": "/giving/",
    "/events": "/events/",
    "/who-is-jesus": "/who-is-jesus/",
}


def S(kind, data=None, **opts):
    """One section of a page: what kind of block it is, its content, and
    the section's own title, lede and colour."""
    d = dict(kind=kind, data=data)
    d.update(opts)
    return d
