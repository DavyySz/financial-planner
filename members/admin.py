from django.contrib import admin

from .models import Member, MemberAttribute, PasswordResetRequest, Transaction


class MemberAdmin(admin.ModelAdmin):
    list_display = ("firstname", "lastname", "user", "joined_date", "monthly_salary", "last_seen")


class MemberAttributeAdmin(admin.ModelAdmin):
    list_display = ("member", "category", "current_rate", "creation_date_of_the_category", "comment")


class TransactionAdmin(admin.ModelAdmin):
    list_display = ("attribute", "amount", "comment", "created")


admin.site.register(Member, MemberAdmin)
admin.site.register(MemberAttribute, MemberAttributeAdmin)
class PasswordResetRequestAdmin(admin.ModelAdmin):
    list_display = ("username", "user", "message", "created", "resolved", "resolved_at")
    list_filter = ("resolved",)


admin.site.register(Transaction, TransactionAdmin)
admin.site.register(PasswordResetRequest, PasswordResetRequestAdmin)
