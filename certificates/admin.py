from django.contrib import admin

from certificates.models import ParseFile, ParseSession


@admin.register(ParseFile)
class ParseFileAdmin(admin.ModelAdmin):
    pass


@admin.register(ParseSession)
class ParseSessionAdmin(admin.ModelAdmin):
    pass
