import os
import zipfile
import uuid
from datetime import datetime

def create_epub_file():
    # Create a unique identifier for the book
    book_id = str(uuid.uuid4())
    current_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Create the necessary directory structure
    os.makedirs("EPUB", exist_ok=True)
    os.makedirs("META-INF", exist_ok=True)
    
    # 1. Create mimetype file (must be first and uncompressed in the EPUB)
    with open("mimetype", "w", encoding="utf-8") as f:
        f.write("application/epub+zip")
    
    # 2. Create container.xml
    with open("META-INF/container.xml", "w", encoding="utf-8") as f:
        f.write('''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="EPUB/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>''')
    
    # 3. Create content.opf (the metadata package file)
    with open("EPUB/content.opf", "w", encoding="utf-8") as f:
        f.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:identifier id="book-id">{book_id}</dc:identifier>
        <dc:title>Affirmations &amp; Principles 2026</dc:title>
        <dc:language>en</dc:language>
        <dc:creator>Author</dc:creator>
        <meta property="dcterms:modified">{current_date}</meta>
        <meta property="apple:content-id">{book_id}</meta>
        <meta property="apple:version">1.0</meta>
    </metadata>
    <manifest>
        <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
        <item id="toc" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
        <item id="content" href="content.xhtml" media-type="application/xhtml+xml"/>
        <item id="css" href="styles.css" media-type="text/css"/>
    </manifest>
    <spine>
        <itemref idref="content"/>
    </spine>
</package>''')
    
    # 4. Create toc.ncx (legacy Table of Contents)
    with open("EPUB/toc.ncx", "w", encoding="utf-8") as f:
        f.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="en">
    <head>
        <meta name="dtb:uid" content="{book_id}"/>
        <meta name="dtb:depth" content="3"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle>
        <text>Affirmations &amp; Principles 2026</text>
    </docTitle>
    <navMap>
        <navPoint id="navpoint-1" playOrder="1">
            <navLabel><text>Affirmations &amp; Principles 2026</text></navLabel>
            <content src="content.xhtml"/>
        </navPoint>
    </navMap>
</ncx>''')
    
    # 5. Create nav.xhtml (modern Table of Contents)
    with open("EPUB/nav.xhtml", "w", encoding="utf-8") as f:
        f.write(f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en">
<head>
    <title>Table of Contents</title>
    <meta charset="utf-8"/>
</head>
<body>
    <nav xmlns:epub="http://www.idpf.org/2007/ops" epub:type="toc" id="toc">
        <h1>Table of Contents</h1>
        <ol>
            <li><a href="content.xhtml">Affirmations &amp; Principles 2026</a>
                <ol>
                    <li><a href="content.xhtml#ch1">Chapter 1: The Foundation of Discipline</a>
                        <ol>
                            <li><a href="content.xhtml#discipline-addiction">Discipline is the Best Addiction</a></li>
                            <li><a href="content.xhtml#if-poem">If— by Rudyard Kipling</a></li>
                            <li><a href="content.xhtml#space-between">The Space Between</a></li>
                            <li><a href="content.xhtml#stoicism-principles">Stoicism principles</a></li>
                        </ol>
                    </li>
                    <li><a href="content.xhtml#ch2">Chapter 2: The Code of Conduct</a>
                        <ol>
                            <li><a href="content.xhtml#focus-jitsu">On Focus and Jitsu</a></li>
                            <li><a href="content.xhtml#digital-protocol">Digital &amp; Communication Protocol</a></li>
                            <li><a href="content.xhtml#social-interactions">Social Interactions</a></li>
                        </ol>
                    </li>
                    <li><a href="content.xhtml#ch3">Chapter 3: The Inner Citadel</a>
                        <ol>
                            <li><a href="content.xhtml#affirmations-mindsets">Affirmations and Mindsets</a></li>
                            <li><a href="content.xhtml#stress-energy">On Stress and Energy</a></li>
                            <li><a href="content.xhtml#habits-goals">Habits and Goals</a></li>
                            <li><a href="content.xhtml#limits-plateaus">On Limits and Plateaus</a></li>
                            <li><a href="content.xhtml#luck">Luck</a></li>
                            <li><a href="content.xhtml#remembering-self">Remembering a Better Self</a></li>
                            <li><a href="content.xhtml#mindfulness-reminders">Mindfulness Reminders</a></li>
                            <li><a href="content.xhtml#what-to-avoid">What to Avoid</a></li>
                        </ol>
                    </li>
                    <li><a href="content.xhtml#ch4">Chapter 4: The Arsenal of Action</a>
                        <ol>
                            <li><a href="content.xhtml#communication-words">Communication Words</a></li>
                            <li><a href="content.xhtml#assertiveness-teamwork">Assertiveness and Teamwork</a></li>
                            <li><a href="content.xhtml#grounding-techniques">Grounding Techniques</a></li>
                            <li><a href="content.xhtml#work-bias">On Work and Bias</a></li>
                            <li><a href="content.xhtml#primacy-of-action">The Primacy of Action</a></li>
                            <li><a href="content.xhtml#chain-of-becoming">The Chain of Becoming</a></li>
                            <li><a href="content.xhtml#mental-rules">Mental Rules</a></li>
                        </ol>
                    </li>
                    <li><a href="content.xhtml#ch5">Chapter 5: The Laws of Power &amp; The Final Admonition</a>
                        <ol>
                            <li><a href="content.xhtml#48-laws">The 48 Laws of Power (Abridged)</a></li>
                            <li><a href="content.xhtml#holly-advice">Holly Butcher's Final Advice</a></li>
                        </ol>
                    </li>
                </ol>
            </li>
        </ol>
    </nav>
</body>
</html>''')
    
    # 6. Create styles.css (your CSS)
    with open("EPUB/styles.css", "w", encoding="utf-8") as f:
        f.write('''body {
    font-family: serif;
    line-height: 1.6;
    margin: 5%;
    text-align: justify;
}
h1, h2 {
    text-align: center;
    page-break-after: avoid;
}
h1 {
    margin-bottom: 2em;
}
h2 {
    margin-top: 3em;
    margin-bottom: 1em;
}
.poem {
    font-style: italic;
    margin-left: 10%;
    margin-right: 10%;
}
.list {
    margin-left: 5%;
}''')
    
    # 7. Create content.xhtml with IDs added to headings for TOC navigation
    with open("EPUB/content.xhtml", "w", encoding="utf-8") as f:
        f.write('''<?xml version="1.0" encoding="utf-8" standalone="no"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en">
<head>
    <title>Affirmations & Principles 2026</title>
    <meta charset="utf-8"/>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
    <h1>Affirmations & Principles 2026</h1>
    <h2 id="ch1">Chapter 1: The Foundation of Discipline</h2>

    <h3 id="discipline-addiction">Discipline is the Best Addiction</h3>
    <p>Discipline is best addiction. Every man is addicted to something, some smoke, some drink, some chase girls, some waste time. But real men, he is addicted to discipline, to early wakes, to prayer, to training, to silence, discipline needs no motivation; discipline moves you without feeling. Discipline say, "I go anyway, even when tired, even when lonely. Discipline is best the addiction" If you want a strong life, discipline builds it. If you want peace, discipline protects it. If you want respect, discipline earns it. No shortcuts only work . Be a man with control, not men with excuses, no crying, no blaming. If you want a better life, start with better habits. Be disciplined, every day, until discipline becomes you.</p>

    <h3 id="if-poem">If— by Rudyard Kipling</h3>
    <div class="poem">
        <p>If you can keep your head when all about you<br/>
        Are losing theirs and blaming it on you,<br/>
        If you can trust yourself when all men doubt you,<br/>
        But make allowance for their doubting too;<br/>
        If you can wait and not be tired by waiting,<br/>
        Or being lied about, don't deal in lies,<br/>
        Or being hated, don't give way to hating,<br/>
        And yet don't look too good, nor talk too wise:</p>

        <p>If you can dream—and not make dreams your master;<br/>
        If you can think—and not make thoughts your aim;<br/>
        If you can meet with Triumph and Disaster<br/>
        And treat those two impostors just the same;<br/>
        If you can bear to hear the truth you've spoken<br/>
        Twisted by knaves to make a trap for fools,<br/>
        Or watch the things you gave your life to, broken,<br/>
        And stoop and build 'em up with worn-out tools:</p>

        <p>If you can make one heap of all your winnings<br/>
        And risk it on one turn of pitch-and-toss,<br/>
        And lose, and start again at your beginnings<br/>
        And never breathe a word about your loss;<br/>
        If you can force your heart and nerve and sinew<br/>
        To serve your turn long after they are gone,<br/>
        And so hold on when there is nothing in you<br/>
        Except the Will which says to them: 'Hold on!'</p>

        <p>If you can talk with crowds and keep your virtue,<br/>
        Or walk with Kings—nor lose the common touch,<br/>
        If neither foes nor loving friends can hurt you,<br/>
        If all men count with you, but none too much;<br/>
        If you can fill the unforgiving minute<br/>
        With sixty seconds' worth of distance run,<br/>
        Yours is the Earth and everything that's in it,<br/>
        And—which is more—you'll be a Man, my son!</p>
    </div>

    <h3 id="space-between">The Space Between</h3>
    <p>Between stimulus and response there is a space. In that space is our power to choose our response. In our response lies our growth and our freedom.</p>
    <p>Everything can be taken from a man but one thing: the last of human freedoms—to choose one's attitude in any given set of circumstances, to choose one's own way. When we are no longer able to change a situation, we are challenged to change ourselves.</p>

<h3 id="stoicism-principles">Stoicism principles </h3>
<p>Today, I focus only on what I can control and release what I cannot.
I guard my mind, my strongest possession, with clarity and discipline.
I act with wisdom, justice, courage, and self-control in all I do.
I decide how events affect me; nothing external has power over my peace.
I accept what happens with calm reason and adapt to it.
I rise above anger and desire, choosing clarity and strength.
I live simply, rationally, and in harmony with nature.
I practice character every day instead of seeking comfort.
I remember life is finite and I use my time with purpose.
I draw happiness from within, never from fortune or chance
Allow the abundance of the universe flow freely into our life.</p>

    <h2 id="ch2">Chapter 2: The Code of Conduct</h2>
    <h3 id="focus-jitsu">On Focus and Jitsu</h3>
    <p>Stop trying to make best friends at jitsu, just learn and get my purple belt and black.</p>

    <h3 id="digital-protocol">Digital & Communication Protocol</h3>
    <p>No social Media commenting, No commenting on Group Chats, No sending emails to groups, no replying to group emails if I am not directly named. No posting on Linkedin, Go dark. Don't engage on any group chats, ask questions directly, do'nt complain and waste my time. just ignore crap.</p>
    <p>Work emails: Stop over communicating via emails. Never react to emails or statements, respond to emails; Use the phone.
    Be careful when communicating in meetings and groups of people and emails , always be calm and listen and ask questions rather than disagree. Don't need to say anything and Only reply when sent directly to me. Awaked silence in a meeting is not my problem.
    Stop being proactive and only provide information when asked.
    Don't CC to everyone. Don't need to answer stupid questions.
    Be careful in Group emails and chats. Don't be a super SE. Stop over communicating feeling like I am not worthy,
    Take my time to respond to any requests. Take 30 mins to respond to any txt or call, 1 hour to emails or more. Don't reply to emails sent to group.</p>

    <h3 id="social-interactions">Social Interactions</h3>
    <p>Peace at home. Stay silent sometimes not everything needs to be said.
    Don't let people put time pressure on me, ask for more time or don't engage. Your lack of planning isn't an urgency on my part.
    People are lazy and they want to be just friends and not get anything done, i break friendships to get things done and fix things, this is my life mistake. Don't complain about this stuff and get into arguments.
    People at work are not your friends.
    Don't give anything that can be used against me .
    Don't kiss anyone's ass.</p>

    <h2 id="ch3">Chapter 3: The Inner Citadel</h2>
    <h3 id="affirmations-mindsets">Affirmations and Mindsets</h3>
    <p>I feel good, I look good, I am intelligent, I am happy and my wife and family love me and I love me.
    Today I shall meet people who are meddling, ungrateful, aggressive, treacherous, malicious, unsocial and I can not be harmed by them as I am good .
    Serendipitous and happy coincidence is a sign of ethereal flow state.
    I am foolish because I am a gentle person and get tricked sometimes.
    You will continue to suffer if you have an emotional reaction to everything that is said to you or done to you. If others' words and actions control you that means everyone else can control you.
    Getting aggressive at provocation is allowing them to win . Silence is the best way to disagree. I can not be controlled by other people's words.
    Perception vs Perspective. Call the police and let them deal with aggression or racism towards me. Don;t let then win by getting angry.
    Self-respect is about having the courage to stand up for yourself when you are being treated in a manner that is less than what you deserve.
    What ever you think you need, will dominate you. If you need nothing, you can not be controlled.
    True power is sitting back and observing things with logic.
    Relax and Enjoy life. Play the game. Have mindfulness, calm confident intensity, presence, and clarity of mind and be private. Single mindedness and don't be lazy. Don't think about others' flaws. Concentrate on improving myself.
    stoic - the endurance of pain or hardship without the display of feelings and without complaint.
    I need pride in myself and have self respect.
    I decided that I'd wait until I actually had a reason to worry—something that was happening, not just something that might happen—before I worried.
    Do not let the behaviour of others destroy your inner peace. Calmness is Power. Breathe and allow things to pass. Energy creates energy. Some fights are not worth it .</p>

    <h3 id="stress-energy">On Stress and Energy</h3>
    <p>If my IQ is exhausted, I have no EQ, so push back, until, I have EQ.
    Box breathing and taking a walk may not effectively alleviate stress, as they activate the nervous system, preparing it for a fight-or-flight response and potentially causing a mental disconnect. Instead, consider practicing quiet, slow, and conscious controlled breathing and be still. This approach promotes relaxation, requiring you to sit down and unwind.</p>

    <h3 id="habits-goals">Habits and Goals</h3>
    <p>One day at a time, One step at a time.
    Every long journey starts with a small step.
    If You Do What is Hard Your Life Will Be Easy.
    Do good things for three weeks, it will turn into an easy habit.
    I need to take advantage of the situation while it lasts and sweat as much as possible using the home gym.
    Any Goal that I work towards, must be able to support the family and pay minimum income and allow me to retire. Anything else is just noise..
    Understand. Don't memorize. Practice principles, not formulas.
    June to August is very cold and I get depressed so I need exercise and get warm.. The only objective should be to stay fit as it's too cold for anything else. Get to work early and train at night.
    What would happen if I jogged each morning during winter?
    What would happen if I did 100 sit ups and push ups every morning?
    What would happen if I passed a certification?
    What would happen if I study instead of watching tv or playing games.
    100 Sit ups per day. 100 Push Ups per day, I would be ripped.
    Become a quite achiever and peaceful yet assertive person and have many friends and contacts.
    I can be as fit as I want to be.</p>

    <h3 id="limits-plateaus">On Limits and Plateaus</h3>
    <p>If you always put limits on everything you do, physical or anything else, it will spread into your work and into your life. There are no limits. There are only plateaus, and you must not stay there, you must go beyond them.</p>

    <h3 id="luck">Luck</h3>
    <p>Blind Luck.
    Luck from Motion.
    Luck from Awareness.
    Luck from Uniqueness - Your unique set of attributes attracts specific luck to you.</p>

    <h3 id="remembering-self">Remembering a Better Self</h3>
    <p>Remember that period in my life when I was awesome , I thought before I spoke , people were drawn to me , I had many good friends . I felt amazing and I was a good person . meditated and take care of my self. Live the way I want. 5 km swim, 10 km jog. Rock sold abs. Basic - yoga, groom.</p>

    <h3 id="mindfulness-reminders">Mindfulness Reminders</h3>
    <p>Mindfulness: 1 hour is a long time. be calm and present. Don't be impulsive. be civil at all times. take my time. Be In the moment. Be self aware. presence of mind. Be in the Present minute. Live in the moment.
    I look good and feel good and have high iq. Singleminded. Presence of mind. Switch on. Have presence and energy and air of confidence. Energy creates energy. I look good I feel good I am calm I am intelligent I am Happy.
    How will I feel tomorrow. I look good I feel good I am happy and I am highly intelligent.
    What do I need to do now to feel awesome going to work on the bus tomorrow?
    I can understand human behavior more than others.
    Think long term. Manage my hyper sensitivity. People are a lot dumber than me and jealous.
    All ways save face calmly. Keep a low profile speak softly. Say it in my head before talking.
    Play the game be successful and happy and show my enemies.</p>

    <h3 id="what-to-avoid">What to Avoid</h3>
    <div class="list">
        <p>Don't Gossip.</p>
        <p>Don't concern myself with other people's problems.</p>
        <p>Don't think negatively.</p>
        <p>Don't act jealous.</p>
        <p>Don't seek validation from others.</p>
        <p>Don't seek revenge.</p>
        <p>Don't hold onto resentment.</p>
        <p>Don't argue for the sake of being right.</p>
        <p>Avoid personal problems and drama.</p>
        <p>Don't over think things.</p>
        <p>Don't follow the crowd.</p>
        <p>Don't take things personally.</p>
        <p>Take care of your body and mind.</p>
        <p>Unless necessary stop apologising.</p>
        <p>Speak the truth even if it is unpopular.</p>
        <p>ignore other peoples opinion.</p>
        <p>learn to say no.</p>
        <p>value your time and energy.</p>
    </div>

    <h2 id="ch4">Chapter 4: The Arsenal of Action</h2>
    <h3 id="communication-words">Communication Words</h3>
    <p>Replace should with ought.
    Request.
    Suggest.
    If I were you.
    Do I have your permission to be 'honest and. direct'
    I want you to consider this..
    Let me get back to you.
    Let me make a case to you why you ought to.</p>

    <h3 id="assertiveness-teamwork">Assertiveness and Teamwork</h3>
    <p>Assertiveness is to talk calmly about an outcome, being clear about your rights, needs, and wants, while being considerate of others' rights, too.
    Challenge honourably, Don't be passive-aggressive.
    Debate is welcome, but we must move forward as a team once a decision is made.
    We reward accomplishments not activity.
    Fight the competition, not your team.
    Embrace deep inspection on everything we do.
    If you need help, ask for it.</p>

    <h3 id="grounding-techniques">Grounding Techniques</h3>
    <p>See, Hear, feel / What can you hear, feel and thoughts in your mind?
    Ground myself, Take a breath, feel the earth, feel the sky, feel the wind.
    Say "om" for 20 mins.</p>

    <h3 id="work-bias">On Work and Bias</h3>
    <p>Protect my job, get certified and learn the product.
    Dunning-Kruger Cognitive bias or effect - remember this exists and use it to your advantage. Let people fail; a cognitive bias whereby people with limited knowledge greatly overestimate their own knowledge.</p>

    <h3 id="primacy-of-action">The Primacy of Action</h3>
    <p>It is important that you get clear for yourself that your only access to impacting life is action. The world does not care what you intend, how committed you are, how you feel or what you think, and certainly it has no interest in what you want and don't want. Take a look at life as it is lived and see for yourself that the world only moves for you when you act.</p>

    <h3 id="chain-of-becoming">The Chain of Becoming</h3>
    <p>Your beliefs become your thoughts, Your thoughts become your words, Your words become your actions, Your actions become your habits, Your habits become your values, Your values become your destiny.
    What you think, you become.
    What you feel, you attract.
    What you imagine, you create.</p>

    <h3 id="mental-rules">Mental Rules</h3>
    <p>Five Four Three Two One Rule.
    I am not my thoughts, I don't have to be controlled by incorrect thoughts.</p>

    <h2 id="ch5">Chapter 5: The Laws of Power & The Final Admonition</h2>
    <h3 id="48-laws">The 48 Laws of Power (Abridged)</h3>
    <div class="list">
        <p>1. Never put too much trust in friends, learn to use enemies.</p>
        <p>2. Conceal your intentions.</p>
        <p>3. Always say less than necessary.</p>
        <p>4. Protect your reputation at all costs.</p>
        <p>极速飞艇开奖直播</p>
        <p>6. Make people come to you.</p>
        <p>7. Win through actions, not arguments.</p>
        <p>8. Avoid unhappy and unlucky people.</p>
        <p>9. Make other people come to you, use bait if necessary, Learn to keep people dependent on you.</p>
        <p>10. Use selective honesty to disarm others.</p>
        <p>11. Appeal to self-interest, not mercy.</p>
        <p>12.极速飞艇开奖直播</p>
        <p>13. Crush your enemy completely.</p>
        <p>14. Use absence to increase respect.</p>
        <p>15. Keep others in suspended terror.</p>
        <p>16. Do not build fortresses; isolation is dangerous.</p>
        <p>17. Know who you're dealing with.</p>
        <p>18. Do not commit to anyone, but极速飞艇开奖直播</p>
        <p>19. Play the sucker to catch a sucker.</p>
        <p>20. Surrender to turn weakness into power.</极速飞艇开奖直播</p>
        <p>21. Concentrate your forces.</p>
        <p>22. Play the perfect courtier.</p>
        <p>23. Re-create yourself.</p>
        <p>24. Keep your hands clean.</p>
        <p>25. Play on people's need to believe.</p>
        <p>26. Enter action boldly.</p>
        <p>27. Plan all the way to the end.</p>
        <p>28. Make your accomplishments seem effortless.</p>
        <p>29. Control the options: let others choose among your terms.</p>
        <p>30. Play to people's fantasies.</p>
        <p>31. Discover each person's weakness.</p>
        <p>32. Act like royalty to be treated like one.</p>
        <p>33. Master the art of timing.</p>
        <p>34. Disdain what you cannot have.</p>
        <p>35. Create compelling spectacles.</极速飞艇开奖直播</p>
        <p>36. Think as you like, but behave like others.</p>
        <p>37. Stir up waters to catch fish.</p>
        <p>38. Despise the free lunch.</p>
        <p>39. Avoid stepping into a great man's shoes.</p>
        <p>40. Strike the shepherd, scatter the sheep.</p>
        <p>41. Work on people's hearts and minds.</p>
        <p>42. Disarm and enrage with the mirror effect.</p>
        <p>43. Preach change but never reform too much at once.</p>
        <p>44. Never appear too perfect.</p>
        <p>45. Do not go past the mark you aimed for.</p>
        <p>46. Be formless, adaptable, and fluid.</p>
    </div>

    <h3 id="holly-advice">Holly Butcher's Final Advice</h3>
    <p>Holly Butcher posted her advice极速飞艇开奖直播</p>
    <p>A bit of life advice from Hol:</p>
    <p>It's a strange thing to come to terms with your own mortality at 26. We go through life expecting tomorrow, planning for the future, and imagining growing old. I dreamed of a life filled with love, children, and laughter—but cancer had other plans.</p>
    <极速飞艇开奖直播</p>
    <p>Be grateful for your body—move it, feed it well, and don't waste energy hating it. Stop fixating on flaws that won't matter in the end. Instead, breathe in fresh air, soak in nature, and take in the beauty of simply being alive.</p>
    <p>Spend your time on experiences, not things. Don't miss a beach trip because you bought another dress. Cook a meal for a friend, write them a heartfelt note, and say "I love you" often.</p>
    <p>Whinge less, help more. Give generously—it brings more joy than anything money can buy. And value people's time—极速飞艇开奖直播</p>
    <p>You don't need a perfect body, a high-paying job, or an Instagram-worthy life. Do what makes your heart happy. Say no to things that drain you, and if something makes you miserable, change it.</p>
</body>
</html>''')
    
    # 8. Create the EPUB zip file
    with zipfile.ZipFile("Affirmations_And_Principles_2026.epub", "w") as epub:
        # Add mimetype first (must be uncompressed)
        epub.write("mimetype", arcname="mimetype", compress_type=zipfile.ZIP_STORED)
        
        # Add other files with compression
        epub.write("META-INF/container.xml", arcname="META-INF/container.xml")
        epub.write("EPUB/content.opf", arcname="EPUB/content.opf")
        epub.write("EPUB/toc.ncx", arcname="EPUB/toc.ncx")
        epub.write("EPUB/nav.xhtml", arcname="EPUB/nav.xhtml")
        epub.write("EPUB/styles.css", arcname="EPUB/styles.css")
        epub.write("EPUB/content.xhtml", arcname="EPUB/content.xhtml")
    
    # Clean up temporary files
    os.remove("mimetype")
    os.remove("META-INF/container.xml")
    os.rmdir("META-INF")
    os.remove("EPUB/content.opf")
    os.remove("EPUB/toc.ncx")
    os.remove("EPUB/nav.xhtml")
    os.remove("EPUB/styles.css")
    os.remove("EPUB/content.xhtml")
    os.rmdir("EPUB")
    
    print("EPUB created successfully: Affirmations_And_Principles_2026.epub")

if __name__ == "__main__":
    create_epub_file()
