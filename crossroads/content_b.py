"""Pages: About and its family, Teaching and its family, serving, giving,
events, and Who is Jesus."""
from data import S, SERVICES, STORIES, CENTRE, OFFICE_EMAIL, INCIDENTS_EMAIL, STORIES_EMAIL, STAFF, COUNCIL, BOARD, \
    CONSTITUTION, POLICIES, SAFE_POLICIES, VIDEOS, WTL_EPISODES, MTS_PASTOR, MTS_CURRENT, MTS_COLLEGE, MTS_NOW, \
    BELIEFS, FORM_NEWSLETTER, FORM_SAFE_MINISTRY, FORM_REPORT, FORM_EVENT, FORM_VENUE, GIVENOW, BANK, MTS_ORG, AFES, \
    FIEC, YOUTUBE, APPLE_PODCASTS, SPOTIFY, APP_IOS, APP_ANDROID

PAGES = []

VISION = ("“To see the news of Jesus producing more and more life-long disciples, who together see the gospel "
          "reach further and deeper into Canberra and beyond.”")

# ---------------------------------------------------------------- about
PAGES.append(dict(
    slug="about", title="About Crossroads",
    desc="Crossroads Christian Church was started in 1996 by former ANU students and is now one church meeting in four places across Canberra. Our people, our beliefs, our stories and our history.",
    lede="Started in 1996 by a handful of former ANU students. Thirty years on, one church meeting in four places across Canberra.",
    photo="25-years", photo_alt="A pastor speaking at the Crossroads 25th birthday service",
    sections=[
        S("prose", (
            f"<h2>Our vision</h2><blockquote>{VISION}</blockquote>"
            "<h2>Our mission</h2><p>To present Christ to everyone. To present everyone mature in Christ.</p>"
            "<p>Crossroads is a member of the <a href=\"" + FIEC + "\" rel=\"noopener\">Fellowship of Independent Evangelical Churches</a>.</p>")),
        S("cards", [
            dict(title="Who we are", img="staff/marcus-reeves", alt="", href="/who-we-are/", text="Our pastoral staff, Church Council and Board of Reference.", go="Meet the team"),
            dict(title="What we believe", img="bible-open", alt="", href="/what-we-believe/", text="Our core beliefs, based on the foundational truths taught in the Bible.", go="Read our beliefs"),
            dict(title="Stories", img="story-woman", alt="", href="/stories/", text="How Jesus has changed the lives of people in our church.", go="Watch and listen"),
            dict(title="History", img="1996", alt="", href="/history/", text="From a first meeting at MacGregor Hall in 1996 to 30 years of God’s faithfulness.", go="Our story so far"),
            dict(title="Global partners", img="globe", alt="", href="/global-partners/", text="People from Crossroads now working cross-culturally to make Jesus known.", go="Our partners"),
            dict(title="MTS", img="mts/trainees-2026", alt="", href="/mts/", text="Two-year ministry apprenticeships, and the people doing them.", go="Ministry training"),
            dict(title="Policies and safe ministry", img="notebooks", alt="", href="/policies/", text="How we keep Crossroads safe, and how to make a report.", go="Read the policies"),
            dict(title="Employment", img="preach-2", alt="", href="/employment/", text="Positions available and how to apply.", go="Work with us"),
            dict(title="Contact", img="ministry-centre-2", alt="", href="/contact/", text="The Ministry Centre in Belconnen, and how to reach the right person.", go="Get in touch"),
        ], plain=True, three=True),
    ],
))

PAGES.append(dict(
    slug="who-we-are", title="Who we are", crumb=("About", "/about/"),
    desc="The pastoral staff, Church Council and Board of Reference of Crossroads Christian Church Canberra.",
    lede="The people who lead Crossroads.",
    sections=[
        S("people", STAFF, title="Pastoral staff"),
        S("people", [(n, r, None) for n, r in COUNCIL], title="Church Council", wide=True,
          lede=f"Crossroads is governed by its Council under our <a href=\"{CONSTITUTION}\" rel=\"noopener\">constitution</a>."),
        S("facts", BOARD, title="Board of Reference"),
        S("raw", (
            "<div class=\"wrap\"><div class=\"split\"><div class=\"prose\"><h2>A member of FIEC</h2>"
            "<p>Crossroads is a member of the Fellowship of Independent Evangelical Churches, a family of independent churches across Australia united by the gospel.</p>"
            f"<p class=\"actions\"><a class=\"btn ghost\" href=\"{FIEC}\" rel=\"noopener\">About FIEC</a></p></div>"
            "<figure class=\"split-media\" style=\"max-width:320px\"><img src=\"/assets/img/fiec.png\" alt=\"Fellowship of Independent Evangelical Churches\" width=\"600\" height=\"221\" loading=\"lazy\" style=\"aspect-ratio:auto;border-radius:0\"></figure></div></div>"), chalk=True),
        S("address", dict(html="<p>Our office is open during the week. Email first if you’re planning to drop in, so the right person is there.</p>"), title="The Crossroads office"),
    ],
))

PAGES.append(dict(
    slug="what-we-believe", title="What we believe", crumb=("About", "/about/"),
    desc="The core beliefs of Crossroads Christian Church: God, the Bible, humanity, Jesus Christ, salvation, the Holy Spirit, the people of God and the future.",
    lede="God created the world for us to live in. He created us to live in relationship with our Creator, and that shapes all that we do.",
    photo="bible-open", photo_alt="An open Bible outdoors in autumn light",
    sections=[
        S("prose", (
            "<h2>Our vision</h2>"
            "<p>To be part of a church family that loves Jesus and is led by Jesus is key to God’s plan for his people and for this world.</p>"
            "<p>For 30 years it’s been our joy to meet together as a family that takes the gospel seriously and seeks to make the most of what Jesus has for his people. "
            "We want to see people reached with the good news of Jesus, connected into our gospel community, growing in love and trust in Christ, and serving God and his people in love.</p>"
            "<p>Even more simply: we would love you to join us as we engage with God’s word in Scripture and dare to trust what God has to say.</p>")),
        S("beliefs", BELIEFS, title="Core beliefs",
          lede="These are the core beliefs of Crossroads, based on the foundational truths taught in the Bible. All of our teaching and ministry is rooted in and flows out of them."),
        S("band", dict(h2="Who are we?", html="Meet the pastors and leaders of Crossroads.", href="/who-we-are/", label="Who we are")),
    ],
))

PAGES.append(dict(
    slug="stories", title="Our stories", crumb=("About", "/about/"),
    desc="Stories of people from across Crossroads: how they came to know Jesus, how God has been shaping them, and how walking alongside others has helped them grow.",
    lede="Every story here is different, but they all show Jesus at work in ordinary lives.",
    sections=[
        S("prose", (
            "<p>These are the stories of people from across Crossroads: how they came to know Jesus, how God has been shaping them, and how walking alongside others in our church community has helped them grow. They’re honest, personal and still unfolding.</p>"
            "<p>Whether you’re new, exploring faith, or have been part of Crossroads for years, our prayer is that you’ll see how God is at work, and be reminded that he is at work in your story too.</p>")),
        S("stories", STORIES),
        S("band", dict(h2="Be part of our story.", html="If you’d like to tell us your story, we’d love to hear it.", href=f"mailto:{STORIES_EMAIL}?subject=Tell%20us%20your%20story", label="Tell us your story")),
        S("services", title="Come and see for yourself", lede="Join us every Sunday at 9.30am or 6.30pm."),
    ],
))

def story_page(i, st):
    slug, name, where, media, blurb, im = st
    others = [x for x in STORIES if x[0] != slug][:3]
    return dict(
        slug=f"stories/{slug}", title=f"{name}’s story", h1=name, crumb=("Stories", "/stories/"),
        desc=f"{name}’s story of Jesus at work: {where}. From Crossroads Christian Church Canberra.",
        lede=where,
        sections=[
            S("embed", dict(src=f"https://subsplash.com/u/-KQBRDK/media/embed/d/{media}?&info=0", title=f"{name}’s story", button=f"Play {name}’s story", note="The story plays from Crossroads’ media library.")),
            S("prose", f"<p>{blurb}</p>" if blurb else f"<p>Watch or listen to {name}’s story of how Jesus has been at work.</p>"),
            S("stories", others, title="More stories", cta=("All stories", "/stories/")),
        ],
    )

for _i, _st in enumerate(STORIES):
    PAGES.append(story_page(_i, _st))

PAGES.append(dict(
    slug="history", title="Our history", crumb=("About", "/about/"),
    desc="Crossroads Christian Church began on 11 February 1996 when a group of former ANU students started a new Canberra church. In 2026 we celebrated 30 years of God’s faithfulness.",
    lede="In 2026, Crossroads celebrated 30 years of God’s faithfulness.",
    photo="1996", photo_alt="John Chapman and Dave McDonald at the first Crossroads morning meeting, 1996",
    photo_cap="11 February 1996: John Chapman and Dave McDonald at the first Crossroads morning meeting, MacGregor Hall.",
    sections=[
        S("timeline", [
            ("11 February 1996", "A group of former ANU students and their families start a new Canberra church called Crossroads, with Dave McDonald as founding pastor. It has no building and isn’t steeped in tradition. It is young, contemporary, and completely committed to university ministry. "
                                 "The morning meeting is at MacGregor Hall; in the evenings Crossroads meets at the Manning Clark Lecture Theatre at ANU, later demolished and rebuilt as Manning Clark Hall in the Kambri Cultural Centre, where Crossroads City still meets."),
            ("June 1999", "Moore College’s <em>Moore News</em> reports on the young church. <a href=\"https://archives.moore.edu.au/Documents/Detail/moore-news-issue-991-june-1999/10730?item=253797\" rel=\"noopener\">Read the issue in the Moore archives</a>."),
            ("20 March 2020", "On the eve of COVID lockdowns in Canberra, Crossroads City can’t meet in Manning Clark Hall and meets at Merici College in Braddon instead. It is the last time we meet in person for almost nine months. Social distancing wasn’t really a thing yet."),
            ("2021", "Crossroads celebrates 25 years, during lockdown. Founding pastor Dave McDonald talks with Marcus Reeves, the current Senior Pastor, about the work of Crossroads and what the future holds."),
            ("2026", "Thirty years of God’s faithfulness. To mark it we hold a special week of evangelism, inviting friends, family and people from across Canberra to discover the hope found in the Lord Jesus."),
        ], title="Thirty years"),
        S("videos", [VIDEOS["history30"], VIDEOS["history25"]], title="Hear the story told",
          lede="Senior Pastor Marcus Reeves reflects on the first 30 years and looks ahead to the next 30, as we keep working, under God, to win Canberra for Christ. And founding pastor Dave McDonald on the first 25."),
        S("band", dict(h2="Be part of the next thirty.", html="Come and see what God is doing at Crossroads this Sunday.", href="/sundays/", label="Find your Sunday")),
    ],
))

PAGES.append(dict(
    slug="global-partners", title="Global and regional partners", crumb=("About", "/about/"),
    desc="Crossroads supports global and regional partners: people who have been part of the Crossroads community and are now working cross-culturally to make Jesus known.",
    lede="People who have been part of the Crossroads community and are now working cross-culturally to make Jesus known.",
    photo="globe", photo_alt="A painted globe",
    sections=[
        S("prose", (
            "<p>Crossroads is firmly committed to the great commission that Jesus left with his disciples in Matthew 28: to take the gospel to the ends of the earth. "
            "So we support our global and regional partners through prayer, financial support and correspondence.</p>"
            "<p>Each of our services supports its own partners, so the people you meet on Sunday are praying for the same people you are.</p>")),
        S("partners", title="Partners by congregation"),
        S("band", dict(h2="Get a partner’s newsletter.", html="Updates and prayer points from one of our global partners, straight to your inbox.", href=FORM_NEWSLETTER, label="Sign up for a newsletter")),
    ],
))

PAGES.append(dict(
    slug="mts", title="Ministry Training Strategy", h1="MTS", crumb=("About", "/about/"),
    desc="MTS at Crossroads: a two-year ministry apprenticeship. Meet the MTS Pastor, the current trainees, and those now at Bible college.",
    lede="A two-year apprenticeship in hands-on training for future gospel ministry. We want to play our part in raising up the next generation of ministry leaders.",
    photo="mts/trainees-2026", photo_alt="Aisha Dunkley, Amy Wiles and Emily Gates, the 2026 MTS trainees",
    photo_cap="Aisha Dunkley, Amy Wiles and Emily Gates.",
    actions=[("Support a trainee", GIVENOW), ("About MTS", MTS_ORG, "ghost")],
    sections=[
        S("prose", (
            "<blockquote>“The harvest is plentiful, but the labourers are few; therefore pray earnestly to the Lord of the harvest to send out labourers into his harvest.”<cite>Matthew 9:37–38</cite></blockquote>"
            "<p>Some of these leaders will be equipped to serve and benefit Canberra. Many will go on to lead and grow other gospel-minded churches and ministries to the ends of the earth. "
            "We want to be generous to global mission so as to best model God’s heart for all people, not just ourselves.</p>"
            f"<p>MTS stands for Ministry Training Strategy. Hundreds of people are doing MTS apprenticeships around the country; <a href=\"{MTS_ORG}\" rel=\"noopener\">find out more at mts.com.au</a>.</p>")),
        S("people", [MTS_PASTOR], title="MTS Pastor", lede="Interested in doing MTS? Email Simon."),
        S("people", MTS_CURRENT, folder="mts", wide=True, title="Current trainees",
          lede="Each year Crossroads asks people to support those undertaking an MTS traineeship.", cta=("Support a trainee", GIVENOW)),
        S("prose", f"<p>Church family members are also doing apprenticeships with our local partner AFES FOCUS. <a href=\"{AFES}\" rel=\"noopener\">Support an AFES apprentice</a>.</p>", chalk=True),
        S("people", MTS_COLLEGE, folder="mts", wide=True, title="Now at Bible college",
          lede="If you’d like updates on their church and ministry life, or would like to support them, get in touch."),
        S("people", MTS_NOW, folder="mts", wide=True, title="Where are they now?"),
    ],
))

PAGES.append(dict(
    slug="policies", title="Policies and safe ministry", crumb=("About", "/about/"),
    desc="Crossroads Christian Church’s constitution, codes of conduct, privacy policy, safe ministry policies, and how to make a report.",
    lede="We want Crossroads to be a safe space for all people, especially the weak and vulnerable.",
    sections=[
        S("prose", (
            "<p>All our staff and volunteers are screened and undergo a training process before they start in their roles. "
            f"If you need to start this process or update your safe ministry details, <a href=\"{FORM_SAFE_MINISTRY}\" rel=\"noopener\">use the safe ministry form</a>.</p>"
            "<p>Alongside our other policies, we have an Incident Reporting and Complaints Policy, which seeks to provide a fair, efficient and effective process for addressing complaints and incidents related to the conduct of staff and volunteers of Crossroads Christian Church.</p>"
            f"<p>Questions about the reporting and complaints process go to our Safe Ministry and Incidents Manager at <a href=\"mailto:{INCIDENTS_EMAIL}\">{INCIDENTS_EMAIL}</a>.</p>"
            f"<p class=\"actions\"><a class=\"btn\" href=\"{FORM_REPORT}\" rel=\"noopener\">Make a report</a></p>")),
        S("notice", "<strong>In an emergency, call the Police on 000.</strong>"),
        S("links", POLICIES, title="Church policies"),
        S("links", SAFE_POLICIES, title="Safe ministry policies"),
    ],
))

PAGES.append(dict(
    slug="contact", title="Contact us", crumb=("About", "/about/"),
    desc="Contact Crossroads Christian Church Canberra. The Ministry Centre is at Level 1, 8 Chandler Street, Belconnen.",
    lede="Tell us who you are and what you need, and we’ll put you in touch with the right person.",
    sections=[
        S("form", dict(to=OFFICE_EMAIL, subject="Website enquiry", submit="Send", fields=[
            ("first", "First name", "text", True), ("last", "Last name", "text", True), ("email", "Email", "email", True),
            ("phone", "Mobile number", "tel", False), ("message", "Your question or message", "textarea", True),
        ]), title="Send us a message", lede="Include your name, question, email address and mobile number so we can work out who best to put you in touch with."),
        S("address", dict(html=""), title="Visit the office", chalk=True),
        S("links", [
            ("General enquiries", f"mailto:{OFFICE_EMAIL}", OFFICE_EMAIL),
            ("Youth and Crossfire", "mailto:youth@crossroads.asn.au", "youth@crossroads.asn.au"),
            ("Safe ministry and incidents", f"mailto:{INCIDENTS_EMAIL}", INCIDENTS_EMAIL),
            ("DivorceCare", "mailto:divorcecare@crossroads.asn.au", "divorcecare@crossroads.asn.au"),
            ("Pastoral staff", "/who-we-are/", "Email addresses on each person"),
        ], title="Or email directly"),
    ],
))

PAGES.append(dict(
    slug="employment", title="Employment", crumb=("About", "/about/"),
    desc="Positions available at Crossroads Christian Church Canberra and how to apply.",
    lede="Positions available at Crossroads, and how to apply.",
    sections=[
        S("prose", (
            "<h2>Associate Pastor</h2>"
            "<p>We are looking for an Associate Pastor. Email the office for the job description.</p>"
            "<h2>How to apply</h2><ol>"
            f"<li>Email your application to <a href=\"mailto:{OFFICE_EMAIL}?subject=Application%20for%20a%20position%20at%20Crossroads\">{OFFICE_EMAIL}</a>. Include:"
            "<ul><li>a short summary (no more than two pages) addressing the key criteria in the job description, showing how your skills and abilities suit the role and how you can best serve Christ and his people at Crossroads</li>"
            "<li>a copy of your CV</li><li>the names of two referees.</li></ul></li>"
            "<li>Successful applicants are shortlisted from this process and go through further steps before interview.</li></ol>"
            f"<p class=\"actions\"><a class=\"btn\" href=\"mailto:{OFFICE_EMAIL}?subject=Application%20for%20a%20position%20at%20Crossroads\">Email an application</a></p>")),
    ],
))

# ---------------------------------------------------------------- teaching
PAGES.append(dict(
    slug="teaching", title="Teaching",
    desc="Bible teaching from Crossroads: sermons from all four services every week, the Word to Life podcast, Bible studies, Crosstrain and recommended resources.",
    lede="Clear, thoughtful Bible teaching that shows how the Scriptures speak into real life. On Sunday, and all week.",
    photo="preach-1", photo_alt="A pastor preaching at a Crossroads service",
    sections=[
        S("cards", [
            dict(title="Sermons", img="preach-2", alt="", href="/sermons/", text="Every week we upload the talks from across our services. Listen in the library, on Apple Podcasts or Spotify, or watch on YouTube.", go="Listen to a sermon"),
            dict(title="Word to Life podcast", img="word-to-life", alt="", href="/word-to-life/", text="One theme or passage from the Bible, a little deeper. A chance to slow down and reflect beyond Sunday.", go="Latest episodes"),
            dict(title="Bible studies", img="bible-desk", alt="", href="/bible-studies/", text="Studies on the passages we’re preaching on, for growth groups and leaders.", go="Find a study"),
            dict(title="Crosstrain", img="books", alt="", href="/crosstrain/", text="Sixteen Monday nights a year to get equipped to serve: bite-sized Bible college and Christian boot camp.", go="Get trained"),
            dict(title="Resources", img="listening", alt="", href="/resources/", text="Books, podcasts and websites we recommend, by topic.", go="What we recommend"),
            dict(title="Apps", img="notebooks", alt="", href="/apps/", text="The Crossroads app, and the Bible apps we recommend.", go="Get the app"),
        ], plain=True, three=True),
    ],
))

PAGES.append(dict(
    slug="sermons", title="Sermons", crumb=("Teaching", "/teaching/"),
    desc="Listen to Crossroads sermons: talks from all four Sunday services uploaded every week, on the sermon library, Apple Podcasts, Spotify and YouTube.",
    lede="There are times when getting to church in person is hard. If you’re unwell, travelling, or away from Canberra, you can still keep listening along.",
    sections=[
        S("sermons", title="This week and every week",
          lede="Each week we upload the sermons from across our services, so you can revisit a talk or catch up if you couldn’t be there."),
        S("prose", (
            "<p>These recordings aren’t only for staying connected. They’re a simple way to share clear, faithful Bible teaching with others.</p>"
            "<p class=\"actions\"><a class=\"btn ghost\" href=\"/word-to-life/\">Word to Life podcast</a><a class=\"btn ghost\" href=\"/bible-studies/\">Bible studies</a></p>"), chalk=True),
    ],
))

PAGES.append(dict(
    slug="word-to-life", title="Word to Life podcast", crumb=("Teaching", "/teaching/"),
    desc="Word to Life, the Crossroads podcast: one theme or passage from the Bible, a little deeper. Latest episodes on Romans, Luke and Jeremiah.",
    lede="One theme or passage from the Bible, dug into a little deeper. A chance to slow down, reflect, and wrestle with what God is saying to us beyond Sunday.",
    sections=[
        S("video", VIDEOS["wtl"], title="What the podcast is"),
        S("links", [("Word to Life on Apple Podcasts", APPLE_PODCASTS), ("Word to Life on Spotify", SPOTIFY)], title="Subscribe"),
        S("episodes", WTL_EPISODES, title="Latest episodes", lede="Press play on any episode to listen here."),
    ],
))

PAGES.append(dict(
    slug="bible-studies", title="Bible studies", crumb=("Teaching", "/teaching/"),
    desc="Bible studies from Crossroads on the passages being preached, for growth groups and leaders, in the Crossroads app.",
    lede="Studies that look deeper into the passages we’re preaching on, for growth groups and for leaders.",
    sections=[
        S("split", dict(img="bible-desk", alt="An open Bible and notebook on a desk", html=(
            "<p>Our Bible studies follow the sermon series, so a growth group can dig into the same passage the church heard on Sunday. Leaders’ resources sit alongside them.</p>"
            "<p>They live in the Crossroads app, next to the sermons on the same passages.</p>"
            f"<p class=\"actions\"><a class=\"btn\" href=\"{APP_IOS}\" rel=\"noopener\">Get the app for iPhone</a><a class=\"btn\" href=\"{APP_ANDROID}\" rel=\"noopener\">Get the app for Android</a></p>"))),
        S("cards", [
            dict(title="Sermons", img="preach-1", alt="", href="/sermons/", text="Listen to the talks on these passages.", go="Sermon library"),
            dict(title="Growth groups", img="growth-group", alt="", href="/growth-groups/", text="Not in a group yet? Join one.", go="Join a group"),
            dict(title="Crosstrain", img="books", alt="", href="/crosstrain/", text="Build your confidence in unpacking the Scriptures.", go="Get trained"),
        ], plain=True, three=True, title="Go further", chalk=True),
    ],
))

PAGES.append(dict(
    slug="resources", title="Recommended resources", crumb=("Teaching", "/teaching/"),
    desc="Books, podcasts, websites and videos recommended by Crossroads Christian Church, by topic.",
    lede="Books, podcasts and websites we recommend, sorted by topic.",
    sections=[
        S("prose", (
            "<p>We keep lists of what we recommend under these headings. Ask any of the pastors for a recommendation, or find the full lists in the Crossroads app.</p><ul>"
            "<li>Christian endurance</li><li>Podcasts</li><li>Discipleship and evangelism</li><li>Theology</li><li>Kids, youth and families</li><li>Christian living</li><li>Websites</li></ul>")),
        S("links", [
            ("Crossroads on YouTube", YOUTUBE, "Sermons and more"),
            ("Crossroads Lego videos", YOUTUBE, "Bible stories in Lego, for kids"),
            ("The Crossroads app", "/apps/", "Sermons, studies and resources"),
        ], title="Watch"),
    ],
))

PAGES.append(dict(
    slug="crosstrain", title="Crosstrain", crumb=("Teaching", "/teaching/"),
    desc="Crosstrain: 16 Monday nights a year at the Crossroads Ministry Centre to get equipped to serve. Bite-sized Bible college and Christian boot camp.",
    lede="Hungry to spur on your growth as a follower of Jesus? Keen to get trained so you can better lead others in the things of Christ?",
    photo="bible-desk", photo_alt="An open Bible with notes on a desk",
    actions=[("Sign up", "#signup")],
    sections=[
        S("facts", [
            ("What", "Sixteen Monday nights across the year: eight per semester, four per term. Each evening we get theological (think bite-sized Bible college) and get practical (think Christian boot camp)."),
            ("When", "Monday nights, 6.30pm to 9pm. You can start the night with dinner (costs apply) and a time to share and encourage each other."),
            ("Where", f'{CENTRE["name"]}, {CENTRE["line1"]}, {CENTRE["line2"]}.'),
            ("Semester 1", "Upskill in growing others as followers of Jesus, and nail down the core doctrines of the Christian faith."),
            ("Semester 2", "Build your confidence in unpacking the Scriptures, and nurture a deeper devotion for the Lord your God."),
            ("Pick", "Semester 1, Semester 2, or both, and see where Crosstrain takes you."),
        ], title="The details"),
        S("dates", ["Mon 24 August", "Mon 31 August", "Mon 7 September", "Mon 14 September", "Mon 26 October", "Mon 2 November", "Mon 9 November", "Mon 16 November"],
          title="Semester 2, 2026", lede="Block 1 in August and September, Block 2 in October and November."),
        S("form", dict(to=OFFICE_EMAIL, subject="Crosstrain sign-up", submit="Sign me up", fields=[
            ("first", "First name", "text", True), ("last", "Last name", "text", True),
            ("service", "Which service do you attend?", "radios", True, ["North", "Belconnen", "City", "Lake G"]),
            ("mobile", "Mobile number", "tel", True), ("message", "Anything else", "textarea", False),
        ]), title="I’m keen to sign up for Crosstrain", id="signup"),
    ],
))

# ---------------------------------------------------------------- serving, giving, events
PAGES.append(dict(
    slug="serving", title="Serve",
    desc="Serve at Crossroads Christian Church Canberra. Tell us where you’d like to help and one of our leaders will be in touch.",
    lede="We would love to have you on one of our teams. Tell us a little about yourself and one of our leaders will be in touch for a chat about ways you could serve.",
    photo="serving-food", photo_alt="Volunteers serving food at a Crossroads meal",
    actions=[("I’d like to serve", "#serve")],
    sections=[
        S("form", dict(to=OFFICE_EMAIL, subject="I’d like to serve", submit="Send my serve request", fields=[
            ("first", "First name", "text", True), ("last", "Last name", "text", True),
            ("service", "Which service do you attend?", "radios", True, ["North", "Belconnen", "City", "Lake G"]),
            ("mobile", "Mobile number", "tel", True),
            ("interests", "There are many ways to serve at Crossroads. Any areas of interest you’d like to flag now?", "textarea", False),
            ("anything", "Anything else you’d like us to know?", "textarea", False),
        ]), title="I’d like to serve", id="serve"),
        S("cards", [
            dict(title="Kids and youth leaders", img="kids-2", alt="", href="/kids/", text="Teaching children to follow Jesus is a great privilege and joy. Regular leaders, one-term leaders, occasional helpers.", go="Kids and youth"),
            dict(title="Crosstrain", img="books", alt="", href="/crosstrain/", text="Get equipped to serve: sixteen Monday nights a year.", go="Get trained"),
            dict(title="MTS", img="mts/trainees-2026", alt="", href="/mts/", text="A two-year apprenticeship for future gospel ministry.", go="Ministry training"),
        ], plain=True, three=True, title="Ways to grow as you serve", chalk=True),
    ],
))

PAGES.append(dict(
    slug="giving", title="Giving",
    desc="Give to Crossroads Christian Church Canberra by direct deposit or GiveNow, or support an MTS trainee.",
    lede="“But when you give to the needy, do not let your left hand know what your right hand is doing, so that your giving may be in secret. Then your Father, who sees what is done in secret, will reward you.” Matthew 6:3–4",
    photo="giving", photo_alt="Two hands passing a small paper heart",
    actions=[("Give online with GiveNow", GIVENOW)],
    sections=[
        S("facts", [
            ("Direct deposit", f"We encourage everyone who is able to set up a direct deposit, so Crossroads can budget knowing you have made a commitment of support.<br>"
                               f"<strong>Account name</strong> {BANK['name']}<br><strong>BSB</strong> {BANK['bsb']}<br><strong>Account</strong> {BANK['acct']}"),
            ("GiveNow", f'Online donations, quickly and easily. <a href="{GIVENOW}" rel="noopener">Give via GiveNow</a>.'),
            ("Support an MTS trainee", 'Each year Crossroads asks people to support those undertaking an MTS traineeship. <a href="/mts/">See who is training this year</a>.'),
        ], title="Ways to give"),
        S("prose", (
            f"<blockquote>{VISION}</blockquote>"
            "<p>To realise this vision, under God we seek to:</p><ul>"
            "<li>keep reaching our community for Christ, see people form meaningful friendships with others at Crossroads, and grow disciples who love the Lord our God and delight in living out the gospel</li>"
            "<li>keep supporting and investing in university ministry in Canberra, particularly with FOCUS Canberra and FOCUS Military</li>"
            "<li>grow the gospel by growing and supporting new churches in Canberra and around Australia, in fellowship with FIEC, and by planting new congregations</li>"
            "<li>support the local, regional and global mission of the church by raising up godly leaders who will serve Christ’s mission into the future, and by supporting those proclaiming God’s goodness now, particularly our global partners.</li></ul>"),
          title="Our vision for ministry", chalk=True),
        S("form", dict(to=OFFICE_EMAIL, subject="Giving question", submit="Send", fields=[
            ("first", "First name", "text", True), ("last", "Last name", "text", True), ("email", "Email", "email", True),
            ("message", "Your question", "textarea", True),
        ]), title="Have a question, or need help?"),
    ],
))

PAGES.append(dict(
    slug="events", title="Events and venue hire",
    desc="Apply to run an event at Crossroads, or hire the Crossroads Ministry Centre in Belconnen.",
    lede="Running an event at Crossroads, or hiring the Ministry Centre.",
    sections=[
        S("links", [("Event application form", FORM_EVENT, "For Crossroads events"), ("Venue hire form", FORM_VENUE, "For hiring the Ministry Centre")], title="Forms"),
        S("address", dict(html=""), title="The venue", chalk=True),
    ],
))

# ---------------------------------------------------------------- who is Jesus
PAGES.append(dict(
    slug="who-is-jesus", title="Who is Jesus?",
    desc="Who is Jesus? The man, his mission and his message, from Crossroads Christian Church Canberra. And Jesus on Life, a short series to investigate his claims.",
    lede="The most significant and influential figure in history. His claims are worth investigating, because if they are true, they change everything.",
    photo="canberra-sunset", photo_alt="The sun setting over the hills around Canberra",
    actions=[("Come to Jesus on Life", "/jesus-on-life/")],
    sections=[
        S("prose", (
            "<h2>The man</h2>"
            "<p>Jesus was born in a small rural town roughly 2000 years ago, into a lower-class family, to a teenage virgin mother, and lived a relatively quiet life until the age of 30. Then he began his public ministry.</p>"
            "<p>Over the next three years, Jesus performed miracles, preached, and proclaimed by his word and his works that he was God. As promised, Jesus was crucified on a Roman cross to save humanity from sin, Satan and death. On the third day he rose from death and appeared to hundreds before ascending to join his heavenly Father.</p>"
            "<h2>The mission</h2>"
            "<p>Jesus arrived on the stage of human history on a mission: to reveal who God is, to show his reign as King, and to reconcile men and women to God.</p>"
            "<p>In reconciling us to God, Jesus lived and died as a sacrificial substitute, living perfectly in the place of sinners and dying gruesomely in the place of the guilty. Jesus is therefore the saviour of the world, the only way for sinners to be saved from the righteous wrath of God. "
            "He accomplished his mission through his death, atoning for our sin, and through his resurrection, rising in victory over Satan, sin and death.</p>"
            "<h2>The message</h2>"
            "<p>Throughout his ministry, Jesus preached a consistent message: true life consists in following him. Jesus calls us to repent of our rebellion and believe in him: to believe that he is our all-satisfying saviour, and that he accomplished his mission in the place of our failure.</p>"
            "<p>To those who believe in him, Jesus promises eternal life, abundant joy, the help of the Holy Spirit and reconciliation with God the Father. Those who believe in Jesus are freed from their sin, guilt and shame, and commissioned to continue his mission in sacrificially serving the world and proclaiming the good news of Jesus.</p>"
            "<p>One day Jesus will return, and all things will be restored to the praise of his glorious grace.</p>")),
        S("band", dict(h2="Find out more at Jesus on Life.", html="A short series that looks at the claims of Jesus through Bible talks, questions and answers, coffee and dessert.", href="/jesus-on-life/", label="About Jesus on Life")),
        S("form", dict(to=OFFICE_EMAIL, subject="A question about Jesus", submit="Send", fields=[
            ("first", "First name", "text", True), ("last", "Last name", "text", True), ("email", "Email", "email", True),
            ("message", "Your question", "textarea", True),
        ]), title="Ask us anything", lede="A question about Jesus or Christianity? A pastor will reply."),
    ],
))
