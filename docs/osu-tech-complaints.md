# OSU Technology Complaints — Student Pain Point Research

> **Research Method:** Firecrawl web search across Reddit (r/OSU, r/OhioStateFootball, r/Columbus), The Lantern, Google Play, and general web sources.
> **Date:** February 2026
> **Purpose:** Identify recurring student frustrations with Ohio State technology to prioritize BuckeyeBot capabilities.

---

## Executive Summary

Ohio State students consistently complain about **6 core technology pain points**, many of which repeat across multiple semesters and years. The most severe are BuckeyeLink downtime during high-traffic periods and Duo/SSO authentication failures that cascade across all OSU systems. These are the highest-value problems for BuckeyeBot to solve via a unified, always-available messaging interface.

---

## Pain Point Rankings

| Rank | Category | Frequency | Primary Tool | BuckeyeBot Opportunity |
|------|----------|-----------|--------------|------------------------|
| 1 | BuckeyeLink outages & UX | 🔴 Very High | BuckeyeLink | Answer status, guide navigation |
| 2 | Duo/SSO authentication failures | 🔴 Very High | Duo + all OSU systems | Notify of outages, guide workarounds |
| 3 | Carmen/Canvas outages & UX | 🔴 Very High | CarmenCanvas | Status updates, assignment queries |
| 4 | eduroam/WiFi failures | 🟠 High | Campus network | Real-time status, IT escalation |
| 5 | OSU Mobile App bugs | 🟠 High | Ohio State App | Replace broken features directly |
| 6 | BuckID / Grubhub / Dining | 🟠 High | BuckID + Grubhub | Order status, charge disputes |
| 7 | Bus tracking inaccuracy | 🟡 Medium | OSU App / COTA | Real-time bus data via MCP |
| 8 | Student ticket access | 🟡 Medium | SIDEARM App | Ticket availability queries |

---

## 1. BuckeyeLink — Portal Failures & UX Nightmare

**Frequency:** Multiple threads per semester, every semester, going back years.

### Documented Complaints

- **Login failures / "Bad Request" errors** — students hit 400 errors trying to log in, requiring cache clearing as a workaround. This recurs constantly.
  > *"every time I try to go on to the website on my computer it says 'Bad Request'. it has been like that for..."* — r/OSU
  > *"Constantly getting this message when logging into buckeyelink or carmen on a mac. I've never had this issue until the past month or two."* — r/OSU

- **Downtime during peak traffic** — BuckeyeLink crashes when large numbers of students access it simultaneously (registration, financial aid deadlines, end of semester).
  > *"We have been trying to log in for over an hour. It's been frustrating."* — r/OSU (`Buckeyelink down?`)
  > *"Buckeyelink down? All hands on deck? End of the world???"* — r/OSU thread title
  > *"Buckeyelink works fine until everyone under the sun is trying to use it at once."* — r/OSU

- **Financial aid data not loading** — incoming students and current students see "no data available" where aid info should appear.
  > *"when I go to look at financial aid summary on Buckeye link it says no data available."* — r/OSU

- **Redesign backlash** — OSU redesigned BuckeyeLink and students hated it, preferring the old broken version over the new confusing one.
  > *"Me: Complains constantly about buckeyelink being outdated. Also me: Wants the old buckeyelink back when they finally update it."* — r/OSU (474 upvotes)
  > *"Does anyone else hate the new buckeye link?"* — r/OSU

- **Outdated class/statement UI** — even outside of outages, students find the class viewing and billing sections confusing and outdated.
  > *"Honestly that part of BuckeyeLink absolutely sucks, like where you view classes and statements. Like how come that part can't get an upgrade..."* — r/OSU

### Sources
- `reddit.com/r/OSU/comments/1hdrd9i/osu_buckeye_link_sucks/`
- `reddit.com/r/OSU/comments/1hdo2vd/buckeyelink_down/`
- `reddit.com/r/OSU/comments/1mtwexm/cant_view_anything_on_buckeyelink/`
- `reddit.com/r/OSU/comments/193fq9e/does_anyone_else_hate_the_new_buckeye_link/`
- `reddit.com/r/OSU/comments/1kvkxgm/issue_logging_into_buckeyelink/`
- `reddit.com/r/OSU/comments/1ow3zxu/buckeyelink_down_all_hands_on_deck_end_of_the/`
- `reddit.com/r/OSU/comments/1ehxzo0/what_is_wrong_with_us_for_real/`

---

## 2. Duo / SSO Authentication — Cascading Failures

**Frequency:** Very high — when Duo goes down, *every* OSU system goes down simultaneously.

### Documented Complaints

- **Duo crashes Microsoft redirects** — any Microsoft 365 product (Outlook, Teams, SharePoint) becomes inaccessible when Duo fails.
  > *"I can't sign into any Microsoft products. It redirects to DUO then crashes. Anyone else having this problem or is it just me?"* — r/OSU

- **IT wait times for bypass codes** — when Duo fails, students must call IT to get bypass codes, resulting in 20+ minute hold times.
  > *"I've been on the phone with IT waiting for assistance for 20 minutes now just to get a bypass code because Duo isn't working."* — r/OSU

- **Systemwide slow/degraded performance** — Duo failures create a single point of failure for the entire OSU tech ecosystem.
  > *"it's not just you. the computer system is very slow right now"* — r/OSU thread title

- **Desire to replace Duo** — students actively seek ways to avoid Duo entirely.
  > *"Is there a way to stop using Duo and use a passkey or my own auth..."* — r/OSUOnlineCS

- **Cross-campus impact** — Duo outages affect multiple OSU campuses (Columbus, Newark, etc.) simultaneously.
  > *"This is an issue impacting multiple Duo deployments and not limited to Ohio State."* — r/OSU (Newark campus)

### Sources
- `reddit.com/r/OSU/comments/1rcjmcl/is_duo_not_working/`
- `reddit.com/r/OSU/comments/1iovawz/duo_security_issue/`
- `reddit.com/r/OSU/comments/1ewykof/its_not_just_you_the_computer_system_is_very_slow/`
- `reddit.com/r/OSU/comments/1iopkp4/anybody_else_at_osu_newark_having_trouble_logging/`

---

## 3. Carmen/Canvas — Outages & Ugly Updates

**Frequency:** High — multiple documented outages per semester, plus recurring UX complaints.

### Documented Complaints

- **Full outages tied to external infrastructure** — CarmenCanvas went fully down during the major AWS outage, affecting all students and professors simultaneously.
  > *"Yes, CarmenCanvas is down. It is connected to the larger AWS (Amazon Web Services) outage. Don't panic. Your instructors are facing the same..."* — r/OSU
  > *"CarmenCanvas back up, systemwide outage fixed"* — The Lantern (Oct 2025)

- **Maintenance-caused outages** — routine maintenance has knocked Carmen offline, as documented by The Lantern.
  > *"An error during a routine maintenance activity left students and professors unable to access Carmen"* — The Lantern (`thelantern.com/tag/carmen-error/`)

- **GUI update backlash** — a visual redesign of Carmen was universally panned as ugly and disorienting.
  > *"They update the carmen gui and it just looks horribly ugly now? everything is still the same in all the same places, but it just looks bad."* — r/OSU

- **Courses not published on time** — professors frequently don't publish courses before the semester starts, leaving students in the dark.
  > *"Class not published on Carmen"* — recurring r/OSU thread topic

- **AI cheating false positives** — students facing AI-use accusations from Carmen-based tools with no explanation or evidence.
  > *"I got a message in Carmen from my professor stating that I am being suspected of using Generative AI. No reasoning as to why..."* — r/OSU

- **High-traffic degradation** — Carmen has suffered performance issues since at least 2016 during high-traffic periods.
  > *"We are currently experiencing an issue with multiple services"* — OSU IT (The Lantern, 2016)

### Sources
- `reddit.com/r/OSU/comments/1obkgzn/carmencanvas_is_down/`
- `reddit.com/r/OSU/comments/1imggng/carmen_down/`
- `reddit.com/r/OSU/comments/1kup5b1/terrible_carmen_canvas_gui_update/`
- `thelantern.com/2025/10/carmencanvas-down-sites-affected-by-system-outage/`
- `thelantern.com/tag/carmen-error/`
- `thelantern.com/2016/08/ohio-state-high-traffic-volume-causing-carmen-woes/`
- `thelantern.com/2013/10/carmen-issues-lead-ohio-state-students-frustration/`

---

## 4. eduroam / Campus WiFi — Chronically Slow

**Frequency:** High — recurring threads across multiple semesters dating back years.

### Documented Complaints

- **Inexplicably slow speeds** — students report sudden degradation in WiFi performance with no clear cause or communication from OSU IT.
  > *"anyone else having issues with eduroam recently? like last week it was fine, this week since monday its been painfully slow and horrid on like all of my devices."* — r/OSU
  > *"eduroam has been straight ass the past week, is this normal and to be expected or is there some kind of outage?"* — r/OSU

- **Building-level outages** — WiFi going down in specific buildings with no OSU communication.
  > *"I'm in journalism bldg and can't connect either my laptop or phone to Eduroam."* — r/OSU

- **Privacy warnings** — some students see "no privacy" warnings on eduroam connections.
  > *"It's been super slow. I also saw they want to move us to eduroam WiFi, but that one when connected shows 'no privacy'"* — r/OSU

- **Multiple network confusion** — students confused by osuwireless vs. eduroam vs. WIFI@OSU, with unclear guidance on which to use.
  > *"Why are eduroam, WIFI@OSU, osuwireless such asswater..."* — r/OSU thread title

### Sources
- `reddit.com/r/OSU/comments/1r94ah7/eduroam_painfully_slow/`
- `reddit.com/r/OSU/comments/1fjr8n4/why_is_eduroam_so_slow/`
- `reddit.com/r/OSU/comments/1i24s3i/osu_campus_wifi_down/`
- `reddit.com/r/OSU/comments/wyait7/why_are_eduroam_wifiosu_osuwireless_such_asswater/`

---

## 5. OSU Mobile App — Broken Features & Hated Redesign

**Frequency:** High — multiple categories of app-specific complaints.

### Documented Complaints

- **Schedule widget displaying wrong classes** — after a system outage, the OSU app began showing incorrect class schedules in home screen widgets.
  > *"my osu app has begun to display my classes incorrectly on my widgets and..."* — r/OSU

- **Bus routes not loading** — the bus tracking feature in the OSU app frequently shows "no buses running" even when routes are active.
  > *"Any time I try to look at the bus routes on the Ohio State app, I either get a message saying that no busses are running at the moment, or the bus icons will..."* — r/OSU

- **"For You" redesign universally disliked** — a major app redesign changed the landing page to a "For You" feed filled with irrelevant promotional content instead of useful student info.
  > *"Has anyone noticed the changes to the latest version of the Ohio State app? Now the landing page is called 'For You,' but it's filled with..."* — r/OSU
  > Thread title: *"New Ohio State App is COMPLETELY B.S"* — r/OSU

- **Ticket sales broken** — the app gives errors when students try to sell or transfer athletic tickets.
  > *"I've been trying to sell my tickets to the Marshall game, but the app keeps giving me an error message saying 'never been updated.'"* — r/OhioStateFootball

- **OSU Buckeyes SIDEARM app: 2.1 stars** — the athletic ticketing app is rated 2.1/5 on Google Play, described as the "worst ticketing app I am forced to use."
  > *"Definitely the worst ticketing app I am forced to use. I encounter issues..."* — Google Play review

- **Bus tracking real-time data unreliable** — real-time bus locations in the app are frequently inaccurate or frozen.
  > *"I cannot look up any real time updates for campus bus on the Ohio state app idk if this is a bug or something"* — r/OSU

### Sources
- `reddit.com/r/OSU/comments/1ohceen/osu_app_glitching_with_schedule/`
- `reddit.com/r/OSU/comments/163w4gb/bus_routes_not_loading/`
- `reddit.com/r/OSU/comments/1hx4azz/new_ohio_state_app_is_completely_bs/`
- `reddit.com/r/OhioStateFootball/comments/1fjtffn/is_the_osu_app_broken_for_anyone_else/`
- `reddit.com/r/OSU/comments/jdlsic/anyone_has_problems_looking_up_cabs_on_ohio_state/`
- `play.google.com` (OSU Buckeyes SIDEARM Sports app — 2.1★)

---

## 6. BuckID / Grubhub / Dining — Payments & Swipes

**Frequency:** High — payment and access failures create urgent, immediate student problems.

### Documented Complaints

- **BuckID disappearing from Grubhub** — students' BuckID payment method vanishes from their Grubhub account, causing all orders to be cancelled.
  > *"my buckid just disappeared from my account and won't readd and every order keeps getting cancelled."* — r/OSU (`Grubhub not working`)

- **Dining gate swipe failures** — BuckID scans green at dining hall gates but the gate doesn't open, resulting in double charges.
  > *"I swiped my buckID and it rung green but the gate didn't open, so I tried again and..."* — r/OSU

- **Meal swipes lost to hardware failure** — swipes are consumed by failed gate reads, and recovery requires calling the dining hall directly.

- **$30 replacement card fee** — students frustrated by high cost of replacing lost BuckID cards.
  > *"Charging students 30 dollars for a replacement ID is absurd."* — r/OSU

- **Dining dollars expire** — leftover BuckID Cash after graduation requires a $5 refund fee to recover.

- **Transaction history buried** — students don't know where to view BuckID transaction history (it's in the OSU app under the "For You" page, poorly discoverable).

### Sources
- `reddit.com/r/OSU/comments/1pkatp1/grubhub_not_working/`
- `reddit.com/r/OSU/comments/1npgizu/getting_swipes_back/`
- `reddit.com/r/OSU/comments/1gbake9/buckid_office_is_a_rip_off/`
- `reddit.com/r/OSU/comments/mylvqr/leftover_buckid_cash_and_dining_dollars_after/`

---

## 7. Bus Tracking — Unreliable Real-Time Data

**Frequency:** Medium — persistent but lower-volume complaints.

### Documented Complaints

- **COTA real-time tracking gaps** — COTA's GTFS feeds that power all bus tracking apps (OSU app, Transit app, Google Maps) are intermittently unavailable.
  > *"real time tracking isn't available so we are showing the scheduled time"* — Columbus transit complaint

- **App shows buses that aren't coming** — arrival time predictions are frequently wrong.
  > *"app said the bus was 2 minutes away the whole time."* — r/Columbus

- **OSU app bus feature unreliable since 2020** — this has been a known issue for years with no fix.

### Sources
- `reddit.com/r/OSU/comments/163w4gb/bus_routes_not_loading/`
- `reddit.com/r/OSU/comments/43zmlx/im_so_tired_of_the_osu_bus_system/`
- `reddit.com/r/Columbus/comments/1me01m6/im_so_sick_of_cota/`

---

## 8. Student Ticket Access

**Frequency:** Medium — seasonal (football/basketball season) but very high emotion.

### Documented Complaints

- **Login failures on ticket portals** — students who purchased season packages can't log in.
  > *"I purchased the top game package to watch OSU football, but I'm unable to log in to my account or find it anywhere."* — r/OSU

- **CFP ticket allocation failures** — systemic issues during high-demand events (College Football Playoff).

### Sources
- `reddit.com/r/OSU/comments/1n5dooz/i_cant_get_access_to_my_tickets_through_student/`

---

## Patterns & Themes

### Cross-Cutting Issues

1. **Single points of failure** — Duo going down takes down BuckeyeLink, Carmen, Microsoft 365, and email simultaneously. Students have no fallback.

2. **Peak-load crashes** — BuckeyeLink and Carmen reliably fail during registration periods, finals week, and financial aid deadlines — exactly when students need them most.

3. **No real-time status communication** — when systems go down, OSU provides no proactive notification. Students resort to Reddit to confirm outages and find workarounds.

4. **Redesigns that make things worse** — both BuckeyeLink and the OSU app received redesigns that students actively prefer the old broken version over.

5. **IT support is slow** — when students hit walls (Duo bypass codes, dining swipe failures, BuckID issues), IT hold times of 20+ minutes are common.

6. **Grubhub + BuckID integration is fragile** — payment method disappears silently; orders fail without clear explanation.

---

## BuckeyeBot Opportunity Map

| Student Pain Point | BuckeyeBot Solution |
|--------------------|---------------------|
| "Is BuckeyeLink down?" | Fetch OSU IT status, reply with real-time answer |
| "I got a Bad Request on BuckeyeLink" | Guide through cache clear / browser workaround |
| "I can't log in with Duo" | Report outage status, provide IT bypass instructions |
| "Is Carmen down?" | Fetch `it.osu.edu` status page, reply immediately |
| "What time does the next bus come?" | Query ohio-state-mcp-server `get_bus_vehicles` |
| "My BuckID disappeared from Grubhub" | Guide reconnection steps, offer to place order via emulation |
| "I got double-charged at the dining hall" | Provide dining hall direct contact, log complaint |
| "I can't find my financial aid on BuckeyeLink" | Navigate BuckeyeLink via browser automation, return aid summary |
| "What's on the menu at [dining hall]?" | Query `get_dining_menu` via MCP |
| "My schedule is wrong in the app" | Pull schedule directly from BuckeyeLink via automation |
| "I can't access my tickets" | Guide to correct URL/login flow |

---

## Data Quality Notes

- **Reddit scraping blocked** — Firecrawl cannot scrape Reddit post content directly; all Reddit data sourced from search result snippets and titles (high fidelity, though not full comment threads)
- **Google Play app page not found** — OSU Mobile app may be listed under a different package ID (`edu.osu.mobile` returned 404); OSU Buckeyes SIDEARM app (ticketing) confirmed at 2.1★
- **The Lantern** — confirmed recurring Carmen outage coverage going back to 2013, indicating a decade-long pattern
- **Research gap** — direct app store review scraping was blocked; a manual review audit of the OSU app on the App Store and Play Store would add quantitative data
