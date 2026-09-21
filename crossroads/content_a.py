"""Pages: home, I'm new, Sundays and the four services, kids, youth, and the
Connect family of pages. Words are Crossroads' own wherever they had them."""
from data import *  # noqa: F401,F403
from data import S, SERVICES, SVC, STORIES, REVIEWS, CENTRE, OFFICE_EMAIL, YOUTH_EMAIL, DIVORCECARE_EMAIL, CLASSIFIEDS, \
    VIDEOS, JOL_STORIES, FORM_KIDS_VISITOR, FORM_YOUTH_VISITOR, FORM_PARTNERSHIP, DIVORCECARE_ORG, \
    CROSSROADS_ENGLISH_FB, APP_IOS, APP_ANDROID, SERMON_LIBRARY, SERMON_VIDEO, APPLE_PODCASTS, SPOTIFY

PAGES = []

KIDS_PROGRAM = (
    "<p>Kids and youth are valued greatly as members of our church family. Crossroads seeks to build lifelong "
    "disciples of Jesus Christ, so we deeply treasure the chance to teach people of all ages the Bible.</p>"
    "<p>At Kids@Church and Youth@Church, our young members learn from the Bible through age-appropriate activities: "
    "Bible studies, games, singing, craft and drama. Both begin part way through the service, so the whole church "
    "family meets together as one body before continuing in age-appropriate spaces.</p>"
    "<p>The school-age groups (Kindergarten to Year 9) learn from the same Bible passage as their parents where "
    "suitable, so the whole church learns and grows together. The under-fives work through foundational Bible "
    "stories and themes that help them grasp God’s love for them.</p>"
)

CONNECT_IN = (
    "<p>If you’re new, we’d love to help you get connected. Connect-In happens before the service and is a relaxed "
    "way to meet other newcomers, church members and some of the pastoral team. It’s designed to help you feel at "
    "home and take your first steps into the life of our church.</p>"
    "<p>You’ll hear the “who”, “why” and “what” of Crossroads, a little about how our church works, and have space "
    "to ask your questions in a friendly, informal setting.</p>"
)

CONNECT_LUNCH = (
    "<p>If you’re new to Crossroads and coming to a morning service, we’d love to have you as our guest at a "
    "Connect Lunch. It’s a relaxed way to meet some of our pastors and get to know other newcomers.</p>"
    "<p>Over lunch you’ll hear a little about who we are, why we exist and what matters most to us as a church. "
    "There’s plenty of space to ask questions and get a feel for what life at Crossroads is like.</p>"
)

# ---------------------------------------------------------------- home
PAGES.append(dict(
    slug="", title="Crossroads Christian Church Canberra",
    desc="One church meeting in four places across Canberra every Sunday: North and Belconnen at 9.30am, City and Lake G at 6.30pm. Come as you are.",
    sections=[
        S("services", title="Four services. One church family.",
          lede="Not sure which one? Come to any of them. You don’t need to know the Bible, have everything sorted, or pretend to be someone you’re not.",
          cta=("What to expect", "/im-new/")),
        S("split", dict(img="sunday-wide", alt="A full hall at a Crossroads Sunday service", html=(
            "<h2>What a Sunday is like</h2>"
            "<p>We sing, pray, hear the Bible read and explained, and spend time together over morning tea or supper. "
            "Each service runs about 90 minutes. Someone will be there to welcome you and help you find your way.</p>"
            "<p>When you arrive, look for someone wearing a Crossroads lanyard. They can help you find the kids program, "
            "bathrooms, seating, morning tea, or simply answer your questions.</p>"
            "<p class=\"actions\"><a class=\"btn ghost\" href=\"/im-new/\">More on what to expect</a></p>"))),
        S("cards", [
            dict(title="Kids and youth", img="kids", alt="Children sitting on the floor at Kids@Church", href="/kids/",
                 text="Kids@Church and Youth@Church on Sunday mornings, KidsBlast and Crossfire on Friday nights.", go="Kids and youth"),
            dict(title="Connect", img="connect-lunch", alt="People eating together at a Connect Lunch", href="/connect/",
                 text="Connect Lunches, growth groups of 8 to 14 people, Jesus on Life, and ways to belong.", go="Ways to connect"),
            dict(title="Teaching", img="preach-1", alt="A pastor preaching from the Bible", href="/teaching/",
                 text="Sermons from all four services every week, the Word to Life podcast, Bible studies and Crosstrain.", go="Listen and learn"),
        ], plain=True, title="Beyond Sunday",
          lede="From Friday night kids and youth gatherings to midweek groups and chances to learn and grow, there’s a lot happening across the life of Crossroads."),
        S("band", dict(h2="Still working out what you believe about Jesus?",
                       html="Jesus is the most significant and influential figure in history. His claims are worth investigating, because if they are true, they change everything.",
                       href="/who-is-jesus/", label="Explore who Jesus is")),
        S("reviews", [REVIEWS[0], REVIEWS[1], REVIEWS[2], REVIEWS[4]], title="What people say",
          lede="From people who walked in the door not long ago."),
        S("stories", STORIES[:3], title="Stories from our church",
          lede="How Jesus has changed the lives of people at Crossroads. Honest, personal and still unfolding.",
          cta=("All stories", "/stories/")),
        S("sermons", title="Listen before you visit",
          lede="Every week we upload the talks from across our services. Hear what a Sunday sounds like."),
        S("address", dict(html=(
            "<p>The Ministry Centre is our office during the week and the home of Crossroads Lake G on Sunday evenings, "
            "KidsBlast and Crossfire on Friday nights, Crosstrain, Jesus on Life and DivorceCare.</p>")),
          title="Find us during the week", chalk=True),
    ],
))

# ---------------------------------------------------------------- I'm new
PAGES.append(dict(
    slug="im-new", title="I’m new",
    desc="New to church? You’re very welcome at Crossroads. What a Sunday is like, when and where we meet, and what there is for kids and teens.",
    lede="New to church? You’re very welcome. You don’t need to know the Bible, have everything sorted, or pretend to be someone you’re not.",
    photo="hall", photo_alt="A packed hall at a Crossroads Sunday service, seen from the back",
    actions=[("Find your Sunday", "/sundays/"), ("Fill in a Connect Card", "/connect-card/", "ghost")],
    sections=[
        S("split", dict(img="posters/545352758", alt="", html=(
            "<h2>Everything starts with Jesus</h2>"
            "<p>Through him, God gives life, meaning and hope, and he is the one we gladly centre our lives around. "
            "We long to see more and more people become lifelong disciples who help his good news reach further across "
            "Canberra and deeper into our community.</p>"
            "<p>We’re a church where anyone can come and explore Jesus for themselves. Whether you’re curious, sceptical, "
            "new to faith, or have followed him for many years, we want you to hear and experience the truth of who he is "
            "in a way that’s clear, grounded and gracious.</p>"
            "<p>We all need a church family that encourages us, challenges us, and walks with us as we learn to trust "
            "Jesus and serve his purposes. As we open the Bible together, we keep discovering the real Jesus: the one who "
            "speaks, leads and gives life.</p>"), rev=True)),
        S("video", VIDEOS["welcome"], title="Two minutes on who we are"),
        S("services", title="When and where we meet",
          lede="Four services, one church. Pick the one nearest you, or the time that suits you best."),
        S("facts", [
            ("How long", "About 90 minutes."),
            ("What happens", "We sing, pray, hear the Bible read and explained, and spend time together over morning tea or supper. You’ll hear clear, thoughtful teaching that shows how the Scriptures speak into real life."),
            ("Who will help", "Look for someone wearing a Crossroads lanyard. They can help you find the kids program, bathrooms, seating, morning tea, or simply answer your questions."),
            ("Kids and teens", "Morning services have a crèche for babies and toddlers, Kids@Church for primary-aged children, and Youth@Church during the Bible talk."),
            ("The feel of it", "Relaxed and friendly, and a community that aims to be theologically deep and spiritually warm. Everything we do centres on hearing God speak through the Bible and responding to him together."),
        ], title="What to expect"),
        S("reviews", [REVIEWS[0], REVIEWS[3], REVIEWS[2]], title="What it was like for others", chalk=True),
        S("cards", [
            dict(title="Kids", img="kids-2", alt="Children at Kids@Church", href="/kids/", text="Kids@Church on Sunday mornings and KidsBlast on Friday nights for Grades 3 to 6.", go="Kids at Crossroads"),
            dict(title="Youth", img="youth-sunset", alt="Teenagers on a hill at sunset", href="/youth/", text="Youth@Church on Sunday mornings and Crossfire on Friday nights for Years 7 to 12.", go="Youth at Crossroads"),
            dict(title="Connect Lunch", img="connect-lunch", alt="People sharing a meal", href="/connect-lunch/", text="Meet other new people, ask our pastors questions, and learn the ins and outs of how Crossroads works.", go="You’re invited"),
        ], plain=True, title="Bringing children or teenagers?",
          lede="Whether your family is familiar with church or exploring it for the first time, our kids and youth programs are welcoming places to make friends, ask questions and learn about Jesus from the Bible."),
        S("split", dict(img="jol-room", alt="A Jesus on Life evening at the Ministry Centre", html=(
            "<h2>Jesus on Life</h2>"
            "<p>If you would like to meet this extraordinary man, the Jesus of the Bible, who changed the world, come to "
            "Jesus on Life. If you don’t know who Jesus is but would like to learn more about this radical thinker and his "
            "claims, it’s for you too. Four casual evenings, a short talk, and your questions over coffee and dessert.</p>"
            "<p class=\"actions\"><a class=\"btn ghost\" href=\"/jesus-on-life/\">About Jesus on Life</a></p>"))),
        S("prose", (
            "<h2>New to Canberra and looking for a place to live?</h2>"
            "<p>The Crossroads Classifieds is a closed Facebook group for people who attend Crossroads, and for people moving to Canberra and looking for accommodation "
            "(say so when you apply). It’s the place to find or list a room, sell and swap second-hand goods, or offer a service.</p>"
            f"<p class=\"actions\"><a class=\"btn ghost\" href=\"{CLASSIFIEDS}\" rel=\"noopener\">Join Crossroads Classifieds</a></p>"), chalk=True),
        S("band", dict(h2="The best way to get to know us is simply to come along.", html="We’d love to see you this Sunday.", href="/sundays/", label="Find your Sunday")),
    ],
))

# ---------------------------------------------------------------- Sundays
PAGES.append(dict(
    slug="sundays", title="Sundays",
    desc="Crossroads meets in four places every Sunday: North and Belconnen at 9.30am, City and Lake G at 6.30pm.",
    lede="Four services. One church family. Every Sunday at 9.30 in the morning and 6.30 in the evening.",
    photo="worship", photo_alt="People standing to sing at a Crossroads service",
    sections=[
        S("services"),
        S("facts", [
            ("How long", "About 90 minutes, then morning tea or supper."),
            ("What happens", "We sing, pray, hear the Bible read and explained, and spend time together."),
            ("Kids and teens", "Crèche, Kids@Church and Youth@Church run at the two morning services, North and Belconnen."),
            ("After church", "Morning tea at North and Belconnen, supper at City, and dinner together at Lake G."),
            ("New here", "Look for someone wearing a Crossroads lanyard, and fill in a <a href=\"/connect-card/\">Connect Card</a> so we can be in touch."),
        ], title="What to expect"),
        S("notice", "Venues do change from time to time, and over Christmas and New Year the usual times and places don’t apply. "
                    f"If you’re planning a visit around then, check our <a href=\"{FACEBOOK}\" rel=\"noopener\">Facebook page</a> or email "
                    f"<a href=\"mailto:{OFFICE_EMAIL}\">{OFFICE_EMAIL}</a> first."),
        S("address", dict(html="<p>Not a Sunday venue for the morning services, but the home of Crossroads Lake G on Sunday evenings and of most things that happen during the week.</p>"),
          title="The Ministry Centre", chalk=True),
    ],
))

def service_page(s):
    morning = s["kids"]
    facts = [
        ("When", s["when"]),
        ("Where", f'{s["venue"]}<br>{s["addr"]}'),
        ("Map", f'<a href="{s["maps"]}" rel="noopener">Open {s["venue"]} in Google Maps</a>'),
    ]
    if morning:
        facts.append(("Kids and teens", "Crèche for babies and toddlers, Kids@Church for primary-aged children, and Youth@Church for Years 7 to 10, all starting part way through the service."))
        facts.append(("After church", "Morning tea."))
    else:
        facts.append(("After church", "Dinner together every week." if s.get("dinner") else "Supper."))
    facts.append(("New here", f'{s["connect"]}: a relaxed way to meet other newcomers and some of the pastoral team. '
                              f'<a href="{s["card"]}" rel="noopener">Fill in the {s["name"]} Connect Card</a> and we’ll tell you the next date.'))
    facts.append(("Facebook group", f'<a href="{s["fb"]}" rel="noopener">{s["full"]} Connections</a>, for meeting up, connecting socially and supporting one another.'))
    facts.append(("Pastor", f'<a href="/who-we-are/">{s["pastor"]}</a>' + (f', with {s["kids_pastor"]} for children’s ministry' if s.get("kids_pastor") else "")))
    intro = {
        "north": ("<p>We love being part of this vibrant part of Canberra and are eager to see the good news of Jesus reach the many people who live, work and study in the inner north and beyond. "
                  "Our church family includes people from all ages and stages, and our morning service offers children’s and youth programs to help young people engage with Jesus in a way that makes sense for them.</p>"),
        "belconnen": ("<p>Our morning church family in Belconnen is keen to reach this important area of Canberra and beyond. With children’s and teens’ ministry each Sunday, we want to see families and people of all ages and stages discipled.</p>"),
        "city": ("<p>Crossroads City is especially keen to reach students and young workers from across Canberra. With strong links to the ANU campus, we also welcome people from all over Australia and from different parts of the world.</p>"),
        "lake-g": ("<p>Our Lake G congregation is keen to reach students and young workers from across Canberra. Anyone and everyone is welcome, whether you’ve been at church before or are looking to find a new family in Canberra. "
                   "We share dinner together after the service every week.</p>"),
    }[s["slug"]]
    sections = [
        S("facts", facts, title="The details"),
        S("prose", intro + "<p>Church on Sunday is the key opportunity to hear from the Scriptures together, praise God in song, and encourage one another to live out the truth of the gospel.</p>",
          title=f"About {s['full']}"),
    ]
    if morning:
        sections.append(S("split", dict(img="kids", alt="Children at Kids@Church", html="<h2>Kids and youth on Sunday</h2>" + KIDS_PROGRAM +
                                        "<p class=\"actions\"><a class=\"btn ghost\" href=\"/kids/\">Kids</a><a class=\"btn ghost\" href=\"/youth/\">Youth</a></p>")))
        sections.append(S("prose", CONNECT_LUNCH + "<p>We host Connect Lunches regularly. Fill in a Connect Form, in person at church or online, and we’ll be in touch with details of the next one.</p>", title="New? Come to a Connect Lunch", chalk=True))
    else:
        sections.append(S("split", dict(img="city-2" if s["slug"] == "city" else "lake-g-900", alt="", html="<h2>New? Come to Connect-In</h2>" + CONNECT_IN +
                                        f"<p class=\"actions\"><a class=\"btn ghost\" href=\"{s['card']}\" rel=\"noopener\">Fill in the {s['name']} Connect Card</a></p>", rev=True)))
    sections.append(S("cards", [
        dict(title="Growth groups", img="growth-group", alt="", href="/growth-groups/", text=f"Groups of 8 to 14 people linked to {s['full']}, meeting weekly to read the Bible, share life and pray.", go="Join a group"),
        dict(title="Global partners", img="globe", alt="", href="/global-partners/", text=f"The people {s['full']} supports as they work cross-culturally to make Jesus known.", go="Our partners"),
        dict(title="Serve", img="serving-food", alt="", href="/serving/", text="We would love to have you on one of our teams.", go="Ways to serve"),
    ], plain=True, title="Part of the family"))
    sections.append(S("band", dict(h2=f"See you at {s['full']} this Sunday.", html=f"{s['when']}, {s['venue']}, {s['addr']}.", href=s["maps"], label="Get directions")))
    return dict(
        slug=f"sundays/{s['slug']}", title=s["full"], crumb=("Sundays", "/sundays/"),
        desc=f"{s['full']} meets {s['when'].lower()} at {s['venue']}, {s['addr']}. {s['blurb']}",
        lede=s["blurb"], photo=s["img"], photo_alt=f"{s['full']} meeting at {s['venue']}", head="side", vt=f"svc-{s['slug']}",
        actions=[("Get directions", s["maps"]), ("Connect Card", s["card"], "ghost")],
        sections=sections,
    )

for _s in SERVICES:
    PAGES.append(service_page(_s))

# ---------------------------------------------------------------- kids
PAGES.append(dict(
    slug="kids", title="Kids",
    desc="Kids@Church on Sunday mornings at North and Belconnen, and KidsBlast on Friday nights for Grades 3 to 6 at the Crossroads Ministry Centre.",
    lede="Children are valued greatly as members of our church family.",
    photo="kids", photo_alt="Children sitting on the floor listening at Kids@Church",
    sections=[
        S("split", dict(img="kids-2", alt="A child with a hand up at Kids@Church", html=(
            "<h2>On Sunday: Kids@Church</h2>"
            "<p>At Kids@Church the children learn from the Bible through age-appropriate activities: games, singing, craft and drama. "
            "Kids@Church begins part way through the service at both our North and Belconnen congregations, so the whole church family meets together as one body first.</p>"
            "<p>Our school-age groups (Kindergarten to Year 6) learn from the same Bible passage as their parents where suitable, so the whole church learns and grows together. "
            "The under-fives work through foundational Bible stories and themes that help them grasp God’s love for them.</p>"
            "<p>Kerryn Rudder at Belconnen and Sarah Rootes at North are the pastors responsible for children’s ministry.</p>"
            "<p class=\"actions\"><a class=\"btn ghost\" href=\"/sundays/north/\">North, 9.30am</a><a class=\"btn ghost\" href=\"/sundays/belconnen/\">Belconnen, 9.30am</a></p>"))),
        S("facts", [
            ("Who", "Kids in Grades 3 to 6."),
            ("When", "Fridays, 5pm to 6.30pm, during ACT school terms."),
            ("Where", f'{CENTRE["name"]}, {CENTRE["line1"]}, {CENTRE["line2"]}. {CENTRE["note"]}'),
            ("What happens", "Every week, kids learn about Jesus from the Bible, play wide games (lots of running), do activities (less running), and talk in a discussion group about what they learnt."),
        ], title="Friday nights: KidsBlast",
          lede="KidsBlast is for all kids to come together and have fun while discovering who Jesus is with their friends."),
        S("split", dict(img="welcome-hall", alt="", html=(
            "<h2>Visiting with children?</h2>"
            "<p>Register your child or children at the Welcome Table when you arrive. The team there will answer any questions and help you and your children settle in for the morning.</p>"
            f"<p class=\"actions\"><a class=\"btn\" href=\"{FORM_KIDS_VISITOR}\" rel=\"noopener\">Register a visiting child</a><a class=\"btn ghost\" href=\"/policies/\">Safe ministry</a></p>"), rev=True)),
        S("prose", (
            "<h2>Volunteer leaders</h2>"
            "<p>All of our kids and youth leaders are members of Crossroads and have completed Safe Ministry training.</p>"
            "<p>Teaching children to follow Jesus is a great privilege and joy, and we encourage all members of Crossroads to consider how they might be involved: "
            "as a regular class leader, leading for one term during the year, helping out on occasion, or supporting with other tasks.</p>"
            "<p class=\"actions\"><a class=\"btn ghost\" href=\"/serving/\">I’d like to help</a></p>"), chalk=True),
        S("address", dict(html="<p>KidsBlast and Crossfire both happen here on Friday nights. There is parking in the Westfield car parks and on the street.</p>"), title="Getting to the Ministry Centre"),
    ],
))

# ---------------------------------------------------------------- youth
PAGES.append(dict(
    slug="youth", title="Youth",
    desc="Crossfire on Friday nights for Years 7 to 12, and Youth@Church on Sunday mornings for Years 7 to 10.",
    lede="We’re passionate about seeing more and more young people finish school on fire for Jesus.",
    photo="youth-sunset", photo_alt="Teenagers on a hilltop at sunset",
    sections=[
        S("prose", (
            "<p>Youth at Crossroads is about:</p><ul>"
            "<li>loving God deeply</li>"
            "<li>reaching young people in Canberra with the great news of Jesus</li>"
            "<li>connecting as the body of Christ</li>"
            "<li>growing in Christian faith</li>"
            "<li>serving Jesus with their whole lives.</li></ul>")),
        S("facts", [
            ("Who", "Students in school Years 7 to 12. Open to all, regardless of belief or background."),
            ("When", "Fridays, 7.15pm to 9.15pm, during ACT school terms."),
            ("Where", f'{CENTRE["name"]}, {CENTRE["line1"]}, {CENTRE["line2"]}. {CENTRE["note"]}'),
            ("What it’s like", "Fun, friendships and Jesus. A great community to explore life with Jesus alongside others, whether you consider yourself a Christian, are uncertain, or are simply interested in discovering more."),
            ("Coming for the first time", f'<a href="{FORM_YOUTH_VISITOR}" rel="noopener">Register as a visitor</a> so we can keep everyone safe, or <a href="mailto:{YOUTH_EMAIL}">email the Crossfire team</a>.'),
        ], title="Friday nights: Crossfire"),
        S("split", dict(img="youth-group", alt="A group of young people at church", html=(
            "<h2>Sunday mornings: Youth@Church</h2>"
            "<p>Youth@Church is for Years 7 to 10 and runs alongside our morning services at North and Belconnen. It begins part way through the service, so the whole church family meets together as one body first.</p>"
            "<p>The morning involves activities, Bible teaching and prayer, and it’s a great chance for the youth to connect with each other, learn from one another and encourage one another. "
            "They learn from the same Bible passage as their parents where suitable, so the whole church learns and grows together.</p>"), rev=True)),
        S("prose", (
            "<h2>The WhatsApp community</h2>"
            "<p>Youth at Crossroads can be part of the WhatsApp community during the week: announcements of upcoming events, photos and encouragement. "
            f"To join, email <a href=\"mailto:{YOUTH_EMAIL}\">{YOUTH_EMAIL}</a>.</p>"
            "<h2>Safe ministry</h2>"
            "<p>All our youth leaders are members of Crossroads and have completed Safe Ministry training. Crossroads adheres to Safe Ministry; <a href=\"/policies/\">read our policies</a>.</p>"), chalk=True),
    ],
))

# ---------------------------------------------------------------- connect
PAGES.append(dict(
    slug="connect", title="Connect",
    desc="Ways in at Crossroads: Connect Cards, Connect Lunches, growth groups, Jesus on Life, partnership, Crossroads English and DivorceCare.",
    lede="Being part of a church is more than Sundays. These are the ways in.",
    photo="connect-lunch", photo_alt="People talking over lunch at the Ministry Centre",
    sections=[
        S("cards", [
            dict(title="Connect Card", img="conversation", alt="", href="/connect-card/", text="New? Tell us who you are and someone will be in touch shortly.", go="Fill in a card"),
            dict(title="Connect Lunch and Connect-In", img="lunch-outdoor", alt="", href="/connect-lunch/", text="Meet other newcomers, church members and some of the pastoral team, and hear the who, why and what of Crossroads.", go="You’re invited"),
            dict(title="Growth groups", img="growth-group", alt="", href="/growth-groups/", text="The life-blood of our church: 8 to 14 people meeting each week to read the Bible, share life and pray.", go="Join a group"),
            dict(title="Jesus on Life", img="jol-room", alt="", href="/jesus-on-life/", text="Four casual evenings on the life of Jesus and what he said about life. For enquirers, doubters and sceptics.", go="Come along"),
            dict(title="Partnership", img="prayer", alt="", href="/partnership/", text="More than attending: a way of saying “this is my church family”.", go="Become a partner"),
            dict(title="Apps", img="word-to-life", alt="", href="/apps/", text="The Crossroads app, and the Bible apps we recommend.", go="Get the app"),
        ], plain=True, three=True),
        S("cards", [
            dict(title="Crossroads English", img="english", alt="", href="/english/", text="Free conversational English classes for speakers of other languages, Tuesday nights in school terms.", go="Free classes"),
            dict(title="DivorceCare", img="two-women", alt="", href="/divorce-care/", text="A 13-week support group for the hurt of separation and divorce, led by people who have been through it.", go="Find support"),
            dict(title="Crossroads Classifieds", img="canberra-sunset", alt="", href=CLASSIFIEDS, text="A closed Facebook group for accommodation, second-hand goods and services, for people at Crossroads and people moving to Canberra.", go="Join the group"),
        ], plain=True, three=True, title="Also at Crossroads", chalk=True),
    ],
))

PAGES.append(dict(
    slug="connect-card", title="Connect Card", crumb=("Connect", "/connect/"),
    desc="Welcome to our church. Fill in the Connect Card for your service and someone will be in touch shortly.",
    lede="Welcome to our church. We’re glad you’re here. Fill in the card for the service you came to, and someone will be in touch shortly.",
    sections=[
        S("links", [(f"{s['full']} ({'morning' if s['kids'] else 'evening'} service)", s["card"], s["when"]) for s in SERVICES], title="Pick your service"),
        S("prose", f"<p>Not sure which one, or came to more than one? Email <a href=\"mailto:{OFFICE_EMAIL}\">{OFFICE_EMAIL}</a> and we’ll sort it out.</p>"),
    ],
))

PAGES.append(dict(
    slug="connect-lunch", title="Connect Lunch and Connect-In", crumb=("Connect", "/connect/"),
    desc="A relaxed way for newcomers to meet church members and the pastoral team: Connect Lunches at the morning services, Connect-In at the evening services.",
    lede="A relaxed way to meet other newcomers, church members and some of the pastoral team, and to hear the who, why and what of Crossroads.",
    photo="lunch-outdoor", photo_alt="People eating lunch together outdoors",
    sections=[
        S("prose", (
            "<p>Depending on your congregation, this looks like a Connect Lunch, with a meal, or a Connect-In before or around a service. "
            "Either way you’ll hear a bit about how our church works, and have the chance to ask your questions in a friendly, informal setting.</p>")),
        S("facts", [
            ("Crossroads North", "Connect Lunch, after the 9.30am service, several times a year."),
            ("Crossroads Belconnen", "Connect Lunch, after the 9.30am service, several times a year."),
            ("Crossroads City", "Connect-In, before the 6.30pm service, monthly."),
            ("Crossroads Lake G", "Connect-In, before the 6.30pm service."),
        ], title="Which one is mine?"),
        S("band", dict(h2="Fill in a Connect Card and we’ll tell you the next date.", html="In person at church, or online. Someone will be in touch with the details.", href="/connect-card/", label="Fill in a Connect Card")),
    ],
))

PAGES.append(dict(
    slug="growth-groups", title="Growth groups", crumb=("Connect", "/connect/"),
    desc="Growth groups at Crossroads: 8 to 14 people meeting weekly to read the Bible, share their lives and pray for one another.",
    lede="The life-blood of our church: 8 to 14 people who meet each week to read God’s word, the Bible, share their lives and pray for one another.",
    photo="growth-group", photo_alt="A growth group around a table with Bibles and coffee",
    sections=[
        S("split", dict(img="notebooks", alt="Open notebooks and Bibles on a table", html=(
            "<p>Being in a group plays an essential role in Christian growth, and Crossroads is all about growing followers of Christ in Canberra and beyond. We hope you’ll join a group and grow together.</p>"
            "<p>Most groups meet in someone’s home. Some meet on university campuses or in cafés. The women’s groups with crèches for children combine to meet at the Crossroads Ministry Centre in Belconnen.</p>"), rev=True)),
        S("prose", (
            "<h2>Sign up for 2026</h2>"
            "<p>We link a set of growth groups to each congregation, so the people in your group are the people you meet each Sunday. We’ve found this helps people become connected much more quickly.</p>"
            "<p>Fill in the Connect Card for your congregation and say you’d like to join a growth group, and a pastor will find you a group.</p>"), title=None),
        S("links", [(f"{s['full']} growth groups", s["card"], "Connect Card") for s in SERVICES]),
        S("prose", f"<p>Questions? Email <a href=\"mailto:{OFFICE_EMAIL}\">{OFFICE_EMAIL}</a>.</p>"),
    ],
))

PAGES.append(dict(
    slug="jesus-on-life", title="Jesus on Life", crumb=("Connect", "/connect/"),
    desc="Jesus on Life is a four-week series on the life of Jesus and what he said about life: a short talk, then your questions over coffee and dessert, at the Crossroads Ministry Centre in Belconnen.",
    lede="A four-week series on the life of Jesus and what he had to say about life. A short talk, then your questions, over coffee and dessert.",
    photo="jol-stage", photo_alt="Two people talking on stage at a Jesus on Life evening",
    actions=[("Sign up", "#signup"), ("Who is Jesus?", "/who-is-jesus/", "ghost")],
    sections=[
        S("prose", (
            "<p>Over the last 2000 years, Jesus has been recognised as the most significant person in history. His unconventional way of thinking, his notion of identity and his ideas of love have revolutionised the world. "
            "His radical ideas of looking after the vulnerable and loving your neighbour are standard practice today. His ideas of going beyond what is expected, to love your enemies, are still divinely profound. And these are only a handful of his claims.</p>"
            "<p>If you would like to meet this extraordinary man, come to Jesus on Life. If you don’t know who Jesus is but would like to learn more about this radical thinker and his claims, it’s for you too. "
            "And if you have questions about Jesus or Christianity, whether you’re a Christian or not, come along.</p>")),
        S("facts", [
            ("Who it’s for", "Enquirers, doubters, sceptics, and anyone who honestly wants to wrestle through the Bible and its teaching."),
            ("Format", "Four casual evenings. A short talk each week, then a chance to ask any question you have about Jesus and Christianity, over coffee and dessert."),
            ("Where", f'{CENTRE["name"]}, {CENTRE["line1"]}, {CENTRE["line2"]}. {CENTRE["note"]}'),
            ("Cost", "Free."),
        ], title="The details"),
        S("videos", [VIDEOS["jol"]] + JOL_STORIES, title="People who came along", lede="What Jesus on Life was like for them."),
        S("form", dict(to=OFFICE_EMAIL, subject="Jesus on Life sign-up", submit="Sign me up", fields=[
            ("first", "First name", "text", True), ("last", "Last name", "text", True), ("email", "Email", "email", True),
            ("phone", "Phone number", "tel", False), ("message", "Anything you’d like us to know", "textarea", False),
        ]), title="Sign up for the next series", id="signup", lede="We’ll email you the dates for the next Jesus on Life."),
        S("address", dict(html=""), title="Where it happens", chalk=True),
    ],
))

PAGES.append(dict(
    slug="divorce-care", title="DivorceCare", crumb=("Connect", "/connect/"),
    desc="DivorceCare at Crossroads: a 13-week support group for the hurt of separation and divorce, run by Crossroads leaders who have experienced it. Next group from Wednesday 2 September.",
    lede="Help and healing for the hurt of separation and divorce. A 13-week support group, run by Crossroads leaders who have experienced the pain of divorce in some way.",
    sections=[
        S("facts", [
            ("Next group", "From Wednesday 2 September, for 13 weeks. If you miss the start date, that’s okay: email us and let us know you’re coming."),
            ("Where", f'{CENTRE["name"]}, {CENTRE["line1"]}, {CENTRE["line2"]}.'),
            ("The program", f'DivorceCare is a divorce recovery support group used around the world. <a href="{DIVORCECARE_ORG}" rel="noopener">Our group on divorcecare.org</a>.'),
            ("Sign up", f'<a href="mailto:{DIVORCECARE_EMAIL}?subject=DivorceCare">Email {DIVORCECARE_EMAIL}</a>.'),
        ], title="The details"),
        S("videos", [VIDEOS["dc1"], VIDEOS["dc2"]], title="What DivorceCare is like"),
        S("band", dict(h2="You don’t have to walk through this alone.", html="Send us an email and we’ll save you a seat in the next group.", href=f"mailto:{DIVORCECARE_EMAIL}?subject=DivorceCare", label="Email the DivorceCare team")),
    ],
))

PAGES.append(dict(
    slug="english", title="Crossroads English", crumb=("Connect", "/connect/"),
    desc="Free English classes in Belconnen for speakers of other languages: conversational, practical English on Tuesday nights, plus meals and outings together.",
    lede="Free classes for speakers of other languages who want to have fun and improve their English. Conversational, real-life English, and help getting to know and love Canberra.",
    photo="english", photo_alt="People talking together outside",
    sections=[
        S("prose", (
            "<h2>What we do</h2><ul>"
            "<li>Free English classes that focus on the practical speaking and listening skills people use most.</li>"
            "<li>A supportive, caring learning community and social network for people who have left family and friends.</li>"
            "<li>Help finding new networks in Canberra.</li>"
            "<li>Help getting to know and enjoy Canberra’s opportunities and facilities.</li>"
            "<li>Help understanding and joining in with Australian culture and customs.</li>"
            "<li>Help understanding why we do what we do.</li></ul>"
            "<h2>Why we do it</h2>"
            "<p>We love Jesus, and he loves people who have left homes and families to live in new places. He wants his family to help people in need who come to their community.</p>")),
        S("facts", [
            ("Classes", "Weekly, intermediate level, during school terms: Tuesdays, 7pm to 9pm."),
            ("Also", "Lunch and dinner get-togethers in our family homes, and special events to enjoy Canberra’s community celebrations, festivals and programs together."),
            ("Where", f'{CENTRE["name"]}, {CENTRE["line1"]}, {CENTRE["line2"]}. Check the Facebook page for where we are currently meeting.'),
            ("Cost", "Free."),
        ], title="When and where"),
        S("videos", [VIDEOS["english1"], VIDEOS["english2"]], title="See a class"),
        S("band", dict(h2="Come along on Tuesday night.", html="Find out more and see where we are meeting this term on Facebook.", href=CROSSROADS_ENGLISH_FB, label="Crossroads English on Facebook")),
    ],
))

PAGES.append(dict(
    slug="partnership", title="Becoming a partner", crumb=("Connect", "/connect/"),
    desc="Partnership at Crossroads: what it means, who can become a partner, what it involves, and how to apply.",
    lede="Being part of the Crossroads family is more than attending on Sundays. Partnership is how we express that commitment.",
    photo="prayer", photo_alt="People praying together in small groups",
    actions=[("Apply to become a partner", FORM_PARTNERSHIP)],
    sections=[
        S("prose", (
            "<p>God calls us to belong to one another, to serve together, and to join him in his mission to see Jesus known and loved across Canberra and beyond. Partnership is a way of saying:</p>"
            "<blockquote>“This is my church family.”<br>“I want to grow in Christ alongside others.”<br>“I’m committed to seeing the gospel reach further and deeper in Canberra.”</blockquote>"
            "<p>Partners play a meaningful role in the life of Crossroads: supporting godly leadership, caring for one another, and helping us remain faithful to the mission God has entrusted to us.</p>")),
        S("prose", (
            "<p>At the heart of Crossroads is the conviction that Jesus Christ is supreme: the one through whom and for whom all things were created, and the one in whom God is reconciling all things (Colossians 1:15–20). Everything we do flows from his greatness and grace.</p>"
            "<p>Because Jesus is Lord, our ministry takes its shape from Colossians 1:28:</p>"
            "<blockquote>“Him we proclaim, warning and teaching everyone with all wisdom, so that we may present everyone mature in Christ.”</blockquote>"
            "<p>Our constitution puts the mission of Crossroads simply:</p>"
            "<blockquote>To present Christ to everyone.<br>To present everyone mature in Christ.</blockquote>"
            "<p>These statements shape our preaching, our ministries, our leadership and our culture. Practically, they mean we want to help people hear and respond to the good news of Jesus, grow deeply in him, and join in God’s work to see his gospel reach further and deeper across Canberra and beyond.</p>"),
          title="Our mission", chalk=True),
        S("prose", (
            "<h2>Who can become a partner?</h2><p>Partnership is open to those who:</p><ul>"
            "<li>are 18 years or older</li>"
            "<li>have put their faith in Jesus and submitted their lives to him as Lord, Saviour and God</li>"
            "<li>are committed to prayerful dependence on God in all of life</li>"
            "<li>have been regularly attending Crossroads for at least three months</li>"
            "<li>are willing to promote and support the mission of Crossroads</li>"
            "<li>are not currently formal members of another church (unless special circumstances apply).</li></ul>"
            "<h2>What partnership involves</h2><p>Becoming a partner is not simply filling out a form. It means:</p><ul>"
            "<li>sharing in the life and mission of Crossroads</li>"
            "<li>supporting and caring for your church family</li>"
            "<li>growing in godliness and maturity</li>"
            "<li>serving according to your gifts and opportunities</li>"
            "<li>giving prayerfully and generously</li>"
            "<li>taking part in decisions at our Annual General Meeting</li>"
            "<li>helping us remain faithful to the gospel.</li></ul>"
            "<p>Partnership is a shared commitment to follow Jesus together in dependence on his grace.</p>"
            "<h2>How to become a partner</h2><ol>"
            "<li>Fill out the partnership form online.</li>"
            "<li>Speak with one of our pastors so they can review your application.</li>"
            "<li>Your application goes to the Church Council for their consideration.</li></ol>")),
        S("band", dict(h2="Ready to call Crossroads your church family?", html="The form takes a few minutes. A pastor will follow up with you.", href=FORM_PARTNERSHIP, label="Apply to become a partner")),
    ],
))

PAGES.append(dict(
    slug="apps", title="Apps", crumb=("Connect", "/connect/"),
    desc="The Crossroads app for sermons, podcasts, Bible studies and notifications, plus the Bible apps we recommend: YouVersion, the Bible App for Kids and Dwell.",
    lede="The Crossroads app keeps you up to date with what’s happening in and around the church. And three Bible apps we recommend.",
    sections=[
        S("split", dict(img="word-to-life", alt="The Crossroads app on a phone", html=(
            "<h2>The Crossroads app</h2>"
            "<p>Read or listen to the Bible. Listen to podcasts and past sermons, or view Bible studies. Find the Lego videos, join social connection groups, and get notifications with timely information about the life of our church.</p>"
            f"<p class=\"actions\"><a class=\"btn\" href=\"{APP_IOS}\" rel=\"noopener\">iPhone and iPad</a><a class=\"btn\" href=\"{APP_ANDROID}\" rel=\"noopener\">Android</a></p>"))),
        S("cards", [
            dict(title="YouVersion Bible app", href="https://www.bible.com/app", text="Keep in touch with others reading the Bible on the app: share the passages you’re reading, comment on them together, and do reading plans and devotions, all free.", go="Get YouVersion"),
            dict(title="The Bible App for Kids", href="https://my.bible.com/en-GB/kids", text="For young children to engage with the Bible in a style they find compelling. Free on any smart device.", go="Get the kids app"),
            dict(title="Dwell", href="https://dwellapp.io", text="A listening Bible app. Hear whole books with different voices and settings, and playlists like “Jesus’ sayings” to take you deep into his teaching.", go="Get Dwell"),
        ], three=True, title="Bible apps we recommend"),
    ],
))
