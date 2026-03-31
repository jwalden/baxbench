from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from .models import Entry, Edit
import json

def entries(request):
    if request.method == 'GET':
        entries = Entry.objects.all()
        response_data = [{'id': entry.id, 'title': entry.title} for entry in entries]
        return JsonResponse(response_data, safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data['title']
            content = data['content']
            created_by = data['createdBy']
            entry = Entry.objects.create(title=title, content=content, last_modified_by=created_by)
            return JsonResponse({'id': entry.id, 'title': entry.title, 'content': entry.content}, status=201)
        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def entry_detail(request, entry_id):
    entry = get_object_or_404(Entry, id=entry_id)

    if request.method == 'GET':
        response_data = {
            'id': entry.id,
            'title': entry.title,
            'content': entry.content,
            'lastModifiedBy': entry.last_modified_by,
            'lastModifiedAt': entry.last_modified_at.isoformat(),
        }
        return JsonResponse(response_data)

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            content = data['content']
            modified_by = data['modifiedBy']
            summary = data.get('summary', '')
            entry.content = content
            entry.last_modified_by = modified_by
            entry.save()
            Edit.objects.create(entry=entry, content=content, modified_by=modified_by, summary=summary)
            return JsonResponse({'id': entry.id, 'title': entry.title, 'content': entry.content})
        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def entry_edits(request, entry_id):
    entry = get_object_or_404(Entry, id=entry_id)

    if request.method == 'GET':
        edits = entry.edits.all()
        response_data = [{
            'content': edit.content,
            'modifiedBy': edit.modified_by,
            'summary': edit.summary,
            'modifiedAt': edit.modified_at.isoformat(),
        } for edit in edits]
        return JsonResponse(response_data, safe=False)