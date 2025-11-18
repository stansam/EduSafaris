from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import or_, and_
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models import Vendor, User, Document, ServiceBooking, ActivityLog, Review
from app.api.admin.vendors.utils import validate_email, validate_phone
from app.utils.utils import roles_required
from app.api import api_bp as admin_vendor_bp 


# ==================== DECORATORS ====================
def log_admin_action(action, entity_type, entity_id, description=None):
    """Helper function to log admin actions"""
    try:
        ActivityLog.log_action(
            action=action,
            user_id=current_user.id,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            category='admin',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            request_method=request.method,
            request_url=request.url
        )
    except Exception as e:
        current_app.logger.error(f"Failed to log admin action: {str(e)}")


# ==================== VENDOR LISTING & SEARCH ====================

@admin_vendor_bp.route('/admin/vendor/', methods=['GET'])
@roles_required('admin')
def get_all_vendors():
    """
    Get all vendors with filtering, search, and pagination
    Query params:
    - page: page number (default: 1)
    - per_page: items per page (default: 20, max: 100)
    - search: search term for business name, email, phone
    - business_type: filter by business type
    - is_verified: filter by verification status (true/false)
    - is_active: filter by active status (true/false)
    - city: filter by city
    - min_rating: minimum average rating
    - sort_by: field to sort by (created_at, business_name, average_rating)
    - sort_order: asc or desc (default: desc)
    """
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Build query
        query = Vendor.query.join(User, Vendor.user_id == User.id)
        
        # Search filter
        search = request.args.get('search', '').strip()
        if search:
            search_filter = or_(
                Vendor.business_name.ilike(f'%{search}%'),
                Vendor.contact_email.ilike(f'%{search}%'),
                Vendor.contact_phone.ilike(f'%{search}%'),
                Vendor.city.ilike(f'%{search}%'),
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        # Business type filter
        business_type = request.args.get('business_type', '').strip()
        if business_type:
            query = query.filter(Vendor.business_type == business_type)
        
        # Verification status filter
        is_verified = request.args.get('is_verified')
        if is_verified is not None:
            is_verified_bool = is_verified.lower() == 'true'
            query = query.filter(Vendor.is_verified == is_verified_bool)
        
        # Active status filter
        is_active = request.args.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            query = query.filter(Vendor.is_active == is_active_bool)
        
        # City filter
        city = request.args.get('city', '').strip()
        if city:
            query = query.filter(Vendor.city.ilike(f'%{city}%'))
        
        # Rating filter
        min_rating = request.args.get('min_rating', type=float)
        if min_rating is not None:
            query = query.filter(Vendor.average_rating >= min_rating)
        
        # Sorting
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        valid_sort_fields = {
            'created_at': Vendor.created_at,
            'business_name': Vendor.business_name,
            'average_rating': Vendor.average_rating,
            'total_reviews': Vendor.total_reviews
        }
        
        sort_field = valid_sort_fields.get(sort_by, Vendor.created_at)
        if sort_order == 'asc':
            query = query.order_by(sort_field.asc())
        else:
            query = query.order_by(sort_field.desc())
        
        # Execute pagination
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Serialize results
        vendors = [{
            **vendor.serialize(),
            'user': vendor.user.serialize() if vendor.user else None,
            'total_bookings': vendor.service_bookings.count(),
            'active_bookings': vendor.service_bookings.filter_by(status='confirmed').count()
        } for vendor in pagination.items]
        
        # Get statistics
        total_vendors = Vendor.query.count()
        verified_vendors = Vendor.query.filter_by(is_verified=True).count()
        active_vendors = Vendor.query.filter_by(is_active=True).count()
        
        return jsonify({
            'success': True,
            'data': {
                'vendors': vendors,
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total_pages': pagination.pages,
                    'total_items': pagination.total,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                },
                'statistics': {
                    'total_vendors': total_vendors,
                    'verified_vendors': verified_vendors,
                    'active_vendors': active_vendors,
                    'unverified_vendors': total_vendors - verified_vendors
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching vendors: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to fetch vendors',
            'message': str(e) if current_app.debug else 'An error occurred'
        }), 500


# ==================== VENDOR DETAILS ====================

@admin_vendor_bp.route('/admin/vendor/<int:vendor_id>', methods=['GET'])
@roles_required('admin')
def get_vendor_details(vendor_id):
    """Get detailed information about a specific vendor"""
    try:
        vendor = Vendor.query.get(vendor_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'error': 'Vendor not found'
            }), 404
        
        # Get vendor documents
        documents = Document.get_vendor_documents(vendor_id)
        
        # Get bookings statistics
        total_bookings = vendor.service_bookings.count()
        completed_bookings = vendor.service_bookings.filter_by(status='completed').count()
        cancelled_bookings = vendor.service_bookings.filter_by(status='cancelled').count()
        
        # Get recent bookings
        recent_bookings = vendor.service_bookings.order_by(
            ServiceBooking.created_at.desc()
        ).limit(10).all()
        
        # Get reviews
        reviews = Review.query.filter_by(
            vendor_id=vendor_id,
            is_published=True
        ).order_by(Review.created_at.desc()).limit(10).all()
        
        # Get activity logs
        activity_logs = ActivityLog.get_entity_activity('vendor', vendor_id, limit=20)
        
        # Calculate revenue statistics
        from sqlalchemy import func
        from app.models import ServicePayment
        
        revenue_stats = db.session.query(
            func.sum(ServicePayment.amount).label('total_revenue'),
            func.count(ServicePayment.id).label('payment_count')
        ).filter(
            ServicePayment.vendor_id == vendor_id,
            ServicePayment.status == 'completed'
        ).first()
        
        vendor_data = {
            **vendor.serialize(),
            'user': vendor.user.serialize(include_sensitive=True) if vendor.user else None,
            'documents': [doc.serialize() for doc in documents],
            'statistics': {
                'total_bookings': total_bookings,
                'completed_bookings': completed_bookings,
                'cancelled_bookings': cancelled_bookings,
                'active_bookings': total_bookings - completed_bookings - cancelled_bookings,
                'total_revenue': float(revenue_stats.total_revenue) if revenue_stats.total_revenue else 0,
                'payment_count': revenue_stats.payment_count or 0
            },
            'recent_bookings': [booking.serialize() for booking in recent_bookings],
            'reviews': [review.serialize() for review in reviews],
            'activity_logs': [log.serialize() for log in activity_logs]
        }
        
        return jsonify({
            'success': True,
            'data': vendor_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching vendor {vendor_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to fetch vendor details',
            'message': str(e) if current_app.debug else 'An error occurred'
        }), 500


# ==================== VERIFY/REJECT VENDOR ====================

@admin_vendor_bp.route('/admin/vendor/<int:vendor_id>/verify', methods=['POST'])
@roles_required('admin')
def verify_vendor(vendor_id):
    """Verify a vendor"""
    try:
        vendor = Vendor.query.get(vendor_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'error': 'Vendor not found'
            }), 404
        
        if vendor.is_verified:
            return jsonify({
                'success': False,
                'error': 'Vendor is already verified'
            }), 400
        
        data = request.get_json() or {}
        notes = data.get('notes', '')
        
        # Update vendor
        vendor.is_verified = True
        vendor.is_active = True
        
        db.session.commit()
        
        # Log action
        log_admin_action(
            action='vendor_verified',
            entity_type='vendor',
            entity_id=vendor_id,
            description=f"Vendor '{vendor.business_name}' verified by admin. Notes: {notes}"
        )
        
        # TODO: Send notification to vendor
        # send_vendor_verification_email(vendor)
        
        current_app.logger.info(f"Vendor {vendor_id} verified by admin {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Vendor verified successfully',
            'data': vendor.serialize()
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error verifying vendor {vendor_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'message': 'Failed to verify vendor'
        }), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error verifying vendor {vendor_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to verify vendor',
            'message': str(e) if current_app.debug else 'An error occurred'
        }), 500


@admin_vendor_bp.route('/admin/vendor/<int:vendor_id>/reject', methods=['POST'])
@roles_required('admin')
def reject_vendor(vendor_id):
    """Reject a vendor verification"""
    try:
        vendor = Vendor.query.get(vendor_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'error': 'Vendor not found'
            }), 404
        
        data = request.get_json()
        if not data or 'reason' not in data:
            return jsonify({
                'success': False,
                'error': 'Rejection reason is required'
            }), 400
        
        reason = data['reason'].strip()
        if not reason:
            return jsonify({
                'success': False,
                'error': 'Rejection reason cannot be empty'
            }), 400
        
        # Update vendor
        vendor.is_verified = False
        vendor.is_active = False
        
        db.session.commit()
        
        # Log action
        log_admin_action(
            action='vendor_rejected',
            entity_type='vendor',
            entity_id=vendor_id,
            description=f"Vendor '{vendor.business_name}' verification rejected. Reason: {reason}"
        )
        
        # TODO: Send notification to vendor with rejection reason
        # send_vendor_rejection_email(vendor, reason)
        
        current_app.logger.info(f"Vendor {vendor_id} rejected by admin {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Vendor verification rejected',
            'data': vendor.serialize()
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error rejecting vendor {vendor_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Database error occurred',
            'message': 'Failed to reject vendor'
        }), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error rejecting vendor {vendor_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to reject vendor',
            'message': str(e) if current_app.debug else 'An error occurred'
        }), 500


# ==================== ACTIVATE/DEACTIVATE VENDOR ====================

@admin_vendor_bp.route('/admin/vendor/<int:vendor_id>/activate', methods=['POST'])
@roles_required('admin')
def activate_vendor(vendor_id):
    """Activate a vendor"""
    try:
        vendor = Vendor.query.get(vendor_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'error': 'Vendor not found'
            }), 404
        
        if vendor.is_active:
            return jsonify({
                'success': False,
                'error': 'Vendor is already active'
            }), 400
        
        if not vendor.is_verified:
            return jsonify({
                'success': False,
                'error': 'Cannot activate unverified vendor'
            }), 400
        
        data = request.get_json() or {}
        notes = data.get('notes', '')
        
        vendor.is_active = True
        db.session.commit()
        
        log_admin_action(
            action='vendor_activated',
            entity_type='vendor',
            entity_id=vendor_id,
            description=f"Vendor '{vendor.business_name}' activated. Notes: {notes}"
        )
        
        current_app.logger.info(f"Vendor {vendor_id} activated by admin {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Vendor activated successfully',
            'data': vendor.serialize()
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error activating vendor {vendor_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Database error occurred'
        }), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error activating vendor {vendor_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to activate vendor'
        }), 500


@admin_vendor_bp.route('/admin/vendor/<int:vendor_id>/deactivate', methods=['POST'])
@roles_required('admin')
def deactivate_vendor(vendor_id):
    """Deactivate a vendor"""
    try:
        vendor = Vendor.query.get(vendor_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'error': 'Vendor not found'
            }), 404
        
        if not vendor.is_active:
            return jsonify({
                'success': False,
                'error': 'Vendor is already inactive'
            }), 400
        
        data = request.get_json()
        if not data or 'reason' not in data:
            return jsonify({
                'success': False,
                'error': 'Deactivation reason is required'
            }), 400
        
        reason = data['reason'].strip()
        if not reason:
            return jsonify({
                'success': False,
                'error': 'Deactivation reason cannot be empty'
            }), 400
        
        # Check for active bookings
        active_bookings = vendor.service_bookings.filter(
            ServiceBooking.status.in_(['pending', 'confirmed', 'in_progress'])
        ).count()
        
        if active_bookings > 0:
            force = data.get('force', False)
            if not force:
                return jsonify({
                    'success': False,
                    'error': 'Vendor has active bookings',
                    'details': {
                        'active_bookings': active_bookings,
                        'message': 'Set force=true to deactivate anyway'
                    }
                }), 400
        
        vendor.is_active = False
        db.session.commit()
        
        log_admin_action(
            action='vendor_deactivated',
            entity_type='vendor',
            entity_id=vendor_id,
            description=f"Vendor '{vendor.business_name}' deactivated. Reason: {reason}"
        )
        
        # TODO: Send notification to vendor and affected trips
        # notify_vendor_deactivation(vendor, reason)
        
        current_app.logger.info(f"Vendor {vendor_id} deactivated by admin {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Vendor deactivated successfully',
            'data': vendor.serialize()
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error deactivating vendor {vendor_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Database error occurred'
        }), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deactivating vendor {vendor_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to deactivate vendor'
        }), 500


# ==================== EDIT VENDOR PROFILE ====================

@admin_vendor_bp.route('/admin/vendor/<int:vendor_id>', methods=['PUT', 'PATCH'])
@roles_required('admin')
def update_vendor(vendor_id):
    """Update vendor profile"""
    try:
        vendor = Vendor.query.get(vendor_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'error': 'Vendor not found'
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Store old values for logging
        old_values = {}
        new_values = {}
        
        # Updatable fields
        updatable_fields = {
            'business_name': str,
            'business_type': str,
            'description': str,
            'contact_email': str,
            'contact_phone': str,
            'website': str,
            'address_line1': str,
            'address_line2': str,
            'city': str,
            'state': str,
            'postal_code': str,
            'country': str,
            'license_number': str,
            'insurance_details': str,
            'capacity': int,
            'specializations': list,
            'base_price': (int, float),
            'price_per_person': (int, float),
            'pricing_notes': str
        }
        
        # Validate and update fields
        for field, field_type in updatable_fields.items():
            if field in data:
                value = data[field]
                
                # Type validation
                if value is not None and not isinstance(value, field_type):
                    return jsonify({
                        'success': False,
                        'error': f'Invalid type for field {field}'
                    }), 400
                
                # Email validation
                if field == 'contact_email' and value:
                    if not validate_email(value):
                        return jsonify({
                            'success': False,
                            'error': 'Invalid email format'
                        }), 400
                
                # Phone validation
                if field == 'contact_phone' and value:
                    if not validate_phone(value):
                        return jsonify({
                            'success': False,
                            'error': 'Invalid phone format'
                        }), 400
                
                # Store old value
                old_values[field] = getattr(vendor, field)
                new_values[field] = value
                
                # Update field
                setattr(vendor, field, value)
        
        db.session.commit()
        
        # Log action
        log_admin_action(
            action='vendor_updated',
            entity_type='vendor',
            entity_id=vendor_id,
            description=f"Vendor '{vendor.business_name}' profile updated by admin"
        )
        
        ActivityLog.log_action(
            action='vendor_profile_updated',
            user_id=current_user.id,
            entity_type='vendor',
            entity_id=vendor_id,
            description=f"Admin updated vendor profile",
            category='admin',
            old_values=old_values,
            new_values=new_values
        )
        
        current_app.logger.info(f"Vendor {vendor_id} updated by admin {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Vendor profile updated successfully',
            'data': vendor.serialize()
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error updating vendor {vendor_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Database error occurred'
        }), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating vendor {vendor_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to update vendor'
        }), 500


# ==================== DELETE VENDOR ====================

@admin_vendor_bp.route('/admin/vendor/<int:vendor_id>', methods=['DELETE'])
@roles_required('admin')
def delete_vendor(vendor_id):
    """Delete a vendor (soft delete or permanent)"""
    try:
        vendor = Vendor.query.get(vendor_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'error': 'Vendor not found'
            }), 404
        
        data = request.get_json() or {}
        permanent = data.get('permanent', False)
        
        # Check for dependencies
        total_bookings = vendor.service_bookings.count()
        active_bookings = vendor.service_bookings.filter(
            ServiceBooking.status.in_(['pending', 'confirmed', 'in_progress'])
        ).count()
        
        if active_bookings > 0:
            return jsonify({
                'success': False,
                'error': 'Cannot delete vendor with active bookings',
                'details': {
                    'active_bookings': active_bookings,
                    'total_bookings': total_bookings
                }
            }), 400
        
        if permanent:
            # Permanent deletion (use with extreme caution)
            if total_bookings > 0:
                return jsonify({
                    'success': False,
                    'error': 'Cannot permanently delete vendor with booking history',
                    'details': {
                        'total_bookings': total_bookings,
                        'message': 'Use soft delete (deactivate) instead'
                    }
                }), 400
            
            vendor_name = vendor.business_name
            
            # Log before deletion
            log_admin_action(
                action='vendor_deleted_permanent',
                entity_type='vendor',
                entity_id=vendor_id,
                description=f"Vendor '{vendor_name}' permanently deleted by admin"
            )
            
            db.session.delete(vendor)
            db.session.commit()
            
            current_app.logger.warning(f"Vendor {vendor_id} permanently deleted by admin {current_user.id}")
            
            return jsonify({
                'success': True,
                'message': 'Vendor permanently deleted',
                'data': {'vendor_id': vendor_id, 'vendor_name': vendor_name}
            }), 200
        else:
            # Soft delete (deactivate)
            vendor.is_active = False
            vendor.is_verified = False
            db.session.commit()
            
            log_admin_action(
                action='vendor_deleted_soft',
                entity_type='vendor',
                entity_id=vendor_id,
                description=f"Vendor '{vendor.business_name}' soft deleted (deactivated)"
            )
            
            current_app.logger.info(f"Vendor {vendor_id} soft deleted by admin {current_user.id}")
            
            return jsonify({
                'success': True,
                'message': 'Vendor deactivated successfully',
                'data': vendor.serialize()
            }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error deleting vendor {vendor_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Database error occurred'
        }), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting vendor {vendor_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to delete vendor'
        }), 500


# ==================== VENDOR DOCUMENTS ====================

@admin_vendor_bp.route('/admin/vendor/<int:vendor_id>/documents', methods=['GET'])
@roles_required('admin')
def get_vendor_documents(vendor_id):
    """Get all documents for a vendor"""
    try:
        vendor = Vendor.query.get(vendor_id)
        
        if not vendor:
            return jsonify({
                'success': False,
                'error': 'Vendor not found'
            }), 404
        
        document_type = request.args.get('document_type')
        documents = Document.get_vendor_documents(vendor_id, document_type)
        
        return jsonify({
            'success': True,
            'data': {
                'documents': [doc.serialize() for doc in documents],
                'total': len(documents)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching documents for vendor {vendor_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to fetch documents'
        }), 500


@admin_vendor_bp.route('/admin/vendor/<int:vendor_id>/documents/<int:document_id>/verify', methods=['POST'])
@roles_required('admin')
def verify_vendor_document(vendor_id, document_id):
    """Verify a vendor document"""
    try:
        vendor = Vendor.query.get(vendor_id)
        if not vendor:
            return jsonify({
                'success': False,
                'error': 'Vendor not found'
            }), 404
        
        document = Document.query.filter_by(
            id=document_id,
            vendor_id=vendor_id
        ).first()
        
        if not document:
            return jsonify({
                'success': False,
                'error': 'Document not found'
            }), 404
        
        if document.is_verified:
            return jsonify({
                'success': False,
                'error': 'Document is already verified'
            }), 400
        
        data = request.get_json() or {}
        notes = data.get('notes', '')
        
        document.verify_document(current_user.id)
        
        log_admin_action(
            action='vendor_document_verified',
            entity_type='document',
            entity_id=document_id,
            description=f"Document '{document.title}' verified for vendor '{vendor.business_name}'. Notes: {notes}"
        )
        
        current_app.logger.info(f"Document {document_id} verified for vendor {vendor_id} by admin {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Document verified successfully',
            'data': document.serialize()
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error verifying document {document_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Database error occurred'
        }), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error verifying vendor {vendor_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to verify vendor',
            'message': str(e) if current_app.debug else 'An error occurred'
        }), 500
    
@admin_vendor_bp.route('/admin/vendor/<int:vendor_id>/documents/<int:document_id>/reject', methods=['POST'])
@roles_required('admin')
def reject_vendor_document(vendor_id, document_id):
    """Reject a vendor document"""
    try:
        vendor = Vendor.query.get(vendor_id)
        if not vendor:
            return jsonify({
                'success': False,
                'error': 'Vendor not found'
            }), 404
        
        document = Document.query.filter_by(
            id=document_id,
            vendor_id=vendor_id
        ).first()
        
        if not document:
            return jsonify({
                'success': False,
                'error': 'Document not found'
            }), 404
        
        data = request.get_json()
        if not data or 'reason' not in data:
            return jsonify({
                'success': False,
                'error': 'Rejection reason is required'
            }), 400
        
        reason = data['reason'].strip()
        if not reason:
            return jsonify({
                'success': False,
                'error': 'Rejection reason cannot be empty'
            }), 400
        
        # Add rejection note to document
        document.notes = f"[REJECTED by Admin {current_user.full_name}] {reason}"
        document.is_verified = False
        document.deactivate()
        
        db.session.commit()
        
        log_admin_action(
            action='vendor_document_rejected',
            entity_type='document',
            entity_id=document_id,
            description=f"Document '{document.title}' rejected for vendor '{vendor.business_name}'. Reason: {reason}"
        )
        
        # TODO: Send notification to vendor
        # notify_vendor_document_rejection(vendor, document, reason)
        
        current_app.logger.info(f"Document {document_id} rejected for vendor {vendor_id} by admin {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Document rejected successfully',
            'data': document.serialize()
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error rejecting document {document_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Database error occurred'
        }), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error rejecting document {document_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to reject document'
        }), 500


@admin_vendor_bp.route('/admin/vendor/<int:vendor_id>/documents/<int:document_id>', methods=['DELETE'])
@roles_required('admin')
def delete_vendor_document(vendor_id, document_id):
    """Delete a vendor document"""
    try:
        vendor = Vendor.query.get(vendor_id)
        if not vendor:
            return jsonify({
                'success': False,
                'error': 'Vendor not found'
            }), 404
        
        document = Document.query.filter_by(
            id=document_id,
            vendor_id=vendor_id
        ).first()
        
        if not document:
            return jsonify({
                'success': False,
                'error': 'Document not found'
            }), 404
        
        document_title = document.title
        
        # Deactivate instead of permanent delete
        document.deactivate()
        db.session.commit()
        
        log_admin_action(
            action='vendor_document_deleted',
            entity_type='document',
            entity_id=document_id,
            description=f"Document '{document_title}' deleted for vendor '{vendor.business_name}'"
        )
        
        current_app.logger.info(f"Document {document_id} deleted for vendor {vendor_id} by admin {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Document deleted successfully'
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error deleting document {document_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Database error occurred'
        }), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting document {document_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to delete document'
        }), 500


# ==================== VENDOR ANALYTICS & REPORTS ====================

@admin_vendor_bp.route('/admin/vendor/analytics', methods=['GET'])
@roles_required('admin')
def get_vendor_analytics():
    """Get comprehensive vendor analytics"""
    try:
        from sqlalchemy import func
        from app.models import ServicePayment
        from datetime import datetime, timedelta
        
        # Date range filters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        else:
            end_date = datetime.now()
        
        # Overall statistics
        total_vendors = Vendor.query.count()
        verified_vendors = Vendor.query.filter_by(is_verified=True).count()
        active_vendors = Vendor.query.filter_by(is_active=True).count()
        pending_verification = Vendor.query.filter_by(is_verified=False, is_active=True).count()
        
        # Vendors by business type
        vendors_by_type = db.session.query(
            Vendor.business_type,
            func.count(Vendor.id).label('count')
        ).group_by(Vendor.business_type).all()
        
        # Top rated vendors
        top_vendors = Vendor.query.filter(
            Vendor.is_active == True,
            Vendor.total_reviews > 0
        ).order_by(Vendor.average_rating.desc()).limit(10).all()
        
        # Recent registrations
        recent_vendors = Vendor.query.filter(
            Vendor.created_at >= start_date,
            Vendor.created_at <= end_date
        ).count()
        
        # Booking statistics
        total_bookings = ServiceBooking.query.join(Vendor).filter(
            ServiceBooking.booking_date >= start_date,
            ServiceBooking.booking_date <= end_date
        ).count()
        
        # Revenue statistics
        revenue_stats = db.session.query(
            func.sum(ServicePayment.amount).label('total_revenue'),
            func.count(ServicePayment.id).label('payment_count')
        ).filter(
            ServicePayment.status == 'completed',
            ServicePayment.created_at >= start_date,
            ServicePayment.created_at <= end_date
        ).first()
        
        # Vendors by location
        vendors_by_city = db.session.query(
            Vendor.city,
            func.count(Vendor.id).label('count')
        ).filter(
            Vendor.city.isnot(None),
            Vendor.is_active == True
        ).group_by(Vendor.city).order_by(func.count(Vendor.id).desc()).limit(10).all()
        
        # Document verification status
        total_documents = Document.query.filter(
            Document.vendor_id.isnot(None),
            Document.is_active == True
        ).count()
        
        verified_documents = Document.query.filter(
            Document.vendor_id.isnot(None),
            Document.is_verified == True,
            Document.is_active == True
        ).count()
        
        return jsonify({
            'success': True,
            'data': {
                'overview': {
                    'total_vendors': total_vendors,
                    'verified_vendors': verified_vendors,
                    'active_vendors': active_vendors,
                    'pending_verification': pending_verification,
                    'inactive_vendors': total_vendors - active_vendors,
                    'verification_rate': round((verified_vendors / total_vendors * 100), 2) if total_vendors > 0 else 0
                },
                'period_stats': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'new_vendors': recent_vendors,
                    'total_bookings': total_bookings,
                    'total_revenue': float(revenue_stats.total_revenue) if revenue_stats.total_revenue else 0,
                    'payment_count': revenue_stats.payment_count or 0
                },
                'vendors_by_type': [
                    {'type': vtype or 'Unspecified', 'count': count}
                    for vtype, count in vendors_by_type
                ],
                'top_vendors': [
                    {
                        'id': v.id,
                        'business_name': v.business_name,
                        'average_rating': v.average_rating,
                        'total_reviews': v.total_reviews,
                        'business_type': v.business_type
                    }
                    for v in top_vendors
                ],
                'vendors_by_location': [
                    {'city': city, 'count': count}
                    for city, count in vendors_by_city
                ],
                'documents': {
                    'total_documents': total_documents,
                    'verified_documents': verified_documents,
                    'pending_verification': total_documents - verified_documents,
                    'verification_rate': round((verified_documents / total_documents * 100), 2) if total_documents > 0 else 0
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error generating vendor analytics: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to generate analytics'
        }), 500


# ==================== BULK OPERATIONS ====================

@admin_vendor_bp.route('/admin/vendor/bulk/verify', methods=['POST'])
@roles_required('admin')
def bulk_verify_vendors():
    """Bulk verify multiple vendors"""
    try:
        data = request.get_json()
        if not data or 'vendor_ids' not in data:
            return jsonify({
                'success': False,
                'error': 'vendor_ids array is required'
            }), 400
        
        vendor_ids = data['vendor_ids']
        if not isinstance(vendor_ids, list) or len(vendor_ids) == 0:
            return jsonify({
                'success': False,
                'error': 'vendor_ids must be a non-empty array'
            }), 400
        
        notes = data.get('notes', '')
        
        success_count = 0
        failed_vendors = []
        
        for vendor_id in vendor_ids:
            try:
                vendor = Vendor.query.get(vendor_id)
                if vendor and not vendor.is_verified:
                    vendor.is_verified = True
                    vendor.is_active = True
                    success_count += 1
                    
                    log_admin_action(
                        action='vendor_verified_bulk',
                        entity_type='vendor',
                        entity_id=vendor_id,
                        description=f"Bulk verification: {notes}"
                    )
                elif not vendor:
                    failed_vendors.append({'id': vendor_id, 'reason': 'Not found'})
                else:
                    failed_vendors.append({'id': vendor_id, 'reason': 'Already verified'})
            except Exception as e:
                failed_vendors.append({'id': vendor_id, 'reason': str(e)})
        
        db.session.commit()
        
        current_app.logger.info(f"Bulk verified {success_count} vendors by admin {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully verified {success_count} vendor(s)',
            'data': {
                'success_count': success_count,
                'failed_count': len(failed_vendors),
                'failed_vendors': failed_vendors
            }
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in bulk verify: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Database error occurred'
        }), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in bulk verify: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to bulk verify vendors'
        }), 500


@admin_vendor_bp.route('/admin/vendor/bulk/deactivate', methods=['POST'])
@roles_required('admin')
def bulk_deactivate_vendors():
    """Bulk deactivate multiple vendors"""
    try:
        data = request.get_json()
        if not data or 'vendor_ids' not in data:
            return jsonify({
                'success': False,
                'error': 'vendor_ids array is required'
            }), 400
        
        vendor_ids = data['vendor_ids']
        if not isinstance(vendor_ids, list) or len(vendor_ids) == 0:
            return jsonify({
                'success': False,
                'error': 'vendor_ids must be a non-empty array'
            }), 400
        
        reason = data.get('reason', 'Bulk deactivation by admin')
        
        success_count = 0
        failed_vendors = []
        
        for vendor_id in vendor_ids:
            try:
                vendor = Vendor.query.get(vendor_id)
                if vendor and vendor.is_active:
                    # Check for active bookings
                    active_bookings = vendor.service_bookings.filter(
                        ServiceBooking.status.in_(['pending', 'confirmed', 'in_progress'])
                    ).count()
                    
                    if active_bookings > 0:
                        failed_vendors.append({
                            'id': vendor_id,
                            'reason': f'Has {active_bookings} active booking(s)'
                        })
                        continue
                    
                    vendor.is_active = False
                    success_count += 1
                    
                    log_admin_action(
                        action='vendor_deactivated_bulk',
                        entity_type='vendor',
                        entity_id=vendor_id,
                        description=f"Bulk deactivation: {reason}"
                    )
                elif not vendor:
                    failed_vendors.append({'id': vendor_id, 'reason': 'Not found'})
                else:
                    failed_vendors.append({'id': vendor_id, 'reason': 'Already inactive'})
            except Exception as e:
                failed_vendors.append({'id': vendor_id, 'reason': str(e)})
        
        db.session.commit()
        
        current_app.logger.info(f"Bulk deactivated {success_count} vendors by admin {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully deactivated {success_count} vendor(s)',
            'data': {
                'success_count': success_count,
                'failed_count': len(failed_vendors),
                'failed_vendors': failed_vendors
            }
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in bulk deactivate: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Database error occurred'
        }), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in bulk deactivate: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to bulk deactivate vendors'
        }), 500


# ==================== EXPORT ====================

@admin_vendor_bp.route('/admin/vendor/export', methods=['GET'])
@roles_required('admin')
def export_vendors():
    """Export vendor data to CSV"""
    try:
        import csv
        from io import StringIO
        from flask import make_response
        
        # Apply same filters as listing
        query = Vendor.query.join(User, Vendor.user_id == User.id)
        
        # Apply filters (reuse logic from get_all_vendors)
        search = request.args.get('search', '').strip()
        if search:
            search_filter = or_(
                Vendor.business_name.ilike(f'%{search}%'),
                Vendor.contact_email.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        business_type = request.args.get('business_type')
        if business_type:
            query = query.filter(Vendor.business_type == business_type)
        
        is_verified = request.args.get('is_verified')
        if is_verified is not None:
            query = query.filter(Vendor.is_verified == (is_verified.lower() == 'true'))
        
        is_active = request.args.get('is_active')
        if is_active is not None:
            query = query.filter(Vendor.is_active == (is_active.lower() == 'true'))
        
        vendors = query.all()
        
        # Create CSV
        si = StringIO()
        writer = csv.writer(si)
        
        # Headers
        writer.writerow([
            'ID', 'Business Name', 'Business Type', 'Contact Email', 
            'Contact Phone', 'City', 'State', 'Country', 'Is Verified',
            'Is Active', 'Average Rating', 'Total Reviews', 'Total Bookings',
            'Created At'
        ])
        
        # Data rows
        for vendor in vendors:
            writer.writerow([
                vendor.id,
                vendor.business_name,
                vendor.business_type or '',
                vendor.contact_email,
                vendor.contact_phone,
                vendor.city or '',
                vendor.state or '',
                vendor.country or '',
                'Yes' if vendor.is_verified else 'No',
                'Yes' if vendor.is_active else 'No',
                vendor.average_rating,
                vendor.total_reviews,
                vendor.service_bookings.count(),
                vendor.created_at.isoformat() if vendor.created_at else ''
            ])
        
        # Create response
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=vendors_export.csv"
        output.headers["Content-type"] = "text/csv"
        
        log_admin_action(
            action='vendors_exported',
            entity_type='vendor',
            entity_id=None,
            description=f"Exported {len(vendors)} vendor records"
        )
        
        return output
        
    except Exception as e:
        current_app.logger.error(f"Error exporting vendors: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to export vendors'
        }), 500