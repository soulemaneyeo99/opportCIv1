# backend/formations/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Category, Formation, Enrollment
from .serializers import CategorySerializer, FormationListSerializer, FormationDetailSerializer, EnrollmentSerializer
from .permissions import IsEnrollmentOwner, IsFormationInstructor


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class FormationViewSet(viewsets.ModelViewSet):
    queryset = Formation.objects.all()
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_online', 'is_free', 'status']
    search_fields = ['title', 'description', 'instructor__username']
    ordering_fields = ['start_date', 'end_date', 'created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FormationDetailSerializer
        return FormationListSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'my_formations']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def enroll(self, request, slug=None):
        formation = self.get_object()

        if formation.is_full:
            return Response({"detail": "Cette formation est complète."}, status=status.HTTP_400_BAD_REQUEST)

        if Enrollment.objects.filter(user=request.user, formation=formation).exists():
            return Response({"detail": "Vous êtes déjà inscrit à cette formation."}, status=status.HTTP_400_BAD_REQUEST)

        enrollment = Enrollment.objects.create(user=request.user, formation=formation, status='pending')
        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_formations(self, request):
        enrollments = Enrollment.objects.filter(user=request.user)
        formations = [e.formation for e in enrollments]

        page = self.paginate_queryset(formations)
        serializer = self.get_serializer(page or formations, many=True)
        return self.get_paginated_response(serializer.data) if page else Response(serializer.data)


class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['formation', 'status']

    def get_queryset(self):
        user = self.request.user
        return Enrollment.objects.all() if user.is_staff else Enrollment.objects.filter(user=user)

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsEnrollmentOwner()]
        if self.action in ['list', 'create', 'provide_feedback']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def provide_feedback(self, request, pk=None):
        enrollment = self.get_object()

        if enrollment.user != request.user:
            return Response({"detail": "Non autorisé à laisser un avis."}, status=status.HTTP_403_FORBIDDEN)

        feedback = request.data.get('feedback')
        rating = request.data.get('rating')

        if feedback:
            enrollment.feedback = feedback

        if rating:
            try:
                rating_value = int(rating)
                if 1 <= rating_value <= 5:
                    enrollment.rating = rating_value
                else:
                    return Response({"detail": "La note doit être entre 1 et 5."}, status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                return Response({"detail": "La note doit être un entier."}, status=status.HTTP_400_BAD_REQUEST)

        enrollment.save()
        serializer = self.get_serializer(enrollment)
        return Response(serializer.data)
