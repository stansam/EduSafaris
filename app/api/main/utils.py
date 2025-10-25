def get_trip_image_url(trip):
    """Get image URL for trip based on category or destination"""
    # Default images by category
    category_images = {
        'wildlife': 'https://images.unsplash.com/photo-1516426122078-c23e76319801?w=800&h=500&fit=crop',
        'nature': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=500&fit=crop',
        'adventure': 'https://images.unsplash.com/photo-1591825729269-caeb344f6df2?w=800&h=500&fit=crop',
        'science': 'https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=800&h=500&fit=crop',
        'history': 'https://images.unsplash.com/photo-1513581166391-887a96ddeafd?w=800&h=500&fit=crop',
        'cultural': 'https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&h=500&fit=crop'
    }
    
    # Return category-specific image or default
    return category_images.get(trip.category.lower() if trip.category else 'adventure', 
                               'https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=800&h=500&fit=crop')


def calculate_trip_rating(trip):
    """Calculate trip rating (placeholder - implement based on reviews)"""
    # TODO: Implement actual rating calculation based on reviews
    # For now, return a default rating
    return 4.8