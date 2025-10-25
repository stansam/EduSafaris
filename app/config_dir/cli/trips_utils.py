from decimal import Decimal
from app.extensions import db
from datetime import date, timedelta
from app.models import User
from flask import current_app


def get_or_create_organizer():
    """Get or create a default organizer user for trips"""
    try:
        organizer = User.query.filter_by(email='organizer@school.com').first()
        teacher_data = {
                'email': 'organizer@school.edu',
                'password': 'organizer123',
                'first_name': 'Mike',
                'last_name': 'Kemboi',
                'role': 'teacher',
                'is_active': True,
                'is_verified': True,
                'phone': '+254712345678',
                'school': 'Mangu High School',
                'emergency_contact': 'Mary Jane',
                'emergency_phone': '+254787654321'
            }
        if not organizer:
            current_app.logger.info("Creating default organizer user...")
            organizer = User(**teacher_data)
            db.session.add(organizer)
            db.session.commit()
            current_app.logger.info(f"Created organizer with ID: {organizer.id}")
        return organizer
    except Exception as e:
        current_app.logger.error(f"Error getting/creating organizer: {str(e)}")
        db.session.rollback()
        raise


def get_trip_data(organizer_id):
    """Return detailed trip data for 12 Kenyan destinations"""
    today = date.today()
    
    trips_data = [
        {
            'title': 'Maasai Mara Wildlife Safari',
            'description': 'Experience the wonder of the Maasai Mara National Reserve, home to the Great Migration and abundant wildlife. Students will learn about ecosystems, wildlife conservation, and Maasai culture through guided game drives and cultural visits.',
            'destination': 'Maasai Mara National Reserve',
            'category': 'wildlife',
            'grade_level': '6-12',
            'start_date': today + timedelta(days=45),
            'end_date': today + timedelta(days=48),
            'registration_deadline': today + timedelta(days=30),
            'max_participants': 40,
            'min_participants': 15,
            'price_per_student': Decimal('25000.00'),
            'status': 'active',
            'featured': True,
            'medical_info_required': True,
            'consent_required': True,
            'organizer_id': organizer_id,
            'itinerary': {
                'day_1': 'Departure from Nairobi, arrival at Maasai Mara, afternoon game drive',
                'day_2': 'Full day game drive, visit to Mara River, wildlife photography session',
                'day_3': 'Morning game drive, visit to Maasai village, cultural exchange program',
                'day_4': 'Early morning game drive, return to Nairobi'
            }
        },
        {
            'title': 'Mount Kenya Hiking Adventure',
            'description': 'Challenge yourself with a trek to Point Lenana on Mount Kenya, Africa\'s second-highest peak. This expedition teaches students about mountain ecosystems, altitude acclimatization, and physical endurance while experiencing breathtaking alpine scenery.',
            'destination': 'Mount Kenya National Park',
            'category': 'adventure',
            'grade_level': '9-12',
            'start_date': today + timedelta(days=60),
            'end_date': today + timedelta(days=65),
            'registration_deadline': today + timedelta(days=40),
            'max_participants': 25,
            'min_participants': 10,
            'price_per_student': Decimal('35000.00'),
            'status': 'active',
            'featured': True,
            'medical_info_required': True,
            'consent_required': True,
            'organizer_id': organizer_id,
            'itinerary': {
                'day_1': 'Nairobi to Naro Moru, acclimatization hike',
                'day_2': 'Trek to Met Station (3,300m)',
                'day_3': 'Met Station to Mackinder\'s Camp (4,200m)',
                'day_4': 'Summit attempt Point Lenana (4,985m), descend to Met Station',
                'day_5': 'Descend to Naro Moru',
                'day_6': 'Return to Nairobi'
            }
        },
        {
            'title': 'Lake Nakuru Flamingo Expedition',
            'description': 'Discover the beauty of Lake Nakuru, famous for its flamingo populations and rhino sanctuary. Students will study ornithology, lake ecosystems, and conservation efforts while observing diverse birdlife and endangered species.',
            'destination': 'Lake Nakuru National Park',
            'category': 'science',
            'grade_level': '3-8',
            'start_date': today + timedelta(days=25),
            'end_date': today + timedelta(days=26),
            'registration_deadline': today + timedelta(days=15),
            'max_participants': 35,
            'min_participants': 12,
            'price_per_student': Decimal('12000.00'),
            'status': 'active',
            'featured': False,
            'medical_info_required': True,
            'consent_required': True,
            'organizer_id': organizer_id,
            'itinerary': {
                'day_1': 'Morning departure, game drive, bird watching session, picnic lunch, rhino tracking, evening return',
                'day_2': 'Early morning bird count, nature walk, conservation talk, return to Nairobi'
            }
        },
        {
            'title': 'Fort Jesus Historical Tour',
            'description': 'Step back in time at Fort Jesus in Mombasa, a UNESCO World Heritage Site. Students will explore Swahili coastal history, Portuguese colonial architecture, and the maritime trade routes that shaped East Africa.',
            'destination': 'Fort Jesus, Mombasa',
            'category': 'history',
            'grade_level': '6-12',
            'start_date': today + timedelta(days=35),
            'end_date': today + timedelta(days=37),
            'registration_deadline': today + timedelta(days=20),
            'max_participants': 45,
            'min_participants': 20,
            'price_per_student': Decimal('18000.00'),
            'status': 'active',
            'featured': True,
            'medical_info_required': False,
            'consent_required': True,
            'organizer_id': organizer_id,
            'itinerary': {
                'day_1': 'Train journey to Mombasa, check-in, Old Town walking tour',
                'day_2': 'Fort Jesus guided tour, museum visit, Swahili culture workshop',
                'day_3': 'Beach time, return journey to Nairobi'
            }
        },
        {
            'title': 'Hell\'s Gate Geology Field Trip',
            'description': 'Explore the dramatic landscapes of Hell\'s Gate National Park, where students can walk among wildlife and study unique geological formations. Learn about geothermal energy, volcanic activity, and rift valley formation.',
            'destination': 'Hell\'s Gate National Park',
            'category': 'science',
            'grade_level': '6-10',
            'start_date': today + timedelta(days=20),
            'end_date': today + timedelta(days=20),
            'registration_deadline': today + timedelta(days=10),
            'max_participants': 50,
            'min_participants': 15,
            'price_per_student': Decimal('6500.00'),
            'status': 'active',
            'featured': False,
            'medical_info_required': False,
            'consent_required': True,
            'organizer_id': organizer_id,
            'itinerary': {
                'day_1': 'Early departure, cycling through the gorge, rock climbing, gorge walk, geothermal plant visit, evening return'
            }
        },
        {
            'title': 'Lamu Island Cultural Immersion',
            'description': 'Experience the timeless beauty of Lamu Island, Kenya\'s oldest living Swahili settlement. Students will engage in cultural exchange, learn about Islamic architecture, traditional dhow building, and coastal conservation.',
            'destination': 'Lamu Island',
            'category': 'cultural',
            'grade_level': '9-12',
            'start_date': today + timedelta(days=70),
            'end_date': today + timedelta(days=74),
            'registration_deadline': today + timedelta(days=50),
            'max_participants': 30,
            'min_participants': 12,
            'price_per_student': Decimal('42000.00'),
            'status': 'active',
            'featured': True,
            'medical_info_required': True,
            'consent_required': True,
            'organizer_id': organizer_id,
            'itinerary': {
                'day_1': 'Flight to Lamu, dhow transfer, orientation walk',
                'day_2': 'Old Town heritage tour, Lamu Museum, Swahili house visit',
                'day_3': 'Dhow sailing trip, mangrove forest exploration',
                'day_4': 'Traditional craft workshop, beach activities',
                'day_5': 'Return flight to Nairobi'
            }
        },
        {
            'title': 'Kakamega Forest Biodiversity Study',
            'description': 'Venture into Kenya\'s last remaining tropical rainforest. Students will conduct biodiversity surveys, study endemic species, learn about forest conservation, and understand the importance of rainforest ecosystems.',
            'destination': 'Kakamega Forest',
            'category': 'science',
            'grade_level': '9-12',
            'start_date': today + timedelta(days=55),
            'end_date': today + timedelta(days=58),
            'registration_deadline': today + timedelta(days=35),
            'max_participants': 28,
            'min_participants': 10,
            'price_per_student': Decimal('22000.00'),
            'status': 'active',
            'featured': False,
            'medical_info_required': True,
            'consent_required': True,
            'organizer_id': organizer_id,
            'itinerary': {
                'day_1': 'Journey to Kakamega, forest orientation, night walk',
                'day_2': 'Canopy walk, butterfly tracking, bird watching',
                'day_3': 'Biodiversity survey, plant identification workshop',
                'day_4': 'Community forest project visit, return journey'
            }
        },
        {
            'title': 'Nairobi National Museum Education Tour',
            'description': 'Discover Kenya\'s rich heritage at the National Museum. Students will explore exhibits on human evolution, tribal cultures, contemporary art, and natural history, gaining comprehensive understanding of Kenya\'s past and present.',
            'destination': 'Nairobi National Museum',
            'category': 'history',
            'grade_level': 'K-8',
            'start_date': today + timedelta(days=12),
            'end_date': today + timedelta(days=12),
            'registration_deadline': today + timedelta(days=7),
            'max_participants': 60,
            'min_participants': 20,
            'price_per_student': Decimal('3500.00'),
            'status': 'active',
            'featured': False,
            'medical_info_required': False,
            'consent_required': True,
            'organizer_id': organizer_id,
            'itinerary': {
                'day_1': 'Museum guided tour, Great Hall of Mammals, Kenya History exhibits, Snake Park visit, art gallery, lunch at museum grounds'
            }
        },
        {
            'title': 'Amboseli Elephant Research Trip',
            'description': 'Study elephant behavior against the backdrop of Mount Kilimanjaro at Amboseli National Park. Students will learn about wildlife research methods, elephant conservation, and the challenges facing Kenya\'s megafauna.',
            'destination': 'Amboseli National Park',
            'category': 'wildlife',
            'grade_level': '9-12',
            'start_date': today + timedelta(days=50),
            'end_date': today + timedelta(days=52),
            'registration_deadline': today + timedelta(days=35),
            'max_participants': 32,
            'min_participants': 12,
            'price_per_student': Decimal('28000.00'),
            'status': 'active',
            'featured': True,
            'medical_info_required': True,
            'consent_required': True,
            'organizer_id': organizer_id,
            'itinerary': {
                'day_1': 'Drive to Amboseli, afternoon game drive, elephant observation',
                'day_2': 'Full day with elephant research team, data collection workshop, photography session',
                'day_3': 'Morning game drive, conservation talk, return to Nairobi'
            }
        },
        {
            'title': 'Tsavo East Adventure Safari',
            'description': 'Explore one of Kenya\'s largest national parks, famous for its red elephants and diverse landscapes. Students will learn about large-scale conservation, anti-poaching efforts, and the ecology of semi-arid regions.',
            'destination': 'Tsavo East National Park',
            'category': 'wildlife',
            'grade_level': '6-12',
            'start_date': today + timedelta(days=80),
            'end_date': today + timedelta(days=82),
            'registration_deadline': today + timedelta(days=60),
            'max_participants': 38,
            'min_participants': 15,
            'price_per_student': Decimal('24000.00'),
            'status': 'active',
            'featured': False,
            'medical_info_required': True,
            'consent_required': True,
            'organizer_id': organizer_id,
            'itinerary': {
                'day_1': 'SGR train to Voi, transfer to park, afternoon game drive',
                'day_2': 'Full day safari, Aruba Dam visit, Lugard Falls exploration',
                'day_3': 'Morning game drive, return via SGR'
            }
        },
        {
            'title': 'Great Rift Valley Geological Survey',
            'description': 'Travel through the dramatic Rift Valley escarpment, studying its formation and geological significance. Students will visit viewpoints, learn about plate tectonics, and understand how the Rift Valley shapes Kenya\'s landscape and climate.',
            'destination': 'Great Rift Valley',
            'category': 'science',
            'grade_level': '6-10',
            'start_date': today + timedelta(days=28),
            'end_date': today + timedelta(days=29),
            'registration_deadline': today + timedelta(days=18),
            'max_participants': 42,
            'min_participants': 15,
            'price_per_student': Decimal('9500.00'),
            'status': 'active',
            'featured': False,
            'medical_info_required': False,
            'consent_required': True,
            'organizer_id': organizer_id,
            'itinerary': {
                'day_1': 'Rift Valley viewpoint, Longonot Crater hike, geological formations study',
                'day_2': 'Lake Naivasha boat ride, Crescent Island walk, return journey'
            }
        },
        {
            'title': 'Bomas of Kenya Cultural Experience',
            'description': 'Immerse in Kenya\'s diverse tribal cultures at Bomas of Kenya. Students will witness traditional dances, music, crafts, and homestead exhibitions representing Kenya\'s 42+ ethnic communities, fostering cultural appreciation and national unity.',
            'destination': 'Bomas of Kenya, Nairobi',
            'category': 'cultural',
            'grade_level': 'K-12',
            'start_date': today + timedelta(days=15),
            'end_date': today + timedelta(days=15),
            'registration_deadline': today + timedelta(days=8),
            'max_participants': 80,
            'min_participants': 25,
            'price_per_student': Decimal('2500.00'),
            'status': 'active',
            'featured': False,
            'medical_info_required': False,
            'consent_required': True,
            'organizer_id': organizer_id,
            'itinerary': {
                'day_1': 'Village homesteads tour, traditional dance performance, craft demonstrations, cultural lunch, interactive workshops'
            }
        }
    ]
    
    return trips_data