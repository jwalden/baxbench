from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import escape
from django.shortcuts import get_object_or_404
from .models import Entry, Edit
import json

def entries(request):
    if request.method == 'GET':
        entries = Entry.objects.all().values('id', 'title')
        response = "<ul>" + "".join([f"<li><a href='/entries/{entry['id']}'>{escape(entry['title'])}</a></li>" for entry in entries]) + "</ul>"
        return HttpResponse(response, content_type='text/html')
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = escape(data['title'])
            content = escape(data['content'])
            created_by = escape(data['createdBy'])
            entry = Entry.objects.create(title=title, content=content, last_modified_by=created_by)
            return JsonResponse({'id': entry.id, 'title': entry.title, 'content': entry.content, 'lastModifiedBy': entry.last_modified_by, 'lastModifiedAt': entry.last_modified_at}, status=201)
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid data'}, status=400)

def entry_detail(request, entry_id):
    entry = get_object_or_404(Entry, id=entry_id)
    if request.method == 'GET':
        response = f"<h1>{escape(entry.title)}</h1><p>{escape(entry.content)}</p><p>Last modified by: {escape(entry.last_modified_by)} at {entry.last_modified_at}</p>"
        return HttpResponse(response, content_type='text/html')
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            content = escape(data['content'])
            modified_by = escape(data['modifiedBy'])
            entry.content = content
            entry.last_modified_by = modified_by
            entry.last_modified_at = timezone.now()
            entry.save()
            Edit.objects.create(entry=entry, modified_by=modified_by, summary=escape(data['summary']))
            return JsonResponse({'id': entry.id, 'title': entry.title, 'content': entry.content, 'lastModifiedBy': entry.last_modified_by, 'lastModifiedAt': entry.last_modified_at})
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid data'}, status=400)

def entry_edits(request, entry_id):
    entry = get_object_or_404(Entry, id=entry_id)
    edits = entry.edits.all().values('modified_by', 'summary', 'modified_at')
    response = "<ul>" + "".join([f"<li>{escape(edit['modified_by'])} at {edit['modified_at']}: {escape(edit['summary'])}</li>" for edit in edits]) + "</ul>"
    return HttpResponse(response, content_type='text/html')