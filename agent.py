from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.backend import ChatModel
from beeai_framework.memory import TokenMemory

# Campus tools
from tools.dining import get_dining_locations, get_dining_locations_with_menus, get_dining_menu
from tools.bus import get_bus_routes, get_bus_stops, get_bus_vehicles
from tools.parking import get_parking_availability
from tools.events import get_campus_events, search_campus_events, get_events_by_date_range
from tools.classes import search_classes
from tools.library import get_library_locations, search_library_locations, get_library_rooms, search_library_rooms, get_rooms_by_capacity, get_rooms_with_amenities
from tools.recsports import get_recsports_facilities, search_recsports_facilities, get_facility_hours, get_facility_events
from tools.buildings import get_buildings, search_buildings, get_building_details, find_room_type
from tools.calendar import get_academic_calendar, get_university_holidays, search_calendar_events
from tools.directory import search_people
from tools.athletics import get_athletics_all, search_sports, get_sport_by_gender, get_upcoming_games
from tools.merchants import get_buckid_merchants, search_merchants, get_merchants_by_food_type, get_merchants_with_meal_plan
from tools.foodtrucks import get_foodtruck_events, search_foodtrucks, get_foodtrucks_by_location
from tools.studentorgs import get_student_organizations, search_student_orgs, get_orgs_by_type, get_orgs_by_career_level

# Canvas tools
from canvas.tools import (
    get_canvas_courses,
    get_course_assignments,
    get_upcoming_assignments,
    get_course_grades,
    get_course_announcements,
    get_canvas_todos,
    get_course_syllabus,
)

# Grubhub tools
from grubhub.tools import search_grubhub_restaurants, get_restaurant_menu, place_grubhub_order

# BuckeyeLink tools
from buckeyelink.tools import (
    get_class_schedule, get_grades, get_financial_aid_status,
    get_holds_and_todos, get_enrollment_info, get_buckeyelink_dashboard,
)


ALL_TOOLS = [
    # Dining
    get_dining_locations, get_dining_locations_with_menus, get_dining_menu,
    # Bus
    get_bus_routes, get_bus_stops, get_bus_vehicles,
    # Parking
    get_parking_availability,
    # Events
    get_campus_events, search_campus_events, get_events_by_date_range,
    # Classes
    search_classes,
    # Library
    get_library_locations, search_library_locations, get_library_rooms,
    search_library_rooms, get_rooms_by_capacity, get_rooms_with_amenities,
    # Rec Sports
    get_recsports_facilities, search_recsports_facilities, get_facility_hours, get_facility_events,
    # Buildings
    get_buildings, search_buildings, get_building_details, find_room_type,
    # Calendar
    get_academic_calendar, get_university_holidays, search_calendar_events,
    # Directory
    search_people,
    # Athletics
    get_athletics_all, search_sports, get_sport_by_gender, get_upcoming_games,
    # Merchants
    get_buckid_merchants, search_merchants, get_merchants_by_food_type, get_merchants_with_meal_plan,
    # Food Trucks
    get_foodtruck_events, search_foodtrucks, get_foodtrucks_by_location,
    # Student Orgs
    get_student_organizations, search_student_orgs, get_orgs_by_type, get_orgs_by_career_level,
    # Canvas
    get_canvas_courses, get_course_assignments, get_upcoming_assignments,
    get_course_grades, get_course_announcements, get_canvas_todos, get_course_syllabus,
    # Grubhub
    search_grubhub_restaurants, get_restaurant_menu, place_grubhub_order,
    # BuckeyeLink
    get_class_schedule, get_grades, get_financial_aid_status,
    get_holds_and_todos, get_enrollment_info, get_buckeyelink_dashboard,
]


def create_agent() -> RequirementAgent:
    llm = ChatModel.from_name("watsonx:ibm/granite-3-8b-instruct")

    agent = RequirementAgent(
        llm=llm,
        tools=ALL_TOOLS,
        memory=TokenMemory(llm),
        role="BuckeyeBot — Ohio State University student assistant",
        instructions=[
            "You help OSU students via text message. Keep responses concise and SMS-friendly (under 1500 characters).",
            "Use campus tools to answer questions about dining, buses, parking, events, classes, library rooms, rec sports, buildings, the academic calendar, student orgs, food trucks, athletics, and BuckID merchants.",
            "Use Canvas tools to check courses, assignments, grades, announcements, and to-do items.",
            "Use Grubhub tools to help order food from nearby restaurants.",
            "Use BuckeyeLink tools to check class schedules, grades, financial aid, holds/to-dos, enrollment info, and the dashboard overview.",
            "When presenting data, summarize the most relevant results rather than dumping raw JSON.",
            "If a tool returns an error, explain the issue simply and suggest alternatives.",
        ],
    )
    return agent
