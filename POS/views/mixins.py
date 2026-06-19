"""
Base View Mixins for consistent pagination, select_related,
and role-based queryset filtering across all POS views.

Usage:
    class ProductListView(EmployeeListMixin, generics.ListCreateAPIView):
        queryset = Product.objects.all()
        serializer_class = ProductListSerializer
        select_related_fields = ['category', 'brand']
"""

from rest_framework import generics
from ..paginations import MyPageNumberPagination


class EmployeeListMixin:
    """
    Mixin for views that list items visible to employees.
    - Paginates list responses
    - Allows select_related/prefetch_related optimization
    """
    pagination_class = MyPageNumberPagination


class PublicListMixin:
    """
    Mixin for publicly-readable list views.
    - Paginates list responses
    """
    pagination_class = MyPageNumberPagination


class OwnerManagerListMixin:
    """
    Mixin for views restricted to owner/manager.
    - Paginates list responses
    """
    pagination_class = MyPageNumberPagination


class EmployeeFilteredListMixin(EmployeeListMixin):
    """
    Mixin for views where customers see only their own records,
    while employees see all records.
    - Paginates list responses
    - Filters by 'user' field for non-employees
    """

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        # Apply select_related if defined on the view
        if hasattr(self, 'select_related_fields') and self.select_related_fields:
            qs = qs.select_related(*self.select_related_fields)
        if hasattr(self, 'prefetch_related_fields') and self.prefetch_related_fields:
            qs = qs.prefetch_related(*self.prefetch_related_fields)

        # Employee roles see all; customers see only their own
        if user.is_authenticated and (
            user.role in ('owner', 'manager', 'salesman')
            or user.is_superuser
            or user.role == 'admin'
        ):
            return qs

        # Filter by the 'user' FK field for customers
        user_field = getattr(self, 'user_filter_field', 'user')
        return qs.filter(**{user_field: user})