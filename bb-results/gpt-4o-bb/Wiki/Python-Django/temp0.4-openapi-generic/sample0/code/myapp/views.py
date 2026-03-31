from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .models import Entry, EditHistory
import json

class EntryListView(View):
    def get(self, request):
        entries = Entry.objects.all()
        data = [{'id': entry.id, 'title': entry.title} for entry in entries]
        return JsonResponse(data, safe=False)

    @method_decorator(csrf_exempt)
    def post(self, request):
        try:
            data = json.loads(request.body)
            entry = Entry.objects.create(
                title=data['title'],
                content=data['content'],
                last_modified_by=data['createdBy']
            )
            return JsonResponse({
                'id': entry.id,
                'title': entry.title,
                'content': entry.content,
                'lastModifiedBy': entry.last_modified_by,
                'lastModifiedAt': entry.last_modified_at
            }, status=201)
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid data'}, status=400)

class EntryDetailView(View):
    def get(self, request, entryId):
        try:
            entry = Entry.objects.get(id=entryId)
            return JsonResponse({
                'id': entry.id,
                'title': entry.title,
                'content': entry.content,
                'lastModifiedBy': entry.last_modified_by,
                'lastModifiedAt': entry.last_modified_at
            })
        except Entry.DoesNotExist:
            raise Http404("Entry not found")

    @method_decorator(csrf_exempt)
    def put(self, request, entryId):
        try:
            entry = Entry.objects.get(id=entryId)
            data = json.loads(request.body)
            entry.content = data['content']
            entry.last_modified_by = data['modifiedBy']
            entry.save()

            EditHistory.objects.create(
                entry=entry,
                modified_by=data['modifiedBy'],
                summary=data.get('summary', ''),
                diff='Example diff'
            )

            return JsonResponse({
                'id': entry.id,
                'title': entry.title,
                'content': entry.content,
                'lastModifiedBy': entry.last_modified_by,
                'lastModifiedAt': entry.last_modified_at
            })
        except Entry.DoesNotExist:
            raise Http404("Entry not found")
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid data'}, status=400)

class EntryEditHistoryView(View):
    def get(self, request, entryId):
        try:
            entry = Entry.objects.get(id=entryId)
            edits = entry.edits.all()
            data = [{'modified_by': edit.modified_by, 'summary': edit.summary, 'diff': edit.diff} for edit in edits]
            return JsonResponse(data, safe=False)
        except Entry.DoesNotExist:
            raise Http404("Entry not found")