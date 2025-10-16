# opportunities/filters.py
import django_filters
from django.db.models import Q
from django.utils import timezone
from ..models import Opportunity

class OpportunityFilter(django_filters.FilterSet):
    """Filtres avancés pour les opportunités"""
    
    category = django_filters.CharFilter(field_name='category__slug')
    type = django_filters.CharFilter(field_name='opportunity_type')
    location = django_filters.CharFilter(method='filter_location')
    deadline_after = django_filters.DateTimeFilter(field_name='deadline', lookup_expr='gte')
    deadline_before = django_filters.DateTimeFilter(field_name='deadline', lookup_expr='lte')
    active = django_filters.BooleanFilter(method='filter_active')
    expired = django_filters.BooleanFilter(method='filter_expired')
    organization = django_filters.CharFilter(field_name='organization', lookup_expr='icontains')
    education_level = django_filters.CharFilter(field_name='education_level', lookup_expr='icontains')
    tags = django_filters.CharFilter(method='filter_tags')
    
    class Meta:
        model = Opportunity
        fields = ['category', 'type', 'location', 'deadline_after', 'deadline_before', 
                 'active', 'expired', 'organization', 'education_level', 'tags', 'is_remote']
    
    def filter_location(self, queryset, name, value):
        """Filtrer par localisation (peut être partielle)"""
        return queryset.filter(location__icontains=value)
    
    def filter_active(self, queryset, name, value):
        """Filtrer les opportunités actives (non expirées)"""
        now = timezone.now()
        if value:  # Si True, retourner uniquement les actives
            return queryset.filter(
                Q(deadline__isnull=True) | Q(deadline__gt=now),
                status='published'
            )
        return queryset  # Sinon, retourner toutes
    
    def filter_expired(self, queryset, name, value):
        """Filtrer les opportunités expirées"""
        now = timezone.now()
        if value:  # Si True, retourner uniquement les expirées
            return queryset.filter(
                deadline__lt=now,
                status='published'
            )
        return queryset  # Sinon, retourner toutes
    
    def filter_tags(self, queryset, name, value):
        """Filtrer par tags (recherche de sous-chaînes)"""
        tags = [tag.strip() for tag in value.split(',')]
        q_objects = Q()
        
        for tag in tags:
            q_objects |= Q(tags__icontains=tag)
        
        return queryset.filter(q_objects)