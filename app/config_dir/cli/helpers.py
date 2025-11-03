
from datetime import datetime, date, timedelta
from decimal import Decimal
import random
import string
from faker import Faker

# Initialize Faker for generating realistic data
fake = Faker(['en_KE', 'en_US'])  # Kenya and US locales


# ============================================================================
# DATA GENERATORS
# ============================================================================

class DataGenerator:
    """Generate realistic sample data for various models"""
    
    # Kenyan city data
    KENYAN_CITIES = [
        {'name': 'Nairobi', 'county': 'Nairobi County'},
        {'name': 'Mombasa', 'county': 'Mombasa County'},
        {'name': 'Kisumu', 'county': 'Kisumu County'},
        {'name': 'Nakuru', 'county': 'Nakuru County'},
        {'name': 'Eldoret', 'county': 'Uasin Gishu County'},
        {'name': 'Thika', 'county': 'Kiambu County'},
        {'name': 'Naivasha', 'county': 'Nakuru County'},
        {'name': 'Malindi', 'county': 'Kilifi County'},
    ]
    
    # Common Kenyan names
    MALE_FIRST_NAMES = [
        'John', 'David', 'James', 'Peter', 'Michael', 'Joseph', 'Samuel',
        'Daniel', 'Brian', 'Kevin', 'Emmanuel', 'Joshua', 'Collins', 'Dennis'
    ]
    
    FEMALE_FIRST_NAMES = [
        'Mary', 'Grace', 'Lucy', 'Sarah', 'Faith', 'Joy', 'Mercy',
        'Rachel', 'Rebecca', 'Esther', 'Ruth', 'Jane', 'Rose', 'Emily'
    ]
    
    LAST_NAMES = [
        'Kamau', 'Njoroge', 'Mwangi', 'Kimani', 'Kariuki', 'Ochieng',
        'Otieno', 'Akinyi', 'Adhiambo', 'Wanjiru', 'Nyambura', 'Wambui',
        'Mutua', 'Muturi', 'Kipchoge', 'Cheruiyot', 'Kiplagat'
    ]
    
    # Trip destinations in Kenya
    DESTINATIONS = [
        {
            'name': 'Maasai Mara National Reserve',
            'country': 'Kenya',
            'type': 'wildlife',
            'coords': (-1.5, 35.1)
        },
        {
            'name': 'Mount Kenya National Park',
            'country': 'Kenya',
            'type': 'mountain',
            'coords': (-0.15, 37.3)
        },
        {
            'name': 'Mombasa Marine National Park',
            'country': 'Kenya',
            'type': 'marine',
            'coords': (-4.05, 39.66)
        },
        {
            'name': 'Lake Nakuru National Park',
            'country': 'Kenya',
            'type': 'lake',
            'coords': (-0.3, 36.08)
        },
        {
            'name': 'Amboseli National Park',
            'country': 'Kenya',
            'type': 'wildlife',
            'coords': (-2.65, 37.25)
        },
        {
            'name': 'Hell\'s Gate National Park',
            'country': 'Kenya',
            'type': 'adventure',
            'coords': (-0.91, 36.31)
        },
        {
            'name': 'Tsavo National Park',
            'country': 'Kenya',
            'type': 'wildlife',
            'coords': (-3.0, 38.5)
        },
        {
            'name': 'Ol Pejeta Conservancy',
            'country': 'Kenya',
            'type': 'conservation',
            'coords': (0.0, 36.95)
        }
    ]
    
    @staticmethod
    def generate_kenyan_phone():
        """Generate a realistic Kenyan phone number"""
        prefixes = ['722', '733', '700', '710', '720', '724', '757', '740']
        return f"+254-{random.choice(prefixes)}-{random.randint(100000, 999999)}"
    
    @staticmethod
    def generate_email(first_name, last_name, domain=None):
        """Generate a realistic email address"""
        domains = domain or ['gmail.com', 'yahoo.com', 'email.com', 'hotmail.com']
        separators = ['.', '_', '']
        sep = random.choice(separators)
        return f"{first_name.lower()}{sep}{last_name.lower()}{random.randint(1, 999)}@{random.choice(domains)}"
    
    @staticmethod
    def generate_kenyan_name(gender='random'):
        """Generate a realistic Kenyan name"""
        if gender == 'random':
            gender = random.choice(['male', 'female'])
        
        if gender == 'male':
            first_name = random.choice(DataGenerator.MALE_FIRST_NAMES)
        else:
            first_name = random.choice(DataGenerator.FEMALE_FIRST_NAMES)
        
        last_name = random.choice(DataGenerator.LAST_NAMES)
        return first_name, last_name
    
    @staticmethod
    def generate_trip_title(destination_type):
        """Generate an appropriate trip title"""
        templates = {
            'wildlife': [
                '{destination} Safari Adventure',
                'Wildlife Exploration at {destination}',
                '{destination} Conservation Trip',
                'Safari Experience: {destination}'
            ],
            'marine': [
                '{destination} Marine Biology Workshop',
                'Coastal Adventure: {destination}',
                '{destination} Snorkeling Expedition',
                'Marine Life Study at {destination}'
            ],
            'mountain': [
                '{destination} Climbing Expedition',
                'Mountain Adventure: {destination}',
                '{destination} Hiking Challenge',
                'Summit Quest: {destination}'
            ],
            'lake': [
                '{destination} Ecology Study',
                'Bird Watching at {destination}',
                '{destination} Environmental Tour',
                'Lake Ecosystem Exploration: {destination}'
            ],
            'adventure': [
                '{destination} Adventure Camp',
                'Outdoor Exploration: {destination}',
                '{destination} Team Building Trip',
                'Adventure Challenge at {destination}'
            ],
            'conservation': [
                '{destination} Conservation Experience',
                'Wildlife Conservation at {destination}',
                '{destination} Eco-Tourism Trip',
                'Conservation Education: {destination}'
            ]
        }
        
        templates_list = templates.get(destination_type, templates['wildlife'])
        return random.choice(templates_list)
    
    @staticmethod
    def generate_trip_description(destination_type):
        """Generate trip description based on type"""
        descriptions = {
            'wildlife': 'An educational safari experience focusing on wildlife conservation, animal behavior, and ecosystem studies. Students will observe wildlife in their natural habitat while learning about biodiversity and conservation efforts.',
            'marine': 'A comprehensive marine biology workshop including snorkeling, coral reef studies, and marine conservation education. Students will explore coastal ecosystems and learn about marine biodiversity.',
            'mountain': 'A challenging mountain expedition with professional guides, focusing on physical geography, mountain ecosystems, and outdoor survival skills. Students will develop teamwork and perseverance.',
            'lake': 'An ecological study trip exploring lake ecosystems, bird species, and environmental conservation. Students will engage in hands-on field research and wildlife observation.',
            'adventure': 'An action-packed adventure trip combining physical challenges with environmental education. Students will develop confidence, teamwork, and appreciation for nature.',
            'conservation': 'An immersive conservation experience where students learn about wildlife protection, habitat preservation, and sustainable tourism practices through hands-on activities.'
        }
        
        return descriptions.get(destination_type, descriptions['wildlife'])
    
    @staticmethod
    def generate_learning_objectives(destination_type):
        """Generate learning objectives based on trip type"""
        objectives = {
            'wildlife': [
                'Wildlife species identification',
                'Understanding ecosystem dynamics',
                'Conservation awareness and practices',
                'Animal behavior observation',
                'Habitat preservation importance'
            ],
            'marine': [
                'Marine biodiversity identification',
                'Coral reef ecology',
                'Ocean conservation methods',
                'Coastal ecosystem understanding',
                'Marine pollution awareness'
            ],
            'mountain': [
                'Physical geography concepts',
                'Mountain ecosystem adaptation',
                'Outdoor survival skills',
                'Team building and leadership',
                'Physical endurance and determination'
            ],
            'lake': [
                'Lake ecosystem dynamics',
                'Bird species identification',
                'Water quality assessment',
                'Environmental photography',
                'Field research techniques'
            ],
            'adventure': [
                'Physical fitness and coordination',
                'Risk assessment and management',
                'Team collaboration',
                'Problem-solving skills',
                'Environmental appreciation'
            ],
            'conservation': [
                'Conservation principles',
                'Habitat restoration techniques',
                'Community conservation involvement',
                'Sustainable tourism practices',
                'Wildlife protection methods'
            ]
        }
        
        return random.sample(objectives.get(destination_type, objectives['wildlife']), 3)
    
    @staticmethod
    def generate_random_date_range(days_from_now, duration_days):
        """Generate a date range starting from days_from_now with given duration"""
        start_date = date.today() + timedelta(days=days_from_now)
        end_date = start_date + timedelta(days=duration_days - 1)
        return start_date, end_date
    
    @staticmethod
    def generate_reference_number(prefix='REF'):
        """Generate a unique reference number"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"{prefix}-{timestamp}-{random_str}"
    
    @staticmethod
    def generate_transaction_id():
        """Generate a transaction ID"""
        return f"TXN{datetime.now().strftime('%Y%m%d')}{random.randint(100000, 999999)}"


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

class ValidationHelper:
    """Helper functions for data validation"""
    
    @staticmethod
    def validate_email(email):
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number format"""
        import re
        # Allow various formats including +254, 07xx, etc.
        pattern = r'^(\+?254|0)?[7][0-9]{8}$'
        clean_phone = phone.replace('-', '').replace(' ', '')
        return re.match(pattern, clean_phone) is not None
    
    @staticmethod
    def validate_date_range(start_date, end_date):
        """Validate that end_date is after start_date"""
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        return end_date >= start_date
    
    @staticmethod
    def validate_age_for_grade(age, grade_level):
        """Validate if age is appropriate for grade level"""
        grade_age_mapping = {
            'Pre-school': (3, 5),
            'Grade 1': (6, 7),
            'Grade 2': (7, 8),
            'Grade 3': (8, 9),
            'Grade 4': (9, 10),
            'Grade 5': (10, 11),
            'Grade 6': (11, 12),
            'Grade 7': (12, 13),
            'Grade 8': (13, 14),
            'Grade 9': (14, 15),
            'Grade 10': (15, 16),
            'Grade 11': (16, 17),
            'Grade 12': (17, 18)
        }
        
        if grade_level in grade_age_mapping:
            min_age, max_age = grade_age_mapping[grade_level]
            return min_age <= age <= max_age + 1
        return True


# ============================================================================
# CALCULATION HELPERS
# ============================================================================

class CalculationHelper:
    """Helper functions for calculations"""
    
    @staticmethod
    def calculate_age(date_of_birth):
        """Calculate age from date of birth"""
        today = date.today()
        if isinstance(date_of_birth, str):
            date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        
        age = today.year - date_of_birth.year
        if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
            age -= 1
        return age
    
    @staticmethod
    def calculate_trip_revenue(registrations, price_per_student):
        """Calculate total revenue from registrations"""
        confirmed_count = sum(1 for r in registrations if r.status == 'confirmed')
        return Decimal(confirmed_count) * price_per_student
    
    @staticmethod
    def calculate_payment_status(total_amount, amount_paid):
        """Determine payment status"""
        if amount_paid >= total_amount:
            return 'paid'
        elif amount_paid > 0:
            return 'partial'
        else:
            return 'unpaid'
    
    @staticmethod
    def calculate_distance_km(lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates in kilometers"""
        import math
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        return c * r


# ============================================================================
# LOGGING HELPERS
# ============================================================================

class LoggingHelper:
    """Helper functions for consistent logging"""
    
    @staticmethod
    def log_entity_creation(logger, entity_type, count, details=None):
        """Log entity creation"""
        message = f"Created {count} {entity_type}"
        if details:
            message += f" - {details}"
        logger.info(message)
    
    @staticmethod
    def log_operation_start(logger, operation):
        """Log start of operation"""
        logger.info(f"Starting {operation}...")
    
    @staticmethod
    def log_operation_complete(logger, operation, count=None):
        """Log completion of operation"""
        message = f"Completed {operation}"
        if count is not None:
            message += f" - {count} items processed"
        logger.info(message)
    
    @staticmethod
    def log_error(logger, operation, error, include_traceback=True):
        """Log error with details"""
        logger.error(f"Error in {operation}: {str(error)}", exc_info=include_traceback)


# ============================================================================
# PROGRESS TRACKING
# ============================================================================

class ProgressTracker:
    """Track progress of initialization operations"""
    
    def __init__(self, total, description="Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = datetime.now()
    
    def update(self, increment=1):
        """Update progress"""
        self.current += increment
        percentage = (self.current / self.total) * 100 if self.total > 0 else 0
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        if self.current > 0:
            rate = self.current / elapsed
            remaining = (self.total - self.current) / rate if rate > 0 else 0
            return f"{self.description}: {self.current}/{self.total} ({percentage:.1f}%) - ETA: {remaining:.0f}s"
        return f"{self.description}: {self.current}/{self.total} ({percentage:.1f}%)"
    
    def is_complete(self):
        """Check if complete"""
        return self.current >= self.total


# ============================================================================
# BATCH PROCESSING
# ============================================================================

class BatchProcessor:
    """Process large datasets in batches"""
    
    def __init__(self, batch_size=100):
        self.batch_size = batch_size
        self.current_batch = []
    
    def add(self, item):
        """Add item to current batch"""
        self.current_batch.append(item)
        
        if len(self.current_batch) >= self.batch_size:
            return self.flush()
        return []
    
    def flush(self):
        """Return and clear current batch"""
        batch = self.current_batch
        self.current_batch = []
        return batch
    
    def has_items(self):
        """Check if there are items in current batch"""
        return len(self.current_batch) > 0


# ============================================================================
# DATA CONSISTENCY CHECKS
# ============================================================================

class ConsistencyChecker:
    """Check data consistency and relationships"""
    
    @staticmethod
    def check_foreign_keys(session, model, foreign_key_field, referenced_model):
        """Check if all foreign keys are valid"""
        from sqlalchemy import inspect
        
        invalid_records = []
        records = session.query(model).all()
        
        for record in records:
            fk_value = getattr(record, foreign_key_field)
            if fk_value is not None:
                referenced = session.query(referenced_model).get(fk_value)
                if not referenced:
                    invalid_records.append(record.id)
        
        return invalid_records
    
    @staticmethod
    def check_date_consistency(records, start_field, end_field):
        """Check if date ranges are consistent"""
        invalid = []
        for record in records:
            start = getattr(record, start_field)
            end = getattr(record, end_field)
            if start and end and start > end:
                invalid.append(record.id)
        return invalid
    
    @staticmethod
    def check_required_relationships(session, model, relationship_name):
        """Check if required relationships exist"""
        from sqlalchemy.orm import class_mapper
        
        missing = []
        records = session.query(model).all()
        
        for record in records:
            related = getattr(record, relationship_name)
            if related is None or (hasattr(related, '__len__') and len(related) == 0):
                missing.append(record.id)
        
        return missing