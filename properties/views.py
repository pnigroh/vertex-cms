from django.views.generic import ListView, DetailView
from django.utils.translation import get_language

from .models import Property


class PropertyListView(ListView):
    model = Property
    template_name = "properties/property_list.html"
    context_object_name = "properties"
    paginate_by = 12

    def get_queryset(self):
        return (
            Property.objects.filter(is_published=True)
            .translated(get_language())
            .select_related("location")
            .prefetch_related("images", "amenities")
            .order_by("-is_featured", "-created_at")
        )


class PropertyDetailView(DetailView):
    model = Property
    template_name = "properties/property_detail.html"
    context_object_name = "property"

    def get_queryset(self):
        return (
            Property.objects.filter(is_published=True)
            .translated(get_language())
            .select_related("location")
            .prefetch_related("images", "amenities__category")
        )

    def get_object(self, queryset=None):
        queryset = queryset or self.get_queryset()
        return queryset.get(translations__slug=self.kwargs["slug"])
