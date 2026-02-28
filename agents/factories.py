from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.backend import ChatModel
from beeai_framework.memory import UnconstrainedMemory

# Campus tools
from backend.integrations.campus.dining import get_dining_locations, get_dining_locations_with_menus, get_dining_menu, search_dining_locations
from backend.integrations.campus.bus import get_bus_routes, get_bus_stops, get_bus_vehicles
from backend.integrations.campus.parking import get_parking_availability
from backend.integrations.campus.events import get_campus_events, search_campus_events, get_events_by_date_range
from backend.integrations.campus.classes import search_classes
from backend.integrations.campus.library import get_library_locations, search_library_locations, get_library_rooms, search_library_rooms, get_rooms_by_capacity, get_rooms_with_amenities
from backend.integrations.campus.recsports import get_recsports_facilities, search_recsports_facilities, get_facility_hours, get_facility_events
from backend.integrations.campus.buildings import get_buildings, search_buildings, get_building_details, find_room_type
from backend.integrations.campus.calendar import get_academic_calendar, get_university_holidays, search_calendar_events
from backend.integrations.campus.utils import get_current_time
from backend.integrations.campus.directory import search_people
from backend.integrations.campus.athletics import get_athletics_all, search_sports, get_sport_by_gender, get_upcoming_games
from backend.integrations.campus.merchants import get_buckid_merchants, search_merchants, get_merchants_by_food_type, get_merchants_with_meal_plan
from backend.integrations.campus.foodtrucks import get_foodtruck_events, search_foodtrucks, get_foodtrucks_by_location
from backend.integrations.campus.studentorgs import get_student_organizations, search_student_orgs, get_orgs_by_type, get_orgs_by_career_level

# Canvas tools
from backend.integrations.canvas.tools import (
    get_canvas_courses,
    get_course_assignments,
    get_upcoming_assignments,
    get_course_grades,
    get_course_announcements,
    get_canvas_todos,
    get_course_syllabus,
)

# Grubhub tools
from backend.integrations.grubhub.tools import (
    search_grubhub_restaurants, get_restaurant_menu, place_grubhub_order,
    schedule_grubhub_order, list_scheduled_grubhub_orders, cancel_scheduled_grubhub_order,
)

# BuckeyeLink tools
from backend.integrations.buckeyelink.tools import (
    get_class_schedule, get_grades, get_financial_aid_status,
    get_holds_and_todos, get_enrollment_info, get_buckeyelink_dashboard,
    query_buckeyelink,
)

# BuckeyeMail tools
from backend.integrations.buckeyemail.tools import (
    get_email_inbox, search_emails, get_unread_email_count, get_email_detail,
)


ALL_TOOLS = [
    # Dining
    get_dining_locations, get_dining_locations_with_menus, get_dining_menu, search_dining_locations,
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
    # Time
    get_current_time,
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
    schedule_grubhub_order, list_scheduled_grubhub_orders, cancel_scheduled_grubhub_order,
    # BuckeyeLink
    get_class_schedule, get_grades, get_financial_aid_status,
    get_holds_and_todos, get_enrollment_info, get_buckeyelink_dashboard,
    query_buckeyelink,
    # BuckeyeMail
    get_email_inbox, search_emails, get_unread_email_count, get_email_detail,
]


def create_granite_agent(tools=None) -> RequirementAgent:
    """Fast/cheap Granite agent for intent classification and SMS formatting."""
    llm = ChatModel.from_name("watsonx:ibm/granite-3-8b-instruct")
    return RequirementAgent(
        llm=llm,
        tools=tools or [],
        memory=UnconstrainedMemory(),
        role="BuckeyeClaw — Ohio State University student assistant",
        instructions=[
            "You help OSU students via text message. Sound like a chill, helpful friend — warm but not over the top. No emojis, no exclamation marks, no robotic language.",
            "Keep responses concise (under 800 characters). No markdown (no **, ##, or * bullets). Use plain text, line breaks, and dashes for lists.",
            "Each message starts with [caller: +1...] — this is the user's phone number. When scheduling Grubhub orders, pass it as from_number.",
            "When a user asks to order food at a specific future time (e.g. 'at 6pm', 'in 2 hours'), use schedule_grubhub_order instead of place_grubhub_order. For immediate orders with no time specified, use place_grubhub_order.",
            "When presenting data, pick out the most relevant info rather than dumping everything.",
            "If a tool returns an error, explain the issue simply and suggest alternatives.",
        ],
    )


GRUBHUB_TOOLS = [
    search_grubhub_restaurants, get_restaurant_menu, place_grubhub_order,
    schedule_grubhub_order, list_scheduled_grubhub_orders, cancel_scheduled_grubhub_order,
]


def create_grubhub_agent() -> RequirementAgent:
    """Dedicated Grubhub food-ordering agent with focused tools and instructions."""
    llm = ChatModel.from_name("anthropic:claude-sonnet-4-6")
    return RequirementAgent(
        llm=llm,
        tools=GRUBHUB_TOOLS,
        memory=UnconstrainedMemory(),
        role="BuckeyeClaw Grubhub Agent — food ordering assistant for OSU students",
        instructions=[
            "You are a food ordering assistant. You help Ohio State students order food from Grubhub.",
            "You have six tools: search restaurants, view menus, place immediate orders, schedule future orders, list scheduled orders, and cancel scheduled orders.",
            "Workflow for ordering: 1) search_grubhub_restaurants to find the restaurant, 2) get_restaurant_menu to see what's available, 3) place_grubhub_order or schedule_grubhub_order to complete the order.",
            "If the user specifies a future time (e.g. 'at 6pm', 'in 2 hours', 'tonight at 8'), use schedule_grubhub_order. For immediate orders with no time specified, use place_grubhub_order.",
            "The user's phone number is provided as [caller: +1...] — pass it as from_number when scheduling orders.",
            "If a search returns no results, suggest the user try a different name or spelling.",
            "If the emulator or Appium is unavailable, let the user know Grubhub ordering is temporarily down.",
            "Keep responses concise and direct — no emojis, no filler. This goes to an SMS user.",
        ],
    )


BUCKEYEMAIL_TOOLS = [
    get_email_inbox, search_emails, get_unread_email_count, get_email_detail,
]


def create_email_agent() -> RequirementAgent:
    """Dedicated BuckeyeMail agent for email queries via Microsoft Graph."""
    llm = ChatModel.from_name("anthropic:claude-sonnet-4-6")
    return RequirementAgent(
        llm=llm,
        tools=BUCKEYEMAIL_TOOLS,
        memory=UnconstrainedMemory(),
        role="BuckeyeClaw Email Agent — BuckeyeMail assistant for OSU students",
        instructions=[
            "You help Ohio State students check their BuckeyeMail (OSU Microsoft 365 email).",
            "You have four tools: get inbox, search emails, get unread count, and get email detail.",
            "IMPORTANT: Always pass the caller's phone number (from [caller: +1...]) as from_number to every tool call.",
            "If the user is not connected yet, the tools will return an onboarding link — just pass that along.",
            "For inbox requests, use get_email_inbox. For searching by sender/subject/keyword, use search_emails.",
            "If the user asks about a specific email, use get_email_detail with the message ID from a previous inbox or search result.",
            "Keep responses concise and direct — no emojis, no filler. This goes to an SMS user.",
        ],
    )


def create_claude_agent() -> RequirementAgent:
    """Claude Opus 4.6 agent for complex reasoning and tool execution."""
    llm = ChatModel.from_name("anthropic:claude-opus-4-6")
    return RequirementAgent(
        llm=llm,
        tools=ALL_TOOLS,
        memory=UnconstrainedMemory(),
        role="BuckeyeClaw planner — Ohio State University student assistant",
        instructions=[
            "You are the planning and execution brain of BuckeyeClaw.",
            "Given the user's intent and parameters, select and call the appropriate tools.",
            "Synthesize tool results into a short, natural response. Sound like a chill, helpful friend — warm but not over the top. No emojis.",
            "NEVER use markdown formatting — no **, no ##, no bullet points with *. Use plain text, line breaks, and dashes for lists.",
            "Be clear and concise but still personable. Under 800 characters when possible.",
            "Use campus tools for dining, buses, parking, events, classes, library rooms, rec sports, buildings, the academic calendar, student orgs, food trucks, athletics, and BuckID merchants.",
            "Use Canvas tools to check courses, assignments, grades, announcements, and to-do items.",
            "Use Grubhub tools to help order food from nearby restaurants.",
            "Use BuckeyeLink tools to check class schedules, grades, financial aid, holds/to-dos, enrollment info, and the dashboard overview.",
            "Use BuckeyeMail tools to check email inbox, search emails, get unread count, or read a specific email. Always pass the caller's phone number as from_number.",
        ],
    )
