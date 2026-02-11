import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Case
from .ai_utils import analyze_case, search_similar_cases, generate_document

# ---------- CRUD дела ----------

def case_list(request):
    cases = Case.objects.all().order_by("-id")
    return render(request, "core/case_list.html", {"cases": cases})

def case_detail(request, pk):
    case = get_object_or_404(Case, pk=pk)
    return render(request, "core/case_detail.html", {"case": case})

def case_create(request):
    if request.method == "POST":
        title = request.POST.get("title")
        text = request.POST.get("text")
        Case.objects.create(title=title, text=text)
        return redirect("case_list")
    return render(request, "core/case_create.html")

def case_delete(request, pk):
    case = get_object_or_404(Case, pk=pk)
    case.delete()
    return redirect("case_list")

# ---------- ИИ-инструменты ----------

# ---------- Анализ юридического кейса ----------
def analyze_case_view(request):
    result = None

    if request.method == "POST":
        # Получаем текст дела из формы
        case_text = request.POST.get("case_text", "")
        if case_text.strip():  # проверяем, что не пусто
            # История для сессии (опционально)
            if "history_analyze" not in request.session:
                request.session["history_analyze"] = []
            history = request.session["history_analyze"]
            history.append(("user", case_text))

            # Анализ через ИИ
            result = analyze_case(case_text, history)

            history.append(("assistant", result))
            request.session["history_analyze"] = history
            request.session.modified = True

    return render(request, "core/analyze_case.html", {"result": result})


@csrf_exempt
def search_cases_view(request):
    if "history_search" not in request.session:
        request.session["history_search"] = []

    results = []
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message", "")
        history = request.session["history_search"]
        history.append(("user", user_message))

        results = search_similar_cases(user_message, history)
        history.append(("assistant", str(results)))
        request.session["history_search"] = history
        request.session.modified = True

        return JsonResponse({"reply": results})

    return render(request, "core/search_cases.html", {"results": results})



def generate_document_view(request):
    if "history_docs" not in request.session:
        request.session["history_docs"] = []

    generated_text = None

    if request.method == "POST":
        user_message = request.POST.get("message", "")
        history = request.session["history_docs"]

        history.append(("user", user_message))
        generated_text = generate_document(user_message, history)
        history.append(("assistant", generated_text))

        request.session["history_docs"] = history
        request.session.modified = True

    return render(request, "core/generate_document.html", {"generated_text": generated_text})
