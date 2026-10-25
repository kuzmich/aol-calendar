from django.contrib import admin

from .models import Event, EventDay, EventType, Place, Status, Teacher


class EventDayInline(admin.TabularInline):
    model = EventDay
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['type', 'start_date', 'end_date', 'place', 'status', 'num_payments', 'teacher_names']
    list_filter = ['type', 'status', 'place']
    list_select_related = ['type', 'place', 'status']
    date_hierarchy = 'start_date'
    search_fields = ['type__name', 'place__name', 'teachers__last_name', 'admin_id']
    filter_horizontal = ['teachers']
    inlines = [EventDayInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('teachers')

    @admin.display(description='Учителя')
    def teacher_names(self, obj):
        return ', '.join(str(t) for t in obj.teachers.all())


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name', 'slug']


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name']
    search_fields = ['last_name', 'first_name']


@admin.register(Place, Status)
class NameAdmin(admin.ModelAdmin):
    search_fields = ['name']
