from django.shortcuts import render

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from routes.models import Route
from .pdf_generator import generate_waybill
import os


def download_waybill(request, route_id):
    """Скачать путевой лист в PDF"""
    route = get_object_or_404(Route, id=route_id)
    
    try:
        filepath = generate_waybill(route.order, route)
        return FileResponse(open(filepath, 'rb'), as_attachment=True, filename=os.path.basename(filepath))
    except Exception as e:
        raise Http404(f"Ошибка генерации PDF: {e}")