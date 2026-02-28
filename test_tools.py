"""Quick smoke-test for every tool integration.

Usage:
    uv run python test_tools.py           # run all tests
    uv run python test_tools.py bus       # run only bus tests
    uv run python test_tools.py dining bus parking  # run specific categories
"""

import asyncio
import sys
import time

# ---------------------------------------------------------------------------
# Test definitions: (category, tool_callable, args, kwargs)
# Each entry calls the raw async function (bypasses the agent/LLM entirely).
# ---------------------------------------------------------------------------

TESTS: list[tuple[str, str, callable, tuple, dict]] = []


def t(category: str, name: str, fn, *args, **kwargs):
    TESTS.append((category, name, fn, args, kwargs))


def register_campus_tools():
    from backend.integrations.campus.dining import get_dining_locations, get_dining_locations_with_menus, get_dining_menu
    from backend.integrations.campus.bus import get_bus_routes, get_bus_stops, get_bus_vehicles
    from backend.integrations.campus.parking import get_parking_availability
    from backend.integrations.campus.events import get_campus_events, search_campus_events, get_events_by_date_range
    from backend.integrations.campus.classes import search_classes
    from backend.integrations.campus.library import (
        get_library_locations, search_library_locations,
        get_library_rooms, search_library_rooms,
        get_rooms_by_capacity, get_rooms_with_amenities,
    )
    from backend.integrations.campus.recsports import get_recsports_facilities, search_recsports_facilities, get_facility_hours, get_facility_events
    from backend.integrations.campus.buildings import get_buildings, search_buildings, get_building_details, find_room_type
    from backend.integrations.campus.calendar import get_academic_calendar, get_university_holidays, search_calendar_events
    from backend.integrations.campus.directory import search_people
    from backend.integrations.campus.athletics import get_athletics_all, search_sports, get_sport_by_gender, get_upcoming_games
    from backend.integrations.campus.merchants import get_buckid_merchants, search_merchants, get_merchants_by_food_type, get_merchants_with_meal_plan
    from backend.integrations.campus.foodtrucks import get_foodtruck_events, search_foodtrucks, get_foodtrucks_by_location
    from backend.integrations.campus.studentorgs import get_student_organizations, search_student_orgs, get_orgs_by_type, get_orgs_by_career_level

    # Dining
    t("dining", "get_dining_locations", get_dining_locations)
    t("dining", "get_dining_locations_with_menus", get_dining_locations_with_menus)

    # Bus
    t("bus", "get_bus_routes", get_bus_routes)
    t("bus", "get_bus_stops(CC)", get_bus_stops, route_code="CC")
    t("bus", "get_bus_vehicles(CC)", get_bus_vehicles, route_code="CC")

    # Parking
    t("parking", "get_parking_availability", get_parking_availability)

    # Events
    t("events", "get_campus_events", get_campus_events)
    t("events", "search_campus_events(football)", search_campus_events, query="football")
    t("events", "get_events_by_date_range", get_events_by_date_range, start_date="2026-02-01", end_date="2026-03-31")

    # Classes
    t("classes", "search_classes(CSE)", search_classes, query="CSE")

    # Library
    t("library", "get_library_locations", get_library_locations)
    t("library", "search_library_locations(Thompson)", search_library_locations, query="Thompson")
    t("library", "get_library_rooms", get_library_rooms)
    t("library", "search_library_rooms(study)", search_library_rooms, query="study")
    t("library", "get_rooms_by_capacity(4)", get_rooms_by_capacity, min_capacity=4)
    t("library", "get_rooms_with_amenities(whiteboard)", get_rooms_with_amenities, amenity="whiteboard")

    # Rec Sports
    t("recsports", "get_recsports_facilities", get_recsports_facilities)
    t("recsports", "search_recsports_facilities(RPAC)", search_recsports_facilities, query="RPAC")
    t("recsports", "get_facility_hours", get_facility_hours)
    t("recsports", "get_facility_events", get_facility_events)

    # Buildings
    t("buildings", "get_buildings", get_buildings)
    t("buildings", "search_buildings(Dreese)", search_buildings, query="Dreese")
    t("buildings", "find_room_type(classroom)", find_room_type, room_type="classroom")

    # Calendar
    t("calendar", "get_academic_calendar", get_academic_calendar)
    t("calendar", "get_university_holidays", get_university_holidays)
    t("calendar", "search_calendar_events(spring)", search_calendar_events, query="spring")

    # Directory
    t("directory", "search_people(lastname=Smith)", search_people, lastname="Smith")

    # Athletics
    t("athletics", "get_athletics_all", get_athletics_all)
    t("athletics", "search_sports(football)", search_sports, query="football")
    t("athletics", "get_sport_by_gender(M)", get_sport_by_gender, gender="M")
    t("athletics", "get_upcoming_games", get_upcoming_games)

    # Merchants
    t("merchants", "get_buckid_merchants", get_buckid_merchants)
    t("merchants", "search_merchants(coffee)", search_merchants, query="coffee")
    t("merchants", "get_merchants_by_food_type(pizza)", get_merchants_by_food_type, food_type="pizza")
    t("merchants", "get_merchants_with_meal_plan", get_merchants_with_meal_plan)

    # Food Trucks
    t("foodtrucks", "get_foodtruck_events", get_foodtruck_events)
    t("foodtrucks", "search_foodtrucks(taco)", search_foodtrucks, query="taco")
    t("foodtrucks", "get_foodtrucks_by_location(oval)", get_foodtrucks_by_location, location="oval")

    # Student Orgs
    t("studentorgs", "get_student_organizations", get_student_organizations)
    t("studentorgs", "search_student_orgs(engineering)", search_student_orgs, query="engineering")
    t("studentorgs", "get_orgs_by_type(Academic)", get_orgs_by_type, org_type="Academic")
    t("studentorgs", "get_orgs_by_career_level(Undergraduate)", get_orgs_by_career_level, career_level="Undergraduate")


async def run_test(category: str, name: str, fn, args, kwargs) -> tuple[str, str, bool, str, float]:
    """Run a single tool test, return (category, name, passed, detail, duration)."""
    start = time.monotonic()
    try:
        # BeeAI @tool wraps functions into FunctionTool objects — use .run(dict)
        run = await fn.run(kwargs if kwargs else {})
        elapsed = time.monotonic() - start
        text = str(run.result)
        if not text or len(text) < 5:
            return (category, name, False, f"Empty response ({len(text)} chars)", elapsed)
        return (category, name, True, f"{len(text)} chars", elapsed)
    except Exception as e:
        elapsed = time.monotonic() - start
        cause = e.__cause__ if e.__cause__ else e
        return (category, name, False, f"{type(cause).__name__}: {cause}", elapsed)


async def main():
    register_campus_tools()

    # Filter by category if args provided
    categories = set(sys.argv[1:]) if len(sys.argv) > 1 else None
    tests = TESTS if categories is None else [t for t in TESTS if t[0] in categories]

    if not tests:
        print(f"No tests found. Available categories: {sorted(set(t[0] for t in TESTS))}")
        return

    print(f"\nRunning {len(tests)} tool tests...\n")
    print(f"{'Category':<14} {'Tool':<45} {'Status':<6} {'Time':>6}  Detail")
    print("-" * 110)

    passed = 0
    failed = 0
    failed_tests = []

    for category, name, fn, args, kwargs in tests:
        cat, nm, ok, detail, elapsed = await run_test(category, name, fn, args, kwargs)
        status = "PASS" if ok else "FAIL"
        marker = "\033[32m" if ok else "\033[31m"
        reset = "\033[0m"
        print(f"{cat:<14} {nm:<45} {marker}{status:<6}{reset} {elapsed:>5.1f}s  {detail[:60]}")
        if ok:
            passed += 1
        else:
            failed += 1
            failed_tests.append((cat, nm, detail))

    print("-" * 110)
    print(f"\n{'Results:':<14} {passed} passed, {failed} failed, {passed + failed} total\n")

    if failed_tests:
        print("FAILURES:")
        for cat, nm, detail in failed_tests:
            print(f"  [{cat}] {nm}")
            print(f"    {detail}\n")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    asyncio.run(main())
