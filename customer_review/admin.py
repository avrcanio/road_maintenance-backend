from django.contrib import admin

from .models import CustomerReview, CustomerReviewDecision, ReviewToken


@admin.register(CustomerReview)
class CustomerReviewAdmin(admin.ModelAdmin):
    list_display = (
        'work_item',
        'version',
        'status',
        'deadline',
        'closed_at',
        'created_at',
    )
    list_filter = ('status', 'created_at', 'deadline')
    search_fields = (
        'work_item__work_order__number',
        'work_item__operation_type__name',
    )
    autocomplete_fields = ('work_item',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(CustomerReviewDecision)
class CustomerReviewDecisionAdmin(admin.ModelAdmin):
    list_display = (
        'customer_review',
        'decided_by_user',
        'action',
        'decided_at',
        'ip_address',
    )
    list_filter = ('action', 'decided_at')
    search_fields = (
        'customer_review__work_item__work_order__number',
        'decided_by_user__username',
    )
    readonly_fields = ('decided_at',)
    ordering = ('-decided_at',)


@admin.register(ReviewToken)
class ReviewTokenAdmin(admin.ModelAdmin):
    list_display = (
        'customer_review',
        'user',
        'scope',
        'issued_at',
        'expires_at',
        'used_at',
        'revoked_at',
    )
    list_filter = ('scope', 'issued_at', 'expires_at')
    search_fields = (
        'customer_review__work_item__work_order__number',
        'user__username',
        'jti',
    )
    readonly_fields = ('issued_at', 'jti')
    ordering = ('-issued_at',)
