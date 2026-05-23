from django.http import JsonResponse

def health(request):
    return JsonResponse({
        "status": "ok",
        "service": "kpi",
        "version": "1.0"
    })
